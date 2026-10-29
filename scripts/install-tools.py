#!/usr/bin/env python3
"""Install pinned public test tools after checking upstream SHA-256 checksums."""
import argparse
import hashlib
import io
from pathlib import Path
import platform
import tarfile
import urllib.request


def download(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def tool_urls(name, system, arch):
    if name == "helm":
        filename = f"helm-v3.19.0-{system}-{arch}.tar.gz"
        return "https://get.helm.sh/", filename, filename + ".sha256sum"
    if name == "kind":
        filename = f"kind-{system}-{arch}"
        return "https://kind.sigs.k8s.io/dl/v0.30.0/", filename, filename + ".sha256sum"
    filename = f"kubeconform-{system}-{arch}.tar.gz"
    return "https://github.com/yannh/kubeconform/releases/download/v0.8.0/", filename, "CHECKSUMS"


def install(name, destination):
    system = platform.system().lower()
    arch = {"x86_64": "amd64", "aarch64": "arm64", "arm64": "arm64"}[platform.machine()]
    base, filename, checksums = tool_urls(name, system, arch)
    payload = download(base + filename)
    lines = download(base + checksums).decode().splitlines()
    checksum = next(line.split()[0] for line in lines if len(lines) == 1 or line.split()[-1].lstrip("*") == filename)
    if hashlib.sha256(payload).hexdigest() != checksum:
        raise ValueError(f"Checksum mismatch for {name}")
    if filename.endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
            member = next(entry for entry in archive if entry.isfile() and Path(entry.name).name == name)
            payload = archive.extractfile(member).read()
    binary = destination / name
    binary.write_bytes(payload)
    binary.chmod(0o755)
    print(f"Installed verified {name}: {binary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tools", nargs="+", choices=["helm", "kind", "kubeconform"])
    parser.add_argument("--destination", type=Path, default=Path("work/bin"))
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    for tool in args.tools:
        install(tool, args.destination)
