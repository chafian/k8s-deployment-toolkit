#!/usr/bin/env bash
# Only targets a disposable cluster created here; never the current user context.
set -euo pipefail
cd "$(dirname "$0")/.."
cluster="toolkit-test-$$"
mkdir -p build
export KUBECONFIG="$(pwd)/build/$cluster.kubeconfig"
cleanup() {
  status=$?
  if [ "$status" -ne 0 ]; then
    kubectl get pods -A -o wide || true
    kubectl -n toolkit-test describe pods || true
    kind export logs "build/$cluster-logs" --name "$cluster" || true
  fi
  kind delete cluster --name "$cluster"
  rm -f "$KUBECONFIG"
  exit "$status"
}
trap cleanup EXIT
kind create cluster --name "$cluster" --image kindest/node:v1.34.0 --wait 120s
kubectl create namespace toolkit-test
kubectl label namespace toolkit-test pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/enforce-version=v1.34
helm upgrade --install nginx charts/app -n toolkit-test -f examples/nginx/values.yaml --wait --atomic --timeout 3m
helm test nginx -n toolkit-test --logs --timeout 60s
helm upgrade nginx charts/app -n toolkit-test -f examples/nginx/values.yaml --set replicaCount=3 --wait --atomic --timeout 3m
test "$(kubectl -n toolkit-test get deployment nginx-app -o jsonpath='{.status.readyReplicas}')" = 3
helm rollback nginx 1 -n toolkit-test --wait --timeout 3m
test "$(kubectl -n toolkit-test get deployment nginx-app -o jsonpath='{.spec.replicas}')" = 2
helm test nginx -n toolkit-test --logs --timeout 60s
# Server validation includes Ingress/HPA/PDB without relying on installed controllers.
helm template production charts/app -n toolkit-test -f environments/production.yaml --skip-tests | kubectl apply --dry-run=server -f -
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.94.2/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
kubectl wait --for=condition=Established crd/servicemonitors.monitoring.coreos.com --timeout=60s
helm template integrations charts/app -n toolkit-test --skip-tests \
  --api-versions monitoring.coreos.com/v1/ServiceMonitor -f tests/fixtures/all-features.yaml | kubectl apply --dry-run=server -f -
if [ "${TEST_SPRING:-0}" = 1 ]; then
  docker build -t toolkit-spring-demo:0.1.0 examples/spring-boot
  kind load docker-image toolkit-spring-demo:0.1.0 --name "$cluster"
  helm upgrade --install spring charts/app -n toolkit-test -f examples/spring-boot/values.yaml --wait --atomic --timeout 5m
  helm test spring -n toolkit-test --logs --timeout 60s
  helm upgrade spring charts/app -n toolkit-test --reuse-values --set tests.path=/actuator/prometheus --wait --timeout 3m
  helm test spring -n toolkit-test --logs --timeout 60s
fi
