"""
FastAPI Backend para o Agente de QA Automatizado
Fornece endpoints REST e WebSocket para controlar o agente e receber logs em tempo real
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import sys
import os
import json
import tempfile
import uuid
import threading
from pathlib import Path

# Adicionar o diretório pai ao path para importar os módulos do agente
sys.path.append(str(Path(__file__).parent.parent))

from main import navegar_com_agente, obter_modelos_disponiveis, obter_modelo_carregado

app = FastAPI(title="Agente QA API", version="1.0.0")

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gerenciador de WebSocket para logs em tempo real
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Estado da execução
execution_state = {
    "is_running": False,
    "stop_requested": False,
    "current_task": None,
    "process": None,
}

# Modelos de dados
class AgentConfig(BaseModel):
    url: str
    max_passos: int = 10
    instrucoes: str = ""
    modelo: str = "openai/gpt-oss-20b"
    modo_extracao: str = "padrao"
    llm_config: dict = {
        "provider": "lmstudio_local",
        "url": "http://localhost:1234",
        "api_key": ""
    }

class LLMTestRequest(BaseModel):
    provider: str
    url: str
    api_key: Optional[str] = ""

# Endpoints

@app.get("/")
async def root():
    """Endpoint raiz - informações da API"""
    return {
        "name": "Agente QA API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "models": "/api/models",
            "start": "/api/agent/start",
            "stop": "/api/agent/stop",
            "status": "/api/agent/status",
            "logs": "/ws/logs"
        }
    }

@app.get("/api/models")
async def get_models():
    """Retorna lista de modelos disponíveis e o modelo carregado"""
    try:
        modelos = obter_modelos_disponiveis()
        modelo_carregado = obter_modelo_carregado()
        return {
            "success": True,
            "models": modelos,
            "loaded_model": modelo_carregado
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/test")
async def test_llm_connection(config: LLMTestRequest):
    """Testa conexão com o LLM"""
    import requests
    
    try:
        if config.provider in ["lmstudio_local", "ollama_local"]:
            test_url = f"{config.url}/v1/models" if config.provider == "lmstudio_local" else f"{config.url}/api/tags"
            response = requests.get(test_url, timeout=5)
            
            if response.status_code == 200:
                return {"success": True, "message": "Conexão estabelecida com sucesso"}
            else:
                return {"success": False, "message": f"Erro de conexão: Status {response.status_code}"}
                
        elif config.provider == "api_externa":
            headers = {"Authorization": f"Bearer {config.api_key}"}
            test_url = f"{config.url}/models"
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {"success": True, "message": "API conectada com sucesso"}
            else:
                return {"success": False, "message": f"API Key inválida: Status {response.status_code}"}
                
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Timeout na conexão"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Não foi possível conectar ao servidor"}
    except Exception as e:
        return {"success": False, "message": f"Erro: {str(e)}"}

@app.post("/api/agent/start")
async def start_agent(config: AgentConfig):
    """Inicia a execução do agente"""
    if execution_state["is_running"]:
        raise HTTPException(status_code=400, detail="Agente já está em execução")
    
    execution_state["is_running"] = True
    execution_state["stop_requested"] = False
    
    # Criar tarefa assíncrona para executar o agente
    async def run_agent():
        try:
            await manager.broadcast(f"🚀 Iniciando agente...\n")
            await manager.broadcast(f"📍 URL: {config.url}\n")
            await manager.broadcast(f"🔢 Max passos: {config.max_passos}\n")
            await manager.broadcast(f"🤖 Modelo: {config.modelo}\n")
            await manager.broadcast(f"🎯 Instruções: {config.instrucoes}\n")
            await manager.broadcast("-" * 60 + "\n")
            
            # Executar o agente em processo separado para evitar conflitos com asyncio
            import subprocess
            
            loop = asyncio.get_running_loop()

            def run_in_process(event_loop: asyncio.AbstractEventLoop):
                try:
                    import traceback

                    base_dir = Path(__file__).parent.parent.resolve()

                    venv_python = base_dir / ".venv" / "Scripts" / "python.exe"
                    if not venv_python.exists():
                        venv_python = Path(sys.executable)
                    venv_python_str = str(venv_python.resolve())

                    config_payload = {
                        "url": config.url,
                        "max_passos": config.max_passos,
                        "instrucoes_customizadas": config.instrucoes,
                        "modelo": config.modelo,
                        "modo_extracao": config.modo_extracao,
                        "llm_config": config.llm_config,
                    }

                    temp_dir = Path(tempfile.gettempdir())
                    config_path = temp_dir / f"llm_agent_config_{uuid.uuid4().hex}.json"
                    config_path.write_text(json.dumps(config_payload, ensure_ascii=False), encoding="utf-8")

                    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
                    command = [venv_python_str, "-m", "backend.runner", str(config_path)]

                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(f"🐍 Python: {venv_python_str}\n"), event_loop
                    )
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(f"📝 Config: {config_path}\n"), event_loop
                    )

                    process = subprocess.Popen(
                        command,
                        cwd=base_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        env=env,
                    )

                    execution_state["process"] = process

                    def stream_stdout():
                        try:
                            assert process.stdout is not None
                            for line in process.stdout:
                                asyncio.run_coroutine_threadsafe(manager.broadcast(line), event_loop)
                        finally:
                            if process.stdout:
                                process.stdout.close()

                    threading.Thread(target=stream_stdout, daemon=True).start()

                    returncode = process.wait()
                    message = (
                        "✅ Navegação concluída com sucesso!\n"
                        if returncode == 0
                        else f"❌ Processo terminou com código {returncode}\n"
                    )
                    asyncio.run_coroutine_threadsafe(manager.broadcast(message), event_loop)

                except Exception as exc:
                    error_trace = traceback.format_exc()
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(f"❌ Erro ao executar: {exc}\n"), event_loop
                    )
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(f"📋 Traceback:\n{error_trace}\n"), event_loop
                    )
                    print(f"ERRO COMPLETO: {error_trace}")
                finally:
                    if 'config_path' in locals() and config_path.exists():
                        try:
                            config_path.unlink()
                        except OSError:
                            pass
                    execution_state["process"] = None
                    execution_state["is_running"] = False
                    execution_state["stop_requested"] = False

            thread = threading.Thread(target=run_in_process, args=(loop,), daemon=True)
            thread.start()
            
        except Exception as e:
            await manager.broadcast(f"❌ Erro ao iniciar: {str(e)}\n")
            execution_state["is_running"] = False
    
    asyncio.create_task(run_agent())
    
    return {"success": True, "message": "Agente iniciado"}

@app.post("/api/agent/stop")
async def stop_agent():
    """Para a execução do agente"""
    if not execution_state["is_running"]:
        raise HTTPException(status_code=400, detail="Agente não está em execução")
    
    execution_state["stop_requested"] = True
    await manager.broadcast("⏹️ Parando agente...\n")

    process = execution_state.get("process")
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except Exception:
            process.kill()
        execution_state["process"] = None
        await manager.broadcast("🛑 Processo do agente terminado.\n")
    
    return {"success": True, "message": "Solicitação de parada enviada"}

@app.get("/api/agent/status")
async def get_agent_status():
    """Retorna o status atual do agente"""
    return {
        "is_running": execution_state["is_running"],
        "stop_requested": execution_state["stop_requested"]
    }

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket para logs em tempo real"""
    await manager.connect(websocket)
    try:
        # Redirecionar stdout para enviar logs via WebSocket
        import io
        
        class WebSocketLogger(io.StringIO):
            def write(self, message):
                if message.strip():
                    asyncio.create_task(manager.broadcast(message))
                return len(message)
            
            def flush(self):
                pass
        
        # Manter conexão aberta
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back para manter conexão ativa
                await websocket.send_text(f"Received: {data}")
            except WebSocketDisconnect:
                break
    finally:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor FastAPI...")
    print("📍 API: http://localhost:8000")
    print("📝 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
