# Audit Evidence Report: bundle-1bc6b2b6fb3b

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:0e1c329642e07f0b71a7f250a60815d3fc9f6ac4f86dda4f3865149ed6c07608`)
**Generated:** 2026-08-14T23:45:43.576Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### GRA-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `graph_topology`  
- **Severity:** `high`  
- **Statement:** build_ring(N=6, k_ring=4) connects each node to its +-1 and +-2 neighbours mod N, producing a connected, 4-regular graph with exactly N*k_ring/2=12 undirected edges and no self-loops.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-ac2d4ae95526

### GRA-02 -- `PASS`

- **Type:** `graph_topology`  
- **Severity:** `medium`  
- **Statement:** build_all_to_all(N=4) is the complete graph K4: connected, 3-regular (every node connects to all others), 6 undirected edges, no self-loops.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-0fe2acbe0268

## Tool invocations

### audit_graph_topology (`audit-ac2d4ae95526`) -- `PASS`

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
- algebraic_connectivity: 4.0

- **Random seed:** n/a
- **Input content hash:** `sha256:5c40abf3df2a3892a6b1a8b048d78b38bba3bd8616aa02da864474bd1182de8c`
- **Output content hash:** `sha256:ce0aedb0c811f8fc27be223807e9161c8d1d9e9afd8187834655940c4dfc4d79`

### audit_graph_topology (`audit-0fe2acbe0268`) -- `PASS`

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
- algebraic_connectivity: 3.9999999999999996

- **Random seed:** n/a
- **Input content hash:** `sha256:c570a62760ea4f883d3c2a6d887a830f42efda13c7bd5f040910e137ed71d152`
- **Output content hash:** `sha256:1704afab10dd91cf17d58db03d5d8786d7d8ac7d4415e02c448b10264c01ba3c`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
