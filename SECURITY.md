# 🔐 Vulnerability Disclosure Workflow (Pro‑Harp)

```
[Discovery]
    |
    v
[Reporter Identifies Vulnerability]
    |
    v
[Private Disclosure to security@yourdomain.com]
    |
    v
[Initial Triage by Maintainers]
    - Validate report
    - Assign severity (Critical/High/Medium/Low)
    - Acknowledge receipt within 72h
    |
    v
[Mitigation Planning]
    - Reproduce issue
    - Identify affected components
    - Draft fix or workaround
    |
    v
[Fix Development & Testing]
    - Patch code in feature/security branch
    - Run CI/CD + regression tests
    - Validate with Virtual Test Harness (VTH)
    |
    v
[Coordinated Release]
    - Merge fix into main
    - Publish patched container/image
    - Update CHANGELOG + SECURITY.md
    |
    v
[Disclosure & Communication]
    - Notify reporter of resolution
    - Public advisory if severity ≥ High
    - Update NOTICE/licenses if dependency-related
    |
    v
[Post‑Mortem & Lessons Learned]
    - Document root cause
    - Update operational playbooks
    - Feed improvements into CI/CD + monitoring
```

---

# ✅ Key Notes for Pro‑Harp
- **Confidentiality:** All reports must come via private email, not GitHub issues.  
- **Timeline:** Acknowledge in 72h, fix within SLA (Critical ≤ 14 days).  
- **Auditability:** Every fix must include SPDX headers, updated NOTICE, and immutable storage of advisories.  
- **Integration:** SOC playbooks should trigger incident drills when a vulnerability is confirmed.  
