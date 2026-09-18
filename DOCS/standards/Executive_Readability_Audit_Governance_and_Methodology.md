# PRIN Executive Readability Audit Governance and Methodology

**Status:** Normative. This document establishes the governance, scope,
methodology, findings classification, remediation protocols, and reporting
requirements for **Executive Readability Audit (ERA) Sessions** in the PRIN
project.

**Relationship to existing governance:** This document extends — and never
overrides — the [Executive Audit Governance and Methodology](Executive_Audit_Governance_and_Methodology.md),
[Executive Documentation Audit Governance and Methodology](Executive_Documentation_Audit_Governance_and_Methodology.md),
[Documentation Standards](Documentation_Standards.md), and
[Official Project Plan](../PRIN_Project_Plan.md). It is registered as a
global session type, following the same "global session, outside the planned
sequence" registration precedent established for Executive Audit (EA),
Executive Mathematical Audit (EMA), and Executive Documentation Audit (EDA)
sessions.

---

## 1. Purpose and Scope

An **Executive Documentation Audit** (EDA) verifies that documentation is
*accurate, complete, and internally consistent*. An **Executive Readability
Audit** (ERA) verifies that documentation is *human-readable* — that it
communicates effectively to its intended audiences, that information is
findable, that density is appropriate, and that the project tells a coherent
story from first contact to deep contribution.

An ERA Session:

1. Evaluates whether documentation serves its **intended audiences** (new
   users, experienced contributors, researchers, reviewers) with appropriate
   density, structure, and entry points.
2. Assesses whether the project presents a **coherent narrative** — a
   newcomer should be able to answer "what is PRIN?", "how do I try it?",
   "how do I contribute?", and "where do I find X?" without reading every
   file.
3. Identifies **readability barriers** — walls of text, missing entry
   points, information buried in unexpected locations, audience mismatch
   (governance-density in user-facing docs), and missing navigational aids.
4. Verifies that **quick-start paths** exist for each major audience — a
   new user can run something in minutes, a contributor can find the
   standards they need, a researcher can locate the scientific claims.
5. **Does not replace** EDA sessions (accuracy/completeness) or EA sessions'
   E5 dimension (standards adherence). ERA is a complementary,
   human-centered verification layer.

### 1.1 When an ERA session is warranted

An ERA session is warranted when:

1. **First audit:** No prior readability audit exists (this session —
   ERA-001).
2. **Major documentation reorganization:** When directory structure, Sphinx
   layout, or README conventions change significantly.
3. **Phase boundaries:** At phase close, complementing the EDA with a
   readability-focused assessment.
4. **Maintainer discretion:** When onboarding friction or documentation
   confusion is reported.

---

## 2. Audit Dimensions

An ERA session examines documentation across 8 dimensions:

| ID | Dimension | Assessment Scope |
|---|---|---|
| **R1** | **First-Impression Clarity** | Can a new visitor understand what PRIN is, what it does, and whether it is relevant to them within 60 seconds of reading the root README? Does the root README avoid jargon overload, provide a clear value proposition, and link to appropriate next steps for different audiences? |
| **R2** | **Quick-Start Path Existence** | Does a new user have a clear, minimal path from "I want to try PRIN" to "I ran something and saw output"? Is there a tutorial, quick-start guide, or notebook that requires no prior knowledge of the project internals? |
| **R3** | **Audience Segmentation** | Are different audiences (users, contributors, researchers, reviewers) served by appropriately-scoped documentation? Are governance-density documents kept separate from user-facing guides? Is there clear signposting for "if you are X, start here"? |
| **R4** | **Information Density & Scannability** | Are READMEs and guides scannable? Do they use appropriate heading hierarchy, tables, bullet lists, and whitespace? Are walls of text broken into digestible sections? Can a reader find specific information without reading everything? |
| **R5** | **Navigational Coherence** | Does the documentation tree have a logical structure? Can a reader navigate from high-level overview to detail and back? Are cross-references bidirectional and discoverable? Is there a sitemap or navigation aid for the documentation tree? |
| **R6** | **Domain Terminology Accessibility** | Are domain-specific terms (PAC, chimera, order parameter, δ/θ/γ bands, Kuramoto, Stuart–Landau) explained or linked to explanations on first use? Is there a glossary? Can a reader unfamiliar with coupled-oscillator physics understand enough to use the API? |
| **R7** | **Directory README Quality** | Does every directory README answer: what is here, why does it exist, how do I use what is here, and what is its current status? Are READMEs proportional to their directory's complexity? |
| **R8** | **Visual Communication** | Does the documentation use diagrams, architecture visualizations, tables, and other visual aids where they would improve comprehension? Are there architecture diagrams, data-flow diagrams, or relationship maps that prose alone cannot convey? |

---

## 3. Severity Classification

ERA findings use a readability-specific severity scale:

| Severity | Definition | Required Response |
|---|---|---|
| **R1 — Critical Barrier** | A new user or contributor cannot accomplish a basic task (install, run, contribute) because documentation is missing, impenetrable, or misleading. | Immediate fix required. |
| **R2 — Significant Barrier** | Documentation exists but is difficult to use: walls of text, missing entry points, audience mismatch, or information buried in unexpected locations. | Fix in remediation step before audit session closure. |
| **R3 — Moderate Barrier** | Documentation is usable but could be improved: missing cross-references, inconsistent structure, or density that could be reduced. | Fix in remediation step or log with explicit future session placeholder. |
| **R4 — Hygiene** | Minor improvements: formatting inconsistencies, missing language tags, or cosmetic issues that do not impede comprehension. | Fix during remediation / documentation alignment step. |

---

## 4. Executive Readability Audit Workflow Lifecycle

An ERA Session proceeds through 7 mandatory sequential tasks:

```
Task 1: Governance & Methodology Definition (this document, first session)
   │     or confirmation of existing methodology (subsequent sessions)
   ▼
Task 2: Documentation Inventory & Audience Mapping
   │     (enumerate all documentation artefacts, identify audiences)
   ▼
Task 3: Multi-Dimension Audit Execution (R1–R8)
   │     (systematic evaluation of each dimension)
   ▼
Task 4: Executive Readability Audit Report Compilation
   │
   ▼
Task 5: Remediation Planning (Immediate vs Pass-Forward)
   │
   ▼
Task 6: Remediation Execution & Verification
   │
   ▼
Task 7: Final Documentation, Session Register/Traceability, Git Commit
```

---

## 5. Reporting and Artifact Rules

1. **Executive Readability Audit Report:** saved as
   `DOCS/audits/EXECUTIVE_READABILITY_AUDIT_REPORT_NNN.md` using
   the report structure established in ERA-001. Findings use the `R-FN`
   identifier prefix (distinct from EA's `E-FN`, EMA's `M-FN`, and EDA's
   `D-FN`).
2. **Session registration:** ERA sessions are global sessions, registered in
   `DOCS/sessions/SESSION_REGISTER.md` under a dedicated "Global sessions —
   Executive Readability Audits" section.
3. **Readability governance updates:** If the audit reveals systemic gaps
   in the Documentation Standards (e.g., no readability requirements for
   READMEs), the standards document is amended in the same session.
4. **Closing checklist:** As a global session, an ERA session's own file
   changes must be registered in CHANGELOG.md and pass quality gates before
   commit.

---

## 6. Readability Standards for READMEs

This section establishes enforceable readability requirements for all
directory READMEs in the PRIN project. These requirements supplement the
existing Documentation Standards (§1 item 3, §7 item 1) and are enforceable
in every future session.

### 6.1 Root README requirements

The root README must:

1. **Open with a one-paragraph value proposition** — what PRIN is, what
   problem it solves, and who it is for. No WP numbers, no session IDs.
2. **Include a "Quick Start" section** — the minimal commands to install
   and run something (a notebook, a test, a benchmark) within 5 minutes.
3. **Include an architecture diagram** — a visual overview of the two-layer
   Rust/Python design, data flow, and key components.
4. **Provide audience-specific entry points** — links labeled "For users:",
   "For contributors:", "For researchers:" pointing to the appropriate
   starting documentation.
5. **Keep the "Status" section scannable** — use a table or bullet list,
   not a dense paragraph of WP numbers.

### 6.2 Directory README requirements

Every directory README must answer four questions:

1. **What is here?** — A one-sentence description of the directory's purpose.
2. **Why does it exist?** — Context within the larger project (which phase,
   which work package, which architectural layer).
3. **How do I use what is here?** — Commands, API entry points, or usage
   examples.
4. **What is its current status?** — Phase, completeness, known gaps.

Additionally:

- **Proportionality:** A README's length should be proportional to its
  directory's complexity. A simple utility directory needs 10–20 lines; a
  complex subsystem may need 100+. Dense walls of text (>200 lines without
  a table of contents) require internal navigation aids.
- **Scannability:** Use tables for structured information (module lists,
  feature matrices), bullet lists for enumerations, and heading hierarchy
  (H2 → H3 → H4) for sections. Avoid paragraphs longer than 5 lines.
- **First-use terminology:** If a README uses domain-specific terms (PAC,
  chimera, order parameter), it must either explain them on first use or
  link to a glossary or explanation.

### 6.3 Prohibited patterns

The following patterns are readability violations:

1. **WP-number soup:** A paragraph consisting primarily of WP numbers and
   session IDs without explanation of what was delivered.
2. **Unbroken walls of text:** More than 200 lines of prose without a
   table, diagram, or internal table of contents.
3. **Audience mismatch:** Governance-density content (audit findings,
   deviation ledgers, session IDs) in user-facing documentation.
4. **Orphan directories:** A directory with source code but no README.
5. **Stale status:** A README claiming a feature is "planned" or "in
   progress" when it has been delivered (or vice versa).

---

## 7. Enforceability

This governance is enforceable in every future session:

1. **S4 documentation sessions** (Documentation Standards §7) must verify
   that any README they create or update complies with §6 of this document.
2. **EDA sessions** (D4 dimension) must verify README currency *and*
   readability compliance.
3. **ERA sessions** provide the comprehensive readability assessment at
   phase boundaries or when warranted (§1.1).
4. **New directory creation** requires a README that answers the four
   questions in §6.2 before the directory's first PR merges.
