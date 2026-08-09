//! Simple element-wise CPU kernels used by the PyO3/DLPack bridge spike.
//!
//! These are intentionally tiny, deterministic, and free of `unsafe` --- they
//! demonstrate that the Rust core can own the numerics while the Python layer
//! only marshals tensors through the DLPack exchange.

/// Negate every element of an `f32` slice.
///
/// This is the representative Rust kernel for the WP-003 DLPack bridge spike:
/// a trivial, fully-typed operation whose result is returned as a new owned
/// allocation.
pub fn negate_f32(input: &[f32]) -> Vec<f32> {
    input.iter().map(|x| -x).collect()
}

/// Negate every element of an `f64` slice.
pub fn negate_f64(input: &[f64]) -> Vec<f64> {
    input.iter().map(|x| -x).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn negate_f32_preserves_sign_flips() {
        let input = [1.0_f32, -2.0, 0.0, 3.5];
        assert_eq!(negate_f32(&input), [-1.0_f32, 2.0, -0.0, -3.5]);
    }

    #[test]
    fn negate_f64_preserves_sign_flips() {
        let input = [1.0_f64, -2.0, 0.0, 3.5];
        assert_eq!(negate_f64(&input), [-1.0_f64, 2.0, -0.0, -3.5]);
    }

    #[test]
    fn negate_f32_empty_is_empty() {
        let input: [f32; 0] = [];
        assert!(negate_f32(&input).is_empty());
    }
}
