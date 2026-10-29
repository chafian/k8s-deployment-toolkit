# Nginx example

Run from the repository root:

```bash
helm upgrade --install nginx charts/app -n toolkit-demo --create-namespace \
  -f examples/nginx/values.yaml --wait --atomic --timeout 3m
helm test nginx -n toolkit-demo --logs
kubectl -n toolkit-demo port-forward service/nginx-app 8080:80
```

The upstream `nginxinc/nginx-unprivileged:1.28.0-alpine` image serves HTTP on
8080 as UID/GID 101. Its writable runtime paths are under `/tmp`; the chart mounts
a bounded emptyDir there. Entrypoint scripts may report that `/etc/nginx` is read-only;
the stock configuration works without rewriting it. If replacing the image, check
its UID, port, runtime paths and health behavior.

See [upstream image documentation](https://github.com/nginx/docker-nginx-unprivileged).
This image has no `/metrics` exporter. The Spring example demonstrates monitoring.
