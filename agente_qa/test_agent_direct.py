import sys
import os
import asyncio

# Configurar encoding UTF-8 para o console
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# CRÍTICO: Configurar policy de asyncio ANTES de qualquer operação async no Windows
if sys.platform == 'win32':
    # Python 3.13+ no Windows precisa do ProactorEventLoop para subprocessos
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.append(r'C:\Users\Thiago\Documents\FOTON\AgenteIA\llm_agent_test')

# Import após configurar tudo
from main import navegar_com_agente

try:
    print("Iniciando teste do agente...")
    navegar_com_agente(
        url=r'https://example.com',
        max_passos=2,
        instrucoes_customizadas=r'Explore a página',
        modelo=r'openai/gpt-oss-20b',
        modo_extracao=r'padrao',
        llm_config={'provider': 'lmstudio_local', 'url': 'http://localhost:1234', 'api_key': ''}
    )
    print("SUCESSO: Navegacao concluida!")
except Exception as e:
    import traceback
    print(f"ERRO: {e}")
    traceback.print_exc()
