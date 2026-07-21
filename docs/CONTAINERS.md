# Docker and Kubernetes Security Gates

TStack v0.12.0 adds dependency-free static security checks for container build and orchestration files.

## Commands

```bash
tstack platform-audit .
tstack docker-audit .
tstack k8s-audit .
tstack platform-audit . --format json --output .tstack/platform-audit.json
tstack platform-audit . --fail-on review
```

Exit code `9` means the configured container-platform gate failed.

## Docker checks

TStack evaluates immutable base-image digests, non-root runtime users, broad context copies, remote `ADD`, unbounded package upgrades, health checks, multi-stage builds, and `.dockerignore` presence.

The scanner does not build or execute the image. Runtime vulnerability scanning, image signing, registry verification, and admission enforcement remain separate release controls.

## Kubernetes checks

For workload manifests, TStack evaluates:

- `runAsNonRoot`
- `allowPrivilegeEscalation: false`
- privileged containers
- read-only root filesystems
- dropped Linux capabilities
- CPU and memory requests/limits
- readiness and liveness probes
- mutable `latest` image tags
- service-account token automount
- NetworkPolicy presence
- PodDisruptionBudget presence

## Recommended production chain

```text
Dockerfile audit
  -> container build
  -> image vulnerability scan
  -> image SBOM
  -> immutable digest
  -> Sigstore/GitHub attestation
  -> Kubernetes manifest audit
  -> admission policy
  -> deployment verification
```

Static checks are evidence gates, not proof that a running cluster is secure. Production clusters should additionally use policy admission, namespace isolation, RBAC review, secret encryption, runtime monitoring, and verified image provenance.
