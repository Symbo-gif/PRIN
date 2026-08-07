# Executive Audit Workflow

Comprehensive project-level executive audit and remediation recipe.

## Steps
1. **Governance Check**: Ensure `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` and `DOCS/audits/TEMPLATE_Executive_Audit_Report.md` exist.
2. **Multi-Domain Audit Execution**:
   - E1 Math & Oscillator Dynamics Core
   - E2 Codebase & Architecture
   - E3 Test Suite & Parity Corpus
   - E4 Security & Supply Chain
   - E5 Standards & Documentation Adherence
   - E6 Evidence, Baselines & Analytics Integrity
   - E7 Session Cycle & Governance Traceability
   - E8 Performance & Benchmarking
   - E9 CI/CD & Build Infrastructure
   - E10 Roadmap, Risks & Future Session Handoff
3. **Audit Report Compilation**: Produce `DOCS/audits/EXECUTIVE_AUDIT_REPORT_001.md`.
4. **Remediation Planning**: Separate immediate fixes vs pass-forward placeholders.
5. **Remediation & Retroactive Documentation**: Execute source/doc fixes, update READMEs/CHANGELOG with `[RETROACTIVE UPDATE - Executive Audit 001]` tags where appropriate.
6. **Full Verification**: Run all local verification one-liner checks + Snyk scans.
7. **Commit & Push**: Document final state, commit with proper format, and push.
