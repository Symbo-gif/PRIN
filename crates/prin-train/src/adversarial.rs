//! FGSM/PGD adversarial attack orchestration for tracker robustness
//! evaluation (WP-031): a direct port of PRINet 3.0's `fgsm_attack`/
//! `pgd_attack`/`adversarial_evaluate`/`adversarial_comparison`
//! (`utils/adversarial_tools.py`).
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! Both attacks maximize the exact loss [`crate::trainer`] trains against:
//! the reference's `fgsm_attack`/`pgd_attack` build `cross_entropy(sim_block
//! / 0.1, arange(N))` inline (`adversarial_tools.py:56-59,121-123`), which
//! is *definitionally* [`crate::losses::hungarian_similarity_loss`] (compare
//! that function's `-(1/N) * sum_i log(exp(s[i,i]/T)/sum_j exp(s[i,j]/T))`,
//! `T=0.1` — the same cross-entropy-with-diagonal-target formula) — this
//! port calls it directly rather than duplicating the loss (Coding
//! Standards §1.1).
//!
//! **Backend-boundary design.** The reference threads perturbations through
//! PyTorch's autodiff graph directly (`dets_t_adv.grad`). Burn's
//! `Tensor::grad` returns a tensor on the *inner* (non-autodiff) backend
//! (`B::InnerBackend`), while the caller-supplied `dets_t`/the accumulated
//! perturbation live on the outer autodiff backend `B` — combining the two
//! requires either backend-conversion plumbing or, as this port does,
//! reading both to the host as `f64` (via `crate::support::to_f64_vec`,
//! the same "host-side non-differentiable bookkeeping" idiom already used by
//! `crate::support::greedy_match_by_similarity`) and reconstructing the
//! perturbed tensor from host data each step. Detection tensors are small
//! (`N` objects × `detection_dim` features), so this host round-trip is not
//! a performance concern; only the sign/clamp arithmetic — never the
//! gradient computation itself — happens off-device.
//!
//! **Sign convention.** Rust's `f64::signum()` returns `1.0` for exactly
//! `0.0` (Rust convention), whereas PyTorch's `torch.sign()` returns `0.0`
//! for exactly `0.0`; this port uses `torch_sign` to match the reference's
//! `.grad.sign()` semantics exactly, since an exact-zero gradient component
//! is possible (e.g. a fully-occluded feature).
//!
//! **`adversarial_evaluate`/`adversarial_comparison`.** The reference's
//! `adversarial_evaluate` is generic over any `model` duck-typing
//! `forward`/`track_sequence`; this port specializes to
//! [`crate::phase_tracker::PhaseTracker`]
//! ([`adversarial_evaluate_phase_tracker`]) and
//! [`crate::slot_attention::TemporalSlotAttentionMOT`]
//! ([`adversarial_evaluate_temporal_slot_attention_mot`]) rather than a
//! generic closure-of-closures abstraction, since the two trackers'
//! `forward` signatures genuinely differ (the latter threads a
//! [`prin_dynamics::Seed`] for its per-call slot-initialization noise, per
//! [`crate::slot_attention`]'s module docs) — the same "concrete per-tracker
//! functions, not a forced shared abstraction" precedent as
//! [`crate::trainer`]'s `train_phase_tracker`/
//! `train_temporal_slot_attention_mot`. [`adversarial_comparison`]
//! orchestrates both, matching the reference's side-by-side PT-vs-SA grid.

use burn::tensor::backend::AutodiffBackend;
use burn::tensor::{Tensor, TensorData};
use prin_dynamics::Seed;

use crate::dataset::SequenceData;
use crate::error::TrainError;
use crate::losses::hungarian_similarity_loss;
use crate::phase_tracker::PhaseTracker;
use crate::slot_attention::TemporalSlotAttentionMOT;
use crate::support::to_f64_vec;

/// PyTorch `torch.sign()` semantics: `0.0` maps to `0.0`, not `1.0` (unlike
/// Rust's [`f64::signum`]) — see module docs.
fn torch_sign(v: f64) -> f64 {
    if v > 0.0 {
        1.0
    } else if v < 0.0 {
        -1.0
    } else {
        0.0
    }
}

fn validate_epsilon(epsilon: f64) -> Result<(), TrainError> {
    if !epsilon.is_finite() || epsilon <= 0.0 {
        return Err(TrainError::InvalidPerturbationBudget {
            name: "epsilon",
            value: epsilon,
        });
    }
    Ok(())
}

/// Fast Gradient Sign Method (FGSM) attack on input detections: perturbs
/// `dets_t` by `epsilon * sign(grad)` to maximize the tracking loss produced
/// by `similarity_fn`.
///
/// `similarity_fn` receives the (leaf, `require_grad`-enabled) adversarial
/// `dets_t` and must return the differentiable similarity matrix a tracker's
/// `forward` would compute against a fixed `dets_t1` (captured by the
/// closure) — see module docs for why this replaces the reference's
/// `model(dets_t_adv, dets_t1)` call.
///
/// Direct port of `fgsm_attack` (`adversarial_tools.py:23-67`). Returns
/// `dets_t` unperturbed if the similarity matrix's matchable block is empty
/// or no gradient reaches `dets_t` (matching the reference's identical
/// early-return guards).
///
/// # Errors
///
/// Returns [`TrainError::InvalidPerturbationBudget`] if `epsilon` is
/// non-finite or `<= 0`.
pub fn fgsm_attack<B: AutodiffBackend>(
    dets_t: Tensor<B, 2>,
    n_objects: usize,
    epsilon: f64,
    similarity_fn: impl FnOnce(Tensor<B, 2>) -> Tensor<B, 2>,
) -> Result<Tensor<B, 2>, TrainError> {
    validate_epsilon(epsilon)?;
    let device = dets_t.device();
    let dims = dets_t.dims();

    let dets_adv = dets_t.clone().detach().require_grad();
    let sim = similarity_fn(dets_adv.clone());
    let [rows, cols] = sim.dims();
    if rows.min(cols).min(n_objects) == 0 {
        return Ok(dets_t);
    }

    let loss = hungarian_similarity_loss(sim, n_objects);
    let grads = loss.backward();
    let Some(grad) = dets_adv.grad(&grads) else {
        return Ok(dets_t);
    };

    let orig = to_f64_vec(dets_t);
    let sign: Vec<f64> = to_f64_vec(grad).into_iter().map(torch_sign).collect();
    let perturbed: Vec<f64> = orig
        .iter()
        .zip(sign.iter())
        .map(|(o, s)| o + epsilon * s)
        .collect();
    Ok(Tensor::from_data(
        TensorData::new(perturbed, dims.to_vec()),
        &device,
    ))
}

/// Projected Gradient Descent (PGD) attack on input detections: iteratively
/// perturbs `dets_t` by `alpha * sign(grad)` per step, projecting back onto
/// the L-infinity `epsilon`-ball after each step.
///
/// `similarity_fn` is called once per step (see [`fgsm_attack`] for the
/// closure contract).
///
/// Direct port of `pgd_attack` (`adversarial_tools.py:70-135`). `alpha`
/// defaults to `epsilon / 4` (reference default, `:100-101`). Stops early
/// (returning the accumulated perturbation so far) if a step's matchable
/// block is empty or no gradient reaches the current iterate, matching the
/// reference's identical `break` guards.
///
/// # Errors
///
/// Returns [`TrainError::InvalidPerturbationBudget`] if `epsilon` is
/// non-finite or `<= 0`, if `alpha` (when supplied) is non-finite or `<=
/// 0`, or [`TrainError::InvalidStepCount`] if `steps == 0`.
#[allow(clippy::too_many_arguments)]
pub fn pgd_attack<B: AutodiffBackend>(
    dets_t: Tensor<B, 2>,
    n_objects: usize,
    epsilon: f64,
    alpha: Option<f64>,
    steps: usize,
    random_start: bool,
    seed: &mut Seed,
    mut similarity_fn: impl FnMut(Tensor<B, 2>) -> Tensor<B, 2>,
) -> Result<Tensor<B, 2>, TrainError> {
    validate_epsilon(epsilon)?;
    let alpha = alpha.unwrap_or(epsilon / 4.0);
    if !alpha.is_finite() || alpha <= 0.0 {
        return Err(TrainError::InvalidPerturbationBudget {
            name: "alpha",
            value: alpha,
        });
    }
    if steps == 0 {
        return Err(TrainError::InvalidStepCount {
            name: "steps",
            value: steps,
        });
    }

    let device = dets_t.device();
    let dims = dets_t.dims();
    let n_elems: usize = dims.iter().product();
    let orig = to_f64_vec(dets_t);

    let mut delta: Vec<f64> = if random_start {
        (0..n_elems)
            .map(|_| seed.next_f64_range(-epsilon, epsilon).unwrap_or(0.0))
            .collect()
    } else {
        vec![0.0; n_elems]
    };

    for _ in 0..steps {
        let adv_data: Vec<f64> = orig.iter().zip(delta.iter()).map(|(o, d)| o + d).collect();
        let dets_adv = Tensor::<B, 2>::from_data(TensorData::new(adv_data, dims.to_vec()), &device)
            .require_grad();
        let sim = similarity_fn(dets_adv.clone());
        let [rows, cols] = sim.dims();
        if rows.min(cols).min(n_objects) == 0 {
            break;
        }

        let loss = hungarian_similarity_loss(sim, n_objects);
        let grads = loss.backward();
        let Some(grad) = dets_adv.grad(&grads) else {
            break;
        };
        let g = to_f64_vec(grad);
        for i in 0..n_elems {
            delta[i] = (delta[i] + alpha * torch_sign(g[i])).clamp(-epsilon, epsilon);
        }
    }

    let final_data: Vec<f64> = orig.iter().zip(delta.iter()).map(|(o, d)| o + d).collect();
    Ok(Tensor::from_data(
        TensorData::new(final_data, dims.to_vec()),
        &device,
    ))
}

/// Which attack [`adversarial_evaluate_phase_tracker`]/
/// [`adversarial_evaluate_temporal_slot_attention_mot`] should run.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum AttackKind {
    /// Single-step FGSM.
    Fgsm,
    /// Iterative PGD with the given step count (reference default `20`).
    Pgd {
        /// Number of PGD iterations.
        steps: usize,
    },
}

/// Result of an adversarial robustness evaluation over a dataset, matching
/// the reference's `adversarial_evaluate` return dict.
#[derive(Clone, Debug, PartialEq)]
pub struct AdversarialEvalResult {
    /// Mean identity preservation on clean (unperturbed) sequences.
    pub clean_ip: f64,
    /// Mean identity preservation on adversarially perturbed sequences.
    pub adv_ip: f64,
    /// `clean_ip - adv_ip`.
    pub degradation: f64,
    /// Per-sequence clean identity preservation.
    pub per_seq_clean: Vec<f64>,
    /// Per-sequence adversarial identity preservation.
    pub per_seq_adv: Vec<f64>,
}

fn build_adversarial_eval_result(clean_ips: Vec<f64>, adv_ips: Vec<f64>) -> AdversarialEvalResult {
    let mean = |v: &[f64]| -> f64 {
        if v.is_empty() {
            0.0
        } else {
            v.iter().sum::<f64>() / v.len() as f64
        }
    };
    let clean_ip = mean(&clean_ips);
    let adv_ip = mean(&adv_ips);
    AdversarialEvalResult {
        clean_ip,
        adv_ip,
        degradation: clean_ip - adv_ip,
        per_seq_clean: clean_ips,
        per_seq_adv: adv_ips,
    }
}

/// Evaluate `tracker`'s identity preservation under adversarial attack
/// across `dataset`, perturbing each frame `t` (as `dets_t = frame[t-1]`
/// against the fixed target `dets_t1 = frame[t]`) and re-running
/// [`PhaseTracker::track_sequence`] on the perturbed frames.
///
/// Direct port of `adversarial_evaluate` (`adversarial_tools.py:138-213`)
/// specialized to [`PhaseTracker`] — see module docs.
///
/// # Errors
///
/// See [`fgsm_attack`]/[`pgd_attack`]. Propagates the first error
/// encountered while attacking any sequence.
pub fn adversarial_evaluate_phase_tracker<B: AutodiffBackend>(
    tracker: &PhaseTracker<B>,
    dataset: &[SequenceData],
    epsilon: f64,
    attack: AttackKind,
    seed: u64,
    device: &B::Device,
) -> Result<AdversarialEvalResult, TrainError> {
    let mut clean_ips = Vec::with_capacity(dataset.len());
    let mut adv_ips = Vec::with_capacity(dataset.len());

    for (i, seq) in dataset.iter().enumerate() {
        let frames = seq.frame_tensors::<B>(device);
        let clean_ip = tracker
            .track_sequence(frames.clone())
            .map(|r| r.identity_preservation)
            .unwrap_or(0.0);
        clean_ips.push(clean_ip);

        let mut adv_frames = Vec::with_capacity(frames.len());
        if !frames.is_empty() {
            adv_frames.push(frames[0].clone());
        }
        for t in 1..frames.len() {
            let dets_prev = frames[t - 1].clone();
            let dets_curr = frames[t].clone();
            let adv = match attack {
                AttackKind::Fgsm => fgsm_attack(dets_prev, seq.n_objects, epsilon, |d| {
                    tracker
                        .forward(d, dets_curr.clone())
                        .expect("frames constructed to match the tracker's detection_dim")
                        .1
                })?,
                AttackKind::Pgd { steps } => {
                    let mut local_seed = Seed::new(seed as u128 + i as u128 * 100 + t as u128, 0);
                    let perturbed = pgd_attack(
                        dets_prev,
                        seq.n_objects,
                        epsilon,
                        None,
                        steps,
                        true,
                        &mut local_seed,
                        |d| {
                            tracker
                                .forward(d, dets_curr.clone())
                                .expect("frames constructed to match the tracker's detection_dim")
                                .1
                        },
                    );
                    perturbed?
                }
            };
            adv_frames.push(adv);
        }

        let adv_ip = tracker
            .track_sequence(adv_frames)
            .map(|r| r.identity_preservation)
            .unwrap_or(0.0);
        adv_ips.push(adv_ip);
    }

    Ok(build_adversarial_eval_result(clean_ips, adv_ips))
}

/// Evaluate `tracker`'s identity preservation under adversarial attack
/// across `dataset` — the [`TemporalSlotAttentionMOT`] counterpart of
/// [`adversarial_evaluate_phase_tracker`], threading a fresh, deterministic
/// [`Seed`] through the tracker's per-call slot-initialization noise for
/// every `forward`/`track_sequence` invocation.
///
/// # Errors
///
/// See [`adversarial_evaluate_phase_tracker`].
pub fn adversarial_evaluate_temporal_slot_attention_mot<B: AutodiffBackend>(
    tracker: &TemporalSlotAttentionMOT<B>,
    dataset: &[SequenceData],
    epsilon: f64,
    attack: AttackKind,
    seed: u64,
    device: &B::Device,
) -> Result<AdversarialEvalResult, TrainError> {
    let mut clean_ips = Vec::with_capacity(dataset.len());
    let mut adv_ips = Vec::with_capacity(dataset.len());

    for (i, seq) in dataset.iter().enumerate() {
        let frames = seq.frame_tensors::<B>(device);

        let mut clean_seed = Seed::new(seed as u128 + i as u128 * 100_000, 0);
        let clean_ip = tracker
            .track_sequence(frames.clone(), &mut clean_seed)
            .map(|r| r.2)
            .unwrap_or(0.0);
        clean_ips.push(clean_ip);

        let mut adv_frames = Vec::with_capacity(frames.len());
        if !frames.is_empty() {
            adv_frames.push(frames[0].clone());
        }
        for t in 1..frames.len() {
            let dets_prev = frames[t - 1].clone();
            let dets_curr = frames[t].clone();
            let mut fwd_seed = Seed::new(seed as u128 + i as u128 * 100 + t as u128 + 1, 1);
            let adv = match attack {
                AttackKind::Fgsm => fgsm_attack(dets_prev, seq.n_objects, epsilon, |d| {
                    tracker
                        .forward(d, dets_curr.clone(), &mut fwd_seed)
                        .expect("frames constructed to match the tracker's detection_dim")
                        .1
                })?,
                AttackKind::Pgd { steps } => {
                    let mut pgd_seed = Seed::new(seed as u128 + i as u128 * 100 + t as u128, 0);
                    let perturbed = pgd_attack(
                        dets_prev,
                        seq.n_objects,
                        epsilon,
                        None,
                        steps,
                        true,
                        &mut pgd_seed,
                        |d| {
                            tracker
                                .forward(d, dets_curr.clone(), &mut fwd_seed)
                                .expect("frames constructed to match the tracker's detection_dim")
                                .1
                        },
                    );
                    perturbed?
                }
            };
            adv_frames.push(adv);
        }

        let mut adv_seed = Seed::new(seed as u128 + i as u128 * 100_000 + 1, 0);
        let adv_ip = tracker
            .track_sequence(adv_frames, &mut adv_seed)
            .map(|r| r.2)
            .unwrap_or(0.0);
        adv_ips.push(adv_ip);
    }

    Ok(build_adversarial_eval_result(clean_ips, adv_ips))
}

/// One `(attack, epsilon)` cell of [`adversarial_comparison`]'s grid.
#[derive(Clone, Debug, PartialEq)]
pub struct AdversarialComparisonCell {
    /// Perturbation budget for this cell.
    pub epsilon: f64,
    /// [`PhaseTracker`]'s clean identity preservation.
    pub pt_clean_ip: f64,
    /// [`PhaseTracker`]'s adversarial identity preservation.
    pub pt_adv_ip: f64,
    /// [`PhaseTracker`]'s IP degradation.
    pub pt_degradation: f64,
    /// [`TemporalSlotAttentionMOT`]'s clean identity preservation.
    pub sa_clean_ip: f64,
    /// [`TemporalSlotAttentionMOT`]'s adversarial identity preservation.
    pub sa_adv_ip: f64,
    /// [`TemporalSlotAttentionMOT`]'s IP degradation.
    pub sa_degradation: f64,
}

/// Side-by-side adversarial robustness comparison between a [`PhaseTracker`]
/// and a [`TemporalSlotAttentionMOT`] across every `(attack, epsilon)`
/// combination.
///
/// Direct port of `adversarial_comparison` (`adversarial_tools.py:216-268`),
/// flattened from the reference's `results[attack][str(eps)]` nested dict
/// into `Vec<(AttackKind, Vec<AdversarialComparisonCell>)>` (one entry per
/// `attack_types` element, in order, each holding one cell per `epsilons`
/// element, in order) — the same information, typed rather than
/// string-keyed.
///
/// # Errors
///
/// See [`adversarial_evaluate_phase_tracker`]/
/// [`adversarial_evaluate_temporal_slot_attention_mot`].
pub fn adversarial_comparison<B: AutodiffBackend>(
    pt_tracker: &PhaseTracker<B>,
    sa_tracker: &TemporalSlotAttentionMOT<B>,
    dataset: &[SequenceData],
    epsilons: &[f64],
    attack_types: &[AttackKind],
    seed: u64,
    device: &B::Device,
) -> Result<Vec<(AttackKind, Vec<AdversarialComparisonCell>)>, TrainError> {
    let mut results = Vec::with_capacity(attack_types.len());
    for &attack in attack_types {
        let mut cells = Vec::with_capacity(epsilons.len());
        for &epsilon in epsilons {
            let pt_result = adversarial_evaluate_phase_tracker(
                pt_tracker, dataset, epsilon, attack, seed, device,
            );
            let pt_res = pt_result?;
            let sa_result = adversarial_evaluate_temporal_slot_attention_mot(
                sa_tracker, dataset, epsilon, attack, seed, device,
            );
            let sa_res = sa_result?;
            cells.push(AdversarialComparisonCell {
                epsilon,
                pt_clean_ip: pt_res.clean_ip,
                pt_adv_ip: pt_res.adv_ip,
                pt_degradation: pt_res.degradation,
                sa_clean_ip: sa_res.clean_ip,
                sa_adv_ip: sa_res.adv_ip,
                sa_degradation: sa_res.degradation,
            });
        }
        results.push((attack, cells));
    }
    Ok(results)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dataset::{generate_dataset, TemporalClevrNConfig};
    use crate::phase_tracker::PhaseTrackerConfig;
    use crate::slot_attention::TemporalSlotAttentionMOTConfig;
    use burn::backend::{Autodiff, NdArray};
    use burn::tensor::backend::Backend;
    use burn::tensor::TensorData;

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestAutodiffBackend as Backend>::Device {
        Default::default()
    }

    fn tracker() -> PhaseTracker<TestAutodiffBackend> {
        let mut seed = Seed::new(1, 0);
        PhaseTrackerConfig::with_params(4, 2, 3, 4, 2, 0.3)
            .unwrap()
            .init(&device(), &mut seed)
    }

    fn sa_tracker() -> TemporalSlotAttentionMOT<TestAutodiffBackend> {
        let mut seed = Seed::new(2, 0);
        TemporalSlotAttentionMOTConfig::with_params(4, 3, 8, 2, 0.3)
            .unwrap()
            .init(&device(), &mut seed)
    }

    fn dets(rows: usize, cols: usize, value: f64) -> Tensor<TestAutodiffBackend, 2> {
        Tensor::from_data(
            TensorData::new(vec![value; rows * cols], vec![rows, cols]),
            &device(),
        )
    }

    /// Distinct-per-row detections: unlike [`dets`] (every row identical),
    /// this avoids the fully-symmetric similarity matrix that makes
    /// [`hungarian_similarity_loss`]'s gradient w.r.t. the input vanish by
    /// symmetry (every row/column of the softmax is then indistinguishable,
    /// a genuine stationary point of the loss, not a bug) — needed for tests
    /// that must observe a nonzero attack gradient.
    fn varied_dets(rows: usize, cols: usize, base: f64) -> Tensor<TestAutodiffBackend, 2> {
        let data: Vec<f64> = (0..rows * cols).map(|i| base + 0.37 * (i as f64)).collect();
        Tensor::from_data(TensorData::new(data, vec![rows, cols]), &device())
    }

    // --- torch_sign ---

    #[test]
    fn torch_sign_matches_pytorch_zero_convention() {
        assert_eq!(torch_sign(0.0), 0.0);
        assert_eq!(torch_sign(2.5), 1.0);
        assert_eq!(torch_sign(-2.5), -1.0);
    }

    // --- fgsm_attack ---

    #[test]
    fn fgsm_attack_perturbation_is_within_epsilon_ball() {
        let t = tracker();
        let dets_t = dets(3, 4, 0.1);
        let dets_t1 = dets(3, 4, 0.15);
        let epsilon = 0.05;
        let perturbed = fgsm_attack(dets_t.clone(), 3, epsilon, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();

        let orig = to_f64_vec(dets_t);
        let adv = to_f64_vec(perturbed);
        for (o, a) in orig.iter().zip(adv.iter()) {
            assert!((a - o).abs() <= epsilon + 1e-9, "|{a} - {o}| > {epsilon}");
        }
    }

    #[test]
    fn fgsm_attack_actually_perturbs_when_gradient_exists() {
        let t = tracker();
        let dets_t = varied_dets(3, 4, 0.1);
        let dets_t1 = varied_dets(3, 4, 0.9);
        let perturbed = fgsm_attack(dets_t.clone(), 3, 0.1, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();
        assert_ne!(to_f64_vec(dets_t), to_f64_vec(perturbed));
    }

    #[test]
    fn fgsm_attack_rejects_invalid_epsilon() {
        let t = tracker();
        let dets_t = dets(3, 4, 0.1);
        let dets_t1 = dets_t.clone();
        let err =
            fgsm_attack(dets_t, 3, 0.0, |d| t.forward(d, dets_t1.clone()).unwrap().1).unwrap_err();
        assert!(matches!(
            err,
            TrainError::InvalidPerturbationBudget {
                name: "epsilon",
                ..
            }
        ));
    }

    #[test]
    fn fgsm_attack_zero_objects_returns_input_unperturbed() {
        let t = tracker();
        let dets_t = dets(3, 4, 0.1);
        let dets_t1 = dets_t.clone();
        let out = fgsm_attack(dets_t.clone(), 0, 0.1, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();
        assert_eq!(to_f64_vec(dets_t), to_f64_vec(out));
    }

    // --- pgd_attack ---

    #[test]
    fn pgd_attack_perturbation_is_within_epsilon_ball() {
        let t = tracker();
        let dets_t = dets(3, 4, 0.1);
        let dets_t1 = dets(3, 4, 0.15);
        let epsilon = 0.05;
        let mut seed = Seed::new(10, 0);
        let perturbed = pgd_attack(dets_t.clone(), 3, epsilon, None, 5, true, &mut seed, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();

        let orig = to_f64_vec(dets_t);
        let adv = to_f64_vec(perturbed);
        for (o, a) in orig.iter().zip(adv.iter()) {
            assert!((a - o).abs() <= epsilon + 1e-9, "|{a} - {o}| > {epsilon}");
        }
    }

    #[test]
    fn pgd_attack_is_deterministic_for_same_seed() {
        let t = tracker();
        let dets_t = dets(3, 4, 0.1);
        let dets_t1 = dets(3, 4, 0.2);

        let mut s1 = Seed::new(42, 0);
        let out1 = pgd_attack(dets_t.clone(), 3, 0.05, None, 4, true, &mut s1, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();

        let mut s2 = Seed::new(42, 0);
        let out2 = pgd_attack(dets_t.clone(), 3, 0.05, None, 4, true, &mut s2, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();

        assert_eq!(to_f64_vec(out1), to_f64_vec(out2));
    }

    #[test]
    fn pgd_attack_different_seeds_give_different_perturbations() {
        let t = tracker();
        let dets_t = dets(3, 4, 0.1);
        let dets_t1 = dets(3, 4, 0.2);

        let mut s1 = Seed::new(1, 0);
        let out1 = pgd_attack(dets_t.clone(), 3, 0.05, None, 4, true, &mut s1, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();

        let mut s2 = Seed::new(2, 0);
        let out2 = pgd_attack(dets_t.clone(), 3, 0.05, None, 4, true, &mut s2, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();

        assert_ne!(to_f64_vec(out1), to_f64_vec(out2));
    }

    #[test]
    fn pgd_attack_default_alpha_is_epsilon_over_four() {
        // Indirect check: a single-step PGD without random start moves by
        // exactly alpha (clamped to epsilon), matching FGSM's epsilon-step
        // only when alpha == epsilon; here we just confirm it runs and stays
        // in-bounds for the reference's `alpha = epsilon / 4` default.
        let t = tracker();
        let dets_t = dets(3, 4, 0.1);
        let dets_t1 = dets(3, 4, 0.3);
        let mut seed = Seed::new(5, 0);
        let out = pgd_attack(dets_t.clone(), 3, 0.08, None, 1, false, &mut seed, |d| {
            t.forward(d, dets_t1.clone()).unwrap().1
        })
        .unwrap();
        let orig = to_f64_vec(dets_t);
        let adv = to_f64_vec(out);
        for (o, a) in orig.iter().zip(adv.iter()) {
            let step = (a - o).abs();
            assert!(step <= 0.02 + 1e-9, "step {step} exceeds alpha=eps/4=0.02");
        }
    }

    #[test]
    fn pgd_attack_rejects_zero_steps() {
        let dets_t = dets(3, 4, 0.1);
        let mut seed = Seed::new(1, 0);
        // The closure is unreachable: `steps == 0` is rejected before any
        // similarity-function call, so its body never executes.
        let err = pgd_attack(dets_t, 3, 0.05, None, 0, true, &mut seed, |_| {
            unreachable!("steps validation must reject before the closure runs")
        })
        .unwrap_err();
        assert!(matches!(
            err,
            TrainError::InvalidStepCount {
                name: "steps",
                value: 0
            }
        ));
    }

    #[test]
    fn pgd_attack_rejects_invalid_alpha() {
        let dets_t = dets(3, 4, 0.1);
        let mut seed = Seed::new(1, 0);
        // Unreachable for the same reason as `pgd_attack_rejects_zero_steps`:
        // an invalid `alpha` is rejected before the closure ever runs.
        let err = pgd_attack(dets_t, 3, 0.05, Some(-1.0), 5, true, &mut seed, |_| {
            unreachable!("alpha validation must reject before the closure runs")
        })
        .unwrap_err();
        assert!(matches!(
            err,
            TrainError::InvalidPerturbationBudget { name: "alpha", .. }
        ));
    }

    // --- adversarial_evaluate_phase_tracker ---

    #[test]
    fn adversarial_evaluate_phase_tracker_ip_is_in_unit_interval() {
        let t = tracker();
        let cfg = TemporalClevrNConfig::new(3, 5).unwrap();
        let dataset = generate_dataset(2, &cfg, 100);
        let result =
            adversarial_evaluate_phase_tracker(&t, &dataset, 0.05, AttackKind::Fgsm, 7, &device())
                .unwrap();
        assert!((0.0..=1.0).contains(&result.clean_ip));
        assert!((0.0..=1.0).contains(&result.adv_ip));
        assert_eq!(result.per_seq_clean.len(), 2);
        assert_eq!(result.per_seq_adv.len(), 2);
        assert!((result.degradation - (result.clean_ip - result.adv_ip)).abs() < 1e-12);
    }

    #[test]
    fn adversarial_evaluate_phase_tracker_pgd_is_deterministic_for_same_seed() {
        let t = tracker();
        let cfg = TemporalClevrNConfig::new(3, 4).unwrap();
        let dataset = generate_dataset(2, &cfg, 200);
        let r1 = adversarial_evaluate_phase_tracker(
            &t,
            &dataset,
            0.05,
            AttackKind::Pgd { steps: 3 },
            99,
            &device(),
        )
        .unwrap();
        let r2 = adversarial_evaluate_phase_tracker(
            &t,
            &dataset,
            0.05,
            AttackKind::Pgd { steps: 3 },
            99,
            &device(),
        )
        .unwrap();
        assert_eq!(r1, r2);
    }

    // --- adversarial_evaluate_temporal_slot_attention_mot ---

    #[test]
    fn adversarial_evaluate_slot_attention_ip_is_in_unit_interval() {
        let t = sa_tracker();
        let cfg = TemporalClevrNConfig::new(3, 4).unwrap();
        let dataset = generate_dataset(2, &cfg, 300);
        let result = adversarial_evaluate_temporal_slot_attention_mot(
            &t,
            &dataset,
            0.05,
            AttackKind::Fgsm,
            11,
            &device(),
        )
        .unwrap();
        assert!((0.0..=1.0).contains(&result.clean_ip));
        assert!((0.0..=1.0).contains(&result.adv_ip));
    }

    // --- adversarial_comparison ---

    #[test]
    fn adversarial_comparison_covers_full_grid() {
        let pt = tracker();
        let sa = sa_tracker();
        let cfg = TemporalClevrNConfig::new(3, 4).unwrap();
        let dataset = generate_dataset(1, &cfg, 400);
        let results = adversarial_comparison(
            &pt,
            &sa,
            &dataset,
            &[0.02, 0.05],
            &[AttackKind::Fgsm, AttackKind::Pgd { steps: 2 }],
            1,
            &device(),
        )
        .unwrap();
        assert_eq!(results.len(), 2);
        for (_, cells) in &results {
            assert_eq!(cells.len(), 2);
            for cell in cells {
                assert!((0.0..=1.0).contains(&cell.pt_clean_ip));
                assert!((0.0..=1.0).contains(&cell.sa_clean_ip));
            }
        }
    }
}
