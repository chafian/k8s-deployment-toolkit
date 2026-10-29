#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/rendered
api=monitoring.coreos.com/v1/ServiceMonitor
helm lint charts/app --strict
helm template contract charts/app --kube-version 1.34.0 > build/rendered/default.yaml
for app in nginx spring-boot; do
  for environment in staging production; do
    helm lint charts/app --strict -f "environments/$environment.yaml" -f "examples/$app/values.yaml"
    helm template contract charts/app --kube-version 1.34.0 \
      -f "environments/$environment.yaml" -f "examples/$app/values.yaml" \
      > "build/rendered/$app-$environment.yaml"
  done
done
helm lint charts/app --strict -f tests/fixtures/all-features.yaml --set serviceMonitor.requireCRD=false
helm template contract charts/app --api-versions "$api" -f tests/fixtures/all-features.yaml > build/rendered/all-features.yaml
helm template contract charts/app --api-versions "$api" -f examples/spring-boot/values.yaml \
  -f examples/spring-boot/values-monitoring.yaml > build/rendered/spring-monitoring.yaml
helm template contract charts/app -f environments/production.yaml -f examples/spring-boot/values.yaml \
  -f examples/spring-boot/values-ingress.yaml > build/rendered/spring-ingress.yaml
python3 -m unittest discover -s tests -v
# CRDs require their own server/schema validation. Never silently skip unknown built-in kinds.
for version in 1.30.0 1.34.0; do
  kubeconform -strict -summary -kubernetes-version "$version" -skip ServiceMonitor build/rendered
done
helm package charts/app --destination build
