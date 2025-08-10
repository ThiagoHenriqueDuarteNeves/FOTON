import time
import logging
import json
from datetime import datetime
from pathlib import Path
from agent.browser import iniciar_navegador
from agent.llm import chamar_llm_lmstudio  # LM Studio como padrão
from agent.testid_injector import injetar_data_testids  # Novo injetor
from agent.utils import (
    extrair_html,
    gerar_prompt_em_chat_format,
    executar_acao,
    fechar_aviso_de_cookies,
    extrair_json_da_resposta,  # Usar a função padrão
    validar_seletor_e_retry,  # Nova função de validação
    extrair_elementos_otimizados_llm,  # Nova função otimizada
    gerar_prompt_otimizado_com_contexto,  # Nova função de prompt otimizado
    gerar_prompt_autonomo_completo  # Nova função completa e autônoma
)
import requests

# Configura log em arquivo
logging.basicConfig(
    filename='navegacao.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def objetivo_atingido(pagina, instrucoes, url_antes=None, url_depois=None):
    """Heurísticas simples para determinar se o objetivo declarado foi cumprido.
    Foco inicial: login (cpf/senha/login/entrar).
    """
    try:
        instr = (instrucoes or "").lower()
        # Só encerramos automaticamente se a instrução pedir explicitamente para finalizar
        pedido_finalizar = any(t in instr for t in ["finalizar", "encerrar", "concluir", "terminar"])
        if any(t in instr for t in ["cpf", "senha", "login", "entrar", "acessar"]) and pedido_finalizar:
            # 1) Se houve navegação e não estamos mais numa URL de login
            if url_antes and url_depois and url_depois != url_antes and 'login' not in (url_depois or '').lower():
                return True, "Mudança de URL pós-login detectada"
            # 2) Se não há mais campo de senha na página e há indicadores de sessão ativa
            try:
                if pagina.locator("input[type='password']").count() == 0:
                    indic_textos = [
                        r"/\\b(Sair|Logout|Minha Conta|Perfil|Bem-vindo|Olá)\\b/i",
                        r"/\\b(Dashboard|Área do Candidato|Minha Área)\\b/i"
                    ]
                    for t in indic_textos:
                        if pagina.locator(f"text:{t}").count() > 0:
                            return True, "Indicadores de sessão ativa na página"
            except Exception:
                pass
        return False, "Objetivo não identificado como concluído"
    except Exception as e:
        print(f"[AVISO] Falha na verificação de objetivo: {e}")
        return False, "Erro na verificação"

def obter_modelos_disponiveis():
    """Obtém a lista de modelos disponíveis do LM Studio"""
    try:
        print("[INFO] Obtendo lista de modelos do LM Studio...")
        resposta = requests.get("http://localhost:1234/v1/models", timeout=5)
        resposta.raise_for_status()
        
        dados = resposta.json()
        modelos = []
        
        if "data" in dados:
            for modelo in dados["data"]:
                if "id" in modelo:
                    modelos.append(modelo["id"])
        
        print(f"[INFO] Modelos encontrados: {modelos}")
        return modelos
        
    except requests.exceptions.ConnectionError:
        print("[AVISO] LM Studio não está disponível. Usando modelos padrão.")
        return [
            "qwen/qwen2.5-vl-7b",
            "gpt-4-vision-preview", 
            "claude-3-5-sonnet-20241022",
            "llava-v1.6-34b",
            "minicpm-v-2_6"
        ]
    except Exception as e:
        print(f"[ERRO] Falha ao obter modelos: {e}")
        return ["qwen/qwen2.5-vl-7b"]  # Modelo padrão como fallback

def obter_modelo_carregado():
    """Obtém o modelo atualmente carregado no LM Studio"""
    try:
        print("[INFO] Verificando modelo carregado no LM Studio...")
        
        # Método 1: Tentar uma requisição simples para identificar o modelo ativo
        payload_teste = {
            "model": "current",  # Alguns LM Studios aceitam "current"
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
            "temperature": 0
        }
        
        try:
            resposta = requests.post("http://localhost:1234/v1/chat/completions", 
                                   json=payload_teste, timeout=5)
            
            if resposta.status_code == 200:
                dados = resposta.json()
                if "model" in dados and dados["model"]:
                    modelo_ativo = dados["model"]
                    print(f"[INFO] Modelo carregado identificado via resposta: {modelo_ativo}")
                    return modelo_ativo
        except:
            pass
        
        # Método 2: Tentar com modelo vazio e ver se retorna erro informativo
        try:
            payload_vazio = {
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            resposta = requests.post("http://localhost:1234/v1/chat/completions", 
                                   json=payload_vazio, timeout=5)
            
            if resposta.status_code == 200:
                dados = resposta.json()
                if "model" in dados and dados["model"]:
                    modelo_ativo = dados["model"]
                    print(f"[INFO] Modelo carregado identificado via payload vazio: {modelo_ativo}")
                    return modelo_ativo
        except:
            pass
        
        # Método 3: Usar o primeiro modelo da lista que não seja embedding
        modelos = obter_modelos_disponiveis()
        for modelo in modelos:
            # Filtrar modelos de embedding
            if not any(termo in modelo.lower() for termo in ['embedding', 'embed']):
                print(f"[INFO] Usando primeiro modelo não-embedding da lista: {modelo}")
                return modelo
        
        # Método 4: Se só há embeddings, usar o primeiro da lista mesmo assim
        if modelos and len(modelos) > 0:
            print(f"[INFO] Usando primeiro modelo da lista: {modelos[0]}")
            return modelos[0]
            
    except Exception as e:
        print(f"[AVISO] Erro ao identificar modelo carregado: {e}")
    
    # Retorna None se não conseguiu identificar
    print("[INFO] Não foi possível identificar modelo carregado automaticamente")
    return None

def salvar_screenshot(pagina, passo):
    Path("prints").mkdir(exist_ok=True)
    caminho = f"prints/passo_{passo}.png"
    pagina.screenshot(path=caminho, full_page=True)
    print(f"[📸] Screenshot salva em: {caminho}")
    logging.info(f"Screenshot salva em: {caminho}")

def salvar_lista_de_seletores(html, passo, screenshot_path=None, instrucoes_customizadas=None, modelo="qwen/qwen2.5-vl-7b", historico_acoes=None):
    Path("logs").mkdir(exist_ok=True)
    caminho = f"logs/seletores_passo_{passo}.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        payload, seletores_validos = gerar_prompt_em_chat_format(html, screenshot_path, instrucoes_customizadas, modelo, historico_acoes)
        f.write(str(payload))
    print(f"[🧾] Lista de seletores salva em: {caminho}")
    logging.info(f"Lista de seletores salva em: {caminho}")
    return payload, seletores_validos

def chamar_llm_openai_style(payload):
    try:
        modelo_usado = payload.get('model', 'modelo-desconhecido')
        print(f"\n🔄 ENVIANDO REQUISIÇÃO PARA LM STUDIO")
        print(f"   Endpoint: http://localhost:1234/v1/chat/completions")
        print(f"   Modelo: {modelo_usado}")
        print(f"   Timeout: 60 segundos")
        
        resposta = requests.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=60)
        
        print(f"📥 RESPOSTA RECEBIDA:")
        print(f"   Status: {resposta.status_code}")
        print(f"   Headers: {dict(resposta.headers)}")
        
        if not resposta.ok:
            # Logar o corpo para entender o 400/erro
            try:
                print(f"❌ ERRO - Response text: {resposta.text}")
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
        # Dica comum: 400 pode ser causado por modelo inválido, payload multimodal em modelo texto ou max_tokens alto
        print("[DICA] Verifique se o modelo suporta o formato enviado (multimodal vs texto) e se max_tokens não está alto.")
        return ""

def agente_explorador(url, max_passos=5, instrucoes_customizadas=None, modelo="qwen/qwen2.5-vl-7b", modo_extracao="padrao"):
    # Verificar se há uma instância da UI para controle de parada
    def check_stop_requested():
        try:
            from ui_agente import current_ui_instance
            return current_ui_instance and current_ui_instance.is_stop_requested()
        except:
            return False
    
    navegador, pagina, playwright = iniciar_navegador()
    pagina.goto(url)

    # Maximiza a janela após abertura
    pagina.evaluate("window.moveTo(0, 0); window.resizeTo(screen.width, screen.height);")

    fechar_aviso_de_cookies(pagina)
    
    # Injetar data-testids únicos para melhor estabilidade
    injetar_data_testids(pagina)
    
    seletores_visitados = set()
    historico_acoes = []  # Histórico de ações para contexto do LLM

    for passo in range(max_passos):
        # Verificar se foi solicitada a parada
        if check_stop_requested():
            print("🛑 Execução interrompida pelo usuário")
            logging.info("Execução interrompida pelo usuário")
            break
            
        print(f"\n[PASSO {passo+1}]")
        logging.info(f"PASSO {passo+1}")

        try:
            # Capturar URL atual antes da extração
            url_atual = pagina.url
            print(f"[INFO] URL atual: {url_atual}")
            
            html = extrair_html(pagina)

            # Salvar screenshot primeiro
            salvar_screenshot(pagina, passo + 1)
            screenshot_path = f"prints/passo_{passo + 1}.png"
            
            # Escolher modo de extração
            if modo_extracao == "otimizado":
                print("🔍 Usando extração otimizada para LLM...")
                navegacao_llm = extrair_elementos_otimizados_llm(pagina)
                
                if navegacao_llm:
                    # Salvar contexto otimizado
                    Path("logs").mkdir(exist_ok=True)
                    caminho_contexto = f"logs/contexto_otimizado_passo_{passo + 1}.json"
                    with open(caminho_contexto, "w", encoding="utf-8") as f:
                        json.dump(navegacao_llm, f, ensure_ascii=False, indent=2)
                    print(f"[📊] Contexto otimizado salvo em: {caminho_contexto}")
                    
                    # HEURÍSTICA DETERMINÍSTICA PARA LOGIN - SHORT-CIRCUIT IMPLEMENTADO
                    url_atual = navegacao_llm['pagina']['url']
                    tem_campos_login = (len(navegacao_llm['campos_formulario']['inputs_texto']) > 0 and 
                                       len(navegacao_llm['campos_formulario']['inputs_senha']) > 0)
                    is_login_page = 'login' in url_atual.lower()
                    tem_instrucao_login = instrucoes_customizadas and ('cpf' in instrucoes_customizadas.lower() or 'login' in instrucoes_customizadas.lower())
                    
                    if is_login_page and tem_campos_login and tem_instrucao_login:
                        print("🎯 DETECTADO: Página de login com campos - FORÇANDO heurística determinística")
                        
                        # Extrair CPF e senha da instrução
                        import re
                        cpf_match = re.search(r'cpf[:\s]*(\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})', instrucoes_customizadas.lower())
                        senha_match = re.search(r'senha[:\s]*(\S+)', instrucoes_customizadas.lower())
                        
                        if cpf_match and senha_match:
                            cpf = cpf_match.group(1).replace('.', '').replace('-', '')  # Apenas números
                            senha = senha_match.group(1)
                            
                            print(f"[🤖] EXECUTANDO LOGIN DETERMINÍSTICO - SEM LLM:")
                            print(f"    CPF extraído: {cpf}")
                            print(f"    Senha extraída: {senha}")
                            
                            # SELETORES ROBUSTOS PARA LOGIN
                            seletores_cpf = [
                                'form input[formcontrolname=cpf]',
                                'form input[name=cpf]',
                                'form input[placeholder*="CPF" i]',
                                'form input#login',
                                'form input[type=tel]',
                                'form input[type=text]:visible'
                            ]
                            
                            seletores_senha = [
                                'form input[formcontrolname=senha]',
                                'form input[name=senha]',
                                'form input[type=password]:visible'
                            ]
                            
                            seletores_submit = [
                                'form button[type=submit]:visible',
                                'form [role="button"]:has-text("Entrar"):visible',
                                'form button:has-text("Entrar"):visible',
                                'form input[type=submit]:visible'
                            ]
                            
                            login_executado = False
                            
                            # Tentar cada seletor de CPF até encontrar um que funcione
                            for sel_cpf in seletores_cpf:
                                try:
                                    if pagina.locator(sel_cpf).count() > 0:
                                        campo_cpf_atual = pagina.locator(sel_cpf).first.input_value()
                                        if campo_cpf_atual != cpf:  # Só preenche se estiver diferente
                                            pagina.locator(sel_cpf).first.wait_for(state="visible", timeout=3000)
                                            pagina.locator(sel_cpf).first.clear()
                                            pagina.locator(sel_cpf).first.fill(cpf)
                                            print(f"[✅] CPF preenchido com: {sel_cpf}")
                                        else:
                                            print(f"[ℹ️] CPF já preenchido em: {sel_cpf}")
                                        break
                                except Exception as e:
                                    print(f"[⚠️] Falhou seletor CPF {sel_cpf}: {e}")
                                    continue
                            
                            # Tentar cada seletor de senha até encontrar um que funcione
                            for sel_senha in seletores_senha:
                                try:
                                    if pagina.locator(sel_senha).count() > 0:
                                        campo_senha_atual = pagina.locator(sel_senha).first.input_value()
                                        if campo_senha_atual != senha:  # Só preenche se estiver diferente
                                            pagina.locator(sel_senha).first.wait_for(state="visible", timeout=3000)
                                            pagina.locator(sel_senha).first.clear()
                                            pagina.locator(sel_senha).first.fill(senha)
                                            print(f"[✅] Senha preenchida com: {sel_senha}")
                                        else:
                                            print(f"[ℹ️] Senha já preenchida em: {sel_senha}")
                                        break
                                except Exception as e:
                                    print(f"[⚠️] Falhou seletor senha {sel_senha}: {e}")
                                    continue
                            
                            # Tentar submit com múltiplas estratégias
                            for sel_submit in seletores_submit:
                                try:
                                    if pagina.locator(sel_submit).count() > 0:
                                        pagina.locator(sel_submit).first.click()
                                        print(f"[✅] Submit executado com: {sel_submit}")
                                        login_executado = True
                                        break
                                except Exception as e:
                                    print(f"[⚠️] Falhou submit {sel_submit}: {e}")
                                    continue
                            
                            # Fallbacks se submit não funcionou
                            if not login_executado:
                                try:
                                    print("[🔄] Tentando fallback: Enter no campo senha")
                                    for sel_senha in seletores_senha:
                                        if pagina.locator(sel_senha).count() > 0:
                                            pagina.locator(sel_senha).first.press("Enter")
                                            login_executado = True
                                            break
                                except Exception as e:
                                    print(f"[⚠️] Fallback Enter falhou: {e}")
                            
                            if not login_executado:
                                try:
                                    print("[🔄] Tentando fallback: Submit do formulário")
                                    pagina.evaluate("document.querySelector('form')?.requestSubmit?.()")
                                    login_executado = True
                                except Exception as e:
                                    print(f"[⚠️] Fallback form submit falhou: {e}")
                            
                            if login_executado:
                                # Aguardar navegação/carregamento
                                print("⏳ Aguardando resultado do login...")
                                time.sleep(5)  # Tempo maior para login
                                
                                # Verificar se houve mudança na URL (sucesso)
                                nova_url_login = pagina.url
                                if nova_url_login != url_atual:
                                    print(f"[🎯] LOGIN AUTOMÁTICO SUCESSO! {url_atual} → {nova_url_login}")
                                    
                                    # Adicionar login automático ao histórico
                                    acao_login_historico = {
                                        "passo": passo + 1,
                                        "acao": f"LOGIN AUTOMÁTICO: CPF={cpf}, Senha=***",
                                        "url_antes": url_atual,
                                        "url_depois": nova_url_login,
                                        "navegacao": True,
                                        "timestamp": datetime.now().strftime("%H:%M:%S")
                                    }
                                    historico_acoes.append(acao_login_historico)
                                    print(f"[📋] Login automático adicionado ao histórico")
                                    
                                    # Injetar data-testids na nova página
                                    injetar_data_testids(pagina)
                                    # Não encerrar automaticamente após login; seguir o fluxo do teste
                                    print("[INFO] Login concluído; prosseguindo com o teste.")
                                    continue
                                else:
                                    print(f"[⚠️] Login pode ter falhado - URL não mudou: {url_atual}")
                            else:
                                print(f"[❌] Falha total no login automático")
                        else:
                            print(f"[⚠️] CPF/senha não encontrados na instrução: {instrucoes_customizadas}")
                    
                    # SE CHEGOU AQUI: login automático falhou ou não aplicável - continuar com LLM
                    # Usar prompt otimizado antigo
                    prompt_otimizado, seletores_validos = gerar_prompt_otimizado_com_contexto(navegacao_llm, instrucoes_customizadas, historico_acoes)
                    
                    if prompt_otimizado:
                        payload = {
                            "model": modelo,
                            "messages": [
                                {"role": "system", "content": "Você é um assistente que analisa páginas web e responde apenas com JSON válido conforme solicitado."},
                                {"role": "user", "content": prompt_otimizado}
                            ],
                            "temperature": 0,
                            "top_p": 1,
                            "max_tokens": 2048,
                            "stop": ["\n\n", "\r\n\r\n"]
                        }
                    else:
                        print("[AVISO] Falha na geração do prompt otimizado, usando método padrão...")
                        payload, seletores_validos = gerar_prompt_em_chat_format(html, screenshot_path, instrucoes_customizadas, modelo, historico_acoes)
                else:
                    print("[AVISO] Falha na extração otimizada, usando método padrão...")
                    payload, seletores_validos = gerar_prompt_em_chat_format(html, screenshot_path, instrucoes_customizadas, modelo, historico_acoes)
            else:
                # USAR NOVA EXTRAÇÃO COMPLETA E AUTÔNOMA PARA MODO PADRÃO
                print("🚀 Usando extração completa e autônoma...")
                try:
                    payload, seletores_validos = gerar_prompt_autonomo_completo(
                        html, screenshot_path, instrucoes_customizadas, modelo, historico_acoes, pagina
                    )
                    
                    if payload and seletores_validos:
                        print(f"✅ Extração completa bem-sucedida: {len(seletores_validos)} elementos interativos encontrados")
                    else:
                        print("[AVISO] Falha na extração completa, usando método padrão...")
                        payload, seletores_validos = gerar_prompt_em_chat_format(html, screenshot_path, instrucoes_customizadas, modelo, historico_acoes)
                except Exception as e:
                    print(f"[ERRO] Falha na extração completa: {e}")
                    print("🔍 Usando método padrão...")
                    payload, seletores_validos = gerar_prompt_em_chat_format(html, screenshot_path, instrucoes_customizadas, modelo, historico_acoes)

            print("\n" + "="*80)
            print("📤 DADOS ENVIADOS AO MODELO LLM")
            print("="*80)
            print(f"🤖 Modelo: {payload['model']}")
            print(f"🌡️  Temperature: {payload['temperature']}")
            print(f"🔢 Max tokens: {payload['max_tokens']}")
            print(f"⏹️  Stop tokens: {payload['stop']}")
            print(f"🎯 Seletores válidos encontrados: {len(seletores_validos)}")
            
            # MOSTRAR TODOS OS SELETORES QUE ESTÃO SENDO ENVIADOS
            print(f"\n📋 LISTA COMPLETA DOS {len(seletores_validos)} SELETORES ENVIADOS AO LLM:")
            print("-" * 60)
            for i, sel in enumerate(seletores_validos, 1):
                print(f"{i:3d}. {sel}")
            print("-" * 60)
            
            # Mostrar o conteúdo das mensagens
            print(f"\n📋 MENSAGENS NO PAYLOAD:")
            for i, msg in enumerate(payload['messages'], 1):
                print(f"\n--- Mensagem {i} ---")
                print(f"Role: {msg['role']}")
                if isinstance(msg['content'], list):
                    # Conteúdo multimodal (imagem + texto)
                    for j, content_item in enumerate(msg['content']):
                        if content_item['type'] == 'image_url':
                            print(f"  [{j+1}] Tipo: Imagem (base64)")
                            print(f"      URL: data:image/png;base64,... ({len(content_item['image_url']['url'])} chars)")
                        elif content_item['type'] == 'text':
                            text_content = content_item['text']
                            print(f"  [{j+1}] Tipo: Texto ({len(text_content)} chars)")
                            # Mostrar primeiras linhas do prompt
                            lines = text_content.split('\n')
                            if len(lines) > 15:
                                preview = '\n'.join(lines[:15]) + f"\n... (mais {len(lines)-15} linhas)"
                            else:
                                preview = text_content
                            print(f"      Preview:\n{preview}")
                            
                            # Verificar se a seção ELEMENTOS DISPONÍVEIS está presente
                            if "ELEMENTOS DISPONÍVEIS:" in text_content:
                                elementos_section = text_content.split("ELEMENTOS DISPONÍVEIS:")[1] if "ELEMENTOS DISPONÍVEIS:" in text_content else ""
                                if elementos_section:
                                    linhas_elementos = [linha for linha in elementos_section.split('\n') if linha.strip() and not linha.startswith('Baseado')]
                                    print(f"      ✅ Seção 'ELEMENTOS DISPONÍVEIS' encontrada com {len(linhas_elementos)} itens")
                                else:
                                    print(f"      ⚠️  Seção 'ELEMENTOS DISPONÍVEIS' vazia")
                            else:
                                print(f"      ❌ Seção 'ELEMENTOS DISPONÍVEIS' não encontrada no texto!")
                else:
                    # Conteúdo apenas texto
                    text_content = msg['content']
                    print(f"  Tipo: Texto ({len(text_content)} chars)")
                    lines = text_content.split('\n')
                    if len(lines) > 15:
                        preview = '\n'.join(lines[:15]) + f"\n... (mais {len(lines)-15} linhas)"
                    else:
                        preview = text_content
                    print(f"  Preview:\n{preview}")
                    
                    # Verificar se a seção ELEMENTOS DISPONÍVEIS está presente
                    if "ELEMENTOS DISPONÍVEIS:" in text_content:
                        elementos_section = text_content.split("ELEMENTOS DISPONÍVEIS:")[1] if "ELEMENTOS DISPONÍVEIS:" in text_content else ""
                        if elementos_section:
                            linhas_elementos = [linha for linha in elementos_section.split('\n') if linha.strip() and not linha.startswith('Baseado')]
                            print(f"  ✅ Seção 'ELEMENTOS DISPONÍVEIS' encontrada com {len(linhas_elementos)} itens")
                        else:
                            print(f"  ⚠️  Seção 'ELEMENTOS DISPONÍVEIS' vazia")
                    else:
                        print(f"  ❌ Seção 'ELEMENTOS DISPONÍVEIS' não encontrada no texto!")
            
            # PAYLOAD COMPLETO (OPCIONAL - DESCOMENTE SE QUISER VER TUDO)
            # print(f"\n🔍 PAYLOAD COMPLETO:")
            # print(json.dumps(payload, indent=2, ensure_ascii=False))
            
            print("="*80)

            # Primeira tentativa
            resposta_llm = chamar_llm_openai_style(payload)

            if not resposta_llm.strip():
                print("[LLM] <Resposta vazia>")
                logging.warning("LLM respondeu vazio")
                continue

            print("[✔️ LLM]", resposta_llm.strip())
            logging.info(f"Resposta LLM: {resposta_llm.strip()}")

            # Validação com retry
            acao = validar_seletor_e_retry(resposta_llm, seletores_validos, chamar_llm_openai_style, payload)
            
            if not acao:
                print("[ERRO] Falha na validação do seletor após todas as tentativas")
                logging.error("Falha na validação do seletor")
                continue

            # Verificar novamente se foi solicitada a parada antes de executar ação
            if check_stop_requested():
                print("🛑 Execução interrompida pelo usuário antes da ação")
                logging.info("Execução interrompida pelo usuário antes da ação")
                break

            if acao.get("action") == "click":
                seletor = acao.get("selector")
                if seletor in seletores_visitados:
                    print(f"[AVISO] Seletor já visitado: {seletor}, pulando para evitar repetição.")
                    logging.info(f"Seletor repetido ignorado: {seletor}")
                    continue
                seletores_visitados.add(seletor)

            # Executar ação e capturar resultado estruturado
            resultado_acao = executar_acao(pagina, resposta_llm)
            
            # Coletar informações para o histórico
            nova_url = pagina.url
            sucesso_navegacao = nova_url != url_atual
            
            # Adicionar ao histórico de ações com resultado da verificação
            acao_historico = {
                "passo": passo + 1,
                "acao": resposta_llm.strip(),
                "url_antes": url_atual,
                "url_depois": nova_url,
                "navegacao": sucesso_navegacao,
                "resultado": resultado_acao,  # ✅ Inclui resultado da ação (sucesso/falha)
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            historico_acoes.append(acao_historico)
            
            # Manter apenas as últimas 5 ações para não sobrecarregar o LLM
            if len(historico_acoes) > 5:
                historico_acoes.pop(0)
            
            # Log do resultado da ação para o usuário
            if resultado_acao:
                status_icon = "✅" if resultado_acao.get('success') else "❌"
                action_desc = resultado_acao.get('action', 'ação')
                message = resultado_acao.get('message', '')
                print(f"[📋] Ação {action_desc}: {status_icon} {message}")
                logging.info(f"Resultado da ação: {resultado_acao}")
            
            print(f"[📋] Ação adicionada ao histórico: {resposta_llm.strip()}")
            
            # Aguardar carregamento da página após ação
            print("⏳ Aguardando carregamento da página...")
            try:
                # Aguarda até que o documento esteja carregado
                pagina.wait_for_load_state("domcontentloaded", timeout=5000)
                print("✅ Página carregada")
            except:
                print("⚠️ Timeout no carregamento - continuando")
            
            # Verificar se a URL mudou
            if sucesso_navegacao:
                print(f"[INFO] Navegação detectada: {url_atual} → {nova_url}")
                logging.info(f"Navegação: {url_atual} → {nova_url}")
                
                # Limpar estado dos campos preenchidos ao mudar de página
                from agent.utils import limpar_estado_campos
                limpar_estado_campos()
                print("[INFO] Estado dos campos limpo devido à navegação")
                
                # Injetar data-testids na nova página
                injetar_data_testids(pagina)
            else:
                print(f"[INFO] Ação executada na mesma página")
            
            # Se o objetivo foi atingido, encerrar
            atingido, motivo = objetivo_atingido(pagina, instrucoes_customizadas, url_atual, nova_url)
            if atingido:
                print(f"🏁 Objetivo cumprido: {motivo}. Encerrando teste.")
                break
            
            time.sleep(2)

        except Exception as e:
            print(f"[ERRO] Falha no passo {passo+1}: {e}")
            logging.error(f"Erro no passo {passo+1}: {e}")

    navegador.close()
    playwright.stop()
    print("\n[FIM] Navegação encerrada.")
    logging.info("Navegação encerrada.")

if __name__ == "__main__":
    # O entry point agora chama a UI diretamente.
    from ui_agente import main as ui_main
    ui_main()

