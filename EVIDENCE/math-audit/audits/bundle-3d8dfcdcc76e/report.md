# Audit Evidence Report: bundle-3d8dfcdcc76e

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-20T04:30:46.855Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### GRA-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `graph_topology`  
- **Severity:** `high`  
- **Statement:** build_ring(N=6, k_ring=4) connects each node to its +-1 and +-2 neighbours mod N, producing a connected, 4-regular graph with exactly N*k_ring/2=12 undirected edges and no self-loops.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-fde740c45d37

### GRA-02 -- `PASS`

- **Type:** `graph_topology`  
- **Severity:** `medium`  
- **Statement:** build_all_to_all(N=4) is the complete graph K4: connected, 3-regular (every node connects to all others), 6 undirected edges, no self-loops.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-ad296a8b94bf

### GRA-01-LEAN -- `PASS`

- **Type:** `lean_theorem`  
- **Severity:** `high`  
- **Statement:** Formal (Lean 4 kernel-checked `decide`) corroboration of GRA-01: build_ring(N=6, k_ring=4)'s declared neighbour structure {i+-1, i+-2 mod 6} is 4-regular (each node has exactly 4 distinct neighbours), has no self-loops, has exactly N*k_ring/2=12 undirected edges after canonicalising directed pairs, and is connected (every node reachable from node 0 via bounded neighbour-closure). EMA-001 M-F3: added to let this high-severity graph_topology claim earn genuine symbolic/formal corroboration (policy.verdict_rules.high_severity_requires_symbolic_or_formal) via a third independent channel (Lean's kernel) alongside GRA-01's own NetworkX evidence, rather than relying on human sign-off alone.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-950737632a96

### GRA-01-SAT -- `PASS`

- **Type:** `graph_regularity_sat`  
- **Severity:** `medium`  
- **Statement:** PySAT corroboration of GRA-01's regularity component: build_ring(N=6, k_ring=4)'s declared edge set is exactly 4-regular. Verified via a CNF cardinality (Sinz sequential-counter) encoding over each node's incident-edge atoms, checked by an independent CDCL SAT solver (glucose3) -- a different implementation stack from GRA-01's NetworkX degree counting and GRA-01-LEAN's Lean kernel `decide`. EMA-004: added as additional crosscheck evidence for the M-F7 REQUIRES_HUMAN_REVIEW policy gate on GRA-01 (does not itself change GRA-01's gated status, which remains resolved-by-design per DV-013/R20; this is supplementary evidence, not a replacement).  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-aa8c6c311228

## Tool invocations

### audit_graph_topology (`audit-fde740c45d37`) -- `PASS`

- **Adapter:** `networkx`
- **Severity:** `high`
- **Duration:** 5 ms
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
- **Output content hash:** `sha256:d3beb49687d281c925a4f90df45c495be7faac4ea2a1f55271f8d5b035eda42e`

### audit_graph_topology (`audit-ad296a8b94bf`) -- `PASS`

- **Adapter:** `networkx`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Graph is confirmed 3-regular.

**Reasoning:** All 4 nodes have degree 3. Additional properties: connected=True.

**Metrics:**
- num_nodes: 4.0
- num_edges: 6.0
- num_connected_components: 1.0
- cycle_basis_size: 3.0
- diameter: 1.0
- average_shortest_path_length: 1.0
- algebraic_connectivity: 3.9999999999999996

- **Random seed:** n/a
- **Input content hash:** `sha256:c570a62760ea4f883d3c2a6d887a830f42efda13c7bd5f040910e137ed71d152`
- **Output content hash:** `sha256:0baf49b8f36b05b0682a9685c112be1040dfccb1a1f3384c269f5f3aa863e763`

### verify_lean_claim (`audit-950737632a96`) -- `PASS`

- **Adapter:** `lean`
- **Severity:** `high`
- **Duration:** 818 ms
- **Summary:** Lean elaborated successfully; expected_outcome='proves'.

**Reasoning:** Ran `C:\Users\there\.elan\bin\lean.EXE C:\dev\PRIN\EVIDENCE\math-audit\scratch\lean\tmpl4jqxukf.lean`. Elaboration succeeded. See lean-diagnostics.txt artifact for full sanitized output.

**Limitations:**
- This adapter drives the Lean CLI and inspects exit status/diagnostics; it does not perform interactive elaboration introspection (a Lean LSP bridge is a documented future extension).

**Artifacts:**
- [Sanitized Lean/lake stdout+stderr](artifacts/lean-diagnostics.txt) (`sha256:081f250f1ad164665ecc88cdcec8ca433c5bbb5b741cf4dbb2d3c355cdbf9d5c`)

- **Random seed:** n/a
- **Input content hash:** `sha256:22c3f8829ed5dcadc0ccad320ad660aa385f293e6b918b08bea4682c0fb6897e`
- **Output content hash:** `sha256:2c2b4c1babf3aa7337705aceeb34428c213e47379aae3f6aa7362875a2ca0ceb`

### audit_graph_regularity_sat (`audit-aa8c6c311228`) -- `PASS`

- **Adapter:** `pysat`
- **Severity:** `medium`
- **Duration:** 10 ms
- **Summary:** PySAT cardinality-encoding check (solver=glucose3) independently confirmed every node has exactly 4 incident edge(s).

**Reasoning:** For each of 6 node(s), asserted its declared incident-edge atoms as unit clauses and checked satisfiability of a Sinz sequential-counter equals(4) cardinality encoding over them via an independent CDCL SAT solver; every node's encoding was satisfiable, which by construction is possible only when its true degree equals expected_degree.

**Limitations:**
- This tool verifies k-regularity only (a concrete, fully-instantiated graph's incidence structure); it does not independently verify connectivity.

- **Random seed:** n/a
- **Input content hash:** `sha256:8b81662938e1ef8d5ca99cf5189ad0a08dbadaac1935f3eba9105c1781b9e247`
- **Output content hash:** `sha256:d04022f17b484f628f0ac265a412e9c89ac0274d9574de03631580a45ce9fd19`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
