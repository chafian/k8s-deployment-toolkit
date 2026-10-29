package io.github.chafian.toolkit;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.autoconfigure.actuate.observability.AutoConfigureObservability;
import org.springframework.boot.test.web.client.TestRestTemplate;

import static org.assertj.core.api.Assertions.assertThat;

// SpringBootTest disables external meter registries unless explicitly enabled.
@AutoConfigureObservability(tracing = false)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class DemoApplicationTest {
    @Autowired
    private TestRestTemplate http;

    @Test
    void applicationAndProbeEndpointsAreReachable() {
        assertThat(http.getForObject("/", String.class)).contains("k8s-deployment-toolkit");
        for (String probe : new String[]{"liveness", "readiness"}) {
            var response = http.getForEntity("/actuator/health/" + probe, String.class);
            assertThat(response.getStatusCode().value()).isEqualTo(200);
            assertThat(response.getBody()).contains("UP");
        }
    }

    @Test
    void metricsAreAvailableButSensitiveActuatorEndpointsAreHidden() {
        var metrics = http.getForEntity("/actuator/prometheus", String.class);
        assertThat(metrics.getStatusCode().value()).isEqualTo(200);
        assertThat(metrics.getBody()).contains("jvm_memory_used_bytes");
        for (String endpoint : new String[]{"env", "configprops", "heapdump"}) {
            assertThat(http.getForEntity("/actuator/" + endpoint, String.class)
                    .getStatusCode().value()).isEqualTo(404);
        }
    }
}
