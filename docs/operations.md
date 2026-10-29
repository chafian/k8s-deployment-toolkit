# Operations

## Rollout and rollback

The Deployment uses maxUnavailable 0 / maxSurge 1 and keeps three revisions.
Readiness controls Service endpoints. Startup probes protect slow-starting apps
from liveness restarts; size the startup failure window for the application's
worst expected startup. Liveness should not depend on remote databases or services.

```bash
helm history demo -n toolkit-demo
kubectl -n toolkit-demo rollout status deployment/demo-app
kubectl -n toolkit-demo get pods
kubectl -n toolkit-demo describe deployment demo-app
kubectl -n toolkit-demo logs deployment/demo-app
# Substitute an actual successful revision from helm history:
helm rollback demo 1 -n toolkit-demo --wait --timeout 3m
```

`--atomic` restores a failed Helm upgrade; it does not reverse database migrations
or external side effects. GitOps users should revert the reviewed Git change and
sync; out-of-band Helm changes conflict with Argo CD ownership.

Successful and failed test hook Pods are retained so `helm test --logs` can read
them. The next test replaces the previous Pod. Helm does not manage hook cleanup
on uninstall; remove it explicitly with `kubectl -n toolkit-demo delete pod demo-app-test`
when no longer needed.

## HPA and disruption budgets

HPA targets the same Deployment and uses CPU utilization relative to requested CPU.
Check `kubectl -n toolkit-production describe hpa demo-app` when replicas do not
change. Missing metrics-server or missing CPU metrics prevents useful scaling.
Enabling HPA removes `spec.replicas` from the rendered Deployment; the first switch
from fixed replicas can cause a transient scale change. Observe that transition.

The production example uses min 3 / max 10 replicas and maxUnavailable 1 in its PDB.
Tune capacity, CPU requests and limits to measured load. A PDB is not zone spreading;
this MVP does not guarantee placement across nodes/zones. maxUnavailable 0 may block
drains. With a single replica, maxUnavailable 1 allows downtime during eviction.

## Ingress and TLS

Provision an ingress controller and TLS Secret externally, match the certificate's
hosts to ingress rules, and configure DNS. The chart does not install cert-manager,
redirect HTTP automatically, or configure a controller-specific authentication
policy. `nginx` is an example ingress class name, not an installed dependency.

The Spring demo keeps ingress disabled when combined with environment overlays.
Its explicit ingress overlay uses an Exact `/` route so public requests cannot
reach `/actuator` through that rule. Cluster-internal metrics are unauthenticated;
restrict their reachability with network policy or an authenticated metrics design
before deploying into a shared untrusted cluster.

## Prometheus

Install Prometheus Operator and a Prometheus instance separately. Ensure its
ServiceMonitor namespace selector and label selector include this release;
`release: monitoring` is an example label, not a universal default. The generated
monitor selects this chart's Service in the same namespace and scrapes the named
`http` port. Review Prometheus targets if no data appears; a valid CRD object alone
does not prove a successful scrape. Scrape timeout must not exceed interval.

## Common failures

| Symptom | Check and action |
| --- | --- |
| ImagePullBackOff | Verify the image/digest exists and pull-secret names are in the release namespace. The Spring image is local until you explicitly publish it. |
| Permission denied / read-only filesystem | Match numeric UID/GID to the image; direct temporary files to /tmp. Do not disable the chart security invariants. |
| CrashLoopBackOff | Read container logs and events; verify probes use an endpoint served on containerPort. |
| Pods Pending | Check CPU/memory capacity, quotas, and image architecture. |
| Missing Secret or ConfigMap | Provision the referenced object in the namespace before deploying. |
| Ingress 404 / invalid TLS | Check class, exact path, DNS, certificate hosts and TLS secret name. |
| HPA shows unknown metrics | Check metrics-server and Pod CPU metrics. |
| Values schema error | Use the supported keys and types in values.schema.json; quote environment values. |
| No ServiceMonitor match | Check CRD discovery, monitor labels, namespace selector, Service port name, and endpoint path. |

## Before production

Review measured resource sizing, image provenance/digests/scans, cluster support,
network isolation, certificate renewal, application authentication, monitoring and
alerts, availability across failure domains, and an exercised rollback procedure.
Secrets should be supplied by your approved secret-management system. This MVP has
no persistent-data recovery, multitenancy, or zero-downtime SLA claim.
