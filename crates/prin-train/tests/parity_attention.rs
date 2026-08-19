//! Rust-vs-PRINet-3.0.0 golden-value parity test for
//! [`OscillatoryAttention::forward`].
//!
//! Reference generation: `DOCS/test_and_benchmark_results/wp026_generate_prinet_references.py`
//! (ad-hoc, gitignored, WP-009/.../WP-025 precedent) — instantiates the
//! actual `prinet.nn.layers.OscillatoryAttention`, extracts its random
//! `nn.Linear` weights via `state_dict()`, overrides `alpha` to a nonzero
//! value (default init is zero, which would make the coherence bias
//! untested), and runs `forward` with `dropout=0.0` and an explicit external
//! `phase` tensor so the computation is fully deterministic.
//!
//! PyTorch's `nn.Linear.weight` is `[d_output, d_input]` (`y = x·Wᵀ + b`);
//! Burn's `Linear.weight` is `[d_input, d_output]` (`y = x·W + b`) — every
//! weight below is transposed accordingly.

use burn::backend::NdArray;
use burn::tensor::{Tensor, TensorData};
use prin_train::attention::{OscillatoryAttentionConfig, OscillatoryAttentionParams};

type TestBackend = NdArray<f64>;

const RTOL: f64 = 1e-6;
const ATOL: f64 = 1e-6;

fn assert_close(actual: &[f64], expected: &[f64], rtol: f64, atol: f64) {
    assert_eq!(actual.len(), expected.len());
    for (i, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert!(
            (a - e).abs() <= atol || (a - e).abs() <= rtol * e.abs(),
            "index {i}: actual {a:.17e} vs expected {e:.17e} (abs {:.3e} > atol {atol:.3e})",
            (a - e).abs()
        );
    }
}

/// Transpose a flat row-major `[rows, cols]` PyTorch `nn.Linear.weight`
/// (`[d_output, d_input]`) into Burn's `[d_input, d_output]` layout.
fn transpose(values: &[f64], rows: usize, cols: usize) -> Vec<f64> {
    let mut out = vec![0.0; values.len()];
    for r in 0..rows {
        for c in 0..cols {
            out[c * rows + r] = values[r * cols + c];
        }
    }
    out
}

fn tensor2(
    values: &[f64],
    shape: [usize; 2],
    device: &<TestBackend as burn::tensor::backend::Backend>::Device,
) -> Tensor<TestBackend, 2> {
    Tensor::from_data(TensorData::new(values.to_vec(), shape.to_vec()), device)
}

fn tensor1(
    values: &[f64],
    device: &<TestBackend as burn::tensor::backend::Backend>::Device,
) -> Tensor<TestBackend, 1> {
    Tensor::from_data(TensorData::new(values.to_vec(), vec![values.len()]), device)
}

#[test]
fn oscillatory_attention_forward_matches_prinet_3_0() {
    let device = Default::default();
    const D: usize = 4;
    const H: usize = 2;

    // PyTorch nn.Linear.weight layout: [d_output, d_input].
    let w_q_weight = [
        0.2576315999031067,
        -0.22068911790847778,
        -0.09693074226379395,
        0.23468446731567383,
        -0.4707184433937073,
        0.29985862970352173,
        -0.1028626561164856,
        0.2543719410896301,
        0.06950849294662476,
        -0.061222076416015625,
        0.13868045806884766,
        0.024665892124176025,
        0.18261408805847168,
        -0.19485050439834595,
        -0.03645437955856323,
        -0.0450136661529541,
    ];
    let w_q_bias = [
        0.0724719762802124,
        -0.0019974112510681152,
        0.43708336353302,
        0.155595064163208,
    ];
    let w_k_weight = [
        -0.18620312213897705,
        -0.3019806742668152,
        -0.08380782604217529,
        -0.21567034721374512,
        -0.16022425889968872,
        0.0239408016204834,
        0.29806387424468994,
        0.27176833152770996,
        -0.48877543210983276,
        0.3099602460861206,
        0.13968193531036377,
        0.4742777347564697,
        0.3300299048423767,
        -0.4555688500404358,
        -0.47540420293807983,
        -0.24116605520248413,
    ];
    let w_k_bias = [
        0.439055860042572,
        -0.08328449726104736,
        0.21397972106933594,
        -0.23235571384429932,
    ];
    let w_v_weight = [
        0.49060899019241333,
        -0.21154922246932983,
        0.37496238946914673,
        0.005920827388763428,
        -0.26340872049331665,
        0.2570074200630188,
        -0.26541006565093994,
        0.1470523476600647,
        -0.14437860250473022,
        -0.05481719970703125,
        -0.480694055557251,
        -0.23839086294174194,
        0.2713170051574707,
        -0.12153863906860352,
        0.49802476167678833,
        0.40079420804977417,
    ];
    let w_v_bias = [
        -0.023411810398101807,
        -0.33374154567718506,
        0.3044810891151428,
        0.15517854690551758,
    ];
    let w_o_weight = [
        -0.32320988178253174,
        0.32477229833602905,
        0.3035508990287781,
        0.443447470664978,
        -0.28027981519699097,
        -0.082302987575531,
        -0.009685933589935303,
        0.07302874326705933,
        -0.3794591426849365,
        -0.3548111915588379,
        0.27200227975845337,
        -0.11724597215652466,
        0.24423670768737793,
        0.02850496768951416,
        0.16417241096496582,
        0.10994434356689453,
    ];
    let w_o_bias = [
        0.18179970979690552,
        0.24785536527633667,
        -0.4630560278892517,
        0.25167572498321533,
    ];
    let phase_proj_weight = [
        -0.35156160593032837,
        -0.3772544860839844,
        0.030407190322875977,
        -0.08520358800888062,
        0.29366201162338257,
        -0.28956782817840576,
        -0.4444909691810608,
        0.3638843894004822,
    ];
    let phase_proj_bias = [-0.07414090633392334, 0.28122860193252563];
    let alpha = [0.5, -0.3];
    let x = [0.1, 0.2, 0.3, 0.4, 0.5, -0.1, 0.2, 0.0, -0.2, 0.3, 0.1, 0.4];
    let phase = [0.1, 0.5, 1.0, 1.5, 2.0, 0.2];
    let expected_out = [
        0.2266453529910344,
        0.2707224726341608,
        -0.3899557955423976,
        0.3322011134634242,
        0.2287373999165369,
        0.27281364065750024,
        -0.3870418116372948,
        0.3294592459413601,
        0.2579095779648132,
        0.2835683615902021,
        -0.3821390103747423,
        0.3196403115548364,
    ];

    let params = OscillatoryAttentionParams {
        w_q_weight: tensor2(&transpose(&w_q_weight, D, D), [D, D], &device),
        w_q_bias: tensor1(&w_q_bias, &device),
        w_k_weight: tensor2(&transpose(&w_k_weight, D, D), [D, D], &device),
        w_k_bias: tensor1(&w_k_bias, &device),
        w_v_weight: tensor2(&transpose(&w_v_weight, D, D), [D, D], &device),
        w_v_bias: tensor1(&w_v_bias, &device),
        w_o_weight: tensor2(&transpose(&w_o_weight, D, D), [D, D], &device),
        w_o_bias: tensor1(&w_o_bias, &device),
        // phase_proj: PyTorch weight is [n_heads, d_model] = [H, D].
        phase_proj_weight: tensor2(&transpose(&phase_proj_weight, H, D), [D, H], &device),
        phase_proj_bias: tensor1(&phase_proj_bias, &device),
        alpha: tensor1(&alpha, &device),
    };

    let attn = OscillatoryAttentionConfig::with_params(D, H, 0.0)
        .unwrap()
        .init_from_params(params)
        .unwrap();

    let x_tensor =
        Tensor::<TestBackend, 3>::from_data(TensorData::new(x.to_vec(), vec![1, 3, D]), &device);
    let phase_tensor = Tensor::<TestBackend, 3>::from_data(
        TensorData::new(phase.to_vec(), vec![1, 3, H]),
        &device,
    );

    let out = attn.forward(x_tensor, Some(phase_tensor)).unwrap();
    let actual = out.to_data().to_vec::<f64>().unwrap();

    assert_close(&actual, &expected_out, RTOL, ATOL);
}
