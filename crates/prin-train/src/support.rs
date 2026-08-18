//! Shared tensor-construction and numerical-guard helpers for `prin-train`
//! modules ([`crate::bands`], [`crate::layers`]).
//!
//! Random parameter initialization is threaded through the project's
//! deterministic [`Seed`] (Coding Standards §1.3) rather than a
//! backend-local, unseeded RNG, so `Config::init` runs are reproducible.

use burn::tensor::{backend::Backend, Tensor, TensorData};
use prin_dynamics::Seed;

use crate::error::TrainError;

/// Draw a tensor of shape `shape` from `seed`, uniform on `[lo, hi]`.
///
/// When `lo == hi` (e.g. a zero-scale coupling init), every element is set to
/// that constant without drawing from `seed`.
pub(crate) fn seeded_uniform<B: Backend, const D: usize>(
    shape: [usize; D],
    lo: f64,
    hi: f64,
    device: &B::Device,
    seed: &mut Seed,
) -> Tensor<B, D> {
    let n: usize = shape.iter().product();
    let data: Vec<f64> = if (hi - lo).abs() < f64::EPSILON {
        vec![lo; n]
    } else {
        (0..n)
            .map(|_| seed.next_f64_range(lo, hi).unwrap_or(lo))
            .collect()
    };
    Tensor::from_data(TensorData::new(data, shape.to_vec()), device)
}

/// Xavier/Glorot-uniform bound for a `(fan_in, fan_out)` weight: the standard
/// formula (PyTorch `nn.init.xavier_uniform_`) with an explicit gain.
pub(crate) fn xavier_bound(fan_in: usize, fan_out: usize, gain: f64) -> f64 {
    gain * (6.0 / (fan_in + fan_out) as f64).sqrt()
}

/// Wrap `z` into `[0, modulus)` using floored (non-negative) modulo — Python
/// `%` semantics.
///
/// Burn's [`Tensor::remainder_scalar`] returns a *signed* remainder (Rust/C
/// `%` semantics: result has the same sign as the dividend, magnitude less
/// than the modulus), which differs from Python's always-non-negative `%`
/// for a negative dividend (e.g. `-0.3 % TAU` is `-0.3` under signed
/// remainder but `TAU - 0.3` under Python/floored modulo). [`crate::layers`]
/// only ever wraps sums of non-negative frequencies so the distinction does
/// not arise there; [`crate::activations::phase_activation`] wraps a
/// `dSiLU` output that can be slightly negative, so it uses this helper
/// instead. The standard `((n % m) + m) % m` trick folds a signed remainder
/// (magnitude already `< modulus`) back into `[0, modulus)`.
pub(crate) fn wrap_floor<B: Backend, const D: usize>(
    z: Tensor<B, D>,
    modulus: f64,
) -> Tensor<B, D> {
    (z.remainder_scalar(modulus) + modulus).remainder_scalar(modulus)
}

/// Validate that `dims` matches `expected`, or return a typed
/// [`TrainError::ShapeMismatch`].
pub(crate) fn check_dims<const D: usize>(
    name: &'static str,
    dims: [usize; D],
    expected: [usize; D],
) -> Result<(), TrainError> {
    if dims != expected {
        return Err(TrainError::ShapeMismatch {
            name,
            expected: expected.to_vec(),
            got: dims.to_vec(),
        });
    }
    Ok(())
}

/// Validate a timestep is finite and strictly positive.
pub(crate) fn validate_dt(dt: f64) -> Result<(), TrainError> {
    if !dt.is_finite() || dt <= 0.0 {
        return Err(TrainError::InvalidTimestep { value: dt });
    }
    Ok(())
}

/// Validate a scalar hyperparameter is finite.
pub(crate) fn validate_finite(name: &'static str, value: f64) -> Result<(), TrainError> {
    if !value.is_finite() {
        return Err(TrainError::NonFiniteParameter { name, value });
    }
    Ok(())
}

/// Under `strict-checks`, verify every element of `tensor` is finite and
/// return a typed [`TrainError::NonFiniteState`] otherwise.
///
/// Without `strict-checks`, this is a no-op that never syncs the tensor to
/// the host, matching the `prin-dynamics` guard convention
/// (`crate::state`, `#[cfg(feature = "strict-checks")]`).
#[cfg(feature = "strict-checks")]
pub(crate) fn check_finite<B: Backend, const D: usize>(
    name: &'static str,
    tensor: &Tensor<B, D>,
) -> Result<(), TrainError> {
    use burn::tensor::ElementConversion;

    // Convert through the backend's own float element type: `to_vec` requires
    // an exact dtype match (no implicit numeric cast), so a hardcoded `f32`
    // target would spuriously fail on an `f64` backend (and vice versa).
    let data = tensor
        .to_data()
        .to_vec::<B::FloatElem>()
        .map_err(|_| TrainError::NonFiniteState { name })?;
    if data.iter().all(|v| v.elem::<f64>().is_finite()) {
        Ok(())
    } else {
        Err(TrainError::NonFiniteState { name })
    }
}

#[cfg(not(feature = "strict-checks"))]
pub(crate) fn check_finite<B: Backend, const D: usize>(
    _name: &'static str,
    _tensor: &Tensor<B, D>,
) -> Result<(), TrainError> {
    Ok(())
}
