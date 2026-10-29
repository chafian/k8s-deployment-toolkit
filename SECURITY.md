# Security policy

## Reporting

Report vulnerabilities privately through
[GitHub private vulnerability reporting](https://github.com/chafian/k8s-deployment-toolkit/security/advisories/new).
Do not disclose sensitive evidence in public issues. Include the affected chart
version, Kubernetes/Helm versions, redacted values, reproduction steps, observed
impact, and any mitigation. Never submit credentials, private client code or
unredacted logs. No response-time SLA is offered.

## Support scope

Security fixes target the newest 0.1.x chart version, with no SLA. Kubernetes API compatibility does not imply upstream
security support for those Kubernetes versions. The deployment owner remains
responsible for supported clusters, image updates and workload security.

## Security model

The chart fixes non-root execution, RuntimeDefault seccomp, read-only root storage,
no privilege escalation, dropped capabilities and disabled API token automount.
It creates no RBAC bindings or Kubernetes Secrets. Existing Secrets/ConfigMaps and
registry credentials are referenced by name. Application environment values are
stored in Helm release state and must not contain secret material.

The demo is a single HTTP service, not a multitenant platform. There is no default
NetworkPolicy, authentication, image signature enforcement, secret manager, runtime
threat detector or certificate controller. Supply those through your platform.
ServiceMonitor and Ingress are opt-in; the Spring ingress example allows only the
application root, while internal metrics are unauthenticated.

Public dependencies, versioned image tags and downloaded tools must be reviewed
and scanned before production. The tool installer checks upstream checksums; these
provide integrity checking, not an independent trust root. CI uses pinned action
commits, read-only permissions, and no publication credentials.
