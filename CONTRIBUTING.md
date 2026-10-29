# Contributing

Use issues for reproducible bugs and focused pull requests for changes.
Contributions are provided under the project's Apache-2.0 license. Only contribute
material you have the right to share. Do not include customer information,
credentials, private configuration, or proprietary source code in issues, tests,
fixtures, or examples.

## Development

Use the setup commands in the README, then run `make validate`. Changes affecting
runtime behavior also need `make cluster-test` with Docker. Java changes are tested
inside the container build or with Maven 3.9+ and Java 17+.

Keep chart values, schema, examples and documentation synchronized. New settings
need a concrete use case, a schema constraint and a meaningful test. Preserve stable
selectors and document migrations for changes that affect existing installations.
Use two-space YAML/JSON indentation, four-space Python/Java, and LF line endings.

Tests should verify rendered Kubernetes behavior, cross-resource wiring and failure
cases with real Helm. Avoid snapshots of entire manifests and mocks of internal
functions. Cluster tests must use a disposable cluster and their own kubeconfig.

## Pull request review

Describe the problem, resulting behavior and validation performed. State checks you
could not run. Include security and compatibility implications when they apply.
Do not add deploy/publish jobs, broad workflow permissions, secret values, or a
GitHub remote publication step without explicit owner agreement.

Changes to the values contract or templates require a chart version change before
release. The 0.x series may introduce documented breaking changes; consumers should
pin chart versions and review release notes. Tool versions and CI action pins must
be updated deliberately and validated together.

Before each release, maintainers should review image dependencies, inspect validation
evidence and verify security reporting and branch-protection settings. CI success
alone is not release approval.
