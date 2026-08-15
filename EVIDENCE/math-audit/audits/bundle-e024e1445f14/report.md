# Audit Evidence Report: bundle-e024e1445f14

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-15T02:29:23.562Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### GRA-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `graph_topology`  
- **Severity:** `high`  
- **Statement:** build_ring(N=6, k_ring=4) connects each node to its +-1 and +-2 neighbours mod N, producing a connected, 4-regular graph with exactly N*k_ring/2=12 undirected edges and no self-loops.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-d1832f16cd52

### GRA-02 -- `PASS`

- **Type:** `graph_topology`  
- **Severity:** `medium`  
- **Statement:** build_all_to_all(N=4) is the complete graph K4: connected, 3-regular (every node connects to all others), 6 undirected edges, no self-loops.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-639bf16a5fcb

### GRA-01-LEAN -- `PASS`

- **Type:** `lean_theorem`  
- **Severity:** `high`  
- **Statement:** Formal (Lean 4 kernel-checked `decide`) corroboration of GRA-01: build_ring(N=6, k_ring=4)'s declared neighbour structure {i+-1, i+-2 mod 6} is 4-regular (each node has exactly 4 distinct neighbours), has no self-loops, has exactly N*k_ring/2=12 undirected edges after canonicalising directed pairs, and is connected (every node reachable from node 0 via bounded neighbour-closure). EMA-001 M-F3: added to let this high-severity graph_topology claim earn genuine symbolic/formal corroboration (policy.verdict_rules.high_severity_requires_symbolic_or_formal) via a third independent channel (Lean's kernel) alongside GRA-01's own NetworkX evidence, rather than relying on human sign-off alone.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-6ad10c370ed4

## Tool invocations

### audit_graph_topology (`audit-d1832f16cd52`) -- `PASS`

- **Adapter:** `networkx`
- **Severity:** `high`
- **Duration:** 15 ms
- **Summary:** Graph is confirmed 4-regular.

**Reasoning:** All 6 nodes have degree 4. Additional properties: connected=True.

**Metrics:**
- num_nodes: 6.0
- num_edges: 12.0
- num_connected_components: 1.0
- cycle_basis_size: 7.0
- diameter: 2.0
- average_shortest_path_length: 1.2
- algebraic_connectivity: 4.000000000000001

- **Random seed:** n/a
- **Input content hash:** `sha256:5c40abf3df2a3892a6b1a8b048d78b38bba3bd8616aa02da864474bd1182de8c`
- **Output content hash:** `sha256:bc52920af5027c157de40d0f994a2ebebef845f7e5f508802ea9dd27d314f0e9`

### audit_graph_topology (`audit-639bf16a5fcb`) -- `PASS`

- **Adapter:** `networkx`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Graph is confirmed 3-regular.

**Reasoning:** All 4 nodes have degree 3. Additional properties: connected=True.

**Metrics:**
- num_nodes: 4.0
- num_edges: 6.0
- num_connected_components: 1.0
- cycle_basis_size: 3.0
- diameter: 1.0
- average_shortest_path_length: 1.0
- algebraic_connectivity: 3.999999999999999

- **Random seed:** n/a
- **Input content hash:** `sha256:c570a62760ea4f883d3c2a6d887a830f42efda13c7bd5f040910e137ed71d152`
- **Output content hash:** `sha256:8ede4217956bfc423b3741c04a7d4ce328e7ebf0281b7f2edcbed830b7bba99c`

### verify_lean_claim (`audit-6ad10c370ed4`) -- `PASS`

- **Adapter:** `lean`
- **Severity:** `high`
- **Duration:** 820 ms
- **Summary:** Lean elaborated successfully; expected_outcome='proves'.

**Reasoning:** Ran `C:\Users\there\.elan\bin\lean.EXE C:\dev\PRIN\EVIDENCE\math-audit\scratch\lean\tmpiuca3wwt.lean`. Elaboration succeeded. See lean-diagnostics.txt artifact for full sanitized output.

**Limitations:**
- This adapter drives the Lean CLI and inspects exit status/diagnostics; it does not perform interactive elaboration introspection (a Lean LSP bridge is a documented future extension).

**Artifacts:**
- [Sanitized Lean/lake stdout+stderr](artifacts/lean-diagnostics.txt) (`sha256:081f250f1ad164665ecc88cdcec8ca433c5bbb5b741cf4dbb2d3c355cdbf9d5c`)

- **Random seed:** n/a
- **Input content hash:** `sha256:22c3f8829ed5dcadc0ccad320ad660aa385f293e6b918b08bea4682c0fb6897e`
- **Output content hash:** `sha256:d15e0b5cefa6643c28578ede0d110ccd68921fb1d4b0b4fcefcb36a73f7f5f72`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
