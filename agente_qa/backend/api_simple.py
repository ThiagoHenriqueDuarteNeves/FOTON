"""
Teste simples do endpoint para debug
"""
from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import sys
from pathlib import Path
import tempfile

app = FastAPI()

class AgentConfig(BaseModel):
    url: str
    max_passos: int = 5
    instrucoes: str = "Complete o formulário"
    modelo: str = "openai/gpt-oss-20b"
    modo_extracao: str = "completo"

@app.post("/api/agent/start")
async def start_agent(config: AgentConfig):
    """Inicia execução do agente de forma simplificada"""
    
    try:
        # Preparar diretório base
        base_dir = Path(__file__).parent.parent.resolve()
        
        # Criar script temporário
        script_content = f"""
import sys
import asyncio
from pathlib import Path

# Configurar Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Path do projeto
sys.path.insert(0, r'{base_dir}')

# Executar
from main import navegar_com_agente

navegar_com_agente(
    url=r'{config.url}',
    max_passos={config.max_passos},
    instrucoes_customizadas=r'''{config.instrucoes}''',
    modelo=r'{config.modelo}',
    modo_extracao=r'{config.modo_extracao}'
)
"""
        
        # Salvar em temp
        temp_dir = Path(tempfile.gettempdir())
        temp_script = temp_dir / "agent_run.py"
        temp_script.write_text(script_content, encoding='utf-8')
        
        # Python do venv
        venv_python = str((base_dir / ".venv" / "Scripts" / "python.exe").resolve())
        
        print(f"[DEBUG] Base dir: {base_dir}")
        print(f"[DEBUG] Venv Python: {venv_python}")
        print(f"[DEBUG] Temp script: {temp_script}")
        print(f"[DEBUG] Script existe: {temp_script.exists()}")
        
        # Executar com nova janela de console
        if sys.platform == 'win32':
            process = subprocess.Popen(
                [venv_python, str(temp_script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            process = subprocess.Popen([venv_python, str(temp_script)])
        
        print(f"[DEBUG] Processo iniciado com PID: {process.pid}")
        
        return {"success": True, "message": f"Agente iniciado (PID: {process.pid})"}
    
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"[ERRO] {error_msg}")
        return {"success": False, "message": f"Erro: {str(e)}", "traceback": error_msg}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
