from flask import Flask, request, jsonify, Response
import nodriver as uc
import asyncio
import logging
import time

# ========== INICIALIZACIÓN DE FLASK (¡ESTA ERA LA LÍNEA QUE FALTABA!) ==========
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURACIÓN ==========
# Argumentos para Chrome que reducen el uso de memoria (clave en Render Free)
CHROME_ARGS = [
    '--headless=new',          # <-- AÑADIDO: Fuerza el modo headless moderno
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--single-process',
    '--no-zygote',
    '--disable-accelerated-2d-canvas',
    '--disable-software-rasterizer',
    '--window-size=1280,720',
]


# ========== FUNCIÓN ASÍNCRONA QUE USA NODRIVER ==========
async def obtener_html_con_nodriver(url_objetivo):
    """
    Lanza Chrome (vía nodriver), espera a que Cloudflare se resuelva solo,
    y devuelve el HTML final de la página.
    """
    driver = await uc.start(
        headless=True,      # Sin interfaz gráfica (esencial en servidor)
        browser_args=CHROME_ARGS,
    )
    try:
        page = await driver.get(url_objetivo)

        # Esperar a que Cloudflare termine (el título deja de ser "Just a moment...")
        for intento in range(15):
            await asyncio.sleep(2)
            title = await page.title()
            logger.info(f"Intento {intento + 1}/15 - Título actual: {title}")

            if "Just a moment" not in title and "Cloudflare" not in title and "Attention Required" not in title:
                logger.info("✅ Cloudflare resuelto.")
                break
        else:
            logger.warning("⚠️ Timeout esperando a que Cloudflare se resuelva.")

        # Esperar un poco más para asegurar que la página cargó el contenido dinámico
        await asyncio.sleep(2)

        html = await page.get_content()
        return html

    finally:
        # Cerrar el navegador SIEMPRE, incluso si hay excepción
        try:
            driver.stop()
        except Exception as e:
            logger.warning(f"No se pudo cerrar el driver limpiamente: {e}")


# ========== ENDPOINT PRINCIPAL ==========
@app.route('/obtener-html', methods=['GET'])
def obtener_html():
    url_objetivo = request.args.get('url')
    if not url_objetivo:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    logger.info(f"🌐 Petición recibida para: {url_objetivo}")
    inicio = time.time()

    try:
        html = asyncio.run(obtener_html_con_nodriver(url_objetivo))
        duracion = round(time.time() - inicio, 2)
        logger.info(f"✅ OK en {duracion}s | {len(html)} bytes")

        return Response(html, status=200, content_type="text/html; charset=utf-8")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({
            "error": "Error al obtener la URL",
            "detalle": str(e),
            "url_solicitada": url_objetivo
        }), 500


# ========== ENDPOINTS DE DIAGNÓSTICO ==========
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "motor": "nodriver"})


@app.route('/test-cloudflare', methods=['GET'])
def test_cloudflare():
    url_test = "https://jkanime.net/"
    logger.info(f"🧪 Test Cloudflare: {url_test}")

    try:
        html = asyncio.run(obtener_html_con_nodriver(url_test))

        bloqueado = (
            "Just a moment" in html or
            "Checking your browser" in html or
            "cf-browser-verification" in html or
            "Enable JavaScript and cookies to continue" in html
        )

        return jsonify({
            "url": url_test,
            "bloqueado_por_cloudflare": bloqueado,
            "tamaño_respuesta": len(html),
            "preview": html[:500],
            "motor": "nodriver"
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "url": url_test,
            "motor": "nodriver"
        }), 500


# ========== MAIN ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
