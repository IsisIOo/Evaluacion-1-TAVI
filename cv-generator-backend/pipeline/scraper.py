# Script de extracción con Playwright/BS4
import json
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright

def cargar_config():
    """Lee el archivo JSON con las areas y busquedas clave"""
    config_path = Path(__file__).with_name('search_config.json')

    with config_path.open('r', encoding='utf-8') as f:
        return json.load(f) 

def bloquear_recursos(route, request):
    """Bloquea recursos innecesarios como imágenes, fuentes, etc"""
    tipos_bloqueados = ["image", "font", "stylesheet", "media"]

    if request.resource_type in tipos_bloqueados:
        route.abort()
    else:
        route.continue_()

def iniciar_scraper():
    areas_config = cargar_config()
    enlaces_totales = []

    with sync_playwright() as p:
        # lanzar navegador
        browser = p.chromium.launch(headless=False, slow_mo=50)

        # crear contexto para disfrazar scraper bot
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            timezone_id="America/Santiago",
            locale="es-CL",
            geolocation={"latitude": -33.4489, "longitude": -70.6693},
            permissions=["geolocation"],
            ignore_https_errors=True
        )
        # abrir pestaña con contexto
        page = context.new_page()
        # bloquear recursos innecesarios
        page.route("**/*", bloquear_recursos)

        for area in areas_config:
            print(f"=== Explorando Area: {area['area']} ===")
            for keyword in area['keywords']:
                print(f"  - Buscando: {keyword}")

                # formatear keyword para URL
                keyword_url = urllib.parse.quote(keyword)
                url_busqueda = f"https://www.bne.cl/ofertas?mostrar=empleo&textoLibre={keyword_url}&numResultadosPorPagina=10&clasificarYPaginar=true"

                try:
                    # navegar a url
                    page.goto(url_busqueda, wait_until="networkidle")
                    # esperar a que carguen las ofertas
                    page.wait_for_selector('article.resultadoOfertas', timeout=8000)
                    # extraer enlaces de ofertas
                    elementos_enlaces = page.query_selector_all('article.resultadoOfertas div.tituloOferta a')
                    # limpiar enlaces
                    links_unicos = set()
                    for elem in elementos_enlaces:
                        href = elem.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                href = f"https://www.bne.cl{href}"
                            links_unicos.add(href)
                    
                    links_finales = list(links_unicos)[:10] # se toman las 10 primeras ofertas
                    enlaces_totales.extend(links_finales)

                    print(f"    Encontrados {len(links_finales)} enlaces para '{keyword}'")
                except Exception as e:
                    print(f"    Error al buscar '{keyword}': {e}")
                
                # pequeña pausa entre búsquedas para evitar bloqueos
                page.wait_for_timeout(2000)

        print(f"\n=== Total de enlaces encontrados: {len(enlaces_totales)} ===")

        context.close()
        browser.close()

if __name__ == "__main__":
    iniciar_scraper()