# Script de extracción con Playwright/BS4
import json
import urllib.parse
import os
import time
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
    ofertas_a_procesar = [] # array de dicts: {"url": link, "area_trabajo": area}

    # archivo de salida
    ruta_salida = Path(__file__).resolve().parent.parent / 'data' / 'datos_ofertas.jsonl'
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

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

        tiempo_inicio = time.time()

        print("||| FASE 1: EXTRACCIÓN DE ENLACES |||")

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
                    for link in links_finales:
                        ofertas_a_procesar.append({
                            "url": link,
                            "area_trabajo": area['area']
                        })

                    print(f"    Encontrados {len(links_finales)} enlaces para '{keyword}'")
                except Exception as e:
                    print(f"    Error al buscar '{keyword}': {e}")
                
                # pequeña pausa entre búsquedas para evitar bloqueos
                page.wait_for_timeout(2000)

        print(f"\n=== Total de enlaces encontrados: {len(ofertas_a_procesar)} ===")

        print("\n||| FASE 2: EXTRACCIÓN DE DESCRIPCIONES |||")

        with ruta_salida.open('w', encoding='utf-8') as f:
            for oferta in ofertas_a_procesar:
                url_oferta = oferta['url']
                area_trabajo = oferta['area_trabajo']

                try:
                    page.goto(url_oferta, wait_until="domcontentloaded")
                    panel_descripcion = page.locator('article.panelFormulario').filter(has_text="DESCRIPCIÓN")
                    parrafo_descripcion = panel_descripcion.locator('.panel-body p').first
                    parrafo_descripcion.wait_for(state="attached", timeout=5000)
                    texto_descripcion = parrafo_descripcion.inner_text().strip()

                    # armar dict
                    registro = {
                        "area_trabajo": area_trabajo,
                        "descripcion": texto_descripcion
                    }
                    f.write(json.dumps(registro, ensure_ascii=False) + "\n")
                    print(f"    Procesada oferta: {url_oferta}")
                except Exception as e:
                    print(f"    [X] Error al procesar '{url_oferta}': {e}")
                
                page.wait_for_timeout(1000) # pausa entre ofertas
        
        tiempo_fin = time.time()
        duracion = tiempo_fin - tiempo_inicio
        print(f"\n=== Scraping finalizado en {duracion:.2f} segundos ===")

        context.close()
        browser.close()

if __name__ == "__main__":
    iniciar_scraper()