//! Coupling topologies and modes.
//!
//! Normalization semantics (`1/N` mean-field vs `1/k` sparse) are preserved
//! exactly from PRINet 3.0 as a documented numerical invariant.

use serde::{Deserialize, Serialize};

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
