"""
Módulo LLM - Comunicação e gerenciamento de Large Language Models
Centraliza todas as operações relacionadas a LLMs: comunicação, payload, validação.

Fluxo de Execução:
- Inicializado no início do agente
- Chamado a cada passo para obter decisões do LLM
- Gerencia diferentes provedores (LM Studio, Ollama, etc.)
"""
import requests
import time
import json
import logging
import re
from datetime import datetime
from .io import salvar_payload_log

BACKEND = "lmstudio"  # agora LM Studio é o padrão


def chamar_llm(prompt, modelo="mistral"):
    """
    Função principal para chamar LLM - roteamento baseado no backend configurado.
    
    Args:
        prompt (str): Prompt para enviar ao LLM
        modelo (str): Nome do modelo a utilizar
    
    Returns:
        str: Resposta do LLM
    
    Fluxo: Ponto de entrada principal para comunicação com LLM
    """
    if BACKEND == "lmstudio":
        return chamar_llm_lmstudio(prompt)
    return chamar_llm_ollama(prompt, modelo)


def chamar_llm_ollama(prompt, modelo="mistral"):
    """
    Comunicação com LLM via Ollama.
    
    Args:
        prompt (str): Prompt para o LLM
        modelo (str): Modelo Ollama a utilizar
    
    Returns:
        str: Resposta do LLM ou string vazia em caso de erro
    
    Fluxo: Chamado quando backend = ollama
    """
    print("\n⌛ Aguardando resposta do LLM (Ollama)...")
    inicio = time.time()

    try:
        resposta = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": modelo,
                "prompt": prompt,
                "stream": False
            },
            timeout=None
        )

        duracao = round(time.time() - inicio, 2)
        print(f"✅ Resposta recebida após {duracao} segundos.")

        if not resposta.ok:
            print(f"[ERRO] Status HTTP {resposta.status_code}: {resposta.text}")
            return ""

        print("\n[DEBUG] Resposta completa recebida do LLM (bruta):")
        print(resposta.text)

        try:
            json_data = resposta.json()
            resposta_final = json_data.get("response", "").strip()
        except Exception as e:
            print(f"[ERRO] Falha ao interpretar JSON da resposta: {e}")
            return ""

        if not resposta_final:
            print("[⚠️ AVISO] O LLM respondeu, mas o campo 'response' está vazio.")
        else:
            print("[✔️ LLM] Resposta extraída com sucesso.")

        return resposta_final

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro ao se comunicar com o LLM: {e}")
        return ""
    except Exception as e:
        print(f"[ERRO] Falha inesperada ao processar a resposta do LLM: {e}")
        return ""


def chamar_llm_lmstudio(prompt):
    """
    Comunicação com LLM via LM Studio (formato completion).
    
    Args:
        prompt (str): Prompt para o LLM
    
    Returns:
        str: Resposta do LLM ou string vazia em caso de erro
    
    Fluxo: Chamado quando backend = lmstudio (formato antigo)
    """
    print("\n⌛ Aguardando resposta do LLM (LM Studio)...")
    inicio = time.time()

    try:
        resposta = requests.post(
            "http://localhost:1234/v1/completions",
            json={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 800,
                "stop": None,
                "n": 1,
                "stream": False,
                "model": "local-model"
            },
            timeout=None
        )

        duracao = round(time.time() - inicio, 2)
        print(f"✅ Resposta recebida após {duracao} segundos.")

        if not resposta.ok:
            print(f"[ERRO] Status HTTP {resposta.status_code}: {resposta.text}")
            return ""

        print("\n[DEBUG] Resposta completa recebida do LLM (bruta):")
        print(resposta.text)

        try:
            json_data = resposta.json()
            resposta_final = json_data.get("choices", [{}])[0].get("text", "").strip()
        except Exception as e:
            print(f"[ERRO] Falha ao interpretar JSON da resposta: {e}")
            return ""

        if not resposta_final:
            print("[⚠️ AVISO] O LLM respondeu, mas o campo 'text' está vazio.")
        else:
            print("[✔️ LLM] Resposta extraída com sucesso.")

        return resposta_final

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro ao se comunicar com o LLM: {e}")
        return ""
    except Exception as e:
        print(f"[ERRO] Falha inesperada ao processar a resposta do LLM: {e}")
        return ""


def obter_modelos_disponiveis():
    """
    Obtém lista de modelos disponíveis do LM Studio.
    
    Returns:
        list: Lista de modelos disponíveis
    
    Fluxo: Chamado durante inicialização para descobrir modelos
    """
    try:
        logging.info("Obtendo lista de modelos do LM Studio...")
        resposta = requests.get("http://localhost:1234/v1/models", timeout=10)
        
        if resposta.ok:
            dados = resposta.json()
            modelos = [modelo["id"] for modelo in dados.get("data", [])]
            logging.info(f"Modelos encontrados: {modelos}")
            return modelos
        else:
            logging.warning(f"Erro ao obter modelos: {resposta.status_code}")
            return []
            
    except Exception as e:
        logging.error(f"Erro ao conectar com LM Studio: {e}")
        # Modelos padrão conhecidos como fallback
        modelos_padrao = [
            "qwen/qwen2.5-vl-7b", 
            "gpt-4-vision-preview", 
            "llava-1.5-7b-hf", 
            "gemini-pro-vision",
            "claude-3-vision"
        ]
        return modelos_padrao


def obter_modelo_carregado():
    """
    Identifica qual modelo está atualmente carregado no LM Studio.
    
    Returns:
        str: Nome do modelo carregado ou None se não conseguir identificar
    
    Fluxo: Chamado para verificar se modelo desejado está ativo
    """
    try:
        logging.info("Verificando modelo carregado no LM Studio...")
        
        # Tentar uma requisição de teste para identificar o modelo
        payload_teste = {
            "model": "test",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
        
        resposta = requests.post("http://localhost:1234/v1/chat/completions", 
                               json=payload_teste, timeout=5)
        
        if resposta.ok:
            dados = resposta.json()
            modelo = dados.get("model", "modelo-desconhecido")
            logging.info(f"Modelo carregado identificado via resposta: {modelo}")
            return modelo
        else:
            # Tentar método alternativo: fazer requisição vazia
            payload_vazio = {
                "model": "",
                "messages": [{"role": "user", "content": ""}],
                "max_tokens": 1
            }
            
            resposta = requests.post("http://localhost:1234/v1/chat/completions", 
                                   json=payload_vazio, timeout=5)
            
            if resposta.ok:
                dados = resposta.json()
                modelo = dados.get("model", "modelo-desconhecido")
                logging.info(f"Modelo carregado identificado via método alternativo: {modelo}")
                return modelo
                
    except Exception as e:
        logging.warning(f"Não foi possível identificar modelo carregado: {e}")
    
    return None


def normalizar_payload(payload, modelo):
    """
    Normaliza payload removendo mensagens system duplicadas e garantindo formato correto.
    
    Args:
        payload (dict): Payload original para LLM
        modelo (str): Nome do modelo (para logs)
    
    Returns:
        dict: Payload normalizado
    
    Fluxo: Chamado antes de enviar qualquer payload para LLM
    """
    try:
        # Copiar payload para evitar modificação do original
        payload_normalizado = payload.copy()
        
        if "messages" not in payload_normalizado:
            return payload_normalizado
            
        messages = payload_normalizado["messages"]
        
        # Encontrar todas as mensagens system
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        
        if len(system_messages) > 1:
            print(f"🚨 [AVISO] {len(system_messages)} mensagens system detectadas - removendo duplicatas")
            logging.warning(f"Duplicação detectada: {len(system_messages)} mensagens system no payload")
            
            # Manter apenas a primeira mensagem system
            primeira_system = system_messages[0]
            
            # Filtrar mensagens removendo systems duplicadas
            messages_filtradas = []
            system_ja_adicionada = False
            
            for msg in messages:
                if msg.get("role") == "system":
                    if not system_ja_adicionada:
                        messages_filtradas.append(primeira_system)
                        system_ja_adicionada = True
                else:
                    messages_filtradas.append(msg)
            
            payload_normalizado["messages"] = messages_filtradas
            
        # Garantir parâmetros padrão se não existirem
        if "temperature" not in payload_normalizado:
            payload_normalizado["temperature"] = 0
            
        if "max_tokens" not in payload_normalizado:
            payload_normalizado["max_tokens"] = 2048
            
        # Removendo adição automática de 'stop' tokens pois causam erro no LM Studio
        # if "stop" not in payload_normalizado:
        #     payload_normalizado["stop"] = ["\n\n", "\r\n\r\n"]
            
        return payload_normalizado
        
    except Exception as e:
        logging.error(f"Erro ao normalizar payload: {e}")
        return payload


def chamar_llm_openai_style(payload):
    """
    Chama LLM usando formato OpenAI API (para LM Studio).
    
    Args:
        payload (dict): Payload normalizado para envio
    
    Returns:
        str: Resposta do LLM ou string vazia em caso de erro
    
    Fluxo: Função principal para comunicação com LLM no formato chat
    """
    try:
        modelo_usado = payload.get('model', 'modelo-desconhecido')
        print(f"\n🔄 ENVIANDO REQUISIÇÃO PARA LM STUDIO")
        print(f"   Endpoint: http://localhost:1234/v1/chat/completions")
        print(f"   Modelo: {modelo_usado}")
        print(f"   Timeout: 60 segundos")
        
        # Salvar payload para auditoria
        salvar_payload_log(payload, modelo_usado)
        
        resposta = requests.post("http://localhost:1234/v1/chat/completions", 
                               json=payload, timeout=60)
        
        print(f"📥 RESPOSTA RECEBIDA:")
        print(f"   Status: {resposta.status_code}")
        print(f"   Headers: {dict(resposta.headers)}")
        
        if not resposta.ok:
            # Logar o corpo para entender o erro
            try:
                error_text = resposta.text
                print(f"❌ ERRO - Response text: {error_text}")
                
                # Verificar se é erro de modelo multimodal e tentar fallback
                if "base64" in error_text or "image" in error_text or "url" in error_text:
                    print("🔄 [FALLBACK] Erro multimodal detectado - tentando conversão para texto puro...")
                    payload_texto = _converter_payload_para_texto_puro(payload)
                    if payload_texto:
                        return chamar_llm_openai_style(payload_texto)
                        
            except Exception:
                pass
            resposta.raise_for_status()
            
        retorno = resposta.json()
        
        print(f"✅ JSON keys recebidos: {list(retorno.keys())}")
        
        if "choices" in retorno and len(retorno["choices"]) > 0:
            content = retorno["choices"][0]["message"]["content"]
            print(f"📝 Conteúdo extraído ({len(content)} chars): '{content[:200]}{'...' if len(content) > 200 else ''}'")
            return content
        else:
            print(f"⚠️  Estrutura inesperada no JSON: {retorno}")
            return ""
            
    except Exception as e:
        print(f"[ERRO] Falha na chamada LLM: {e}")
        print("[DICA] Verifique se o modelo suporta o formato enviado (multimodal vs texto) e se max_tokens não está alto.")
        return ""


def _converter_payload_para_texto_puro(payload):
    """
    Converte payload multimodal para texto puro (fallback).
    
    Args:
        payload (dict): Payload original (possivelmente multimodal)
        
    Returns:
        dict: Payload convertido para texto puro ou None se não for possível
    """
    try:
        payload_texto = payload.copy()
        
        if "messages" not in payload_texto:
            return None
            
        messages_convertidas = []
        
        for message in payload_texto["messages"]:
            message_convertida = message.copy()
            
            # Se o conteúdo é uma lista (multimodal), extrair apenas o texto
            if isinstance(message.get("content"), list):
                texto_extraido = ""
                for item in message["content"]:
                    if item.get("type") == "text":
                        texto_extraido += item.get("text", "") + "\n"
                    elif item.get("type") == "image_url":
                        texto_extraido += "[IMAGEM_REMOVIDA_PARA_COMPATIBILIDADE]\n"
                
                message_convertida["content"] = texto_extraido.strip()
            
            messages_convertidas.append(message_convertida)
        
        payload_texto["messages"] = messages_convertidas
        
        print("✅ [FALLBACK] Payload convertido para texto puro com sucesso")
        return payload_texto
        
    except Exception as e:
        print(f"❌ [FALLBACK] Erro ao converter payload: {e}")
        return None
