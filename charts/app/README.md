# app chart

Helm 3 application chart, version 0.1.0. See the repository README and
`docs/configuration.md` for usage. `values.yaml` documents defaults and
`values.schema.json` validates the merged values. This chart does not require any
Helm dependencies.

Default install: `helm install demo ./charts/app --wait` from the repository root.
Use `helm test demo --logs` to check HTTP reachability through the Service.
The default container is unprivileged Nginx; override the image, numeric non-root
identity, resource sizing, and probe paths for another application.

Optional ServiceMonitor requires its CRD. Optional Ingress needs a controller and
existing TLS Secret; HPA requires metrics-server. The chart creates no Secret,
Role, RoleBinding, or Namespace. The test Pod is a Helm hook and is not part of
normal application traffic.

Licensed under Apache-2.0. LICENSE and NOTICE are included in the chart package.
