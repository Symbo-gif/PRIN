//! Training losses for temporal-tracking similarity matrices (WP-027): a
//! direct port of PRINet 3.0's `hungarian_similarity_loss`/
//! `temporal_smoothness_loss` (`utils/temporal_training.py:261-336`).
//!
//! Both are consumed by [`crate::trainer::train_phase_tracker`] to train
//! [`crate::phase_tracker::PhaseTracker`] (and, symmetrically, could drive
//! [`crate::slot_attention::TemporalSlotAttentionMOT`]) on differentiable
//! similarity matrices produced by `forward`/`process_frame` +
//! `slot_similarity` — never on `track_sequence`'s `no_grad` output, exactly
//! as the reference's own `_train_step_pt`/`_train_step_sa` do
//! (`temporal_training.py:540-627`).

use burn::tensor::activation::log_softmax;
use burn::tensor::backend::Backend;
use burn::tensor::{Tensor, TensorData};

/// Assignment loss on a similarity matrix: cross-entropy over each row
/// (temperature-scaled) with the identity permutation as the target,
/// encouraging the similarity diagonal (`sim[i, i]`, i.e. "object `i`
/// matches object `i`") to dominate its row.
///
/// Direct port of `hungarian_similarity_loss` (`temporal_training.py:261-303`):
///
/// ```text
/// L = -(1/N) * sum_i log( exp(s[i,i]/T) / sum_j exp(s[i,j]/T) ),  T = 0.1
/// ```
///
/// where `N = min(sim.rows, sim.cols, n_objects)` and only the top-left
/// `N x N` block of `sim` is used. Returns a zero-valued scalar if `N == 0`.
pub fn hungarian_similarity_loss<B: Backend>(sim: Tensor<B, 2>, n_objects: usize) -> Tensor<B, 1> {
    const TEMPERATURE: f64 = 0.1;

    let [rows, cols] = sim.dims();
    let n = rows.min(cols).min(n_objects);
    let device = sim.device();
    if n == 0 {
        return Tensor::zeros([1], &device);
    }

    let sim_block = sim.slice([0..n, 0..n]);
    let logits = sim_block.div_scalar(TEMPERATURE);
    let log_probs = log_softmax(logits, 1); // [n, n]

    let mask = diagonal_mask::<B>(n, &device);
    let diag_log_probs = (log_probs * mask).sum_dim(1); // [n, 1]
    diag_log_probs.mean().neg()
}

/// Penalize jittery similarity-matrix evolution across frames: mean squared
/// difference between each pair of consecutive similarity matrices (only
/// their shared top-left block, when shapes differ).
///
/// Direct port of `temporal_smoothness_loss`
/// (`temporal_training.py:306-336`). Returns a zero-valued scalar if fewer
/// than two matrices are supplied.
pub fn temporal_smoothness_loss<B: Backend>(sims: &[Tensor<B, 2>]) -> Tensor<B, 1> {
    if sims.len() < 2 {
        let device = sims.first().map(|s| s.device()).unwrap_or_default();
        return Tensor::zeros([1], &device);
    }

    let mut diffs = Vec::with_capacity(sims.len() - 1);
    for pair in sims.windows(2) {
        let [pr, pc] = pair[0].dims();
        let [cr, cc] = pair[1].dims();
        let n = pr.min(cr);
        let m = pc.min(cc);
        let prev_block = pair[0].clone().slice([0..n, 0..m]);
        let curr_block = pair[1].clone().slice([0..n, 0..m]);
        let diff = prev_block - curr_block;
        diffs.push((diff.clone() * diff).mean());
    }

    Tensor::cat(diffs, 0).mean()
}

/// A `[n, n]` identity-matrix tensor, used to extract the diagonal of a
/// similarity matrix via elementwise multiply-and-sum (differentiable
/// w.r.t. the multiplicand; the mask itself carries no gradient).
fn diagonal_mask<B: Backend>(n: usize, device: &B::Device) -> Tensor<B, 2> {
    let mut data = vec![0.0_f64; n * n];
    for i in 0..n {
        data[i * n + i] = 1.0;
    }
    Tensor::from_data(TensorData::new(data, vec![n, n]), device)
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::NdArray;

    type TestBackend = NdArray<f64>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    fn tensor(data: Vec<f64>, rows: usize, cols: usize) -> Tensor<TestBackend, 2> {
        Tensor::from_data(TensorData::new(data, vec![rows, cols]), &device())
    }

    // --- hungarian_similarity_loss ---

    #[test]
    fn perfect_diagonal_similarity_gives_near_zero_loss() {
        // sim = [[10, -10], [-10, 10]] -> after /0.1 -> [[100,-100],[-100,100]]
        // softmax essentially puts all mass on the diagonal -> loss ~ 0.
        let sim = tensor(vec![10.0, -10.0, -10.0, 10.0], 2, 2);
        let loss = hungarian_similarity_loss(sim, 2);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert!(v.abs() < 1e-6, "loss {v} not ~0");
    }

    #[test]
    fn hand_computed_2x2_uniform_similarity_matches_log2() {
        // sim = 0 everywhere -> logits = 0 -> softmax uniform over 2 classes
        // -> -log(1/2) = ln(2) per row -> mean = ln(2).
        let sim = tensor(vec![0.0, 0.0, 0.0, 0.0], 2, 2);
        let loss = hungarian_similarity_loss(sim, 2);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert!((v - std::f64::consts::LN_2).abs() < 1e-9, "loss {v}");
    }

    #[test]
    fn zero_n_objects_gives_zero_loss() {
        let sim = tensor(vec![1.0, 2.0, 3.0, 4.0], 2, 2);
        let loss = hungarian_similarity_loss(sim, 0);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert_eq!(v, 0.0);
    }

    #[test]
    fn rectangular_similarity_uses_top_left_square_block() {
        // 2x3 similarity: only the top-left 2x2 block participates.
        let sim = tensor(vec![10.0, -10.0, 0.0, -10.0, 10.0, 0.0], 2, 3);
        let loss = hungarian_similarity_loss(sim, 5); // n = min(2,3,5) = 2
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert!(v.abs() < 1e-6, "loss {v} not ~0");
    }

    #[test]
    fn gradients_flow_through_similarity_matrix() {
        let _guard = crate::support::autodiff_test_guard();
        use burn::backend::Autodiff;
        type AutodiffBackend = Autodiff<TestBackend>;
        let dev: <AutodiffBackend as Backend>::Device = Default::default();
        let sim = Tensor::<AutodiffBackend, 2>::from_data(
            TensorData::new(vec![1.0, 0.5, 0.5, 1.0], vec![2, 2]),
            &dev,
        )
        .require_grad();
        let loss = hungarian_similarity_loss(sim.clone(), 2);
        let grads = loss.backward();
        let grad = sim.grad(&grads).expect("gradient must flow to sim");
        let g = grad.to_data().to_vec::<f64>().unwrap();
        assert!(g.iter().all(|v| v.is_finite()));
        assert!(g.iter().any(|v| v.abs() > 0.0));
    }

    // --- temporal_smoothness_loss ---

    #[test]
    fn identical_consecutive_matrices_give_zero_smoothness_loss() {
        let a = tensor(vec![1.0, 2.0, 3.0, 4.0], 2, 2);
        let b = a.clone();
        let loss = temporal_smoothness_loss(&[a, b]);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert!(v.abs() < 1e-12, "loss {v} not ~0");
    }

    #[test]
    fn single_matrix_gives_zero_smoothness_loss() {
        let a = tensor(vec![1.0, 2.0, 3.0, 4.0], 2, 2);
        let loss = temporal_smoothness_loss(&[a]);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert_eq!(v, 0.0);
    }

    #[test]
    fn empty_slice_gives_zero_smoothness_loss() {
        let loss = temporal_smoothness_loss::<TestBackend>(&[]);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert_eq!(v, 0.0);
    }

    #[test]
    fn hand_computed_mse_between_two_matrices() {
        // diff = [[1,1],[1,1]] everywhere -> squared = 1 everywhere -> mean = 1.
        let a = tensor(vec![0.0, 0.0, 0.0, 0.0], 2, 2);
        let b = tensor(vec![1.0, 1.0, 1.0, 1.0], 2, 2);
        let loss = temporal_smoothness_loss(&[a, b]);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert!((v - 1.0).abs() < 1e-12, "loss {v}");
    }

    #[test]
    fn mismatched_shapes_use_shared_top_left_block() {
        let a = tensor(vec![0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 2, 3);
        let b = tensor(vec![1.0, 1.0, 1.0, 1.0], 2, 2);
        // shared block is 2x2, diff = 1 everywhere -> mean squared = 1.
        let loss = temporal_smoothness_loss(&[a, b]);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert!((v - 1.0).abs() < 1e-12, "loss {v}");
    }

    #[test]
    fn three_matrices_averages_two_consecutive_diffs() {
        let a = tensor(vec![0.0, 0.0, 0.0, 0.0], 2, 2);
        let b = tensor(vec![1.0, 1.0, 1.0, 1.0], 2, 2); // diff(a,b) mse = 1
        let c = tensor(vec![1.0, 1.0, 1.0, 1.0], 2, 2); // diff(b,c) mse = 0
        let loss = temporal_smoothness_loss(&[a, b, c]);
        let v = loss.into_data().to_vec::<f64>().unwrap()[0];
        assert!((v - 0.5).abs() < 1e-12, "loss {v}");
    }
}
