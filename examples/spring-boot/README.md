# Spring Boot example

This original demonstration app uses Java 17, Spring Boot 3.5.16, Actuator and
Micrometer Prometheus. It has no customer code, database, credentials, or private
service dependencies. `/` returns a fixed greeting to demonstrate HTTP routing.

## Build and deploy to kind

From the repository root, with Docker, Helm 3, kind and kubectl installed:

```bash
mkdir -p work
docker build -t toolkit-spring-demo:0.1.0 examples/spring-boot
kind create cluster --name toolkit-spring --image kindest/node:v1.34.0 \
  --kubeconfig ./work/spring.kubeconfig
export KUBECONFIG="$PWD/work/spring.kubeconfig"
kind load docker-image toolkit-spring-demo:0.1.0 --name toolkit-spring
helm upgrade --install spring charts/app -n toolkit-demo --create-namespace \
  -f examples/spring-boot/values.yaml --wait --atomic --timeout 5m
helm test spring -n toolkit-demo --logs
kubectl -n toolkit-demo port-forward service/spring-app 8080:80
```

Create `work/` first if it does not exist. The Docker build runs the Java integration
tests before packaging. The image runs as UID/GID 10001 with a read-only root
filesystem and bounded `/tmp`. Readiness and liveness use separate Actuator health
groups on the application port; startup allows up to 300 seconds. Shutdown drains
for up to 20 seconds within the chart's 30-second termination grace period.

With the port-forward running, in another terminal:

```bash
curl --fail http://localhost:8080/
curl --fail http://localhost:8080/actuator/health/readiness
curl --fail http://localhost:8080/actuator/health/liveness
curl --fail http://localhost:8080/actuator/prometheus
```

Only health and prometheus Actuator endpoints are exposed; health details are
hidden. The demo has no authentication and is intended for an isolated environment.
Metrics remain accessible to cluster clients that can reach the Service.

## Environment and monitoring overlays

Apply environment values first, then this application's values. The Spring values
disable the generic public ingress to prevent accidentally exposing `/actuator`.
For optional public access, review `values-ingress.yaml`, replace its host and
TLS Secret, and apply it last; it exposes only the exact `/` route.

```bash
helm template spring charts/app \
  -f environments/production.yaml \
  -f examples/spring-boot/values.yaml \
  -f examples/spring-boot/values-ingress.yaml
```

After installing Prometheus Operator and configuring its selectors, add
`-f examples/spring-boot/values-monitoring.yaml` to your install/upgrade. The monitor
scrapes `/actuator/prometheus`. For a remote cluster, build, scan and publish the
image to an approved registry only after authorization, then override the repository
and digest in your own deployment values. This project publishes nothing itself.

For application-only tests with Java 17+ and Maven 3.9+, use
`mvn -f examples/spring-boot/pom.xml verify`.

Cleanup:

```bash
kind delete cluster --name toolkit-spring
rm -f ./work/spring.kubeconfig
```
