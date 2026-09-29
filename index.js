const express = require('express');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/obtener-html', async (req, res) => {
    const urlDestino = req.query.url;

    if (!urlDestino) {
        return res.status(400).send('Debes enviar una URL');
    }

    let browser;
    try {
        console.log(`Extrayendo: ${urlDestino}`);
        // Abrimos el navegador con configuraciones para parecer más "humano"
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--window-size=1280,720'
            ]
        });
        
        const page = await browser.newPage();
        
        // Ponemos un User-Agent de un humano real
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36');

        await page.goto(urlDestino, { waitUntil: 'domcontentloaded', timeout: 45000 });
        
        // === LÓGICA ANTI-CLOUDFLARE ===
        let title = await page.title();
        let intentos = 0;
        
        // Si el título dice "Just a moment..." estamos atrapados en Cloudflare
        while ((title.includes('Just a moment') || title.includes('Cloudflare')) && intentos < 15) {
            console.log(`Atrapado en Cloudflare. Esperando... (Intento ${intentos + 1}/15)`);
            await new Promise(r => setTimeout(r, 2000)); // Esperamos 2 segundos
            
            // Simulamos mover el ratón y hacer clics al azar (esto a veces engaña al Captcha de Cloudflare)
            try {
                const x = 300 + Math.floor(Math.random() * 200);
                const y = 300 + Math.floor(Math.random() * 200);
                await page.mouse.click(x, y);
            } catch(e) {}

            title = await page.title(); // Volvemos a revisar el título
            intentos++;
        }

        // Si salimos del bucle, esperamos 3 segundos extra para que cargue la página real de anime
        await new Promise(r => setTimeout(r, 3000));

        // Extraemos el HTML ya limpio
        const htmlLimpio = await page.content();
        await browser.close();

        // Lo devolvemos a Apps Script
        res.send(htmlLimpio);

    } catch (error) {
        console.error(error);
        if (browser) await browser.close();
        res.status(500).send('Error extrayendo la página');
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`API iniciada y escuchando en el puerto ${PORT}`);
});
