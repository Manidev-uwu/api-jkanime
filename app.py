import nodriver as uc
import asyncio

async def obtener_html_con_nodriver(url_objetivo):
    # Lanza el navegador con opciones para ahorrar memoria
    driver = await uc.start(
        headless=True, # Ejecución sin interfaz gráfica
        browser_args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage', # Importante para entornos con poca memoria
            '--single-process', # Puede ayudar a reducir el uso de memoria
            '--no-zygote',
            '--disable-gpu',
        ]
    )
    try:
        page = await driver.get(url_objetivo)
        # Esperar a que el desafío de Cloudflare se resuelva (el título cambia)
        for _ in range(15):
            await asyncio.sleep(2)
            title = await page.title()
            if "Just a moment" not in title and "Cloudflare" not in title:
                break
        html = await page.get_content()
        return html
    finally:
        await driver.stop()

@app.route('/obtener-html', methods=['GET'])
def obtener_html():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Falta url"}), 400
    try:
        html = asyncio.run(obtener_html_con_nodriver(url))
        return Response(html, content_type="text/html; charset=utf-8")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
