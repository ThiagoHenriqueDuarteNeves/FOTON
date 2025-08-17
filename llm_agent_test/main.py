import time
import logging
import json
import re
from datetime import datetime
from pathlib import Path
from agent.browser import iniciar_navegador
from agent.llm import chamar_llm_openai_style, obter_modelos_disponiveis, obter_modelo_carregado, normalizar_payload  # LLM functions
from agent.io import configurar_logging, salvar_screenshot, salvar_payload_log, salvar_resposta_modelo  # I/O functions
from agent.validation import objetivo_atingido, validar_resposta_llm  # Validation functions
from agent.browser_actions import executar_acao, fechar_aviso_de_cookies, limpar_estado_campos  # Browser actions
from agent.html_parser import extrair_html  # HTML parsing
from agent.prompt_generator import gerar_prompt_em_chat_format, extrair_elementos_otimizados_llm, gerar_prompt_autonomo_completo, validar_seletor_e_retry, gerar_prompt_otimizado_com_contexto  # Prompt generation
from agent.testid_injector import injetar_data_testids  # Novo injetor
import requests

# Configurar logging usando módulo de I/O
configurar_logging('navegacao.log')

def capturar_valores_atuais(pagina):
    """Captura valores atuais de todos os campos de formulário na página"""
    try:
        valores_campos = {}
        
        # Usar método síncrono do Playwright para capturar valores
        # Capturar valores de inputs de texto, email, tel, password, etc.
        try:
            inputs = pagina.locator('input[type="text"], input[type="email"], input[type="tel"], input[type="password"], input[type="number"], input[type="url"], input:not([type])').all()
            for input_elem in inputs:
                try:
                    value = input_elem.input_value() or ''  # Usar input_value() em vez de get_attribute('value')
                    if value.strip():
                        # Tentar identificar o campo pelo name, id ou placeholder
                        name = input_elem.get_attribute('name') or input_elem.get_attribute('id') or input_elem.get_attribute('placeholder') or 'campo_sem_nome'
                        valores_campos[f"[name='{name}']"] = value.strip()  # Formato seletor consistente
                except:
                    continue
        except:
            pass
                
        # Capturar valores de textareas
        try:
            textareas = pagina.locator('textarea').all()
            for textarea in textareas:
                try:
                    value = textarea.input_value() or ''  # Usar input_value() em vez de get_attribute('value')
                    if value.strip():
                        name = textarea.get_attribute('name') or textarea.get_attribute('id') or textarea.get_attribute('placeholder') or 'textarea_sem_nome'
                        valores_campos[f"[name='{name}']"] = value.strip()
                except:
                    continue
        except:
            pass
                
        # Capturar valores de selects
        try:
            selects = pagina.locator('select').all()
            for select in selects:
                try:
                    value = select.input_value() or ''  # Usar input_value() para selects também
                    if value.strip() and value.strip() != '':
                        name = select.get_attribute('name') or select.get_attribute('id') or 'select_sem_nome'
                        valores_campos[f"[name='{name}']"] = value.strip()
                except:
                    continue
        except:
            pass
        
        return valores_campos
    except Exception as e:
        print(f"⚠️ Erro ao capturar valores atuais: {e}")
        return {}

def normalizar_acao_llm(acao_data):
    """
    Normaliza resposta do LLM para formato padronizado em inglês
    """
    if not isinstance(acao_data, dict):
        return None
    
    # Mapeamento de chaves português -> inglês
    mapeamento_chaves = {
        "acao": "action",
        "seletor": "selector", 
        "valor": "value",
        "confianca": "confidence",
        "justificativa": "justification"
    }
    
    # Mapeamento de ações português -> inglês/padronizado
    mapeamento_acoes = {
        "cadastro": "click",     # Mapear cadastro para click
        "clicar": "click",
        "clique": "click", 
        "digitar": "type",
        "escrever": "type",
        "rolar": "scroll",
        "aguardar": "wait",
        "enviar": "submit"
    }
    
    # Criar nova estrutura normalizada
    acao_normalizada = {}
    
    for chave_pt, chave_en in mapeamento_chaves.items():
        if chave_pt in acao_data:
            valor = acao_data[chave_pt]
            
            # Normalizar ação se for a chave "acao"
            if chave_pt == "acao" and valor in mapeamento_acoes:
                valor = mapeamento_acoes[valor]
            
            acao_normalizada[chave_en] = valor
        elif chave_en in acao_data:
            # Já está em inglês
            acao_normalizada[chave_en] = acao_data[chave_en]
    
    # Garantir campos obrigatórios
    if "action" not in acao_normalizada:
        acao_normalizada["action"] = "click"  # padrão
    
    print(f"🔧 [NORMALIZAÇÃO] {acao_data} → {acao_normalizada}")
    return acao_normalizada


def navegar_com_agente(url, max_passos=5, instrucoes_customizadas=None, modelo=None, modo_extracao="padrao"):
    """
    Agente explorador que navega automaticamente em páginas web usando IA.
    
    Args:
        url (str): URL inicial para navegação
        max_passos (int): Número máximo de passos/ações
        instrucoes_customizadas (str): Instruções específicas do usuário
        modelo (str): Modelo LLM a usar (se None, detecta automaticamente)
        modo_extracao (str): Modo de extração ("padrao", "autonomo", "completo")
    """
    # Detectar modelo automaticamente se não especificado
    if modelo is None:
        modelo_detectado = obter_modelo_carregado()
        if modelo_detectado:
            modelo = modelo_detectado
            print(f"✅ Modelo pré-selecionado: {modelo}")
        else:
            modelo = "qwen/qwen2.5-vl-7b"  # fallback
            print(f"⚠️ Nenhum modelo detectado, usando fallback: {modelo}")

    # Iniciar navegador e executar loop de navegação dentro da função
    print("🚀 DEBUG: Prestes a iniciar navegador...")
    navegador, pagina, playwright = iniciar_navegador()
    print("🚀 DEBUG: Navegador iniciado com sucesso!")
    
    print("🚀 DEBUG: Navegando para a URL...")
    pagina.goto(url)
    print("🚀 DEBUG: Navegação para URL concluída!")

    # Maximiza a janela após abertura
    print("🚀 DEBUG: Maximizando janela...")
    pagina.evaluate("window.moveTo(0, 0); window.resizeTo(screen.width, screen.height);")
    print("🚀 DEBUG: Janela maximizada!")

    print("🚀 DEBUG: Fechando avisos de cookies...")
    fechar_aviso_de_cookies(pagina)
    print("🚀 DEBUG: Avisos de cookies fechados!")
    
    # Injetar data-testids únicos para melhor estabilidade
    print("🚀 DEBUG: Injetando data-testids...")
    injetar_data_testids(pagina)
    print("🚀 DEBUG: Data-testids injetados!")
    
    seletores_visitados = set()
    historico_acoes = []  # Histórico de ações para contexto do LLM
    seletores_validos_anteriores = None  # Para detectar mudança de seletores

    print("🚀 DEBUG: Iniciando loop principal...")
    for passo in range(max_passos):
        print(f"🚀 DEBUG: Iniciando PASSO {passo+1}/{max_passos}...")
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
            
            # Aguardar carregamento completo da página
            print("⏳ Aguardando carregamento completo da página...")
            pagina.wait_for_load_state('networkidle', timeout=10000)
            pagina.wait_for_timeout(2000)  # Aguarda mais 2 segundos para elementos dinâmicos
            
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
                    prompt_otimizado, seletores_validos = gerar_prompt_otimizado_com_contexto(navegacao_llm, instrucoes_customizadas, historico_acoes, modelo)
                    
                    if prompt_otimizado:
                        payload = {
                            "model": modelo,
                            "messages": [
                                {"role": "system", "content": "Você é um assistente que analisa páginas web e responde apenas com JSON válido conforme solicitado."},
                                {"role": "user", "content": prompt_otimizado}
                            ],
                            "temperature": 0,
                            "top_p": 1,
                            "max_tokens": 2048
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

            # ★ CAPTURAR VALORES ATUAIS DOS CAMPOS PARA EVITAR LOOPS ★
            print("🔍 Capturando valores atuais dos campos...")
            valores_atuais = capturar_valores_atuais(pagina)
            
            if valores_atuais:
                print(f"📋 CAMPOS JÁ PREENCHIDOS DETECTADOS:")
                for campo, valor in valores_atuais.items():
                    print(f"   • {campo}: '{valor}'")
                
                # Adicionar informações dos campos preenchidos ao payload
                if isinstance(payload, dict) and 'messages' in payload:
                    for msg in payload['messages']:
                        if msg.get('role') == 'user':
                            if isinstance(msg['content'], str):
                                # Adicionar seção de campos preenchidos ao prompt
                                campos_preenchidos_info = "\n\n=== CAMPOS JÁ PREENCHIDOS ===\n"
                                campos_preenchidos_info += "⚠️ NÃO preencha novamente estes campos que já possuem valores:\n"
                                for campo, valor in valores_atuais.items():
                                    campos_preenchidos_info += f"  • Campo '{campo}': já contém '{valor}'\n"
                                campos_preenchidos_info += "========================\n"
                                
                                msg['content'] = msg['content'] + campos_preenchidos_info
                                break
                            elif isinstance(msg['content'], list):
                                # Para conteúdo multimodal, adicionar ao texto
                                for content_item in msg['content']:
                                    if content_item.get('type') == 'text':
                                        campos_preenchidos_info = "\n\n=== CAMPOS JÁ PREENCHIDOS ===\n"
                                        campos_preenchidos_info += "⚠️ NÃO preencha novamente estes campos que já possuem valores:\n"
                                        for campo, valor in valores_atuais.items():
                                            campos_preenchidos_info += f"  • Campo '{campo}': já contém '{valor}'\n"
                                        campos_preenchidos_info += "========================\n"
                                        
                                        content_item['text'] = content_item['text'] + campos_preenchidos_info
                                        break
            else:
                print("📋 Nenhum campo preenchido detectado")

            print("\n" + "="*80)
            print("📤 DADOS ENVIADOS AO MODELO LLM")
            print("="*80)
            print(f"🤖 Modelo: {payload['model']}")
            print(f"🌡️  Temperature: {payload['temperature']}")
            print(f"🔢 Max tokens: {payload['max_tokens']}")
            if 'stop' in payload:
                print(f"⏹️  Stop tokens: {payload['stop']}")
            print(f"🎯 Seletores válidos encontrados: {len(seletores_validos)}")
            
            # Verificar se a lista de seletores mudou e resetar histórico se necessário
            if seletores_validos_anteriores is not None:
                seletores_atuais_set = set(seletores_validos)
                seletores_anteriores_set = set(seletores_validos_anteriores)
                
                if seletores_atuais_set != seletores_anteriores_set:
                    print(f"🔄 Lista de seletores mudou - resetando histórico")
                    print(f"   Seletores anteriores: {len(seletores_anteriores_set)} elementos")
                    print(f"   Seletores atuais: {len(seletores_atuais_set)} elementos")
                    historico_acoes = []  # Reset do histórico
                    seletores_visitados = set()  # Reset dos seletores visitados
            
            # Atualizar lista de seletores para próxima comparação  
            seletores_validos_anteriores = seletores_validos.copy()
            
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

            # Preparar e enviar payload ao LLM
            print("\n" + "="*80)
            print("📤 DADOS ENVIADOS AO MODELO LLM")
            print("="*80)
            try:
                payload = normalizar_payload(payload, modelo)
            except Exception:
                # Se normalizar falhar, continuar com payload original
                pass
            try:
                salvar_payload_log(payload, modelo)
            except Exception:
                pass

            # Chamar LLM
            try:
                resposta_llm = chamar_llm_openai_style(payload)
            except Exception as e:
                print(f"[ERRO] Falha ao chamar LLM: {e}")
                logging.error(f"Erro ao chamar LLM: {e}")
                continue

            if not resposta_llm or not resposta_llm.strip():
                print("[LLM] <Resposta vazia>")
                logging.warning("LLM respondeu vazio")
                continue

            print("[✔️ LLM]", resposta_llm.strip())
            logging.info(f"Resposta LLM: {resposta_llm.strip()}")

            if '```' in resposta_llm:
                print("🚨 [AVISO] LLM usou markdown - formato será corrigido automaticamente")

            # Validar seletor e tentar retry se necessário
            acao = validar_seletor_e_retry(resposta_llm, seletores_validos, chamar_llm_openai_style, payload)
            if not acao:
                print("[ERRO] Falha na validação do seletor após todas as tentativas")
                logging.error("Falha na validação do seletor")
                continue

            # Normalizar ação
            acao = normalizar_acao_llm(acao)
            if not acao:
                print("[ERRO] Falha na normalização da ação")
                continue

            # Salvar resposta completa do modelo para análise
            try:
                salvar_resposta_modelo(resposta_llm, acao, passo, modelo)
            except Exception as e:
                print(f"⚠️ Aviso: Erro ao salvar resposta do modelo: {e}")

            seletor_acao = acao.get("selector", "")
            # Usar validação flexível em vez de verificar apenas na lista
            if seletor_acao:
                from agent.validation import validar_seletor_existente
                if not validar_seletor_existente(seletor_acao, seletores_validos):
                    print(f"🚨 [ERRO CRÍTICO] Seletor '{seletor_acao}' inválido - ação rejeitada")
                    print(f"📋 Seletores válidos (exemplo): {seletores_validos[:5]}")
                    continue

            if check_stop_requested():
                print("🛑 Execução interrompida pelo usuário antes da ação")
                logging.info("Execução interrompida pelo usuário antes da ação")
                break

            action_type = acao.get('action')
            selector = acao.get('selector')
            value = acao.get('value')
            
            if action_type == 'type':
                print(f"📝 [PREENCHENDO] Campo {selector}")
                if value:
                    print(f"   ✏️  Valor: '{value}'")
            elif action_type == 'click':
                print(f"🎯 [CLICANDO] {selector}")
            elif action_type == 'submit':
                print(f"📤 [ENVIANDO] Formulário via {selector}")
            else:
                print(f"🎯 [EXECUTANDO] {action_type} em {selector}")
                if value:
                    print(f"   Valor: {value}")

            # Verificar se é ação repetida (mas não bloquear)
            seletor = acao.get("selector")
            acao_repetida = seletor and seletor in seletores_visitados
            
            if acao_repetida:
                print(f"[INFO] Ação repetida detectada para seletor: {seletor} - executando mesmo assim")
                logging.info(f"Ação repetida executada: {seletor}")
            
            # Adicionar à lista de visitados
            if seletor:
                seletores_visitados.add(seletor)

            # Preparar payload normalizado para execução: converter a ação validada (em inglês) para JSON string
            try:
                if isinstance(acao, dict):
                    payload_exec = {
                        "action": acao.get("action"),
                        "selector": acao.get("selector", ""),
                        "value": acao.get("value", ""),
                        # manter confidence/justification se disponíveis
                        **({"confidence": acao.get("confidence")} if acao.get("confidence") is not None else {}),
                        **({"justification": acao.get("justification")} if acao.get("justification") else {})
                    }
                    resposta_para_execucao = json.dumps(payload_exec, ensure_ascii=False)
                else:
                    # fallback: usar a resposta LLm bruta
                    resposta_para_execucao = resposta_llm
            except Exception as e:
                logging.error(f"Erro ao preparar payload de execução: {e}")
                resposta_para_execucao = resposta_llm

            # Executar a ação uma única vez usando payload normalizado
            try:
                resultado_acao = executar_acao(pagina, resposta_para_execucao)
            except Exception as e:
                print(f"[ERRO] Falha ao executar ação: {e}")
                logging.error(f"Falha ao executar ação: {e}")
                resultado_acao = None

            # Normalizar o resultado para um dicionário consistente
            resultado_dict = None
            try:
                if isinstance(resultado_acao, tuple) and len(resultado_acao) >= 2:
                    sucesso_flag = bool(resultado_acao[0])
                    mensagem = str(resultado_acao[1]) if len(resultado_acao) > 1 else ""
                    resultado_dict = {"success": sucesso_flag, "message": mensagem}
                elif isinstance(resultado_acao, dict):
                    resultado_dict = resultado_acao
                elif resultado_acao is None:
                    resultado_dict = None
                else:
                    resultado_dict = {"success": False, "message": str(resultado_acao)}
            except Exception as e:
                logging.error(f"Erro ao normalizar resultado_acao: {e}")
                resultado_dict = {"success": False, "message": f"Erro ao normalizar resultado: {e}"}

            nova_url = pagina.url
            sucesso_navegacao = nova_url != url_atual

            # Adicionar informação sobre ação repetida ao histórico
            acao_info = resposta_llm.strip()
            if acao_repetida:
                acao_info += f" [AÇÃO REPETIDA: seletor {seletor} já foi usado anteriormente]"

            # Extrair justificativa da ação para histórico mais rico
            justificativa = acao.get('justification', acao.get('justificativa', 'Não informada'))
            confianca = acao.get('confidence', acao.get('confianca', 0))

            acao_historico = {
                "passo": passo + 1,
                "acao": acao.get('action', acao.get('acao', 'N/A')),
                "seletor": acao.get('selector', acao.get('seletor', 'N/A')), 
                "valor": acao.get('value', acao.get('valor', '')),
                "justificativa": justificativa,
                "confianca": confianca,
                "sucesso": resultado_dict.get('success', False),
                "url_antes": url_atual,
                "url_depois": nova_url,
                "navegacao": sucesso_navegacao,
                "resultado": resultado_dict,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "repetida": acao_repetida  # Flag para uso interno
            }
            historico_acoes.append(acao_historico)

            # Não limitamos mais o histórico por número fixo de ações
            # O histórico será mantido até que a lista de seletores mude

            if resultado_dict:
                status_icon = "✅" if resultado_dict.get('success') else "❌"
                action_desc = resultado_dict.get('action', 'ação')
                message = resultado_dict.get('message', '') or resultado_dict.get('message', '')
                print(f"[📋] Ação {action_desc}: {status_icon} {message}")
                logging.info(f"Resultado da ação: {resultado_dict}")

            # Aguardar carregamento
            try:
                pagina.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass

            # Checar objetivo
            atingido, motivo = objetivo_atingido(pagina, instrucoes_customizadas, url_atual, nova_url)
            if atingido:
                print(f"🏁 Objetivo cumprido: {motivo}. Encerrando teste.")
                break

            time.sleep(2)

        except Exception as e:
            print(f"[ERRO] Falha no passo {passo+1}: {e}")
            logging.error(f"Erro no passo {passo+1}: {e}")

    try:
        navegador.close()
    except Exception:
        pass
    try:
        playwright.stop()
    except Exception:
        pass
    print("\n[FIM] Navegação encerrada.")
    logging.info("Navegação encerrada.")

def check_stop_requested():
    """Verificar se há uma instância da UI para controle de parada"""
    try:
        from ui_agente import current_ui_instance
        return current_ui_instance and current_ui_instance.is_stop_requested()
    except:
        return False


if __name__ == "__main__":
    import argparse
    import sys
    
    # Se tem argumentos de linha de comando, processar diretamente
    if len(sys.argv) > 1:
        print("🚀 DEBUG: Processando argumentos da linha de comando...")
        
        parser = argparse.ArgumentParser(description='Agente IA para navegação web')
        parser.add_argument('--url', required=True, help='URL inicial para navegação')
        parser.add_argument('--instrucoes', required=True, help='Instruções para o agente')
        parser.add_argument('--max_passos', type=int, default=10, help='Número máximo de passos')
        parser.add_argument('--modelo', help='Modelo LLM a usar')
        parser.add_argument('--modo_extracao', default='padrao', help='Modo de extração')
        
        args = parser.parse_args()
        
        print("🚀 DEBUG: Argumentos processados, iniciando navegar_com_agente...")
        navegar_com_agente(
            url=args.url,
            max_passos=args.max_passos,
            instrucoes_customizadas=args.instrucoes,
            modelo=args.modelo,
            modo_extracao=args.modo_extracao
        )
    else:
        # Se não tem argumentos, chamar a UI
        from ui_agente import main as ui_main
        ui_main()

