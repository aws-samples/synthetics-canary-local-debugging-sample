// Import Synthetics Canary SDK
import { synthetics } from '@amzn/synthetics-playwright';

export const handler = async (event, context) => {
    try {
        console.log('Running Synthetics Playwright canary');
        // Launch browser
        const browser = await synthetics.launch();
        const browserContext = await browser.newContext();

        // Get page
        const page = await synthetics.newPage(browserContext);

        // Execute step
        await synthetics.executeStep("home-page", async () => {
            const response = await page.goto('https://www.example.com', { waitUntil: 'load', timeout: 30000 });
            const status = response.status();
            // If the response status code is not a 2xx success code
            if (status < 200 || status > 299) {
                console.error(`Failed to load url: ${url}, status code: ${status}`);
                throw new Error('Home page did not load');
            }
        })

        await synthetics.executeStep("verify-title", async () => {
            const title = await page.title();
            if (title !== "Example Domain") {
                throw new Error('Expected title did not match');
            }
        })

    } finally {
        // Ensure browser is closed
        await synthetics.close();
    }
};