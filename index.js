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
        // Abrimos el navegador Chrome invisible
        browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        });
        
        const page = await browser.newPage();
        
        // Vamos a la página y esperamos a que el tráfico de red se calme
        await page.goto(urlDestino, { waitUntil: 'networkidle2', timeout: 45000 });
        
        // Esperamos 3 segundos extra para asegurar que Cloudflare terminó su verificación
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Extraemos el HTML puro
        const htmlLimpio = await page.content();
        await browser.close();

        // Lo devolvemos a tu Apps Script
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
