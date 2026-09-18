# tools/code-intelligence/tests/

Pytest suite for the code-intelligence subsystem. Not part of the root
`tests/` suite (`pyproject.toml`'s `testpaths`); run explicitly:

```powershell
python -m pytest tools\code-intelligence\tests -v
```

- `conftest.py` puts `tools/code-intelligence/` on `sys.path` and provides
  the `fixture_repo`/`indexed_store` fixtures.
- `fixtures/mini_repo/` is a small, synthetic, multi-language repository
  (Python with a deliberate import cycle, Rust with a `mod` declaration and
  a `Cargo.toml`, one Lean declaration file, TOML/JSON/YAML config, a
  `.gitignore`d directory, a secret-like `credentials.json`, and two TS
  files) used to deterministically exercise every adapter, the cycle
  detector, the secret-exclusion filter, and Mermaid generation without
  depending on the real PRIN codebase's current shape. **It is excluded
  from real repository indexing** (`ci_config.DEFAULT_EXCLUDE_PATH_PREFIXES`)
  so its deliberately-fake cycle and secret file never appear in a real
  analysis of PRIN itself.
- `test_indexer.py`, `test_analytics.py`, `test_mermaid.py`,
  `test_security.py`, `test_mcp_server.py`, `test_telemetry.py` — one file
  per subsystem area.
