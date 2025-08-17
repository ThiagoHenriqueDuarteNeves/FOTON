"""
Módulo de I/O - Operações de entrada e saída de arquivos
Centraliza todas as operações de arquivos do projeto para melhor organização.

Fluxo de Execução:
- Chamado durante execução do agente para salvar screenshots, logs e payloads
- Fornece interface unificada para todas as operações de I/O
"""
import os
import json
import base64
import logging
from datetime import datetime
from pathlib import Path
import re


def configurar_logging(arquivo='navegacao.log', level=logging.INFO):
    """
    Configura o sistema de logging do projeto.
    
    Args:
        arquivo (str): Nome do arquivo de log
        level: Nível de logging (INFO, DEBUG, etc.)
    
    Fluxo: Chamado no início da execução do agente
    """
    logging.basicConfig(
        filename=arquivo,
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        encoding='utf-8'
    )


def criar_diretorio_se_necessario(caminho):
    """
    Cria diretório se não existir.
    
    Args:
        caminho (str): Caminho do diretório
    
    Fluxo: Chamado antes de qualquer operação de salvamento
    """
    Path(caminho).mkdir(parents=True, exist_ok=True)


def salvar_screenshot(pagina, passo):
    """
    Salva screenshot da página atual.
    
    Args:
        pagina: Objeto da página do Playwright
        passo (int): Número do passo atual
    
    Returns:
        str: Caminho do arquivo salvo
    
    Fluxo: Chamado a cada passo do agente para documentar progresso
    """
    try:
        # Criar diretório de prints se não existir
        criar_diretorio_se_necessario("prints")
        
        # Gerar nome do arquivo
        screenshot_path = f"prints/passo_{passo}.png"
        
        # Salvar screenshot
        pagina.screenshot(path=screenshot_path, full_page=True)
        
        logging.info(f"Screenshot salva em: {screenshot_path}")
        return screenshot_path
        
    except Exception as e:
        logging.error(f"Erro ao salvar screenshot: {e}")
        return None


def salvar_payload_log(payload, modelo):
    """
    Salva payload enviado para LLM em arquivo de log.
    
    Args:
        payload (dict): Payload enviado para o LLM
        modelo (str): Nome do modelo utilizado
    
    Returns:
        str: Caminho do arquivo salvo ou None se erro
    
    Fluxo: Chamado antes de cada requisição ao LLM para auditoria/debug
    """
    try:
        # Criar diretório de logs de payloads
        criar_diretorio_se_necessario("logs/payloads")
        
        # Gerar timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitizar nome do modelo para filesystem (remover caracteres especiais)
        modelo_limpo = re.sub(r'[^\w\-.]', '-', modelo)
        
        # Gerar nome do arquivo: modelo_YYYYMMDD_HHMMSS.json
        nome_arquivo = f"{modelo_limpo}_{timestamp}.json"
        caminho_arquivo = f"logs/payloads/{nome_arquivo}"
        
        # Salvar payload em JSON formatado
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Payload salvo em: {caminho_arquivo}")
        logging.info(f"Payload salvo em: {caminho_arquivo}")
        return caminho_arquivo
        
    except Exception as e:
        print(f"⚠️ Erro ao salvar payload: {e}")
        logging.warning(f"Erro ao salvar payload: {e}")
        return None


def salvar_resposta_modelo(resposta_llm, acao_parseada, passo, modelo):
    """
    Salva resposta completa do modelo incluindo justificativas.
    
    Args:
        resposta_llm (str): Resposta bruta do LLM
        acao_parseada (dict): Ação parseada e normalizada
        passo (int): Número do passo atual
        modelo (str): Nome do modelo utilizado
    
    Returns:
        str: Caminho do arquivo salvo ou None se erro
    
    Fluxo: Chamado após cada resposta do LLM para análise detalhada
    """
    try:
        # Criar diretório de respostas se não existir
        criar_diretorio_se_necessario("logs/model_responses")
        
        # Gerar timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitizar nome do modelo
        modelo_limpo = re.sub(r'[^\w\-.]', '-', modelo)
        
        # Gerar nome do arquivo
        nome_arquivo = f"passo{passo}_{modelo_limpo}_{timestamp}.json"
        caminho_arquivo = f"logs/model_responses/{nome_arquivo}"
        
        # Preparar dados para salvamento
        dados_resposta = {
            "passo": passo,
            "timestamp": timestamp,
            "modelo": modelo,
            "resposta_bruta": resposta_llm,
            "acao_parseada": acao_parseada,
            "justificativa": acao_parseada.get('justification', acao_parseada.get('justificativa', 'Não fornecida')),
            "confianca": acao_parseada.get('confidence', acao_parseada.get('confianca', 0)),
            "metadados": {
                "acao": acao_parseada.get('action', acao_parseada.get('acao', 'N/A')),
                "seletor": acao_parseada.get('selector', acao_parseada.get('seletor', 'N/A')),
                "valor": acao_parseada.get('value', acao_parseada.get('valor', '')),
                "tem_markdown": '```' in resposta_llm,
                "tamanho_resposta": len(resposta_llm)
            }
        }
        
        # Salvar em JSON formatado
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_resposta, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Resposta do modelo salva em: {caminho_arquivo}")
        print(f"💭 Justificativa: {dados_resposta['justificativa']}")
        print(f"🎯 Confiança: {dados_resposta['confianca']}")
        
        logging.info(f"Resposta do modelo salva em: {caminho_arquivo}")
        return caminho_arquivo
        
    except Exception as e:
        print(f"⚠️ Erro ao salvar resposta do modelo: {e}")
        logging.warning(f"Erro ao salvar resposta do modelo: {e}")
        return None


def salvar_lista_seletores(elementos, passo):
    """
    Salva lista de seletores extraídos em arquivo de log.
    
    Args:
        elementos (list): Lista de elementos/seletores extraídos
        passo (int): Número do passo atual
    
    Returns:
        str: Caminho do arquivo salvo
    
    Fluxo: Chamado após extração de elementos para auditoria
    """
    try:
        # Criar diretório de logs se não existir
        criar_diretorio_se_necessario("logs")
        
        # Gerar nome do arquivo
        arquivo_path = f"logs/seletores_passo_{passo}.txt"
        
        # Salvar lista de seletores
        with open(arquivo_path, 'w', encoding='utf-8') as f:
            f.write(f"SELETORES EXTRAÍDOS - PASSO {passo}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, elemento in enumerate(elementos, 1):
                f.write(f"{i}. {elemento}\n")
        
        logging.info(f"Lista de seletores salva em: {arquivo_path}")
        return arquivo_path
        
    except Exception as e:
        logging.error(f"Erro ao salvar lista de seletores: {e}")
        return None


def carregar_configuracao(arquivo='config.json'):
    """
    Carrega configurações de arquivo JSON.
    
    Args:
        arquivo (str): Caminho do arquivo de configuração
    
    Returns:
        dict: Dicionário com configurações ou configurações padrão
    
    Fluxo: Chamado no início da execução para carregar configurações
    """
    configuracao_padrao = {
        "max_passos": 10,
        "timeout_llm": 60,
        "modelo_padrao": "qwen/qwen2.5-vl-7b",
        "screenshots_habilitados": True,
        "nivel_log": "INFO"
    }
    
    try:
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return {**configuracao_padrao, **config}  # Merge com padrões
        else:
            return configuracao_padrao
            
    except Exception as e:
        logging.warning(f"Erro ao carregar configuração: {e}. Usando padrões.")
        return configuracao_padrao
