"""
Módulo para injetar data-testids únicos em elementos interativos.
Isso torna os seletores mais estáveis e determinísticos.
"""

def injetar_data_testids(pagina):
    """
    Injeta data-testids únicos em elementos interativos da página.
    PULA elementos invisíveis para evitar que o modelo tente clicar neles.
    """
    script = """
    () => {
        let counter = 1;
        
        // Selecionar todos os elementos interativos
        const elements = document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [onclick], [role="button"]');
        
        elements.forEach(el => {
            // VERIFICAR SE O ELEMENTO ESTÁ VISÍVEL
            const style = window.getComputedStyle(el);
            const isVisible = (
                el.offsetParent !== null &&
                style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                style.opacity !== '0' &&
                el.offsetWidth > 0 &&
                el.offsetHeight > 0
            );
            
            // Só adicionar testid se não tem E se está visível
            if (!el.hasAttribute('data-testid') && isVisible) {
                let testid = '';
                
                // Gerar testid baseado no texto ou contexto
                const text = el.textContent?.trim() || el.value || el.getAttribute('aria-label') || '';
                
                if (text) {
                    // Limpar texto para criar um ID válido
                    testid = text
                        .toLowerCase()
                        .replace(/[áàâãä]/g, 'a')
                        .replace(/[éèêë]/g, 'e')
                        .replace(/[íìîï]/g, 'i')
                        .replace(/[óòôõö]/g, 'o')
                        .replace(/[úùûü]/g, 'u')
                        .replace(/[ç]/g, 'c')
                        .replace(/[^a-z0-9]/g, '-')
                        .replace(/-+/g, '-')
                        .replace(/^-|-$/g, '')
                        .substring(0, 30);
                }
                
                // Se não conseguiu gerar do texto, usar tag + contador
                if (!testid) {
                    testid = el.tagName.toLowerCase() + '-' + counter;
                }
                
                // Garantir unicidade
                const finalTestid = 'auto-' + testid + '-' + counter;
                el.setAttribute('data-testid', finalTestid);
                counter++;
            }
        });
        
        return counter - 1; // Retorna quantos foram processados
    }
    """
    
    try:
        elementos_processados = pagina.evaluate(script)
        print(f"[🏷️] {elementos_processados} data-testids injetados na página")
        return elementos_processados
    except Exception as e:
        print(f"[⚠️] Erro ao injetar data-testids: {e}")
        return 0
