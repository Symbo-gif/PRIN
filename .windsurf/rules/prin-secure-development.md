---
description: PRIN repository authority and secure-development protocol
alwaysApply: true
priority: 1
---

# PRIN secure-development protocol

Before editing, read the active session brief, `DOCS/PRIN_Project_Plan.md`, the
applicable standards, latest Project State Report and deviation ledger, and any
governing audit. Verify implementation facts from current repository code and
configuration. `DOCS/archive/` is historical and non-authoritative.

Follow Coding Standards §6. Run Snyk Code for new or modified supported source.
For dependency changes, run Snyk Open Source plus every applicable native audit.
Fix findings attributable to the change and rescan. Do not suppress findings
without approved governance. Snyk does not replace `cargo audit`, `pip-audit`,
GitHub secret scanning, or push protection. Never claim an unavailable or
unexecuted scan passed.

Do not use retired VibeCheck state as current truth or emit unverifiable badges.
