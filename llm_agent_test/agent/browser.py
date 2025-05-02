from playwright.sync_api import sync_playwright

def iniciar_navegador():
    playwright = sync_playwright().start()

    navegador = playwright.chromium.launch(
        headless=False,
        args=[
            "--start-maximized",
            "--disable-infobars",
            "--disable-notifications",
            "--force-device-scale-factor=1",
            "--window-size=1920,1080",
        ]
    )

    contexto = navegador.new_context(
        viewport=None,  # permite ao browser usar toda a tela disponível
        device_scale_factor=1,
        screen={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )

    pagina = contexto.new_page()

    # Redimensiona via JS para garantir que a janela ocupe a área total visível
    pagina.evaluate("""
        () => {
            window.moveTo(0, 0);
            window.resizeTo(screen.availWidth, screen.availHeight);
        }
    """)

    print("[INFO] Navegador iniciado em tela cheia.")
    return navegador, pagina, playwright
