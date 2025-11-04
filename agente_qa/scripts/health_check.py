#!/usr/bin/env python3
"""
Script para verificar a saúde do projeto (health check).
Verifica dependências, configurações e conectividade.
Uso: python scripts/health_check.py
"""

import sys
import subprocess
import importlib
import os
from pathlib import Path
import requests

class HealthCheck:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def check_python_version(self):
        """Verifica versão do Python"""
        print("\n🐍 Verificando versão do Python...")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.passed.append(f"Python {version.major}.{version.minor}.{version.micro} ✅")
            print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        else:
            self.issues.append("Python 3.8+ é necessário")
            print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (3.8+ necessário)")
    
    def check_venv(self):
        """Verifica se está em virtual environment"""
        print("\n📦 Verificando virtual environment...")
        
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        if in_venv:
            self.passed.append("Virtual environment ativado ✅")
            print("  ✅ Virtual environment ativado")
        else:
            self.warnings.append("Recomendado usar virtual environment")
            print("  ⚠️  Não está em um virtual environment")
    
    def check_python_dependencies(self):
        """Verifica dependências Python"""
        print("\n📚 Verificando dependências Python...")
        
        required = [
            'playwright',
            'fastapi',
            'uvicorn',
            'requests',
            'beautifulsoup4',
            'pydantic'
        ]
        
        for package in required:
            try:
                importlib.import_module(package.replace('-', '_'))
                print(f"  ✅ {package}")
                self.passed.append(f"{package} instalado ✅")
            except ImportError:
                print(f"  ❌ {package} não encontrado")
                self.issues.append(f"{package} não instalado")
    
    def check_playwright_browsers(self):
        """Verifica browsers do Playwright"""
        print("\n🌐 Verificando browsers do Playwright...")
        
        try:
            result = subprocess.run(
                ['playwright', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'chromium' in result.stdout.lower():
                print("  ✅ Browsers do Playwright instalados")
                self.passed.append("Playwright browsers ✅")
            else:
                print("  ⚠️  Browsers podem não estar instalados")
                self.warnings.append("Execute: playwright install")
        
        except Exception as e:
            print(f"  ❌ Erro ao verificar Playwright: {e}")
            self.issues.append("Playwright pode não estar configurado corretamente")
    
    def check_node_and_npm(self):
        """Verifica Node.js e npm"""
        print("\n📦 Verificando Node.js e npm...")
        
        try:
            node_result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if node_result.returncode == 0:
                version = node_result.stdout.strip()
                print(f"  ✅ Node.js {version}")
                self.passed.append(f"Node.js {version} ✅")
            else:
                print("  ❌ Node.js não encontrado")
                self.issues.append("Node.js não instalado")
        
        except FileNotFoundError:
            print("  ❌ Node.js não encontrado")
            self.issues.append("Node.js não instalado")
        
        try:
            npm_result = subprocess.run(
                ['npm', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if npm_result.returncode == 0:
                version = npm_result.stdout.strip()
                print(f"  ✅ npm {version}")
                self.passed.append(f"npm {version} ✅")
            else:
                print("  ❌ npm não encontrado")
                self.issues.append("npm não instalado")
        
        except FileNotFoundError:
            print("  ❌ npm não encontrado")
            self.issues.append("npm não instalado")
    
    def check_frontend_dependencies(self):
        """Verifica dependências do frontend"""
        print("\n⚛️  Verificando dependências do frontend...")
        
        node_modules = Path('frontend/node_modules')
        
        if node_modules.exists():
            print("  ✅ node_modules encontrado")
            self.passed.append("Frontend dependencies ✅")
        else:
            print("  ⚠️  node_modules não encontrado")
            self.warnings.append("Execute: cd frontend && npm install")
    
    def check_env_file(self):
        """Verifica arquivo .env"""
        print("\n🔐 Verificando arquivo .env...")
        
        env_file = Path('.env')
        env_example = Path('.env.example')
        
        if env_file.exists():
            print("  ✅ .env encontrado")
            self.passed.append(".env configurado ✅")
        else:
            if env_example.exists():
                print("  ⚠️  .env não encontrado (.env.example existe)")
                self.warnings.append("Copie .env.example para .env e configure")
            else:
                print("  ⚠️  .env não encontrado")
                self.warnings.append("Crie arquivo .env com configurações")
    
    def check_directories(self):
        """Verifica estrutura de diretórios"""
        print("\n📁 Verificando estrutura de diretórios...")
        
        required_dirs = ['agent', 'backend', 'frontend', 'docs']
        optional_dirs = ['logs', 'prints', 'tests', 'scripts', 'config']
        
        for directory in required_dirs:
            path = Path(directory)
            if path.exists():
                print(f"  ✅ {directory}/")
                self.passed.append(f"Diretório {directory}/ ✅")
            else:
                print(f"  ❌ {directory}/ não encontrado")
                self.issues.append(f"Diretório {directory}/ ausente")
        
        for directory in optional_dirs:
            path = Path(directory)
            if path.exists():
                print(f"  ✅ {directory}/")
            else:
                print(f"  ℹ️  {directory}/ não encontrado (opcional)")
    
    def check_backend_connectivity(self):
        """Verifica se o backend está rodando"""
        print("\n🔌 Verificando conectividade do backend...")
        
        try:
            response = requests.get('http://localhost:8000/', timeout=5)
            if response.status_code == 200:
                print("  ✅ Backend está rodando (porta 8000)")
                self.passed.append("Backend online ✅")
            else:
                print(f"  ⚠️  Backend respondeu com status {response.status_code}")
                self.warnings.append("Backend pode não estar funcionando corretamente")
        
        except requests.ConnectionError:
            print("  ℹ️  Backend não está rodando")
            print("  💡 Execute: python scripts/start_servers.py")
        
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar backend: {e}")
    
    def check_llm_providers(self):
        """Verifica conectividade com provedores LLM"""
        print("\n🤖 Verificando provedores LLM...")
        
        # LM Studio
        try:
            response = requests.get('http://localhost:1234/v1/models', timeout=3)
            if response.status_code == 200:
                print("  ✅ LM Studio acessível (porta 1234)")
                self.passed.append("LM Studio online ✅")
            else:
                print("  ⚠️  LM Studio respondeu mas com erro")
        except:
            print("  ℹ️  LM Studio não acessível (porta 1234)")
        
        # Ollama
        try:
            response = requests.get('http://localhost:11434/', timeout=3)
            if response.status_code == 200:
                print("  ✅ Ollama acessível (porta 11434)")
                self.passed.append("Ollama online ✅")
            else:
                print("  ⚠️  Ollama respondeu mas com erro")
        except:
            print("  ℹ️  Ollama não acessível (porta 11434)")
    
    def print_summary(self):
        """Imprime resumo da verificação"""
        print("\n" + "=" * 60)
        print("📊 RESUMO DA VERIFICAÇÃO")
        print("=" * 60)
        
        if self.passed:
            print(f"\n✅ Verificações Passou: {len(self.passed)}")
            for item in self.passed[:5]:  # Mostra apenas os 5 primeiros
                print(f"   • {item}")
            if len(self.passed) > 5:
                print(f"   ... e mais {len(self.passed) - 5}")
        
        if self.warnings:
            print(f"\n⚠️  Avisos: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if self.issues:
            print(f"\n❌ Problemas Encontrados: {len(self.issues)}")
            for issue in self.issues:
                print(f"   • {issue}")
        
        print("\n" + "=" * 60)
        
        if self.issues:
            print("❌ Sistema com problemas - resolva os issues acima")
            return False
        elif self.warnings:
            print("⚠️  Sistema OK mas com avisos - considere resolver")
            return True
        else:
            print("✅ Sistema totalmente saudável!")
            return True
    
    def run_all_checks(self):
        """Executa todas as verificações"""
        print("=" * 60)
        print("🏥 Health Check - Agente de QA")
        print("=" * 60)
        
        self.check_python_version()
        self.check_venv()
        self.check_python_dependencies()
        self.check_playwright_browsers()
        self.check_node_and_npm()
        self.check_frontend_dependencies()
        self.check_env_file()
        self.check_directories()
        self.check_backend_connectivity()
        self.check_llm_providers()
        
        return self.print_summary()

def main():
    checker = HealthCheck()
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
