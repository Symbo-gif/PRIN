//! Coupling topologies and modes.
//!
//! Normalization semantics (`1/N` mean-field vs `1/k` sparse) are preserved
//! exactly from PRINet 3.0 as a documented numerical invariant.
//!
//! ## Topology builders
//!
//! [`Topology`] enumerates structured coupling patterns (all-to-all, ring
//! lattice, Watts–Strogatz small-world). Each variant builds an `N × N`
//! coupling matrix in row-major order via [`Topology::build_matrix`], which
//! can be fed to [`CouplingMode::Full`] `{ matrix: Some(...) }`. The
//! normalization rule for all topology builders is `K / degree` per edge
//! (analogous to `K / N` for all-to-all and `K / k` for sparse k-NN), keeping
//! the total coupling energy per oscillator constant regardless of topology.

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::seed::Seed;

/// Errors raised by coupling topology construction.
#[derive(Debug, Error)]
pub enum CouplingError {
    /// The population size is zero.
    #[error("coupling topology requires n >= 1, got {n}")]
    EmptyPopulation {
        /// Offending population size.
        n: usize,
    },

    /// A structural parameter is invalid for the requested topology.
    #[error("invalid topology parameter `{name}` = {value} for n = {n}")]
    InvalidParameter {
        /// Name of the offending parameter.
        name: &'static str,
        /// Offending value (encoded as f64 for uniform reporting).
        value: f64,
        /// Population size.
        n: usize,
    },

    /// A custom matrix has the wrong length.
    #[error("custom matrix length {got} does not match expected {expected}")]
    MatrixLengthMismatch {
        /// Expected length.
        expected: usize,
        /// Actual length.
        got: usize,
    },

    /// A matrix entry is not finite.
    #[error("non-finite matrix entry at index {index}: {value}")]
    NonFiniteEntry {
        /// Index of the offending entry.
        index: usize,
        /// Offending value.
        value: f64,
    },
}

/// Enum representing coupling semantics across oscillator models.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum CouplingMode {
    /// Global complex order parameter mean-field coupling (O(N)).
    MeanField,

    /// Full pairwise matrix coupling (O(N²)).
    ///
    /// If `matrix` is `None`, uniform all-to-all coupling scaled by `K/N` with zero diagonal is used.
    Full {
        /// Optional custom N x N coupling matrix stored in row-major order.
        matrix: Option<Vec<f64>>,
    },

    /// Sparse k-nearest phase neighbors coupling (O(N k)).
    ///
    /// If `k` is `None`, `k` defaults to `max(1, ceil(log2(N)))`.
    SparseKnn {
        /// Optional number of nearest phase neighbors `k`.
        k: Option<usize>,
    },
}

impl Default for CouplingMode {
    fn default() -> Self {
        Self::Full { matrix: None }
    }
}

/// Structured coupling topology patterns that produce `N × N` matrices.
///
/// Each variant builds a coupling matrix via [`Topology::build_matrix`] that
/// can be supplied to [`CouplingMode::Full`] `{ matrix: Some(...) }`.
///
/// Normalization: every edge weight is `K / degree`, where `degree` is the
/// number of outgoing edges per oscillator. This keeps the total coupling
/// energy per oscillator constant regardless of topology, matching the `K/N`
/// (all-to-all) and `K/k` (sparse k-NN) conventions.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum Topology {
    /// All-to-all uniform coupling with zero diagonal.
    ///
    /// Each off-diagonal entry is `K / N`; the diagonal is `0`. This is the
    /// default matrix used by [`CouplingMode::Full`] `{ matrix: None }` and
    /// serves as the reference for sparse/full equivalence tests.
    AllToAll,

    /// Ring lattice: each node connects to its `k_ring` nearest neighbours
    /// (`k_ring/2` on each side, wrapping around).
    ///
    /// Each edge weight is `K / k_ring`. Requires `k_ring >= 2` and even
    /// (so that neighbours are symmetric on each side); `k_ring` is clamped
    /// to `N - 1` if it exceeds the population.
    Ring {
        /// Number of neighbours per node (must be `>= 2` and even).
        k_ring: usize,
    },

    /// Watts–Strogatz small-world network.
    ///
    /// Starts from a [`Topology::Ring`] lattice with `k_ring` neighbours and
    /// rewires each edge to a random target with probability `rewire_prob`.
    /// Rewiring uses the supplied [`Seed`] for deterministic reproducibility.
    /// Edge weights remain `K / k_ring`; self-loops and duplicate edges are
    /// avoided. The diagonal is always zero.
    SmallWorld {
        /// Number of neighbours per node in the base ring lattice.
        k_ring: usize,
        /// Rewiring probability in `[0, 1]`.
        rewire_prob: f64,
        /// Deterministic seed for rewiring.
        seed: Seed,
    },
}

impl Topology {
    /// Build the `N × N` coupling matrix (row-major) for this topology.
    ///
    /// The matrix is stored as a flat `Vec<f64>` of length `N * N`. Entry
    /// `(i, j)` is at index `i * N + j`. The diagonal is always zero.
    ///
    /// # Errors
    ///
    /// Returns [`CouplingError`] for an empty population, invalid structural
    /// parameters, or non-finite `coupling_strength`.
    ///
    /// # Example
    ///
    /// ```
    /// use prin_dynamics::coupling::{CouplingMode, Topology};
    ///
    /// let topo = Topology::Ring { k_ring: 4 };
    /// let matrix = topo.build_matrix(6, 1.5).unwrap();
    /// let mode = CouplingMode::Full { matrix: Some(matrix.clone()) };
    /// assert_eq!(mode, CouplingMode::Full { matrix: Some(matrix) });
    /// ```
    pub fn build_matrix(
        &self,
        n: usize,
        coupling_strength: f64,
    ) -> Result<Vec<f64>, CouplingError> {
        if n == 0 {
            return Err(CouplingError::EmptyPopulation { n });
        }
        if !coupling_strength.is_finite() {
            return Err(CouplingError::InvalidParameter {
                name: "coupling_strength",
                value: coupling_strength,
                n,
            });
        }
        match self {
            Topology::AllToAll => build_all_to_all(n, coupling_strength),
            Topology::Ring { k_ring } => build_ring(n, *k_ring, coupling_strength),
            Topology::SmallWorld {
                k_ring,
                rewire_prob,
                seed,
            } => build_small_world(n, *k_ring, *rewire_prob, coupling_strength, seed.clone()),
        }
    }
}

/// Build the all-to-all coupling matrix: `K/N` off-diagonal, `0` diagonal.
fn build_all_to_all(n: usize, k: f64) -> Result<Vec<f64>, CouplingError> {
    let inv_n = k / (n as f64);
    let mut mat = vec![inv_n; n * n];
    for i in 0..n {
        mat[i * n + i] = 0.0;
    }
    Ok(mat)
}

/// Build a ring lattice coupling matrix.
///
/// Each node `i` connects to `k_ring/2` neighbours on each side (wrapping).
/// Edge weight is `K / k_ring`. The diagonal is zero.
fn build_ring(n: usize, k_ring: usize, k: f64) -> Result<Vec<f64>, CouplingError> {
    if k_ring < 2 {
        return Err(CouplingError::InvalidParameter {
            name: "k_ring",
            value: k_ring as f64,
            n,
        });
    }
    if k_ring % 2 != 0 {
        return Err(CouplingError::InvalidParameter {
            name: "k_ring",
            value: k_ring as f64,
            n,
        });
    }
    // Clamp k_ring to N-1 (must leave at least the diagonal empty).
    let k_ring = k_ring.min(n - 1);
    if k_ring < 2 {
        // N too small for a ring with k_ring >= 2; fall back to all-to-all.
        return build_all_to_all(n, k);
    }

    let weight = k / (k_ring as f64);
    let half = k_ring / 2;
    let mut mat = vec![0.0; n * n];
    for i in 0..n {
        for d in 1..=half {
            let left = (i + n - d) % n;
            let right = (i + d) % n;
            mat[i * n + left] = weight;
            mat[i * n + right] = weight;
        }
    }
    Ok(mat)
}

/// Build a Watts–Strogatz small-world coupling matrix.
///
/// Starts from a ring lattice, then rewires each edge `i → j` to a random
/// target `j'` with probability `rewire_prob`. Self-loops and duplicate edges
/// are avoided. Edge weights remain `K / k_ring`.
fn build_small_world(
    n: usize,
    k_ring: usize,
    rewire_prob: f64,
    k: f64,
    mut seed: Seed,
) -> Result<Vec<f64>, CouplingError> {
    if !rewire_prob.is_finite() || !(0.0..=1.0).contains(&rewire_prob) {
        return Err(CouplingError::InvalidParameter {
            name: "rewire_prob",
            value: rewire_prob,
            n,
        });
    }
    // Start from the ring lattice.
    let mut mat = build_ring(n, k_ring, k)?;
    let half = (k_ring.min(n - 1)) / 2;
    let weight = k / (k_ring.min(n - 1) as f64);

    // Rewire: for each node i, consider each right-neighbour edge (i, i+d)
    // and rewire to a random target with probability rewire_prob.
    for i in 0..n {
        for d in 1..=half {
            let j = (i + d) % n;
            if seed.next_f64() < rewire_prob {
                // Pick a random target != i that is not already connected from i.
                let mut new_target = i;
                let mut attempts = 0;
                while (new_target == i || mat[i * n + new_target] != 0.0) && attempts < n {
                    new_target = (seed.next_f64() * (n as f64)) as usize;
                    attempts += 1;
                }
                if new_target != i && mat[i * n + new_target] == 0.0 {
                    // Remove old edge, add new.
                    mat[i * n + j] = 0.0;
                    mat[i * n + new_target] = weight;
                }
            }
        }
    }
    Ok(mat)
}

/// Validate that a coupling matrix has the correct length and finite entries.
///
/// # Errors
///
/// Returns [`CouplingError::MatrixLengthMismatch`] if the length is not
/// `n * n`, or [`CouplingError::NonFiniteEntry`] if any entry is non-finite.
pub fn validate_coupling_matrix(matrix: &[f64], n: usize) -> Result<(), CouplingError> {
    let expected = n * n;
    if matrix.len() != expected {
        return Err(CouplingError::MatrixLengthMismatch {
            expected,
            got: matrix.len(),
        });
    }
    for (i, &v) in matrix.iter().enumerate() {
        if !v.is_finite() {
            return Err(CouplingError::NonFiniteEntry { index: i, value: v });
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coupling_mode_default_is_full_no_matrix() {
        assert_eq!(CouplingMode::default(), CouplingMode::Full { matrix: None });
    }

    #[test]
    fn topology_all_to_all_matches_default_full_matrix() {
        let mat = Topology::AllToAll.build_matrix(4, 1.0).unwrap();
        validate_coupling_matrix(&mat, 4).unwrap();
        // Off-diagonal = K/N = 0.25, diagonal = 0.
        for i in 0..4 {
            for j in 0..4 {
                let val = mat[i * 4 + j];
                if i == j {
                    assert_eq!(val, 0.0);
                } else {
                    assert!((val - 0.25).abs() < 1e-12);
                }
            }
        }
    }

    #[test]
    fn topology_all_to_all_rejects_empty() {
        let err = Topology::AllToAll.build_matrix(0, 1.0).unwrap_err();
        assert!(matches!(err, CouplingError::EmptyPopulation { n: 0 }));
    }

    #[test]
    fn topology_ring_basic() {
        // N=6, k_ring=4 → each node connects to 2 left + 2 right.
        let mat = Topology::Ring { k_ring: 4 }.build_matrix(6, 1.0).unwrap();
        validate_coupling_matrix(&mat, 6).unwrap();
        let weight = 1.0 / 4.0; // K / k_ring
        // Node 0: neighbours are 5, 4 (left) and 1, 2 (right).
        assert!((mat[1] - weight).abs() < 1e-12);
        assert!((mat[2] - weight).abs() < 1e-12);
        assert!((mat[4] - weight).abs() < 1e-12);
        assert!((mat[5] - weight).abs() < 1e-12);
        assert_eq!(mat[0], 0.0);
        assert_eq!(mat[3], 0.0);
    }

    #[test]
    fn topology_ring_rejects_odd_k() {
        let err = Topology::Ring { k_ring: 3 }
            .build_matrix(6, 1.0)
            .unwrap_err();
        assert!(matches!(
            err,
            CouplingError::InvalidParameter { name: "k_ring", .. }
        ));
    }

    #[test]
    fn topology_ring_rejects_k_too_small() {
        let err = Topology::Ring { k_ring: 1 }
            .build_matrix(6, 1.0)
            .unwrap_err();
        assert!(matches!(
            err,
            CouplingError::InvalidParameter { name: "k_ring", .. }
        ));
    }

    #[test]
    fn topology_ring_clamps_k_to_n_minus_1() {
        // k_ring=10 with N=6 → clamped to 5 (but 5 is odd, clamped to 4).
        // Actually k_ring.min(n-1) = 5, which is odd → but we clamp before the odd check.
        // The build_ring clamps k_ring to n-1=5, then checks if k_ring < 2 (no),
        // then uses half = 5/2 = 2. So effectively k_ring=4 edges.
        let mat = Topology::Ring { k_ring: 10 }.build_matrix(6, 1.0).unwrap();
        validate_coupling_matrix(&mat, 6).unwrap();
        // Each row should have at most 4 non-zero entries (2 left + 2 right).
        for i in 0..6 {
            let nonzero = (0..6).filter(|&j| mat[i * 6 + j] != 0.0).count();
            assert!(nonzero <= 4, "row {i} has {nonzero} nonzeros");
        }
    }

    #[test]
    fn topology_ring_small_n_falls_back_to_all_to_all() {
        // N=2, k_ring=4 → k_ring clamped to 1 < 2 → fall back to all-to-all.
        let mat = Topology::Ring { k_ring: 4 }.build_matrix(2, 1.0).unwrap();
        // All-to-all: K/N = 0.5 off-diagonal.
        assert!((mat[1] - 0.5).abs() < 1e-12);
        assert!((mat[2] - 0.5).abs() < 1e-12);
        assert_eq!(mat[0], 0.0);
        assert_eq!(mat[3], 0.0);
    }

    #[test]
    fn topology_small_world_deterministic_with_seed() {
        let seed1 = Seed::new(0, 42);
        let seed2 = Seed::new(0, 42);
        let topo1 = Topology::SmallWorld {
            k_ring: 4,
            rewire_prob: 0.3,
            seed: seed1,
        };
        let topo2 = Topology::SmallWorld {
            k_ring: 4,
            rewire_prob: 0.3,
            seed: seed2,
        };
        let mat1 = topo1.build_matrix(8, 1.0).unwrap();
        let mat2 = topo2.build_matrix(8, 1.0).unwrap();
        assert_eq!(mat1, mat2);
    }

    #[test]
    fn topology_small_world_zero_rewire_equals_ring() {
        let seed = Seed::new(0, 1);
        let sw = Topology::SmallWorld {
            k_ring: 4,
            rewire_prob: 0.0,
            seed,
        };
        let ring = Topology::Ring { k_ring: 4 };
        let mat_sw = sw.build_matrix(8, 1.0).unwrap();
        let mat_ring = ring.build_matrix(8, 1.0).unwrap();
        assert_eq!(mat_sw, mat_ring);
    }

    #[test]
    fn topology_small_world_validates_rewire_prob() {
        let seed = Seed::new(0, 1);
        let err = Topology::SmallWorld {
            k_ring: 4,
            rewire_prob: 1.5,
            seed,
        }
        .build_matrix(8, 1.0)
        .unwrap_err();
        assert!(matches!(
            err,
            CouplingError::InvalidParameter {
                name: "rewire_prob",
                ..
            }
        ));
    }

    #[test]
    fn topology_small_world_preserves_edge_count() {
        // With rewiring, the total number of edges should stay the same
        // (each rewired edge is moved, not removed).
        let seed = Seed::new(0, 99);
        let sw = Topology::SmallWorld {
            k_ring: 4,
            rewire_prob: 0.5,
            seed,
        };
        let mat = sw.build_matrix(10, 1.0).unwrap();
        let ring = Topology::Ring { k_ring: 4 }.build_matrix(10, 1.0).unwrap();
        let sw_edges: usize = mat.iter().filter(|&&v| v != 0.0).count();
        let ring_edges: usize = ring.iter().filter(|&&v| v != 0.0).count();
        assert_eq!(sw_edges, ring_edges);
    }

    #[test]
    fn topology_rejects_non_finite_coupling_strength() {
        let err = Topology::AllToAll.build_matrix(4, f64::NAN).unwrap_err();
        assert!(matches!(
            err,
            CouplingError::InvalidParameter {
                name: "coupling_strength",
                ..
            }
        ));
    }

    #[test]
    fn validate_coupling_matrix_rejects_wrong_length() {
        let err = validate_coupling_matrix(&[0.0; 3], 2).unwrap_err();
        assert!(matches!(err, CouplingError::MatrixLengthMismatch { .. }));
    }

    #[test]
    fn validate_coupling_matrix_rejects_non_finite() {
        let mut mat = vec![0.0; 4];
        mat[1] = f64::NAN;
        let err = validate_coupling_matrix(&mat, 2).unwrap_err();
        assert!(matches!(
            err,
            CouplingError::NonFiniteEntry { index: 1, .. }
        ));
    }

    #[test]
    fn topology_ring_diagonal_is_zero() {
        let mat = Topology::Ring { k_ring: 4 }.build_matrix(8, 1.0).unwrap();
        for i in 0..8 {
            assert_eq!(mat[i * 8 + i], 0.0);
        }
    }

    #[test]
    fn topology_small_world_diagonal_is_zero() {
        let seed = Seed::new(0, 7);
        let mat = Topology::SmallWorld {
            k_ring: 4,
            rewire_prob: 0.5,
            seed,
        }
        .build_matrix(10, 1.0)
        .unwrap();
        for i in 0..10 {
            assert_eq!(mat[i * 10 + i], 0.0);
        }
    }

    #[test]
    fn topology_serialization_roundtrip() {
        let topo = Topology::Ring { k_ring: 4 };
        let json = serde_json::to_string(&topo).unwrap();
        let restored: Topology = serde_json::from_str(&json).unwrap();
        assert_eq!(topo, restored);
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn all_to_all_matrix_shape_and_diagonal(n in 1usize..=32, k in 0.1f64..=5.0) {
            let mat = Topology::AllToAll.build_matrix(n, k).unwrap();
            prop_assert_eq!(mat.len(), n * n);
            for i in 0..n {
                prop_assert_eq!(mat[i * n + i], 0.0);
                for j in 0..n {
                    if i != j {
                        let expected = k / (n as f64);
                        prop_assert!((mat[i * n + j] - expected).abs() < 1e-12);
                    }
                }
            }
        }
    }

    proptest! {
        #[test]
        fn ring_matrix_shape_and_diagonal(
            n in 3usize..=32,
            k_ring in 2usize..=8,
            k in 0.1f64..=5.0,
        ) {
            // Only test even k_ring.
            let k_ring = k_ring / 2 * 2;
            prop_assume!(k_ring >= 2);
            let mat = Topology::Ring { k_ring }.build_matrix(n, k).unwrap();
            prop_assert_eq!(mat.len(), n * n);
            for i in 0..n {
                prop_assert_eq!(mat[i * n + i], 0.0);
            }
        }
    }

    proptest! {
        #[test]
        fn small_world_deterministic_same_seed(
            n in 4usize..=16,
            k_ring in (2usize..=6).prop_map(|x| x / 2 * 2),
            rewire in 0.0f64..=1.0,
            key in any::<u128>(),
        ) {
            prop_assume!(k_ring >= 2);
            let topo1 = Topology::SmallWorld {
                k_ring,
                rewire_prob: rewire,
                seed: Seed::new(0, key),
            };
            let topo2 = Topology::SmallWorld {
                k_ring,
                rewire_prob: rewire,
                seed: Seed::new(0, key),
            };
            let m1 = topo1.build_matrix(n, 1.0).unwrap();
            let m2 = topo2.build_matrix(n, 1.0).unwrap();
            prop_assert_eq!(m1, m2);
        }
    }
}
