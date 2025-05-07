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
            "--window-size=1920,1080",  # ainda útil para forçar o tamanho da janela
        ]
    )

    contexto = navegador.new_context(
        viewport={"width": 1920, "height": 1080},  # define viewport visível
        device_scale_factor=1,
        screen={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )

    pagina = contexto.new_page()

    print("[INFO] Navegador iniciado em 1920x1080.")
    return navegador, pagina, playwright
