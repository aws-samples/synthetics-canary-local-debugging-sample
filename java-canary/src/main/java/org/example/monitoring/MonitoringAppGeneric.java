package org.example.monitoring;

import java.net.HttpURLConnection;
import java.net.URL;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class MonitoringAppGeneric {
    private static final Logger logger = LogManager.getLogger(MonitoringAppGeneric.class);

    public void handler() throws Exception {
        logger.info("Executing generic code without steps");
        URL obj = new URL("https://httpbin.org/delay/2");
        HttpURLConnection con = (HttpURLConnection)obj.openConnection();
        con.setRequestMethod("GET");
        con.setConnectTimeout(5000);
        con.setReadTimeout(5000);
        int status = con.getResponseCode();
        if (status != 200) {
            throw new Exception("Canary failed: HTTP status " + status + " (expected 200)");
        }
        logger.info("Canary passed: HTTP status " + status);
    }
}

