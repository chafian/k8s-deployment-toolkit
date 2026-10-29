# Configuration contract

Helm validates merged values before rendering. Unknown keys are errors. Values are
data; none are evaluated with Helm's `tpl` function. Arrays replace earlier arrays
when layering files. Optional features are disabled by default except probes and
the HTTP test hook.

| Setting | Contract |
| --- | --- |
| `nameOverride`, `fullnameOverride` | Optional DNS labels, maximum 63 characters. The final resource name (including the Helm release prefix) must start with a letter for Service compatibility. Use fullnameOverride to correct a digit-leading release name. Changing names/selectors after installation can require recreation. |
| `replicaCount` | Positive integer, default 2. Omitted from Deployment when HPA is enabled. |
| `image.repository`, `tag`, `digest`, `pullPolicy` | Tag or digest required. Digest wins. Pull policy: Always, IfNotPresent, Never. |
| `imagePullSecrets` | Array of existing Secret names, also used by the test hook. |
| `containerPort` | HTTP container port, 1024–65535. Named `http` throughout the chart. |
| `command`, `args` | Optional arrays of strings, passed directly to the container. |
| `env` | Map of environment names to **strings**; quote booleans/numbers. Not for secrets. |
| `envFrom.configMaps`, `envFrom.secrets` | Existing names in the release namespace. Updates do not automatically restart Pods. |
| `service.port`, `service.annotations` | ClusterIP port (default 80); string annotations. |
| `serviceAccount.create`, `name`, `annotations` | Default: dedicated account. Existing account requires a name. Token automount is always disabled on Pods. |
| `podAnnotations` | String annotation map, for example for an external restart controller. |
| `security.runAsUser`, `runAsGroup`, `fsGroup` | Positive numeric identity. Defaults 101; Spring demo uses 10001. Root is rejected. |
| `resources.requests`, `resources.limits` | CPU and memory are required positive quantity strings. The API server also checks requests do not exceed limits. |
| `tmpSizeLimit` | Positive quantity, default 64Mi; disk-backed ephemeral volume mounted at `/tmp`. |
| `terminationGracePeriodSeconds` | Positive seconds, default 30. Spring demo graceful shutdown timeout is 20 seconds. |
| `probes.startup`, `readiness`, `liveness` | Each has enabled, absolute HTTP path, periodSeconds, timeoutSeconds, failureThreshold. One named HTTP port. |
| `ingress.enabled`, `className`, `annotations`, `hosts`, `tls` | Enabled requires class and hosts. Each host has paths with path/pathType. TLS entries require secretName and hosts. |
| `autoscaling.enabled`, `minReplicas`, `maxReplicas`, `targetCPUUtilizationPercentage` | CPU utilization HPA, max >= min; 300-second scale-down stabilization. CPU requests are mandatory. |
| `pdb.enabled`, `maxUnavailable` | Optional budget with integer unavailable count; default 1. Protects voluntary evictions, not all failures. |
| `serviceMonitor.enabled`, `labels`, `path`, `interval`, `scrapeTimeout`, `requireCRD` | Default path /metrics, interval 30s, timeout 10s. Extra labels cannot overwrite chart identity labels. |
| `tests.enabled`, `image`, `path` | Helm test Pod using `wget --spider`, default busybox:1.37.0 and `/`. |

Security invariants are not configurable: non-root, RuntimeDefault seccomp,
read-only root filesystem, no privilege escalation, drop ALL capabilities, no
service-account token. Applications needing sidecars, root, persistent storage,
additional ports, or writes outside `/tmp` are outside this MVP.

The quantity schema accepts a practical subset of Kubernetes quantity syntax;
it intentionally rejects zero resources and omits exotic forms. API validation
is still necessary: JSON Schema does not prove that an image exists, Secret names
resolve, requests fit node capacity, or TLS hosts match issued certificates.

An invalid example such as `--set service.port=70000` fails schema validation with
`service.port` in the error. If ServiceMonitor rendering reports a missing CRD,
install Prometheus Operator first. For offline rendering only, declare the API:

```bash
helm template demo charts/app \
  -f examples/spring-boot/values.yaml \
  -f examples/spring-boot/values-monitoring.yaml \
  --api-versions monitoring.coreos.com/v1/ServiceMonitor
```

`requireCRD: false` bypasses this early check for tools without discovery (including
`helm lint`); it does not install the CRD. Keep it true for cluster installation.
Set scrape timeout no longer than interval. The Prometheus Operator performs
additional semantic checks. Nginx itself does not export Prometheus metrics in
this example; do not enable its ServiceMonitor without adding a metrics endpoint.
