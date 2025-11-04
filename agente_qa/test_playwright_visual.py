"""Teste simples do Playwright"""
from playwright.sync_api import sync_playwright
import time

print("🚀 Iniciando teste do Playwright...")

with sync_playwright() as p:
    print("✅ Playwright iniciado")
    
    browser = p.chromium.launch(headless=False)
    print("✅ Browser lançado (headless=False)")
    
    page = browser.new_page()
    print("✅ Página criada")
    
    page.goto("https://example.com")
    print("✅ Navegado para example.com")
    
    print("⏳ Aguardando 10 segundos para você ver o browser...")
    time.sleep(10)
    
    browser.close()
    print("✅ Teste concluído!")
