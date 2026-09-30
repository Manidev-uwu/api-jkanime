from flask import Flask, request, jsonify, Response
from curl_cffi import requests as curl_requests
import logging
import time

app = Flask(__name__)

# Configurar logging para ver qué pasa en Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURACIÓN ==========
# Navegador a impersonar. chrome124 es el más reciente y efectivo.
NAVEGADOR_IMPERSONAR = "chrome124"

# Headers para parecer un navegador real
HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


# ========== ENDPOINT PRINCIPAL (Reemplaza a /obtener-html) ==========
@app.route('/obtener-html', methods=['GET'])
def obtener_html():
    """
    Endpoint que actúa como proxy para obtener el HTML de una URL.
    Usa curl_cffi para impersonar la huella TLS de un navegador real.
    """
    url_objetivo = request.args.get('url')

    if not url_objetivo:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    logger.info(f"🌐 Petición recibida para: {url_objetivo}")
    inicio = time.time()

    try:
        response = curl_requests.get(
            url_objetivo,
            headers=HEADERS_BASE,
            impersonate=NAVEGADOR_IMPERSONAR,
            timeout=30,
            allow_redirects=True,
        )

        duracion = round(time.time() - inicio, 2)
        logger.info(f"✅ Status: {response.status_code} | Duración: {duracion}s | Tamaño: {len(response.text)} bytes")

        # Devolver el HTML con el mismo status code
        return Response(
            response.text,
            status=response.status_code,
            content_type="text/html; charset=utf-8"
        )

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
    """Endpoint simple para verificar que el servicio está vivo."""
    return jsonify({
        "status": "ok",
        "navegador_impersonado": NAVEGADOR_IMPERSONAR
    })


@app.route('/test-cloudflare', methods=['GET'])
def test_cloudflare():
    """
    Endpoint de prueba para verificar si podemos pasar Cloudflare.
    Hace una petición a jkanime.net y reporta el resultado.
    """
    url_test = "https://jkanime.net/"
    logger.info(f"🧪 Test Cloudflare contra: {url_test}")

    try:
        response = curl_requests.get(
            url_test,
            headers=HEADERS_BASE,
            impersonate=NAVEGADOR_IMPERSONAR,
            timeout=30,
            allow_redirects=True,
        )

        html = response.text
        # Detectar si Cloudflare nos bloqueó
        bloqueado = (
            "Just a moment" in html or
            "Checking your browser" in html or
            "cf-browser-verification" in html or
            "Enable JavaScript and cookies to continue" in html
        )

        return jsonify({
            "url": url_test,
            "status_code": response.status_code,
            "bloqueado_por_cloudflare": bloqueado,
            "tamaño_respuesta": len(html),
            "preview": html[:500],
            "navegador_usado": NAVEGADOR_IMPERSONAR
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "url": url_test,
            "navegador_usado": NAVEGADOR_IMPERSONAR
        }), 500


# ========== MAIN ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
