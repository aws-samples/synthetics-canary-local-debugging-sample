package org.example.monitoring;

import java.net.HttpURLConnection;
import java.net.URL;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import software.amazon.synthetics.StepConfiguration;
import software.amazon.synthetics.StepOptions;
import software.amazon.synthetics.Synthetics;

public class MonitoringAppWithSteps {
    private static final Logger logger = LogManager.getLogger(MonitoringAppWithSteps.class);

    public void handler(Synthetics synthetics) throws Exception {
        createStep("Step1", synthetics, "https://httpbin.org/delay/4");
        createStep("Step2", synthetics, "https://httpbin.org/redirect/2");
        return;
    }
  
    private void createStep(String stepName, Synthetics synthetics, String url) throws Exception {
        logger.info("Executing step: " + stepName);
        synthetics.executeStep(stepName,() -> {
            URL obj = new URL(url);
            HttpURLConnection con = (HttpURLConnection)obj.openConnection();
            con.setRequestMethod("GET");
            con.setConnectTimeout(5000);
            con.setReadTimeout(5000);
            int status = con.getResponseCode();
            if(status != 200){
                throw new Exception("Failed to load" + url + "status code:" + status);
            }
            return null;
        }).get();
    }
}
