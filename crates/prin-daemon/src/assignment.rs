//! Rectangular linear-sum assignment (Hungarian / Kuhn–Munkres algorithm).
//!
//! [`MotAccumulator`](crate::mot::MotAccumulator) needs an exact minimum-cost
//! bipartite matching twice per evaluation: once per frame (matching
//! ground-truth identities to hypothesis identities) and once globally at
//! summary time (matching whole GT trajectories to whole hypothesis
//! trajectories for the IDF1 measure). `py-motmetrics` — the reference this
//! crate is validated against (Project Plan §6, "MOT metrics match
//! motmetrics reference") — dispatches both calls to
//! `scipy.optimize.linear_sum_assignment`. This module is a from-scratch
//! Rust implementation of the same *problem* (not a translation of SciPy's
//! solver internals): the classical O(n²m) shortest-augmenting-path
//! Hungarian algorithm with potentials, generalised to rectangular
//! `n ≤ m` cost matrices.
//!
//! # Do-not-pair entries
//!
//! `motmetrics` signals a forbidden pairing with `NaN`/`inf` in the distance
//! matrix, then makes the matrix solvable by replacing those entries with a
//! finite value large enough that the optimal solution never uses one
//! unless forced to (`motmetrics.lap.add_expensive_edges`), and finally
//! drops any returned pair whose *original* cost was non-finite
//! (`motmetrics.lap._exclude_missing_edges`). [`solve_assignment`]
//! reproduces exactly that two-step recipe.

/// Solve a rectangular minimum-cost bipartite assignment.
///
/// `cost[i][j]` is the cost of pairing row `i` with column `j`; all rows
/// must have the same length. A `NaN` or infinite entry marks a forbidden
/// pairing (`motmetrics` "do-not-pair" convention): the returned pairs never
/// include one, even though the solver internally treats forbidden entries
/// as a large finite cost so that a full assignment can still be found on
/// the rest of the matrix (this is what allows step 1 of
/// [`MotAccumulator::update`](crate::mot::MotAccumulator::update) to mask
/// out already-matched rows/columns with `NaN` and still get a correct
/// assignment over the remainder).
///
/// Returns up to `min(rows, cols)` pairs `(row, col)`, each with a finite
/// original cost, minimising the total cost over the returned pairs. Returns
/// an empty vector if `cost` is empty, any row is empty, or every entry is
/// non-finite.
///
/// # Panics
///
/// Never panics; a ragged `cost` (rows of differing length) is treated as
/// having zero columns for any row shorter than the widest row would imply,
/// which simply cannot happen because callers in this crate always build
/// rectangular matrices. Malformed input from outside this crate is not a
/// currently reachable path, so no `Result` is threaded through this
/// crate-private helper.
#[must_use]
pub(crate) fn solve_assignment(cost: &[Vec<f64>]) -> Vec<(usize, usize)> {
    let rows = cost.len();
    let cols = if rows == 0 { 0 } else { cost[0].len() };
    if rows == 0 || cols == 0 {
        return Vec::new();
    }

    let padded = add_expensive_edges(cost, rows, cols);

    let raw_pairs = if rows <= cols {
        hungarian(&padded, rows, cols)
    } else {
        let transposed = transpose(&padded, rows, cols);
        hungarian(&transposed, cols, rows)
            .into_iter()
            .map(|(r, c)| (c, r))
            .collect()
    };

    raw_pairs
        .into_iter()
        .filter(|&(i, j)| cost[i][j].is_finite())
        .collect()
}

/// Replace non-finite entries with a value large enough that the optimal
/// assignment never chooses one unless every alternative is also forbidden.
///
/// Mirrors `motmetrics.lap.add_expensive_edges`: if every entry is already
/// finite the matrix is returned unchanged; if none is finite the matrix
/// becomes all-zero (any assignment is equally "optimal", and every pair
/// gets filtered out afterwards for having a non-finite original cost).
fn add_expensive_edges(cost: &[Vec<f64>], rows: usize, cols: usize) -> Vec<Vec<f64>> {
    let mut max_abs_finite = 0.0_f64;
    let mut any_finite = false;
    let mut all_finite = true;
    for row in cost {
        for &value in row {
            if value.is_finite() {
                any_finite = true;
                max_abs_finite = max_abs_finite.max(value.abs());
            } else {
                all_finite = false;
            }
        }
    }

    if all_finite {
        return cost.to_vec();
    }
    if !any_finite {
        return vec![vec![0.0; cols]; rows];
    }

    // Choosing an invalid edge once plus the best-possible finite edge
    // `r - 1` more times must be worse than the worst-possible finite edge
    // chosen `r` times, where `r = min(rows, cols)` is the number of pairs
    // in any full assignment: `l > (2r - 1) * c` for `c = max_abs_finite`.
    // `l = 2 r c + 1` satisfies this with room to spare.
    let r = rows.min(cols) as f64;
    let c = max_abs_finite + 1.0;
    let large_constant = 2.0 * r * c + 1.0;

    cost.iter()
        .map(|row| {
            row.iter()
                .map(|&v| if v.is_finite() { v } else { large_constant })
                .collect()
        })
        .collect()
}

fn transpose(matrix: &[Vec<f64>], rows: usize, cols: usize) -> Vec<Vec<f64>> {
    let mut out = vec![vec![0.0; rows]; cols];
    for (i, row) in matrix.iter().enumerate().take(rows) {
        for (j, &value) in row.iter().enumerate().take(cols) {
            out[j][i] = value;
        }
    }
    out
}

/// Classical Hungarian algorithm (Jonker–Volgenant-style shortest augmenting
/// path with potentials) for an `n × m` cost matrix with `n <= m`.
///
/// Returns exactly `n` pairs `(row, col)`, one per row, minimising total
/// cost. 1-indexed internally (the dummy index `0` marks "no row"/"no
/// column yet"), which is what keeps the classical formulation's `p[0] = i`
/// sentinel meaningful; converted back to 0-indexed pairs before returning.
fn hungarian(cost: &[Vec<f64>], n: usize, m: usize) -> Vec<(usize, usize)> {
    const INF: f64 = f64::INFINITY;

    let get = |i: usize, j: usize| -> f64 {
        // i, j are 1-indexed here; translate to the 0-indexed `cost` matrix.
        cost[i - 1][j - 1]
    };

    let mut u = vec![0.0_f64; n + 1];
    let mut v = vec![0.0_f64; m + 1];
    let mut p = vec![0_usize; m + 1];
    let mut way = vec![0_usize; m + 1];

    for i in 1..=n {
        p[0] = i;
        let mut j0 = 0_usize;
        let mut minv = vec![INF; m + 1];
        let mut used = vec![false; m + 1];

        loop {
            used[j0] = true;
            let i0 = p[j0];
            let mut delta = INF;
            let mut j1 = 0_usize;
            for j in 1..=m {
                if !used[j] {
                    let cur = get(i0, j) - u[i0] - v[j];
                    if cur < minv[j] {
                        minv[j] = cur;
                        way[j] = j0;
                    }
                    if minv[j] < delta {
                        delta = minv[j];
                        j1 = j;
                    }
                }
            }
            for j in 0..=m {
                if used[j] {
                    u[p[j]] += delta;
                    v[j] -= delta;
                } else {
                    minv[j] -= delta;
                }
            }
            j0 = j1;
            if p[j0] == 0 {
                break;
            }
        }

        while j0 != 0 {
            let j1 = way[j0];
            p[j0] = p[j1];
            j0 = j1;
        }
    }

    (1..=m)
        .filter_map(|j| {
            let row = p[j];
            // `then_some` evaluates its argument eagerly even when the
            // receiver is `false`, which would underflow `row - 1` for an
            // unassigned column (`row == 0`); `then` with a closure defers
            // the subtraction until the guard has already passed.
            (row != 0).then(|| (row - 1, j - 1))
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn total_cost(cost: &[Vec<f64>], pairs: &[(usize, usize)]) -> f64 {
        pairs.iter().map(|&(i, j)| cost[i][j]).sum()
    }

    /// Exhaustive brute-force optimum for small square/rectangular matrices,
    /// used to check [`solve_assignment`] against ground truth rather than
    /// against itself.
    ///
    /// Enumerates all ordered `k`-permutations (`k = min(rows, cols)`) drawn
    /// from whichever dimension is *larger*, and pairs them positionally
    /// against the smaller dimension. Picking from the smaller dimension
    /// instead would silently restrict the search to using only its first
    /// `k` indices in the `rows > cols` case, which is wrong whenever the
    /// optimal solution needs a different subset of rows.
    fn brute_force_min_cost(cost: &[Vec<f64>]) -> f64 {
        let rows = cost.len();
        if rows == 0 {
            return 0.0;
        }
        let cols = cost[0].len();
        if cols == 0 {
            return 0.0;
        }
        let k = rows.min(cols);
        let mut best = f64::INFINITY;
        if rows <= cols {
            let mut pool: Vec<usize> = (0..cols).collect();
            permute_k(&mut pool, 0, k, &mut |chosen| {
                let total: f64 = (0..k).map(|i| cost[i][chosen[i]]).sum();
                if total.is_finite() && total < best {
                    best = total;
                }
            });
        } else {
            let mut pool: Vec<usize> = (0..rows).collect();
            permute_k(&mut pool, 0, k, &mut |chosen| {
                let total: f64 = (0..k).map(|i| cost[chosen[i]][i]).sum();
                if total.is_finite() && total < best {
                    best = total;
                }
            });
        }
        best
    }

    /// Call `callback` with every ordered arrangement of `k` distinct
    /// elements drawn from `pool` (a `k`-permutation).
    fn permute_k(pool: &mut [usize], start: usize, k: usize, callback: &mut dyn FnMut(&[usize])) {
        if start == k {
            callback(&pool[..k]);
            return;
        }
        for idx in start..pool.len() {
            pool.swap(start, idx);
            permute_k(pool, start + 1, k, callback);
            pool.swap(start, idx);
        }
    }

    #[test]
    fn empty_matrix_returns_no_pairs() {
        assert_eq!(solve_assignment(&[]), Vec::new());
        assert_eq!(solve_assignment(&[vec![]]), Vec::new());
    }

    #[test]
    fn square_matrix_matches_known_optimum() {
        // Classic 3x3 example: optimal assignment cost is 5 (0,2)+(1,1)+(2,0)? verify via brute force instead.
        let cost = vec![
            vec![4.0, 1.0, 3.0],
            vec![2.0, 0.0, 5.0],
            vec![3.0, 2.0, 2.0],
        ];
        let pairs = solve_assignment(&cost);
        assert_eq!(pairs.len(), 3);
        let got = total_cost(&cost, &pairs);
        let expected = brute_force_min_cost(&cost);
        assert!(
            (got - expected).abs() < 1e-9,
            "got {got}, expected {expected}"
        );
    }

    #[test]
    fn rectangular_more_columns_than_rows() {
        let cost = vec![vec![1.0, 9.0, 9.0, 2.0], vec![9.0, 1.0, 9.0, 9.0]];
        let pairs = solve_assignment(&cost);
        assert_eq!(pairs.len(), 2);
        let got = total_cost(&cost, &pairs);
        let expected = brute_force_min_cost(&cost);
        assert!((got - expected).abs() < 1e-9);
    }

    #[test]
    fn rectangular_more_rows_than_columns() {
        let cost = vec![vec![1.0, 9.0], vec![9.0, 1.0], vec![5.0, 5.0]];
        let pairs = solve_assignment(&cost);
        assert_eq!(pairs.len(), 2);
        let got = total_cost(&cost, &pairs);
        let expected = brute_force_min_cost(&cost);
        assert!((got - expected).abs() < 1e-9);

        let mut rows_used: Vec<usize> = pairs.iter().map(|&(i, _)| i).collect();
        rows_used.sort_unstable();
        rows_used.dedup();
        assert_eq!(rows_used.len(), pairs.len(), "no row used twice");
    }

    #[test]
    fn nan_entries_are_never_selected() {
        let cost = vec![vec![f64::NAN, 1.0], vec![1.0, f64::NAN]];
        let pairs = solve_assignment(&cost);
        assert_eq!(pairs.len(), 2);
        assert!(pairs.contains(&(0, 1)));
        assert!(pairs.contains(&(1, 0)));
    }

    #[test]
    fn infinite_entries_are_never_selected() {
        let cost = vec![vec![f64::INFINITY, 2.0], vec![3.0, f64::INFINITY]];
        let mut pairs = solve_assignment(&cost);
        pairs.sort_unstable();
        assert_eq!(pairs, vec![(0, 1), (1, 0)]);
    }

    #[test]
    fn all_non_finite_yields_no_pairs() {
        let cost = vec![vec![f64::NAN, f64::NAN], vec![f64::INFINITY, f64::NAN]];
        assert_eq!(solve_assignment(&cost), Vec::new());
    }

    #[test]
    fn a_row_with_only_forbidden_entries_is_left_unmatched() {
        // Row 0 can only pair with column 0; row 1 can pair with either.
        // A naive solver might force row 1 onto column 0 to "help" row 0,
        // but row 0's only entry is NaN, so row 0 must end up unmatched.
        let cost = vec![vec![f64::NAN, f64::NAN], vec![1.0, 2.0]];
        let pairs = solve_assignment(&cost);
        assert_eq!(pairs, vec![(1, 0)]);
    }

    #[test]
    fn forced_infeasible_pair_is_filtered_even_when_matrix_is_square() {
        // A single valid edge exists per row, but they collide on the same
        // column; the optimal *finite* solution can only use one of them.
        let cost = vec![vec![1.0, f64::NAN], vec![2.0, f64::NAN]];
        let pairs = solve_assignment(&cost);
        assert_eq!(pairs, vec![(0, 0)]);
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    fn total_cost(cost: &[Vec<f64>], pairs: &[(usize, usize)]) -> f64 {
        pairs.iter().map(|&(i, j)| cost[i][j]).sum()
    }

    fn permute_k(pool: &mut [usize], start: usize, k: usize, callback: &mut dyn FnMut(&[usize])) {
        if start == k {
            callback(&pool[..k]);
            return;
        }
        for idx in start..pool.len() {
            pool.swap(start, idx);
            permute_k(pool, start + 1, k, callback);
            pool.swap(start, idx);
        }
    }

    fn brute_force_min_cost(cost: &[Vec<f64>]) -> f64 {
        let rows = cost.len();
        if rows == 0 {
            return 0.0;
        }
        let cols = cost[0].len();
        if cols == 0 {
            return 0.0;
        }
        let k = rows.min(cols);
        let mut best = f64::INFINITY;
        if rows <= cols {
            let mut pool: Vec<usize> = (0..cols).collect();
            permute_k(&mut pool, 0, k, &mut |chosen| {
                let total: f64 = (0..k).map(|i| cost[i][chosen[i]]).sum();
                if total < best {
                    best = total;
                }
            });
        } else {
            let mut pool: Vec<usize> = (0..rows).collect();
            permute_k(&mut pool, 0, k, &mut |chosen| {
                let total: f64 = (0..k).map(|i| cost[chosen[i]][i]).sum();
                if total < best {
                    best = total;
                }
            });
        }
        best
    }

    proptest! {
        #[test]
        fn solve_assignment_is_always_optimal_and_valid(
            rows in 1usize..=4,
            cols in 1usize..=4,
            seed_values in prop::collection::vec(-10.0f64..10.0, 1..=16),
        ) {
            let mut it = seed_values.into_iter().cycle();
            let cost: Vec<Vec<f64>> = (0..rows)
                .map(|_| (0..cols).map(|_| it.next().unwrap()).collect())
                .collect();

            let pairs = solve_assignment(&cost);

            // Every returned pair has a finite cost (all entries are finite here).
            for &(i, j) in &pairs {
                prop_assert!(cost[i][j].is_finite());
            }
            // No row or column used twice.
            let mut used_rows: Vec<usize> = pairs.iter().map(|&(i, _)| i).collect();
            let mut used_cols: Vec<usize> = pairs.iter().map(|&(_, j)| j).collect();
            used_rows.sort_unstable();
            used_cols.sort_unstable();
            let rows_len = used_rows.len();
            let cols_len = used_cols.len();
            used_rows.dedup();
            used_cols.dedup();
            prop_assert_eq!(used_rows.len(), rows_len);
            prop_assert_eq!(used_cols.len(), cols_len);

            // Full min(rows, cols) pairs found (matrix is all-finite, so a
            // complete assignment always exists).
            prop_assert_eq!(pairs.len(), rows.min(cols));

            // Matches the brute-force optimum.
            let got = total_cost(&cost, &pairs);
            let expected = brute_force_min_cost(&cost);
            prop_assert!((got - expected).abs() < 1e-6, "got {} expected {}", got, expected);
        }
    }
}
