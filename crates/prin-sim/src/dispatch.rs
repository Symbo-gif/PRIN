//! CPU reference/parallel dispatch for element-wise and row-wise hot loops.
//!
//! `rayon` parallel iterators pay real thread-pool dispatch and join/collect
//! synchronization cost on every call. For the small CSR row dot products and
//! single-FLOP element-wise operations in [`crate::csr_coupling`] and
//! [`crate::engine`], that overhead dominates the actual work below a few
//! tens of thousands of elements — the S1 implementation parallelized every
//! such loop unconditionally (via `par_bridge()` or plain `par_iter()`) and
//! was, per WP016-F1 benchmark evidence, up to 6x *slower* than a sequential
//! loop at the N = 256–16384 problem sizes exercised by `sweep_bench.rs`.
//!
//! [`map_dispatch`] and [`zip_map_dispatch`] give every hot loop a single
//! call site that is simultaneously the sequential CPU reference path
//! (Coding Standards §1.1 "one algorithm, one implementation") and the
//! rayon-parallel path, selected by problem size against
//! [`PARALLEL_LEN_THRESHOLD`].

use rayon::prelude::*;

/// Minimum slice length at which parallel (`rayon`) dispatch outperforms a
/// sequential loop for the trivial per-element/per-row work done in
/// `csr_coupling` and `engine`.
///
/// Tuned against `crates/prin-sim/benches/sweep_bench.rs` on 16-core
/// hardware (WP016-F1 remediation, S3): below this length, thread-pool
/// dispatch and join/collect synchronization cost more than the work being
/// parallelized.
pub(crate) const PARALLEL_LEN_THRESHOLD: usize = 32_768;

/// Map `f` over `items`, dispatching to rayon only when `items.len()` is at
/// or above `threshold`.
///
/// Kept separate from [`map_dispatch`] so tests can exercise both the
/// sequential and parallel branches deterministically without depending on
/// the tuned [`PARALLEL_LEN_THRESHOLD`] constant.
fn map_dispatch_with_threshold<T, R>(
    items: &[T],
    threshold: usize,
    f: impl Fn(&T) -> R + Sync + Send,
) -> Vec<R>
where
    T: Sync,
    R: Send,
{
    if items.len() < threshold {
        items.iter().map(&f).collect()
    } else {
        items.par_iter().map(f).collect()
    }
}

/// Zip-map `f` over two equal-length slices, dispatching to rayon only when
/// `a.len()` is at or above `threshold`.
fn zip_map_dispatch_with_threshold<A, B, R>(
    a: &[A],
    b: &[B],
    threshold: usize,
    f: impl Fn(&A, &B) -> R + Sync + Send,
) -> Vec<R>
where
    A: Sync,
    B: Sync,
    R: Send,
{
    if a.len() < threshold {
        a.iter().zip(b.iter()).map(|(x, y)| f(x, y)).collect()
    } else {
        a.par_iter()
            .zip(b.par_iter())
            .map(|(x, y)| f(x, y))
            .collect()
    }
}

/// Map `f` over `items`, dispatching to rayon only when `items.len() >=
/// `[`PARALLEL_LEN_THRESHOLD`].
pub(crate) fn map_dispatch<T, R>(items: &[T], f: impl Fn(&T) -> R + Sync + Send) -> Vec<R>
where
    T: Sync,
    R: Send,
{
    map_dispatch_with_threshold(items, PARALLEL_LEN_THRESHOLD, f)
}

/// Zip-map `f` over two equal-length slices, dispatching to rayon only when
/// `a.len() >= `[`PARALLEL_LEN_THRESHOLD`].
pub(crate) fn zip_map_dispatch<A, B, R>(
    a: &[A],
    b: &[B],
    f: impl Fn(&A, &B) -> R + Sync + Send,
) -> Vec<R>
where
    A: Sync,
    B: Sync,
    R: Send,
{
    zip_map_dispatch_with_threshold(a, b, PARALLEL_LEN_THRESHOLD, f)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn map_dispatch_sequential_matches_reference() {
        let items: Vec<i64> = (0..64).collect();
        let expected: Vec<i64> = items.iter().map(|&x| x * x).collect();
        let got = map_dispatch_with_threshold(&items, usize::MAX, |&x| x * x);
        assert_eq!(got, expected);
    }

    #[test]
    fn map_dispatch_parallel_matches_reference() {
        let items: Vec<i64> = (0..64).collect();
        let expected: Vec<i64> = items.iter().map(|&x| x * x).collect();
        let got = map_dispatch_with_threshold(&items, 0, |&x| x * x);
        assert_eq!(got, expected);
    }

    #[test]
    fn map_dispatch_default_threshold_matches_reference() {
        let items: Vec<i64> = (0..1000).collect();
        let expected: Vec<i64> = items.iter().map(|&x| x + 1).collect();
        let got = map_dispatch(&items, |&x| x + 1);
        assert_eq!(got, expected);
    }

    #[test]
    fn zip_map_dispatch_sequential_matches_reference() {
        let a: Vec<f64> = (0..64).map(|i| i as f64).collect();
        let b: Vec<f64> = (0..64).map(|i| i as f64 * 2.0).collect();
        let expected: Vec<f64> = a.iter().zip(b.iter()).map(|(&x, &y)| x + y).collect();
        let got = zip_map_dispatch_with_threshold(&a, &b, usize::MAX, |&x, &y| x + y);
        assert_eq!(got, expected);
    }

    #[test]
    fn zip_map_dispatch_parallel_matches_reference() {
        let a: Vec<f64> = (0..64).map(|i| i as f64).collect();
        let b: Vec<f64> = (0..64).map(|i| i as f64 * 2.0).collect();
        let expected: Vec<f64> = a.iter().zip(b.iter()).map(|(&x, &y)| x + y).collect();
        let got = zip_map_dispatch_with_threshold(&a, &b, 0, |&x, &y| x + y);
        assert_eq!(got, expected);
    }

    #[test]
    fn map_dispatch_empty_slice() {
        let items: Vec<i64> = vec![];
        let got = map_dispatch(&items, |&x| x);
        assert!(got.is_empty());
    }
}
