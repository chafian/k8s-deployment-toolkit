"""Contract tests against real Helm rendering; no cluster or network required."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHART = ROOT / "charts/app"
HELM = os.environ.get("HELM", "helm")
API = "monitoring.coreos.com/v1/ServiceMonitor"


def render(overrides=None, files=(), api=True, release="contract"):
    with tempfile.TemporaryDirectory() as directory:
        values = Path(directory) / "values.json"
        values.write_text(json.dumps(overrides or {}))
        command = [HELM, "template", release, str(CHART), "--namespace", "toolkit-test"]
        if api:
            command += ["--api-versions", API]
        for path in files:
            command += ["-f", str(ROOT / path)]
        command += ["-f", str(values)]
        return subprocess.run(command, capture_output=True, text=True, check=False)


def resources(testcase, **kwargs):
    rendered = render(**kwargs)
    testcase.assertEqual(rendered.returncode, 0, rendered.stderr)
    return {doc["kind"]: doc for doc in yaml.safe_load_all(rendered.stdout) if doc}


class ChartContractTests(unittest.TestCase):
    def test_default_service_and_deployment_are_wired_and_hardened(self):
        docs = resources(self)
        pod = docs["Deployment"]["spec"]["template"]
        container = pod["spec"]["containers"][0]
        self.assertEqual(docs["Service"]["spec"]["selector"], pod["metadata"]["labels"])
        self.assertEqual(docs["Deployment"]["spec"]["selector"]["matchLabels"], pod["metadata"]["labels"])
        self.assertEqual(docs["Service"]["spec"]["ports"][0]["targetPort"], container["ports"][0]["name"])
        self.assertFalse(pod["spec"]["automountServiceAccountToken"])
        self.assertEqual(pod["spec"]["serviceAccountName"], docs["ServiceAccount"]["metadata"]["name"])
        self.assertTrue(pod["spec"]["securityContext"]["runAsNonRoot"])
        self.assertEqual(pod["spec"]["securityContext"]["seccompProfile"]["type"], "RuntimeDefault")
        self.assertFalse(container["securityContext"]["allowPrivilegeEscalation"])
        self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
        self.assertEqual(container["securityContext"]["capabilities"]["drop"], ["ALL"])
        self.assertEqual(container["volumeMounts"][0]["mountPath"], "/tmp")
        self.assertIn("sizeLimit", pod["spec"]["volumes"][0]["emptyDir"])
        for probe in ("startupProbe", "readinessProbe", "livenessProbe"):
            self.assertEqual(container[probe]["httpGet"]["port"], "http")
        for kind in ("Ingress", "HorizontalPodAutoscaler", "ServiceMonitor", "PodDisruptionBudget", "Secret"):
            self.assertNotIn(kind, docs)

    def test_http_hook_keeps_logs_and_is_excluded_from_application_selectors(self):
        docs = resources(self)
        hook = docs["Pod"]
        self.assertEqual(hook["metadata"]["annotations"]["helm.sh/hook-delete-policy"], "before-hook-creation")
        selectors = docs["Service"]["spec"]["selector"]
        self.assertFalse(all(hook["metadata"]["labels"].get(key) == value for key, value in selectors.items()))

    def test_integrations_share_target_and_do_not_fight_autoscaler(self):
        docs = resources(self, files=["tests/fixtures/all-features.yaml"])
        deployment = docs["Deployment"]
        spec = deployment["spec"]
        pod = spec["template"]["spec"]
        container = pod["containers"][0]
        self.assertNotIn("replicas", spec)
        self.assertNotIn("ServiceAccount", docs)
        self.assertEqual(pod["serviceAccountName"], "existing-account")
        self.assertEqual(pod["imagePullSecrets"], [{"name": "registry-credentials"}])
        self.assertEqual(container["envFrom"], [{"configMapRef": {"name": "app-config"}}, {"secretRef": {"name": "app-credentials"}}])
        self.assertEqual(container["env"], [{"name": "APP_MODE", "value": "test"}])
        self.assertTrue(container["image"].endswith("@sha256:" + "a" * 64))
        self.assertEqual(docs["HorizontalPodAutoscaler"]["spec"]["scaleTargetRef"]["name"], deployment["metadata"]["name"])
        ingress = docs["Ingress"]["spec"]
        self.assertEqual(ingress["tls"][0]["hosts"], [ingress["rules"][0]["host"]])
        backend = ingress["rules"][0]["http"]["paths"][0]["backend"]["service"]
        self.assertEqual(backend["name"], docs["Service"]["metadata"]["name"])
        monitor = docs["ServiceMonitor"]["spec"]
        for key, value in monitor["selector"]["matchLabels"].items():
            self.assertEqual(docs["Service"]["metadata"]["labels"][key], value)
        self.assertEqual(monitor["endpoints"][0]["port"], docs["Service"]["spec"]["ports"][0]["name"])
        self.assertEqual(docs["PodDisruptionBudget"]["spec"]["selector"]["matchLabels"], spec["selector"]["matchLabels"])

    def test_invalid_configuration_fails_with_actionable_field(self):
        cases = [
            ({"replicaCount": 0}, "replicaCount"),
            ({"resources": {"requests": {"cpu": "0m"}}}, "cpu"),
            ({"serviceMonitor": {"labels": {"app.kubernetes.io/name": "wrong"}}}, "app.kubernetes.io/name"),
            ({"replicas": 3}, "replicas"),
            ({"service": {"port": 70000}}, "port"),
            ({"security": {"runAsUser": 0}}, "runAsUser"),
            ({"env": {"ENABLED": True}}, "ENABLED"),
            ({"image": {"digest": "sha256:bad"}}, "digest"),
            ({"image": {"tag": ""}}, "image.tag"),
            ({"ingress": {"enabled": True}}, "ingress"),
            ({"serviceAccount": {"create": False}}, "name"),
            ({"autoscaling": {"enabled": True, "minReplicas": 5, "maxReplicas": 2}}, "minReplicas"),
            ({"probes": {"readiness": {"path": "relative"}}}, "path"),
            ({"resources": {"requests": {"cpu": "banana"}}}, "cpu"),
        ]
        for overrides, field in cases:
            with self.subTest(overrides=overrides):
                rendered = render(overrides)
                self.assertNotEqual(rendered.returncode, 0)
                self.assertIn(field, rendered.stderr)

    def test_monitor_requires_crd_but_offline_api_can_be_declared(self):
        rendered = render({"serviceMonitor": {"enabled": True}}, api=False)
        self.assertNotEqual(rendered.returncode, 0)
        self.assertIn("Prometheus Operator CRD", rendered.stderr)
        docs = resources(self, overrides={"serviceMonitor": {"enabled": True}})
        self.assertIn("ServiceMonitor", docs)

    def test_optional_probes_and_test_hook_can_be_disabled(self):
        docs = resources(self, overrides={"probes": {name: {"enabled": False} for name in ("startup", "readiness", "liveness")}, "tests": {"enabled": False}})
        container = docs["Deployment"]["spec"]["template"]["spec"]["containers"][0]
        self.assertFalse(any(key.endswith("Probe") for key in container))
        self.assertNotIn("Pod", docs)

    def test_supported_example_compositions_render(self):
        for application in ("nginx", "spring-boot"):
            for environment in ("staging", "production"):
                with self.subTest(application=application, environment=environment):
                    docs = resources(self, files=[f"environments/{environment}.yaml", f"examples/{application}/values.yaml"])
                    container = docs["Deployment"]["spec"]["template"]["spec"]["containers"][0]
                    expected = "/actuator/health/readiness" if application == "spring-boot" else "/"
                    self.assertEqual(container["readinessProbe"]["httpGet"]["path"], expected)
                    self.assertEqual("HorizontalPodAutoscaler" in docs, environment == "production")

    def test_yaml_ambiguous_names_remain_strings_across_resources(self):
        for name in ("on", "true", "123"):
            with self.subTest(name=name):
                full_name = name if name != "123" else "app-123"
                docs = resources(self, files=["tests/fixtures/all-features.yaml"],
                                 overrides={"nameOverride": name, "fullnameOverride": full_name,
                                            "serviceAccount": {"create": True, "name": name}},
                                 release="true")
                for doc in docs.values():
                    self.assertIsInstance(doc["metadata"]["name"], str)
                    self.assertTrue(all(isinstance(value, str) for value in doc["metadata"]["labels"].values()))
                deployment = docs["Deployment"]["spec"]
                self.assertEqual(deployment["selector"]["matchLabels"]["app.kubernetes.io/name"], name)
                self.assertEqual(deployment["template"]["spec"]["serviceAccountName"], name)
                self.assertEqual(docs["Service"]["spec"]["selector"], deployment["selector"]["matchLabels"])
                self.assertEqual(docs["HorizontalPodAutoscaler"]["spec"]["scaleTargetRef"]["name"], full_name)
                backend = docs["Ingress"]["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]
                self.assertEqual(backend["name"], full_name)

    def test_digit_leading_service_names_fail_with_remediation(self):
        for overrides, release, error in (({"fullnameOverride": "123"}, "contract", "fullnameOverride"),
                                          ({}, "123", "set fullnameOverride")):
            with self.subTest(overrides=overrides, release=release):
                rendered = render(overrides, release=release)
                self.assertNotEqual(rendered.returncode, 0)
                self.assertIn(error, rendered.stderr)
        docs = resources(self, overrides={"fullnameOverride": "app-123"}, release="123")
        self.assertEqual(docs["Service"]["metadata"]["name"], "app-123")

    def test_long_release_names_keep_hook_name_within_dns_limit(self):
        docs = resources(self, overrides={"fullnameOverride": "a" * 63})
        self.assertLessEqual(len(docs["Pod"]["metadata"]["name"]), 63)
        self.assertEqual(docs["Service"]["metadata"]["name"], "a" * 63)


if __name__ == "__main__":
    unittest.main()
