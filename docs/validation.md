# Local validation record

Validated on **29 October 2026**, Europe/Madrid, on an Apple Silicon host with Docker.
This records local execution, not a production certification. Public CI results are
available in [GitHub Actions](https://github.com/chafian/k8s-deployment-toolkit/actions).

## Results

| Check | Result |
| --- | --- |
| Helm 3.19.0 strict lint | Passed for defaults, four app/environment combinations and all-features configuration. Only informational recommendation: chart icon. |
| Helm template | Eight render variants passed, including Spring ingress and monitoring overlays. |
| Chart contract suite | 10 tests passed, including data-driven invalid configuration and application/environment combinations. |
| kubeconform 0.8.0 | Each Kubernetes 1.30.0 and 1.34.0 pass validated 43 built-in resources; 0 invalid, 0 errors. Two ServiceMonitor objects explicitly skipped and covered separately through the CRD. |
| Helm packaging | app-0.1.0.tgz created successfully; local review artifact only. |
| kind 0.30.0 / Kubernetes 1.34.0 | Nginx installed under Restricted Pod Security, HTTP test succeeded, upgrade to 3 ready replicas passed, rollback to 2 passed, HTTP retest succeeded. |
| Optional resource API validation | Production Ingress/HPA/PDB and all-features objects passed server dry-run. ServiceMonitor validated against Prometheus Operator v0.94.2 CRD. |
| Spring Boot 3.5.16 / Java 17 container build | Maven verify passed: 2 tests, 0 failures/errors/skips. Image built successfully. |
| Spring live deployment | Rollout passed under Restricted Pod Security. Helm tests reached both `/` and `/actuator/prometheus` through the Service. |
| GitHub Actions syntax | actionlint 1.7.7 passed. |
| Shell scripts | Bash syntax checks passed. |
| Secret scan | Gitleaks 8.24.2 scanned the source-only publication snapshot: no leaks found. |
| Documentation | Local relative links checked; commands, option names, overlays and stated limitations reviewed against the implementation. |

Reproduce the core validation with `make validate` and the live checks with
`make cluster-test`; see the root README for tool setup. The live test script creates
its own cluster/kubeconfig and deletes them on completion. No kind clusters remain
from this session. The local demo image and downloaded public Docker build/image
cache remain available for reuse; no image was pushed.

## Fixes found during validation and review

- `charts/app/templates/tests/http.yaml` — retain completed hook Pods so Helm can fetch `--logs`; replace on the next test.
- `charts/app/templates/tests/http.yaml` — exclude hook Pods from application Service/PDB selectors.
- `charts/app/values.schema.json` — reject zero CPU/memory/storage quantities.
- `charts/app/values.schema.json` — prevent ServiceMonitor extra labels from replacing chart identity labels.
- `examples/spring-boot/values.yaml` and `values-ingress.yaml` — disable inherited generic ingress and provide an explicit Exact `/` route that keeps `/actuator` out of that public rule.

clean-code-guard: 5 fixed, 0 flagged for author

The Spring test setup explicitly enables observability because Spring Boot suppresses
external meter registries in full-context tests by default. The HTTP/metrics assertion
was retained and now passes with the real registry. The chart test suite retains a
regression test for hook log retention and selector isolation. test-guard and
docs-guard final passes found no remaining issues within their scope.

## Limits of this evidence

- GitHub Actions results are recorded separately by the hosted workflow. No container image is published by this repository.
- Ingress/TLS termination, certificate issuance/renewal, live HPA scaling and eviction under PDB were not exercised with their controllers.
- Prometheus scraping/alerts and Argo CD reconciliation were not exercised. ServiceMonitor received real API/CRD validation; Argo CD files are a reviewed configuration example.
- Kubernetes 1.30 received schema checks, not a live cluster test. Live cluster evidence is limited to 1.34.0 on arm64; GitHub Actions runs the same suite on hosted amd64 runners; consult its run history for that separate evidence.
- No vulnerability scan, load test, failure-domain test or uptime guarantee is asserted. Review current image dependencies and production requirements before release.
- Apache-2.0 and public repository publication were approved by the owner on 29 October 2026. No packaged release or container registry publication is implied.


## Final publication review

### Standards

Two findings were fixed: quote all dynamic YAML string fields, and reject generated
Service names beginning with digits. The independent reviewer confirmed both fixes;
0 remaining findings. The schema and configuration guide now explain the naming
contract, and the suite includes regression cases for both failures.

### Spec

The independent specification review found the same two naming defects. Both are
fixed and all requested MVP features are present; 0 remaining findings. This review
does not expand the runtime evidence beyond the limitations listed above.

clean-code-guard: 2 fixed, 0 flagged for author in the final publication pass.

The approved license is applied to the source and chart distribution. Documentation
now describes public usage and private vulnerability reporting instead of a license
proposal. docs-guard and test-guard checks were repeated for the changed material.
