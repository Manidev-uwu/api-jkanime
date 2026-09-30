from flask import Flask, request, jsonify, Response
import nodriver as uc
import asyncio
import logging
import time

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ARGUMENTOS DE CHROME (con --headless=new) ==========
CHROME_ARGS = [
    '--headless=new',
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


async def obtener_html_con_nodriver(url_objetivo):
    logger.info(f"Iniciando nodriver para: {url_objetivo}")

    driver = await uc.start(
        headless=True,
        browser_args=CHROME_ARGS,
        browser_executable_path="/usr/bin/chromium",
    )

    # Verificación defensiva: si driver es None, uc.start() falló
    if driver is None:
        raise Exception(
            "uc.start() devolvió None. Posibles causas: "
            "1) websockets incompatible (usa websockets==13.1), "
            "2) Chromium no encontrado en /usr/bin/chromium, "
            "3) Falta --headless=new en browser_args."
        )

    try:
        page = await driver.get(url_objetivo)

        for intento in range(15):
            await asyncio.sleep(2)
            title = await page.title()
            logger.info(f"Intento {intento + 1}/15 - Título: {title}")

            if "Just a moment" not in title and "Cloudflare" not in title and "Attention Required" not in title:
                logger.info("✅ Cloudflare resuelto.")
                break
        else:
            logger.warning("⚠️ Timeout esperando a que Cloudflare se resuelva.")

        await asyncio.sleep(2)
        html = await page.get_content()
        return html

    finally:
        try:
            driver.stop()
        except Exception as e:
            logger.warning(f"Error al cerrar driver: {e}")


@app.route('/obtener-html', methods=['GET'])
def obtener_html():
    url_objetivo = request.args.get('url')
    if not url_objetivo:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    logger.info(f"🌐 Petición: {url_objetivo}")
    inicio = time.time()

    try:
        html = asyncio.run(obtener_html_con_nodriver(url_objetivo))
        duracion = round(time.time() - inicio, 2)
        logger.info(f"✅ OK en {duracion}s | {len(html)} bytes")
        return Response(html, status=200, content_type="text/html; charset=utf-8")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return jsonify({
            "error": str(e),
            "url_solicitada": url_objetivo
        }), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "motor": "nodriver"})


@app.route('/test-cloudflare', methods=['GET'])
def test_cloudflare():
    url_test = "https://jkanime.net/"
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
        return jsonify({"error": str(e), "url": url_test}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
