# paper/

NeurIPS paper artefacts, carried over unchanged from PRINet 3.0 (project plan
§14). Figures and tables are regenerated from the stored JSON artefacts by
`tools/reproduce.py`; the SHA-256 manifest guarantees byte-comparable output.

## Artefact manifest

`artefact_manifest.json` is the governed SHA-256 manifest for the 172
immutable stored benchmark JSON artefacts in `benchmarks/results/`. Each
record contains the plain filename, exact byte size, and lowercase SHA-256
digest. The manifest is append-only: existing records are verified before new
ones are added, so mutation or removal of an accepted artefact is a hard
failure. Run `python tools/reproduce.py --verify-manifest` to check every
stored artefact against the manifest before regenerating all 14 figures and
11 LaTeX tables.
