#!/usr/bin/env python3
"""
Script para iniciar backend (FastAPI) e frontend (Vite) simultaneamente.

Requisitos:
1. Estar com o virtualenv ativo OU executar via caminho absoluto do python do venv
    Exemplo: C:\\Users\\Thiago\\Documents\\FOTON\\AgenteIA\\llm_agent_test\\.venv\\Scripts\\python.exe scripts\\start_servers.py
2. Rodar a partir da raiz do projeto (pasta llm_agent_test)

Uso:
    - Dentro do PowerShell:  .\\.venv\\Scripts\\Activate.ps1; python scripts/start_servers.py
    - Ou pela rota absoluta:  C:\\...\\.venv\\Scripts\\python.exe scripts\\start_servers.py
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Cores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.ENDC):
    """Print colored message"""
    print(f"{color}{message}{Colors.ENDC}")


def get_project_root() -> Path:
    """Retorna o diretório raiz do projeto (onde fica .venv)."""
    return Path(__file__).resolve().parent.parent


def get_venv_python() -> str:
    """Retorna o executável do python dentro do venv ou faz fallback para sys.executable."""
    root = get_project_root()
    if sys.platform == 'win32':
        candidate = root / '.venv' / 'Scripts' / 'python.exe'
    else:
        candidate = root / '.venv' / 'bin' / 'python'

    if candidate.exists():
        return str(candidate.resolve())

    # Fallback apenas se o python do venv não existir (garante que usamos o ambiente certo)
    return sys.executable


def get_npm_command() -> str:
    """Retorna o comando correto do npm para cada plataforma."""
    return 'npm.cmd' if sys.platform == 'win32' else 'npm'

def check_venv():
    """Verifica se está dentro de um virtual environment"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_colored("⚠️  AVISO: Python atual não é do virtualenv!", Colors.WARNING)
        print_colored("    Ative com .\\.venv\\Scripts\\Activate.ps1 ou use C:\\...\\.venv\\Scripts\\python.exe", Colors.WARNING)

def check_port_available(port):
    """Verifica se uma porta está disponível"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def start_backend():
    """Inicia o servidor backend (FastAPI)"""
    print_colored("\n🚀 Iniciando Backend (FastAPI)...", Colors.OKBLUE)

    python_cmd = get_venv_python()
    project_root = get_project_root()
    print_colored(f"🐍 Python utilizado: {python_cmd}", Colors.OKCYAN)
    env = os.environ.copy()
    env.setdefault('PYTHONIOENCODING', 'utf-8')
    
    if not check_port_available(8000):
        print_colored("❌ Porta 8000 já está em uso!", Colors.FAIL)
        return None
    
    try:
        # Windows
        if sys.platform == 'win32':
            process = subprocess.Popen(
                [python_cmd, '-m', 'uvicorn', 'backend.api:app', '--reload', '--port', '8000'],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=project_root,
                env=env
            )
        # Linux/Mac
        else:
            process = subprocess.Popen(
                [python_cmd, '-m', 'uvicorn', 'backend.api:app', '--reload', '--port', '8000'],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
        
        print_colored("✅ Backend iniciado na porta 8000", Colors.OKGREEN)
        print_colored("📖 Docs disponível em: http://localhost:8000/docs", Colors.OKCYAN)
        return process
    
    except Exception as e:
        print_colored(f"❌ Erro ao iniciar backend: {e}", Colors.FAIL)
        return None

def start_frontend():
    """Inicia o servidor frontend (Vite)"""
    print_colored("\n🚀 Iniciando Frontend (React + Vite)...", Colors.OKBLUE)
    
    frontend_dir = get_project_root() / 'frontend'
    if not frontend_dir.exists():
        print_colored("❌ Diretório 'frontend' não encontrado!", Colors.FAIL)
        return None
    
    if not check_port_available(3000):
        print_colored("⚠️  Porta 3000 já está em uso!", Colors.WARNING)
        response = input("Deseja tentar iniciar mesmo assim? (s/n): ")
        if response.lower() != 's':
            return None
    
    # Verifica se node_modules existe
    node_modules = frontend_dir / 'node_modules'
    npm_cmd = get_npm_command()

    if not node_modules.exists():
        print_colored("📦 node_modules não encontrado. Executando npm install...", Colors.WARNING)
        print_colored(f"    (Usando comando: {npm_cmd} install)", Colors.OKCYAN)
        install_process = subprocess.run([npm_cmd, 'install'], cwd=frontend_dir)
        if install_process.returncode != 0:
            print_colored("❌ Erro ao instalar dependências do frontend!", Colors.FAIL)
            return None
    
    try:
        # Windows
        if sys.platform == 'win32':
            process = subprocess.Popen(
                [npm_cmd, 'run', 'dev'],
                cwd=frontend_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        # Linux/Mac
        else:
            process = subprocess.Popen(
                [npm_cmd, 'run', 'dev'],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        print_colored("✅ Frontend iniciado na porta 3000 (provavelmente)", Colors.OKGREEN)
        print_colored("🌐 Acesse: http://localhost:3000", Colors.OKCYAN)
        return process
    
    except Exception as e:
        print_colored(f"❌ Erro ao iniciar frontend: {e}", Colors.FAIL)
        return None

def main():
    """Função principal"""
    print_colored("=" * 60, Colors.HEADER)
    print_colored("🚀 Iniciando Servidores do Agente de QA", Colors.HEADER)
    print_colored("=" * 60, Colors.HEADER)
    
    # Verifica virtual environment
    check_venv()
    
    processes = []
    
    # Inicia backend
    backend_process = start_backend()
    if backend_process:
        processes.append(('backend', backend_process))
        time.sleep(2)  # Aguarda backend iniciar
    
    # Inicia frontend
    frontend_process = start_frontend()
    if frontend_process:
        processes.append(('frontend', frontend_process))
    
    if not processes:
        print_colored("\n❌ Nenhum servidor foi iniciado!", Colors.FAIL)
        sys.exit(1)
    
    print_colored("\n" + "=" * 60, Colors.HEADER)
    print_colored("✅ Servidores iniciados com sucesso!", Colors.OKGREEN)
    print_colored("=" * 60, Colors.HEADER)
    
    print_colored("\n📋 URLs disponíveis:", Colors.BOLD)
    print_colored("   Backend API: http://localhost:8000", Colors.OKCYAN)
    print_colored("   Backend Docs: http://localhost:8000/docs", Colors.OKCYAN)
    print_colored("   Frontend: http://localhost:3000", Colors.OKCYAN)
    
    print_colored("\n💡 Dica: Pressione Ctrl+C para parar todos os servidores", Colors.WARNING)
    
    # Aguarda interrupção
    try:
        while True:
            time.sleep(1)
            # Verifica se processos ainda estão rodando
            for name, process in processes:
                if process.poll() is not None:
                    print_colored(f"\n⚠️  Servidor {name} parou inesperadamente!", Colors.WARNING)
    
    except KeyboardInterrupt:
        print_colored("\n\n⏹️  Parando servidores...", Colors.WARNING)
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print_colored(f"✅ {name} parado", Colors.OKGREEN)
            except Exception as e:
                print_colored(f"❌ Erro ao parar {name}: {e}", Colors.FAIL)
                try:
                    process.kill()
                except:
                    pass
        
        print_colored("\n👋 Até logo!", Colors.HEADER)
        sys.exit(0)

if __name__ == '__main__':
    main()
