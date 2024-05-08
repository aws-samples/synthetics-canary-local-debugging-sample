/**
 * This is a sample heartbeat canary to run in local dev environment.
 */
const synthetics = require('Synthetics');
const log = require('SyntheticsLogger');
const { simpleFaker } = require('@faker-js/faker');


const heartbeatCanary = async function () {
    log.info("UUID: " + simpleFaker.string.uuid());

    const URL = "https://www.example.com/";

    let page = await synthetics.getPage();
    const response = await page.goto(URL, {waitUntil: 'domcontentloaded', timeout: 30000});
    if (!response) {
        throw new Error("Failed to load page!");
    }
    // Wait for few seconds
    await new Promise(r => setTimeout(r, 5000));
    await synthetics.takeScreenshot('loaded', 'loaded');
    let pageTitle = await page.title();
    log.info('Page title: ' + pageTitle);

    //If the response status code is not a 2xx success code
    if (response.status() < 200 || response.status() > 299) {
        throw new Error("Failed to load page!");
    }
};

exports.handler = async () => {
    return await heartbeatCanary();
};