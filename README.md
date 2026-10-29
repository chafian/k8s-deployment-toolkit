# k8s-deployment-toolkit

A reusable Helm 3 chart for deploying stateless HTTP applications, with runnable
Nginx and Spring Boot examples, maintained by [chafian](https://github.com/chafian).

**Version:** 0.1.0. **License:** Apache-2.0.
See [licensing](docs/licensing.md) and [local validation evidence](docs/validation.md).

## What is included

- Deployment and ClusterIP Service with stable selectors and rolling updates.
- JSON Schema validation, including unknown-setting rejection and bounded ports.
- Non-root containers, read-only root filesystems, dropped capabilities, runtime
  seccomp, no mounted API token, resource requests/limits, and bounded `/tmp` storage.
- HTTP startup, readiness, and liveness probes; optional Ingress/TLS, CPU HPA,
  PodDisruptionBudget, and Prometheus ServiceMonitor.
- Existing ConfigMap/Secret references and image pull secret references.
- Staging/production overlays, a restricted Argo CD project and manual-sync example.
- Render contract tests, Kubernetes schema checks, Helm HTTP tests, and disposable
  cluster install/upgrade/rollback tests in GitHub Actions.

The chart intentionally covers **one Linux container and one HTTP port**. It does
not provision databases, persistent volumes, certificates, ingress controllers,
metrics-server, Prometheus, or Argo CD. It grants no RBAC permissions. Network policy
and workload-specific authentication remain deployment decisions.

## Quick start: Nginx

Prerequisites: Helm 3 (tested with **3.19.0**), `kubectl`, and a Kubernetes cluster.
Chart API range: **1.30–1.34**; schema validation covers both endpoints and live tests
use **1.34.0**. This is an API compatibility range, not a recommendation to run an
unsupported Kubernetes version. See [validation](docs/validation.md) for limits.

Clone the repository, then run from its root with your intended cluster selected:

```bash
git clone https://github.com/chafian/k8s-deployment-toolkit.git
cd k8s-deployment-toolkit
```

```bash
helm lint charts/app --strict
helm upgrade --install demo charts/app \
  --namespace toolkit-demo --create-namespace \
  -f examples/nginx/values.yaml --wait --atomic --timeout 3m
helm test demo --namespace toolkit-demo --logs
kubectl -n toolkit-demo port-forward service/demo-app 8080:80
```

Open `http://localhost:8080`. The default image is the upstream unprivileged Nginx
image on port 8080. It runs as UID/GID 101 with `/tmp` as its writable directory.

```bash
# Remove this example when finished.
helm uninstall demo --namespace toolkit-demo
kubectl -n toolkit-demo delete pod demo-app-test --ignore-not-found
```

Uninstall removes chart resources; it does not delete the namespace or referenced
Secrets/ConfigMaps.

## Configure an application

[Default values](charts/app/values.yaml) contain every setting;
[values.schema.json](charts/app/values.schema.json) is the validation contract.
The [configuration guide](docs/configuration.md) explains the options and their
interaction. The chart supports HTTP applications able to run without root and
write temporary files only under `/tmp`.

```yaml
image:
  repository: registry.example.com/team/web
  tag: "1.0.0"
containerPort: 8080
security:
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
env:
  APP_ENV: production
envFrom:
  configMaps: [web-config]
  secrets: [web-credentials]
```

This is a configuration illustration, not a public image. Create the referenced
resources separately in the release namespace. Secret **values** must never be
committed to Helm values: Helm stores release configuration in the cluster.

## Environments

The generic overlays demonstrate Nginx sizing and routing. Before enabling ingress,
replace `example.com` hosts, select an installed ingress class, and provision the
named TLS Secret in the release namespace. TLS settings reference a certificate;
they do not issue one or enforce an HTTP-to-HTTPS redirect across every controller.
Production autoscaling also requires metrics-server and suitable cluster capacity.

```bash
helm template demo charts/app \
  -f environments/production.yaml -f examples/nginx/values.yaml

# Only after configuring the DNS, TLS, ingress controller, and metrics prerequisites:
helm upgrade --install demo charts/app -n toolkit-production --create-namespace \
  -f environments/production.yaml -f examples/nginx/values.yaml \
  --wait --atomic --timeout 5m
```

Values files apply **left to right**. Environment settings go first, then application
settings so Spring's memory sizing and health endpoints take precedence. Use a final
private deployment overlay for real hostnames, approved image digests and sizing.
For production, set `image.digest` to a verified `sha256:…`; a digest overrides the
tag. Example image tags are versioned but mutable and must be scanned and reviewed
before use. The all-features test fixture contains a synthetic digest for rendering
only; never install that fixture.

## Spring Boot, monitoring, and GitOps

- [Spring Boot demo](examples/spring-boot/README.md): build an original Java 17 app,
  load it into kind, deploy it, and verify Actuator probes and Prometheus metrics.
- [Nginx example](examples/nginx/README.md): image constraints and deployment steps.
- [Operations](docs/operations.md): HPA, ServiceMonitor, TLS, rollout, rollback,
  troubleshooting, and production review.
- [Argo CD example](gitops/argocd/README.md): namespace-scoped permissions and manual
  sync, using a reviewed immutable commit from this repository.

## Run the checks

Python 3.9+ is used for local checks (CI uses 3.12). Install test tools locally:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-test.txt
python scripts/install-tools.py helm kubeconform kind
export PATH="$PWD/work/bin:$PATH"
make validate
```

The installer downloads pinned versions and verifies upstream SHA-256 checksums.
Validation lints/renders the chart and examples, runs contract tests, validates
built-in Kubernetes resources against 1.30/1.34 schemas, and packages the chart in
`build/`. ServiceMonitor is separately validated against the real CRD in the cluster
suite; it is explicitly skipped by kubeconform, not silently accepted.

With Docker running and `kubectl` installed:

```bash
make cluster-test
```

This creates its own kind cluster and kubeconfig, enforces Restricted Pod Security
in the test namespace, checks Nginx install/upgrade/rollback and HTTP, validates
optional resources against the API server, builds/tests the Spring Boot image, and
checks its HTTP and metrics endpoints. It deletes the cluster on success or failure.
It downloads public images, dependencies, and a pinned ServiceMonitor CRD; it never
uses the current cluster context. Budget several GB of disk and sufficient Docker
memory for one control plane and the demo workloads.

GitHub Actions runs these commands on pull requests and main-branch pushes.
It has read-only repository permissions and contains no deploy or publish job.
Actions are pinned to commits; Dependabot proposes dependency updates.

## Repository map

| Path | Purpose |
| --- | --- |
| `charts/app/` | Reusable chart, schema, and HTTP test hook |
| `environments/` | Generic staging and production overlays |
| `examples/` | Nginx values and original Spring Boot demo |
| `gitops/argocd/` | AppProject and Application references |
| `tests/` | Real Helm rendering contract tests |
| `scripts/` | Validation, tool installation, isolated cluster tests |
| `docs/` | Configuration, operations, licensing, validation evidence |

Read [CONTRIBUTING](CONTRIBUTING.md) before changes and [SECURITY](SECURITY.md)
before reporting vulnerabilities. Licensed under [Apache-2.0](LICENSE);
see [NOTICE](NOTICE) for attribution.
