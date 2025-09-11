# SECURITY

Focus: key handling, surface minimization, data integrity, abuse prevention.

## Threat Model (Concise)
| Vector | Risk | Mitigation |
|--------|------|------------|
| API misuse | Prompt injection, excessive load | Input validation, rate limits (future), strict prompt template slots |
| Data poisoning | Malicious file ingest | Hash + quarantine staging, allowlist extensions, size limits |
| Model exfil (remote) | API key leakage | .env only, never log keys, restricted FS perms |
| Sensitive data leakage | Returning disallowed context | Metadata classification tags + filter (future) |
| Integrity tampering | Chunk text altered post-hash | Store chunk_hash; verify on retrieval (planned) |
| Replay / reindex drift | Outdated index with new metadata | Embed pipeline version gating + reindex marker |

## Current Controls
- Environment variable secrets (.env excluded from VCS)
- Minimal external dependencies
- Deterministic chunk hashing (sha256)
- Separation: metadata DB vs. raw source files

## Planned Controls
| Control | Description |
|---------|-------------|
| Request size limits | FastAPI body size guard |
| Rate limiting | Token bucket (Redis / in-memory) |
| AuthN/Z | API key header or mTLS |
| Prompt slot sanitization | Reject unexpected template variables |
| Chunk hash verification | On retrieval path |
| Sensitive classification | Simple regex then ML tagger |
| Signed bundles | Private key sign prompt/context hashes |

## Secure Configuration Guidelines
- Principle: disable remote calls if `OPENAI_BASE_URL` empty
- Provide `READ_ONLY_MODE` for inference-only deployments
- Run under non-root user; restrict write dirs to data paths

## Logging Hygiene
- Never log full API keys or raw prompts containing secrets
- Optional redaction hook for patterns (API_KEY, PASSWORD)

## Incident Response (Playbook Skeleton)
1. Detect anomaly (error spike / unauthorized access)
2. Freeze ingest (toggle feature flag)
3. Export affected bundles (scope assessment)
4. Verify chunk hashes vs. DB
5. Rotate credentials (.env regeneration)
6. Post-mortem: root cause + control gap

## Roadmap
- Supply chain: pin dependencies + hash verification
- SBOM generation (cyclonedx)
- Secrets scanner in CI (gitleaks)
