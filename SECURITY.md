# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

---

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security issue in PyShield — including bugs in the sandboxing layer, PII detection bypass vectors, or seal forgery paths — please report it privately via GitHub's [Security Advisories](https://github.com/biswa-mohapatro/PySheild/security/advisories/new).

Include:
1. A description of the vulnerability and its potential impact.
2. Steps to reproduce, including a minimal Python test file if applicable.
3. Your assessment of severity (critical / high / medium / low).

We aim to acknowledge reports within **48 hours** and provide a resolution timeline within **7 days** for critical issues.

---

## Scope

| In scope | Out of scope |
|---|---|
| Sandboxed execution escaping the mock boundary | Issues in your own code found by PyShield |
| PII leak detection false negatives that can be reliably reproduced | Third-party MCP client vulnerabilities |
| SHA-256 seal collision attacks | Demo files in `demos/` |
| Arbitrary code execution via crafted source files | General Python runtime issues |

---

## Security Design Notes

PyShield is designed with a strict air-gap principle:

- No network sockets, remote telemetry, or external API calls are made by the engine.
- All subprocess calls originating from user code under test are mocked during sandboxed execution.
- All write-mode `open()` calls originating from user code under test are mocked.
- Cryptographic seals use SHA-256 (collision-resistant) for file attestation.

These properties are tested in `tests/test_runner.py` and are considered part of the public security contract.
