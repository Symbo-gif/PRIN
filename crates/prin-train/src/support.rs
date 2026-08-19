//! Shared tensor-construction and numerical-guard helpers for `prin-train`
//! modules ([`crate::bands`], [`crate::layers`]).
//!
//! Random parameter initialization is threaded through the project's
//! deterministic [`Seed`] (Coding Standards §1.3) rather than a
//! backend-local, unseeded RNG, so `Config::init` runs are reproducible.

use burn::module::Param;
use burn::tensor::{backend::Backend, ElementConversion, Tensor, TensorData};
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

/// Draw a tensor of shape `shape` from `seed`, standard normal (`N(0, 1)`),
/// via the Box–Muller transform.
///
/// Used by [`crate::slot_attention::SlotAttentionModule::forward`]'s
/// per-call slot-initialization noise (`torch.randn_like` in the PRINet 3.0
/// reference) — a genuinely per-forward-call stochastic entry point (not a
/// one-time `Config::init` draw), so it takes `&mut Seed` directly rather
/// than going through [`seeded_uniform`]'s scale-only-matters precedent.
pub(crate) fn seeded_standard_normal<B: Backend, const D: usize>(
    shape: [usize; D],
    device: &B::Device,
    seed: &mut Seed,
) -> Tensor<B, D> {
    let n: usize = shape.iter().product();
    let mut data = Vec::with_capacity(n);
    while data.len() < n {
        let u1 = seed.next_f64().max(f64::MIN_POSITIVE);
        let u2 = seed.next_f64();
        let r = (-2.0 * u1.ln()).sqrt();
        let theta = std::f64::consts::TAU * u2;
        data.push(r * theta.cos());
        if data.len() < n {
            data.push(r * theta.sin());
        }
    }
    Tensor::from_data(TensorData::new(data, shape.to_vec()), device)
}

/// Xavier/Glorot-uniform bound for a `(fan_in, fan_out)` weight: the standard
/// formula (PyTorch `nn.init.xavier_uniform_`) with an explicit gain.
pub(crate) fn xavier_bound(fan_in: usize, fan_out: usize, gain: f64) -> f64 {
    gain * (6.0 / (fan_in + fan_out) as f64).sqrt()
}

/// Build a [`burn::nn::Linear`] with Xavier-uniform (gain `1.0`) weights and
/// bias, both drawn from `seed`.
///
/// Deliberately does **not** go through [`burn::nn::LinearConfig::init`],
/// which draws from Burn's backend-global RNG (`Backend::seed`) rather than
/// this project's [`Seed`] — that global state is a `static Mutex` shared by
/// every `NdArray`-backend tensor in the process (see `burn_ndarray::backend`),
/// so two `Config::init` calls racing across parallel test threads can
/// observe each other's draws, breaking reproducibility (discovered while
/// gradchecking [`crate::attention::OscillatoryAttention`]). Constructing
/// [`burn::nn::Linear`] directly from its public `weight`/`bias` fields
/// keeps every draw sourced from the explicit, thread-local `Seed` the
/// caller owns, matching Coding Standards §1.3 ("no hidden globals").
pub(crate) fn seeded_linear<B: Backend>(
    d_input: usize,
    d_output: usize,
    bias: bool,
    device: &B::Device,
    seed: &mut Seed,
) -> burn::nn::Linear<B> {
    let bound = xavier_bound(d_input, d_output, 1.0);
    let weight = seeded_uniform::<B, 2>([d_input, d_output], -bound, bound, device, seed);
    let bias = if bias {
        Some(Param::initialized(
            Default::default(),
            seeded_uniform::<B, 1>([d_output], -bound, bound, device, seed).require_grad(),
        ))
    } else {
        None
    };
    burn::nn::Linear {
        weight: Param::initialized(Default::default(), weight.require_grad()),
        bias,
    }
}

/// Build a [`burn::nn::gru::Gru`] (single-layer GRU) with Xavier-uniform
/// (gain `1.0`) weights and biases, all drawn from `seed`.
///
/// Deliberately does **not** go through [`burn::nn::gru::GruConfig::init`] —
/// same reason as [`seeded_linear`] (`Backend::seed` is a shared global).
/// Constructs each gate's [`burn::nn::GateController`] directly from its
/// public `input_transform`/`hidden_transform` [`burn::nn::Linear`] fields.
pub(crate) fn seeded_gru<B: Backend>(
    d_input: usize,
    d_hidden: usize,
    device: &B::Device,
    seed: &mut Seed,
) -> burn::nn::gru::Gru<B> {
    fn gate<B: Backend>(
        d_input: usize,
        d_hidden: usize,
        device: &B::Device,
        seed: &mut Seed,
    ) -> burn::nn::GateController<B> {
        burn::nn::GateController {
            input_transform: seeded_linear::<B>(d_input, d_hidden, true, device, seed),
            hidden_transform: seeded_linear::<B>(d_hidden, d_hidden, true, device, seed),
        }
    }
    burn::nn::gru::Gru {
        update_gate: gate::<B>(d_input, d_hidden, device, seed),
        reset_gate: gate::<B>(d_input, d_hidden, device, seed),
        new_gate: gate::<B>(d_input, d_hidden, device, seed),
        d_hidden,
    }
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

/// Apply one heavy-ball-momentum SGD update, PyTorch `torch.optim.SGD`
/// semantics: `d_p = grad (+ weight_decay·param)`; with momentum, `buf =
/// buf·momentum + d_p·(1 − dampening)` (or `d_p` verbatim on the first
/// update) and `d_p = buf`; finally `param − lr·d_p`.
///
/// Shared by [`crate::sync_gd::SyncGd`] and [`crate::scalr::Scalr`], whose
/// PRINet 3.0 references (`SynchronizedGradientDescent.step`,
/// `SCALROptimizer.step`) apply this identical core, differing only in how
/// `lr` is derived from oscillator feedback. SCALR's reference has no
/// `dampening` parameter (its momentum buffer update is `buf·momentum +
/// d_p`, i.e. `alpha=1.0`); callers without dampening pass `0.0`.
pub(crate) fn sgd_update<B: Backend, const D: usize>(
    param: Tensor<B, D>,
    grad: Tensor<B, D>,
    weight_decay: f64,
    momentum: f64,
    dampening: f64,
    momentum_buffer: &mut Option<Tensor<B, D>>,
    lr: f64,
) -> Tensor<B, D> {
    let mut d_p = grad;
    if weight_decay != 0.0 {
        d_p = d_p + param.clone().mul_scalar(weight_decay);
    }
    if momentum != 0.0 {
        let buf = match momentum_buffer.take() {
            None => d_p.clone(),
            Some(prev) => prev.mul_scalar(momentum) + d_p.clone().mul_scalar(1.0 - dampening),
        };
        *momentum_buffer = Some(buf.clone());
        d_p = buf;
    }
    param - d_p.mul_scalar(lr)
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

/// Round `x` to the nearest integer using Python's `round()` semantics
/// (round-half-to-even / "banker's rounding"), not Rust's `f64::round()`
/// (round-half-away-from-zero).
///
/// Used by [`crate::allocation`], whose PRINet 3.0 reference (`round(...)`
/// on oscillator-count formulas) relies on Python's built-in rounding.
pub(crate) fn python_round(x: f64) -> i64 {
    let floor = x.floor();
    let diff = x - floor;
    let floor_i = floor as i64;
    match diff.partial_cmp(&0.5) {
        Some(std::cmp::Ordering::Less) => floor_i,
        Some(std::cmp::Ordering::Greater) => floor_i + 1,
        _ => {
            if floor_i % 2 == 0 {
                floor_i
            } else {
                floor_i + 1
            }
        }
    }
}

/// Read a float tensor's elements back to the host as `f64`, backend-generic
/// (works for both `f32` and `f64` backends via [`ElementConversion`]).
///
/// Used by host-side, non-differentiable post-processing (greedy matching,
/// scalar hyperparameter derivation) where Burn has no tensor-native
/// equivalent of the source operation (PRINet 3.0's `.item()`/Python `for`
/// loop over `argsort` results).
pub(crate) fn to_f64_vec<B: Backend, const D: usize>(tensor: Tensor<B, D>) -> Vec<f64> {
    tensor
        .to_data()
        .to_vec::<B::FloatElem>()
        .expect("tensor dtype matches its own backend's FloatElem")
        .into_iter()
        .map(|v| v.elem::<f64>())
        .collect()
}

/// Read an integer tensor's elements back to the host as `i64`,
/// backend-generic. See [`to_f64_vec`].
pub(crate) fn to_i64_vec<B: Backend, const D: usize>(
    tensor: Tensor<B, D, burn::tensor::Int>,
) -> Vec<i64> {
    tensor
        .to_data()
        .to_vec::<B::IntElem>()
        .expect("tensor dtype matches its own backend's IntElem")
        .into_iter()
        .map(|v| v.elem::<i64>())
        .collect()
}

/// Phase-coherence similarity: `sim[a, b] = (Σ_k cos(phase_a[a,k] −
/// phase_b[b,k])) / (√n_osc + ε)²`.
///
/// Shared by [`crate::phase_tracker::PhaseTracker::phase_similarity`] and
/// [`crate::ablation::PhaseTrackerStatic::phase_similarity`], both of whose
/// PRINet 3.0 references (`PhaseTracker.phase_similarity`,
/// `PhaseTrackerStatic.phase_similarity`) apply the identical
/// `torch.complex64`-based formula — kept as one implementation here per
/// Coding Standards §1.1 ("one algorithm, one implementation"). See
/// [`crate::phase_tracker`]'s module docs for the real-valued reformulation
/// this computes directly (Burn has no complex-tensor autodiff).
///
/// Does not validate shapes; callers are expected to check
/// `phase_a`/`phase_b` share an oscillator width first (each exposes its own
/// public `phase_similarity` with a crate-specific typed-error contract).
pub(crate) fn phase_coherence_similarity<B: Backend>(
    phase_a: Tensor<B, 2>,
    phase_b: Tensor<B, 2>,
    n_osc: usize,
    eps: f64,
) -> Tensor<B, 2> {
    let a = phase_a.unsqueeze_dim::<3>(1); // [N_a, 1, n]
    let b = phase_b.unsqueeze_dim::<3>(0); // [1, N_b, n]
    let cos_diff_sum = (a - b).cos().sum_dim(2).squeeze::<2>(2); // [N_a, N_b]
    let denom = ((n_osc as f64).sqrt() + eps).powi(2);
    cos_diff_sum.div_scalar(denom)
}

/// Greedy bipartite matching by descending similarity, matching PRINet 3.0's
/// tracker `forward`/`track_sequence` assignment loop exactly: sort rows by
/// their best (max) similarity, descending, then for each row in that order
/// assign it to its best still-unused column if that similarity exceeds
/// `threshold`.
///
/// Returns a `Vec<i64>` of length `sim.dims()[0]` (rows): the matched column
/// index for each row, or `-1` if unmatched. This is host-side index
/// bookkeeping (identical in kind to PRINet 3.0's `.item()`-per-element
/// Python loop), not a differentiable computation — no gradient flows
/// through the returned indices.
pub(crate) fn greedy_match_by_similarity<B: Backend>(
    sim: &Tensor<B, 2>,
    threshold: f64,
) -> Vec<i64> {
    let [n_rows, n_cols] = sim.dims();
    if n_rows == 0 || n_cols == 0 {
        return vec![-1; n_rows];
    }

    let (max_sims, max_idxs) = sim.clone().max_dim_with_indices(1);
    let sims: Vec<f64> = to_f64_vec(max_sims.clone().squeeze::<1>(1));
    let idxs: Vec<i64> = to_i64_vec(max_idxs.squeeze::<1>(1));
    let order: Vec<i64> = to_i64_vec(max_sims.squeeze::<1>(1).argsort_descending(0));

    let mut matches = vec![-1i64; n_rows];
    let mut used = vec![false; n_cols];
    for &row in &order {
        let row = row as usize;
        let best_j = idxs[row] as usize;
        if best_j < n_cols && !used[best_j] && sims[row] > threshold {
            matches[row] = best_j as i64;
            used[best_j] = true;
        }
    }
    matches
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn python_round_matches_python_semantics() {
        // Non-half cases: ordinary rounding.
        assert_eq!(python_round(2.4), 2);
        assert_eq!(python_round(2.6), 3);
        assert_eq!(python_round(-2.4), -2);
        // Exact-half cases: round to even (Python's `round(2.5) == 2`,
        // `round(3.5) == 4`), not away-from-zero (`f64::round` semantics).
        assert_eq!(python_round(2.5), 2);
        assert_eq!(python_round(3.5), 4);
        assert_eq!(python_round(0.5), 0);
        assert_eq!(python_round(1.5), 2);
    }
}
