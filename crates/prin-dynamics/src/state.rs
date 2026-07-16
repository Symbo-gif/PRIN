//! Oscillator state as a struct-of-arrays: phase, amplitude, natural frequency.
//!
//! Provides phase wrapping to `[0, 2π)`, atan2-safe phase differences, NaN/Inf
//! guards (behind the `strict-checks` feature), derivative clamping (±1e4),
//! amplitude clamping `[1e-6, 10]`, and the sort-based k-NN phase index
//! (`O(N log N)`, rayon parallel sort).
//!
//! Implementation lands in Phase 1 (see `DOCS/PRIN_Project_Plan.md`).
