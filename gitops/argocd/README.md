# Argo CD reference

These files are not applied automatically. Before use:

1. Install Argo CD (the example uses `helm.valuesObject`, available in Argo CD 2.6+).
2. Replace `REPLACE_WITH_REVIEWED_COMMIT_SHA` in application.yaml with an immutable
   reviewed commit from the published repository. Update repoURL/sourceRepos if using
   a fork. Choose an Argo CD release supported by your organization.
3. Create `toolkit-staging` yourself, and configure ingress class, DNS and the
   `app-staging-tls` certificate Secret. Review the staging values in Git first.
4. Apply project.yaml and application.yaml, then review the diff and manually sync
   using the Argo CD UI. There is no automated sync, prune, or self-heal in this example.

```bash
kubectl create namespace toolkit-staging
kubectl apply -f gitops/argocd/project.yaml
kubectl apply -f gitops/argocd/application.yaml
```

The AppProject permits only this source repository, the local cluster's
`toolkit-staging` namespace, and the namespaced kinds this chart needs. It grants
no cluster-scoped resource permissions. The chart cannot create the namespace;
`CreateNamespace` is intentionally absent. AppProject rules scope Argo CD deployment
access; they do not replace Kubernetes RBAC for people or application isolation.

Value-file paths are relative to `charts/app`. Both the Argo CD Application name
and Helm release name are `toolkit-nginx-staging`; keep them aligned because Argo CD
may track resources with `app.kubernetes.io/instance`. Helm test hooks are disabled
in this Application; CI executes them independently.

For production, create a separate reviewed AppProject destination and Application,
use production values and an immutable commit, and review any pruning or automatic
sync policy before enabling it. Review [Argo CD's Helm integration](https://argo-cd.readthedocs.io/en/stable/user-guide/helm/).
