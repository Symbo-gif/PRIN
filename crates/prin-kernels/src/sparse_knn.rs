//! Sparse phase-neighbor coupling: a CSR sparse graph type, a CPU reference,
//! and (behind the `cpu`/`cuda`/`wgpu` features) a single-source CubeCL
//! kernel set for CUDA, wgpu, and CPU-SIMD backends.
//!
//! This kernel computes the Kuramoto-style sparse k-nearest-phase-neighbor
//! coupling *derivative* contribution — `(dphase, damplitude, dfrequency)` —
//! for every oscillator, given a precomputed CSR neighbor graph. It does not
//! integrate a step (that is [`crate::mean_field_rk4`]'s and a future WP's
//! fused discrete step's job); it is the O(N·k) sparse analogue of
//! `mean_field_rk4::order_param`'s O(N) mean-field reduction, matching the
//! `SparseKnn` coupling mode's math in
//! `prin_dynamics::models::KuramotoOscillator` (see the module-level parity
//! note in the crate's S1 handoff for the cross-crate equivalence check).
//!
//! # CSR / index interoperability
//!
//! [`SparseKnnGraph`] stores the neighbor relation in compressed sparse row
//! (CSR) format: `indptr` (length `N + 1`) and `indices` (length `nnz`), both
//! `u32` (matching the element type CubeCL kernels index arrays with, and
//! bounding supported graphs to `N, nnz <= u32::MAX`, ample headroom above
//! this WP's `N = 16K` target). A graph can be built two ways:
//!
//! - [`SparseKnnGraph::from_csr`] — accept an externally built CSR structure
//!   (e.g. flattened from `prin_dynamics::state::build_phase_knn_index`'s
//!   ragged neighbor lists by another caller, or from
//!   `prin_sim::csr_coupling::SparseCoupling`'s `sprs::CsMat` via its
//!   `indptr()`/`indices()` accessors).
//! - [`SparseKnnGraph::from_phase_knn`] — build directly from a phase array
//!   and `k`, reusing `prin_dynamics::state::build_phase_knn_index`'s
//!   `O(N log N)` sort-based neighbor search (Coding Standards §1: "one
//!   algorithm, one implementation" — the neighbor-search algorithm is not
//!   re-implemented here).
//!
//! # Normalization
//!
//! Each row's edge weight is `K / degree(i)`, matching the `K / degree`
//! convention documented on `prin_dynamics::coupling::Topology` (`K/N` for
//! all-to-all, `K/k` for uniform-degree k-NN): this keeps the total coupling
//! energy per oscillator constant regardless of how many neighbors a
//! particular row has, so rows with different edge counts (e.g. a boundary
//! node in a truncated k-NN graph, or `k = 0`) do not lose or gain energy
//! relative to a uniform-degree row. A row with `degree(i) == 0` contributes
//! zero coupling (isolated oscillator).

use thiserror::Error;

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
pub mod cubecl;

/// Parameters for the sparse k-NN coupling derivative.
///
/// PRINet 3.0 uses `K` for coupling strength, `decay` (lambda) for amplitude
/// damping, and `gamma` for frequency adaptation — the same three scalars
/// [`crate::mean_field_rk4::MeanFieldRk4Params`] uses, minus `dt` (this
/// kernel computes derivatives, not an integrated step).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct SparseKnnParams {
    /// Coupling strength `K`.
    pub k: f32,
    /// Amplitude decay rate `lambda`.
    pub decay: f32,
    /// Frequency adaptation rate `gamma`.
    pub gamma: f32,
}

/// Output of a sparse k-NN coupling evaluation: `(dphase, damplitude, dfrequency)`.
pub type SparseKnnOutput = (Vec<f32>, Vec<f32>, Vec<f32>);

/// Errors raised by the sparse k-NN coupling kernels and [`SparseKnnGraph`]
/// construction.
#[derive(Debug, Error)]
pub enum SparseKnnError {
    /// Input state buffers have inconsistent lengths.
    #[error("input length mismatch: phase={phase}, amplitude={amp}, frequency={freq}")]
    LengthMismatch {
        /// Phase buffer length.
        phase: usize,
        /// Amplitude buffer length.
        amp: usize,
        /// Frequency buffer length.
        freq: usize,
    },
    /// Empty oscillator population.
    #[error("oscillator population is empty")]
    EmptyPopulation,
    /// The graph's node count does not match the state buffer length.
    #[error("graph size ({graph_n}) does not match oscillator count ({state_n})")]
    GraphSizeMismatch {
        /// Node count the graph was built for.
        graph_n: usize,
        /// Node count derived from the input state slices.
        state_n: usize,
    },
    /// `indptr` failed a CSR structural invariant.
    #[error("invalid CSR indptr: {reason}")]
    InvalidIndptr {
        /// Human-readable description of the violated invariant.
        reason: String,
    },
    /// A neighbor index in `indices` is out of range for the graph's node count.
    #[error("neighbor index {index} out of range for n = {n}")]
    IndexOutOfRange {
        /// Offending index value.
        index: u32,
        /// Graph node count.
        n: usize,
    },
    /// Non-finite parameter value.
    #[error("non-finite parameter: {name} = {value}")]
    NonFiniteParameter {
        /// Parameter name.
        name: &'static str,
        /// Parameter value.
        value: f32,
    },
    /// Neighbor-index construction (via `prin_dynamics::state`) failed.
    #[error("neighbor index construction failed: {0}")]
    NeighborIndexFailed(#[from] prin_dynamics::state::StateError),
    /// Device backend read-back failed.
    #[error("device backend read-back failed")]
    BackendReadError,
    /// The requested compute backend (wgpu/CUDA) is not available on this host.
    #[error("backend unavailable: {name}")]
    BackendUnavailable {
        /// Backend name.
        name: &'static str,
    },
    /// A device dispatch was handed a state and a derivative-output buffer set
    /// sized for different oscillator counts.
    #[error("device buffer count mismatch: state has {state} oscillators, derivs has {derivs}")]
    DeviceBufferMismatch {
        /// Oscillator count the device state was built for.
        state: usize,
        /// Oscillator count the derivative-output buffers were built for.
        derivs: usize,
    },
}

/// A sparse phase-neighbor graph in CSR (compressed sparse row) format.
///
/// See the module documentation for the CSR layout and construction paths.
///
/// # Invariants
///
/// - `indptr.len() == n + 1`, `indptr[0] == 0`, `indptr` is non-decreasing,
///   and `indptr[n] as usize == indices.len()`.
/// - Every entry of `indices` is `< n`.
#[derive(Clone, Debug, PartialEq)]
pub struct SparseKnnGraph {
    n: usize,
    indptr: Vec<u32>,
    indices: Vec<u32>,
}

impl SparseKnnGraph {
    /// Build a graph from a caller-supplied CSR structure.
    ///
    /// # Errors
    ///
    /// Returns [`SparseKnnError::EmptyPopulation`] if `n == 0`,
    /// [`SparseKnnError::InvalidIndptr`] if `indptr` violates a CSR
    /// structural invariant, or [`SparseKnnError::IndexOutOfRange`] if any
    /// `indices` entry is `>= n`.
    pub fn from_csr(n: usize, indptr: Vec<u32>, indices: Vec<u32>) -> Result<Self, SparseKnnError> {
        if n == 0 {
            return Err(SparseKnnError::EmptyPopulation);
        }
        if indptr.len() != n + 1 {
            return Err(SparseKnnError::InvalidIndptr {
                reason: format!("expected length {}, got {}", n + 1, indptr.len()),
            });
        }
        if indptr[0] != 0 {
            return Err(SparseKnnError::InvalidIndptr {
                reason: format!("indptr[0] must be 0, got {}", indptr[0]),
            });
        }
        for w in indptr.windows(2) {
            if w[1] < w[0] {
                return Err(SparseKnnError::InvalidIndptr {
                    reason: format!("indptr must be non-decreasing, got {} then {}", w[0], w[1]),
                });
            }
        }
        let nnz = indptr[n] as usize;
        if nnz != indices.len() {
            return Err(SparseKnnError::InvalidIndptr {
                reason: format!(
                    "indptr[n] = {nnz} does not match indices.len() = {}",
                    indices.len()
                ),
            });
        }
        for &idx in &indices {
            if idx as usize >= n {
                return Err(SparseKnnError::IndexOutOfRange { index: idx, n });
            }
        }
        Ok(Self { n, indptr, indices })
    }

    /// Build a graph from a phase array by taking the `k` nearest phase
    /// neighbors of every oscillator.
    ///
    /// Reuses `prin_dynamics::state::build_phase_knn_index`'s `O(N log N)`
    /// sort-based neighbor search (Coding Standards §1: one algorithm, one
    /// implementation). `k == 0` produces a graph with every row empty
    /// (every oscillator isolated).
    ///
    /// # Errors
    ///
    /// Returns [`SparseKnnError::EmptyPopulation`] if `phase` is empty,
    /// [`SparseKnnError::NeighborIndexFailed`] if the underlying neighbor
    /// search rejects the input (non-finite phase, or `k >= n`), or
    /// [`SparseKnnError::NonFiniteParameter`] if any phase value is
    /// non-finite (checked before the `f64` conversion so the error names
    /// the offending `f32` value).
    pub fn from_phase_knn(phase: &[f32], k: usize) -> Result<Self, SparseKnnError> {
        if phase.is_empty() {
            return Err(SparseKnnError::EmptyPopulation);
        }
        for (i, &p) in phase.iter().enumerate() {
            if !p.is_finite() {
                return Err(SparseKnnError::NonFiniteParameter {
                    name: "phase",
                    value: p,
                });
            }
            let _ = i;
        }
        let phase64: Vec<f64> = phase.iter().map(|&p| f64::from(p)).collect();
        let neighbors = prin_dynamics::state::build_phase_knn_index(&phase64, k)?;

        let n = phase.len();
        let mut indptr = Vec::with_capacity(n + 1);
        let mut indices = Vec::new();
        indptr.push(0u32);
        for row in &neighbors {
            for &j in row {
                indices.push(j as u32);
            }
            indptr.push(indices.len() as u32);
        }
        Ok(Self { n, indptr, indices })
    }

    /// Number of oscillators (graph node count).
    pub fn n(&self) -> usize {
        self.n
    }

    /// Number of stored edges.
    pub fn nnz(&self) -> usize {
        self.indices.len()
    }

    /// Out-degree of node `i` (number of neighbors).
    ///
    /// # Panics
    ///
    /// Panics if `i >= self.n()`.
    pub fn degree(&self, i: usize) -> usize {
        (self.indptr[i + 1] - self.indptr[i]) as usize
    }

    /// Borrow the CSR row-pointer array (length `n + 1`).
    pub fn indptr(&self) -> &[u32] {
        &self.indptr
    }

    /// Borrow the CSR neighbor-index array (length `nnz`).
    pub fn indices(&self) -> &[u32] {
        &self.indices
    }
}

/// Validate state buffer lengths against the graph's node count.
fn validate_state(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    graph: &SparseKnnGraph,
) -> Result<usize, SparseKnnError> {
    if phase.len() != amplitude.len() || phase.len() != frequency.len() {
        return Err(SparseKnnError::LengthMismatch {
            phase: phase.len(),
            amp: amplitude.len(),
            freq: frequency.len(),
        });
    }
    if phase.is_empty() {
        return Err(SparseKnnError::EmptyPopulation);
    }
    if phase.len() != graph.n() {
        return Err(SparseKnnError::GraphSizeMismatch {
            graph_n: graph.n(),
            state_n: phase.len(),
        });
    }
    Ok(phase.len())
}

/// Validate that a scalar parameter is finite.
fn validate_param(name: &'static str, value: f32) -> Result<(), SparseKnnError> {
    if !value.is_finite() {
        return Err(SparseKnnError::NonFiniteParameter { name, value });
    }
    Ok(())
}

/// Compute the sparse k-NN coupling derivative on the CPU (numerical
/// authority).
///
/// For each oscillator `i` with neighbors `NN(i)` (the CSR row `i` of
/// `graph`) and `degree(i) = |NN(i)|`:
///
/// ```text
/// weight_i   = K / degree(i)                                  (0 if degree(i) == 0)
/// sin_sum_i  = weight_i * sum_{j in NN(i)} sin(phase_j - phase_i) * amplitude_j
/// cos_sum_i  = weight_i * sum_{j in NN(i)} cos(phase_j - phase_i) * amplitude_j
/// dphase_i     = frequency_i + sin_sum_i
/// damplitude_i = -decay * amplitude_i + cos_sum_i
/// dfrequency_i = gamma * sin_sum_i / degree(i)                (0 if degree(i) == 0)
/// ```
///
/// `sin(phase_j - phase_i)` and `cos(phase_j - phase_i)` are computed via the
/// angle-difference trig identity (`sin_j*cos_i - cos_j*sin_i`, matching
/// `prin_sim::csr_coupling::SparseCoupling::kuramoto_coupling`'s SpMV
/// decomposition) rather than a raw subtraction, avoiding any large-angle
/// precision loss and matching the GPU kernel's per-thread computation
/// exactly (no host/device algorithmic divergence). Per-row sums accumulate
/// in `f64` before downcasting to `f32` (Coding Standards §2.2: "f64 for
/// reference paths and accumulations of reductions").
///
/// This matches `prin_dynamics::models::KuramotoOscillator`'s
/// `CouplingMode::SparseKnn` derivative formula exactly when every row has
/// the same degree `k` (the uniform-degree case that neighbor search always
/// produces): `weight_i = K/degree(i) = K/k` for every row.
///
/// # Errors
///
/// Returns [`SparseKnnError`] on mismatched buffer lengths, an empty
/// population, a graph/state size mismatch, or a non-finite parameter.
pub fn sparse_knn_derivatives_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    graph: &SparseKnnGraph,
    params: &SparseKnnParams,
) -> Result<SparseKnnOutput, SparseKnnError> {
    let n = validate_state(phase, amplitude, frequency, graph)?;
    validate_param("k", params.k)?;
    validate_param("decay", params.decay)?;
    validate_param("gamma", params.gamma)?;

    let mut dphase = Vec::with_capacity(n);
    let mut damplitude = Vec::with_capacity(n);
    let mut dfrequency = Vec::with_capacity(n);

    let indptr = graph.indptr();
    let indices = graph.indices();

    for i in 0..n {
        let row_start = indptr[i] as usize;
        let row_end = indptr[i + 1] as usize;
        let degree = row_end - row_start;

        let (si, ci) = phase[i].sin_cos();

        let mut sin_sum = 0.0_f64;
        let mut cos_sum = 0.0_f64;

        if degree > 0 {
            let weight = f64::from(params.k) / degree as f64;
            for &e in &indices[row_start..row_end] {
                let j = e as usize;
                let (sj, cj) = phase[j].sin_cos();
                let diff_sin = f64::from(sj) * f64::from(ci) - f64::from(cj) * f64::from(si);
                let diff_cos = f64::from(cj) * f64::from(ci) + f64::from(sj) * f64::from(si);
                sin_sum += weight * diff_sin * f64::from(amplitude[j]);
                cos_sum += weight * diff_cos * f64::from(amplitude[j]);
            }
        }

        let sin_sum_f32 = sin_sum as f32;
        dphase.push(frequency[i] + sin_sum_f32);
        damplitude.push(-params.decay * amplitude[i] + cos_sum as f32);
        dfrequency.push(if degree > 0 {
            params.gamma * sin_sum_f32 / degree as f32
        } else {
            0.0
        });
    }

    Ok((dphase, damplitude, dfrequency))
}

#[cfg(test)]
mod tests {
    use super::*;

    const DEFAULT_PARAMS: SparseKnnParams = SparseKnnParams {
        k: 2.0,
        decay: 0.1,
        gamma: 0.01,
    };

    fn ring_graph(n: usize, half_k: usize) -> SparseKnnGraph {
        // Each node connects to `half_k` neighbors on each side (wrapping).
        let mut indptr = Vec::with_capacity(n + 1);
        let mut indices = Vec::new();
        indptr.push(0u32);
        for i in 0..n {
            for d in 1..=half_k {
                indices.push(((i + n - d) % n) as u32);
                indices.push(((i + d) % n) as u32);
            }
            indptr.push(indices.len() as u32);
        }
        SparseKnnGraph::from_csr(n, indptr, indices).unwrap()
    }

    // ── SparseKnnGraph::from_csr ────────────────────────────────────────

    #[test]
    fn from_csr_basic_ring() {
        let g = ring_graph(6, 1);
        assert_eq!(g.n(), 6);
        assert_eq!(g.nnz(), 12);
        for i in 0..6 {
            assert_eq!(g.degree(i), 2);
        }
    }

    #[test]
    fn from_csr_rejects_empty() {
        let err = SparseKnnGraph::from_csr(0, vec![0], vec![]).unwrap_err();
        assert!(matches!(err, SparseKnnError::EmptyPopulation));
    }

    #[test]
    fn from_csr_rejects_wrong_indptr_length() {
        let err = SparseKnnGraph::from_csr(3, vec![0, 1], vec![1]).unwrap_err();
        assert!(matches!(err, SparseKnnError::InvalidIndptr { .. }));
    }

    #[test]
    fn from_csr_rejects_nonzero_start() {
        let err = SparseKnnGraph::from_csr(2, vec![1, 1, 1], vec![]).unwrap_err();
        assert!(matches!(err, SparseKnnError::InvalidIndptr { .. }));
    }

    #[test]
    fn from_csr_rejects_decreasing_indptr() {
        let err = SparseKnnGraph::from_csr(2, vec![0, 2, 1], vec![1, 0]).unwrap_err();
        assert!(matches!(err, SparseKnnError::InvalidIndptr { .. }));
    }

    #[test]
    fn from_csr_rejects_indptr_indices_mismatch() {
        let err = SparseKnnGraph::from_csr(2, vec![0, 1, 3], vec![1]).unwrap_err();
        assert!(matches!(err, SparseKnnError::InvalidIndptr { .. }));
    }

    #[test]
    fn from_csr_rejects_out_of_range_index() {
        let err = SparseKnnGraph::from_csr(2, vec![0, 1, 1], vec![5]).unwrap_err();
        assert!(matches!(
            err,
            SparseKnnError::IndexOutOfRange { index: 5, n: 2 }
        ));
    }

    #[test]
    fn from_csr_allows_empty_rows() {
        // n=3, only node 0 has a neighbor (node 1); nodes 1, 2 are isolated.
        let g = SparseKnnGraph::from_csr(3, vec![0, 1, 1, 1], vec![1]).unwrap();
        assert_eq!(g.degree(0), 1);
        assert_eq!(g.degree(1), 0);
        assert_eq!(g.degree(2), 0);
    }

    // ── SparseKnnGraph::from_phase_knn ──────────────────────────────────

    #[test]
    fn from_phase_knn_matches_uniform_degree() {
        let phase = vec![0.0_f32, 0.5, 1.0, 1.5, 2.0, 3.0];
        let g = SparseKnnGraph::from_phase_knn(&phase, 2).unwrap();
        assert_eq!(g.n(), 6);
        for i in 0..6 {
            assert_eq!(g.degree(i), 2);
        }
    }

    #[test]
    fn from_phase_knn_k_zero_isolates_all() {
        let phase = vec![0.0_f32, 1.0, 2.0];
        let g = SparseKnnGraph::from_phase_knn(&phase, 0).unwrap();
        assert_eq!(g.nnz(), 0);
        for i in 0..3 {
            assert_eq!(g.degree(i), 0);
        }
    }

    #[test]
    fn from_phase_knn_rejects_empty() {
        let err = SparseKnnGraph::from_phase_knn(&[], 1).unwrap_err();
        assert!(matches!(err, SparseKnnError::EmptyPopulation));
    }

    #[test]
    fn from_phase_knn_rejects_non_finite_phase() {
        let err = SparseKnnGraph::from_phase_knn(&[0.0, f32::NAN], 1).unwrap_err();
        assert!(matches!(
            err,
            SparseKnnError::NonFiniteParameter { name: "phase", .. }
        ));
    }

    #[test]
    fn from_phase_knn_rejects_k_ge_n() {
        let err = SparseKnnGraph::from_phase_knn(&[0.0, 1.0, 2.0], 3).unwrap_err();
        assert!(matches!(err, SparseKnnError::NeighborIndexFailed(_)));
    }

    // ── sparse_knn_derivatives_cpu ──────────────────────────────────────

    #[test]
    fn zero_coupling_derivative_is_free_run() {
        let n = 8;
        let graph = ring_graph(n, 1);
        let mut params = DEFAULT_PARAMS;
        params.k = 0.0;
        let phase: Vec<_> = (0..n).map(|i| 0.1 * i as f32).collect();
        let amp = vec![1.0_f32; n];
        let freq: Vec<_> = (0..n).map(|i| 0.1 * (i as f32 - 3.5)).collect();

        let (dphase, damp, dfreq) =
            sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &params).unwrap();

        for i in 0..n {
            assert!((dphase[i] - freq[i]).abs() < 1e-6);
            assert!((damp[i] - (-params.decay * amp[i])).abs() < 1e-6);
            assert_eq!(dfreq[i], 0.0);
        }
    }

    #[test]
    fn synchronized_state_has_zero_sin_sum_and_max_cos_sum() {
        // All phases equal -> sin(phase_j - phase_i) = 0 for every edge, and
        // cos(phase_j - phase_i) = 1, so cos_sum = K * amplitude (uniform amp).
        let n = 6;
        let graph = ring_graph(n, 1);
        let phase = vec![0.7_f32; n];
        let amp = vec![1.0_f32; n];
        let freq = vec![0.0_f32; n];
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.0,
            gamma: 0.0,
        };

        let (dphase, damp, _) =
            sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &params).unwrap();

        for i in 0..n {
            assert!(dphase[i].abs() < 1e-6, "dphase[{i}] = {}", dphase[i]);
            assert!((damp[i] - params.k).abs() < 1e-5, "damp[{i}] = {}", damp[i]);
        }
    }

    #[test]
    fn isolated_node_has_zero_derivative_contribution() {
        let graph = SparseKnnGraph::from_csr(3, vec![0, 1, 1, 2], vec![1, 0]).unwrap();
        let phase = vec![0.3_f32, 1.1, 2.2];
        let amp = vec![1.0_f32; 3];
        let freq = vec![0.5_f32, -0.5, 0.2];

        let (dphase, damp, dfreq) =
            sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &DEFAULT_PARAMS).unwrap();

        // Node 1 (index 1) is isolated (degree 0).
        assert!((dphase[1] - freq[1]).abs() < 1e-6);
        assert!((damp[1] - (-DEFAULT_PARAMS.decay * amp[1])).abs() < 1e-6);
        assert_eq!(dfreq[1], 0.0);
    }

    #[test]
    fn matches_uniform_degree_k_normalization() {
        // Weight must be exactly K/degree regardless of how the graph varies
        // per row; a fully-connected star (node 0 has degree n-1, all others
        // degree 1) exercises non-uniform degree per row.
        let n = 5;
        let mut indptr = vec![0u32];
        let mut indices = Vec::new();
        for j in 1..n {
            indices.push(j as u32);
        }
        indptr.push(indices.len() as u32);
        for _ in 1..n {
            indices.push(0u32);
            indptr.push(indices.len() as u32);
        }
        let graph = SparseKnnGraph::from_csr(n, indptr, indices).unwrap();
        assert_eq!(graph.degree(0), n - 1);
        for i in 1..n {
            assert_eq!(graph.degree(i), 1);
        }

        let phase = vec![0.0_f32; n];
        let amp = vec![1.0_f32; n];
        let freq = vec![0.0_f32; n];
        let params = SparseKnnParams {
            k: 4.0,
            decay: 0.0,
            gamma: 0.0,
        };
        let (_, damp, _) =
            sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &params).unwrap();
        // Synchronized phases -> cos_sum_i = K (weight * degree * cos(0) * amp = K).
        for (i, &d) in damp.iter().enumerate() {
            assert!((d - params.k).abs() < 1e-5, "damp[{i}] = {d}");
        }
    }

    #[test]
    fn rejects_mismatched_lengths() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 4];
        let amp = vec![1.0_f32; 5];
        let freq = vec![0.0_f32; 4];
        let err =
            sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &DEFAULT_PARAMS).unwrap_err();
        assert!(matches!(err, SparseKnnError::LengthMismatch { .. }));
    }

    #[test]
    fn rejects_empty_population() {
        let graph = SparseKnnGraph::from_csr(1, vec![0, 0], vec![]).unwrap();
        let err = sparse_knn_derivatives_cpu(&[], &[], &[], &graph, &DEFAULT_PARAMS).unwrap_err();
        assert!(matches!(err, SparseKnnError::EmptyPopulation));
    }

    #[test]
    fn rejects_graph_size_mismatch() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 6];
        let amp = vec![1.0_f32; 6];
        let freq = vec![0.0_f32; 6];
        let err =
            sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &DEFAULT_PARAMS).unwrap_err();
        assert!(matches!(
            err,
            SparseKnnError::GraphSizeMismatch {
                graph_n: 4,
                state_n: 6,
            }
        ));
    }

    #[test]
    fn rejects_non_finite_k() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 4];
        let mut params = DEFAULT_PARAMS;
        params.k = f32::NAN;
        let err = sparse_knn_derivatives_cpu(&phase, &phase, &phase, &graph, &params).unwrap_err();
        assert!(matches!(
            err,
            SparseKnnError::NonFiniteParameter { name: "k", .. }
        ));
    }

    #[test]
    fn rejects_non_finite_decay() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 4];
        let mut params = DEFAULT_PARAMS;
        params.decay = f32::INFINITY;
        let err = sparse_knn_derivatives_cpu(&phase, &phase, &phase, &graph, &params).unwrap_err();
        assert!(matches!(
            err,
            SparseKnnError::NonFiniteParameter { name: "decay", .. }
        ));
    }

    #[test]
    fn rejects_non_finite_gamma() {
        let graph = ring_graph(4, 1);
        let phase = vec![0.0_f32; 4];
        let mut params = DEFAULT_PARAMS;
        params.gamma = f32::NAN;
        let err = sparse_knn_derivatives_cpu(&phase, &phase, &phase, &graph, &params).unwrap_err();
        assert!(matches!(
            err,
            SparseKnnError::NonFiniteParameter { name: "gamma", .. }
        ));
    }

    // ── Cross-crate parity: prin_dynamics::models::KuramotoOscillator ──────

    #[test]
    fn parity_against_prin_dynamics_kuramoto_sparse_knn() {
        use prin_dynamics::coupling::CouplingMode;
        use prin_dynamics::models::{Dynamics, KuramotoOscillator};
        use prin_dynamics::state::OscillatorState;

        let n = 6;
        let k_neighbors = 2;
        let phase64: Vec<f64> = (0..n).map(|i| 0.3 * i as f64).collect();
        let amp64 = vec![1.0_f64; n];
        let freq64: Vec<f64> = (0..n).map(|i| 0.1 * (i as f64 - 2.5)).collect();

        let model = KuramotoOscillator::new(
            n,
            2.0,
            0.1,
            0.01,
            CouplingMode::SparseKnn {
                k: Some(k_neighbors),
            },
        )
        .unwrap();
        let state =
            OscillatorState::new(phase64.clone(), amp64.clone(), freq64.clone(), None).unwrap();
        let reference = model.compute_derivatives(&state).unwrap();

        let phase32: Vec<f32> = phase64.iter().map(|&p| p as f32).collect();
        let amp32: Vec<f32> = amp64.iter().map(|&a| a as f32).collect();
        let freq32: Vec<f32> = freq64.iter().map(|&f| f as f32).collect();
        let graph = SparseKnnGraph::from_phase_knn(&phase32, k_neighbors).unwrap();
        let params = SparseKnnParams {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
        };
        let (dphase, damp, dfreq) =
            sparse_knn_derivatives_cpu(&phase32, &amp32, &freq32, &graph, &params).unwrap();

        for i in 0..n {
            assert!(
                (dphase[i] as f64 - reference.dphase[i]).abs() < 1e-4,
                "dphase[{i}]: prin-kernels={}, prin-dynamics={}",
                dphase[i],
                reference.dphase[i]
            );
            assert!(
                (damp[i] as f64 - reference.damplitude[i]).abs() < 1e-4,
                "damplitude[{i}]: prin-kernels={}, prin-dynamics={}",
                damp[i],
                reference.damplitude[i]
            );
            assert!(
                (dfreq[i] as f64 - reference.dfrequency[i]).abs() < 1e-4,
                "dfrequency[{i}]: prin-kernels={}, prin-dynamics={}",
                dfreq[i],
                reference.dfrequency[i]
            );
        }
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    const TAU: f32 = core::f32::consts::TAU;

    fn any_params() -> impl Strategy<Value = SparseKnnParams> {
        (0.0_f32..=2.0_f32, 0.0_f32..=0.5_f32, -0.1_f32..=0.1_f32)
            .prop_map(|(k, decay, gamma)| SparseKnnParams { k, decay, gamma })
    }

    fn ring_graph(n: usize, half_k: usize) -> SparseKnnGraph {
        let mut indptr = Vec::with_capacity(n + 1);
        let mut indices = Vec::new();
        indptr.push(0u32);
        for i in 0..n {
            for d in 1..=half_k {
                indices.push(((i + n - d) % n) as u32);
                indices.push(((i + d) % n) as u32);
            }
            indptr.push(indices.len() as u32);
        }
        SparseKnnGraph::from_csr(n, indptr, indices).unwrap()
    }

    #[test]
    fn derivative_outputs_are_always_finite() {
        let config = ProptestConfig::with_cases(64);
        proptest!(config, |(
            n in 4usize..=32,
            params in any_params(),
            phase_seed in proptest::collection::vec(0.0_f32..TAU, 32),
            amp_seed in proptest::collection::vec(0.0_f32..=2.0_f32, 32),
            freq_seed in proptest::collection::vec(-1.0_f32..=1.0_f32, 32),
        )| {
            let phase = phase_seed[..n].to_vec();
            let amp = amp_seed[..n].to_vec();
            let freq = freq_seed[..n].to_vec();
            let graph = ring_graph(n, 1);

            let (dphase, damp, dfreq) =
                sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &params).unwrap();

            for i in 0..n {
                prop_assert!(dphase[i].is_finite());
                prop_assert!(damp[i].is_finite());
                prop_assert!(dfreq[i].is_finite());
            }
        });
    }

    #[test]
    fn zero_coupling_matches_free_run_analytically() {
        let config = ProptestConfig::with_cases(64);
        proptest!(config, |(
            n in 4usize..=32,
            decay in 0.0_f32..=0.5_f32,
            phase_seed in proptest::collection::vec(0.0_f32..TAU, 32),
            amp_seed in proptest::collection::vec(0.0_f32..=2.0_f32, 32),
            freq_seed in proptest::collection::vec(-1.0_f32..=1.0_f32, 32),
        )| {
            let phase = phase_seed[..n].to_vec();
            let amp = amp_seed[..n].to_vec();
            let freq = freq_seed[..n].to_vec();
            let graph = ring_graph(n, 1);
            let params = SparseKnnParams { k: 0.0, decay, gamma: 0.0 };

            let (dphase, damp, dfreq) =
                sparse_knn_derivatives_cpu(&phase, &amp, &freq, &graph, &params).unwrap();

            for i in 0..n {
                prop_assert!((dphase[i] - freq[i]).abs() < 1e-5);
                prop_assert!((damp[i] - (-decay * amp[i])).abs() < 1e-5);
                prop_assert_eq!(dfreq[i], 0.0);
            }
        });
    }
}
