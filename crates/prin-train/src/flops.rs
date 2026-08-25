//! FLOPs estimation and wall-time measurement for efficiency comparison
//! (WP-031): a direct port of PRINet 3.0's `count_flops`/`measure_wall_time`
//! (`utils/y4q1_tools.py:498-635`).
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! The reference's `count_flops` introspects a live `nn.Module` tree
//! (`model.named_modules()`), branching on `isinstance(module, nn.Linear |
//! nn.Conv2d | nn.GRUCell)`. Burn has no equivalent generic reflection API
//! (a `Module`'s field types are erased behind [`burn::module::ModuleVisitor`],
//! which only visits tensor parameters, not layer *kinds*), so this port
//! takes a caller-supplied [`LayerSpec`] description instead — the same
//! shape of information (`in_features`/`out_features`/`kernel_size`/etc.)
//! the reference extracts from each module via its own field access, applied
//! to the *same three closed-form formulas* (`y4q1_tools.py:524-568`). This
//! is a structural port, not a bit-parity one: [`count_flops`]'s FLOPs
//! totals reproduce the reference exactly for any given layer shape, but the
//! per-layer `params` figure is likewise formula-derived here (`in *
//! out (+ out if bias)` for [`LayerSpec::Linear`], analogous closed forms
//! for [`LayerSpec::Conv2d`]/[`LayerSpec::GruCell`]) rather than summed from
//! live parameter tensors as the reference's `sum(p.numel() for p in
//! module.parameters())` does — the two coincide exactly for
//! [`LayerSpec::Linear`] (the reference's own per-layer `params` field is
//! *also* formula-derived there, `y4q1_tools.py:534-536`), and coincide for
//! [`LayerSpec::Conv2d`]/[`LayerSpec::GruCell`] under the PyTorch default
//! bias configuration this port assumes (documented on each variant).
//!
//! **Documented reference discrepancy — `Conv2d` FLOPs.** The reference's
//! own docstring states the Conv2d formula as `2 * C_in * C_out * K² *
//! H_out * W_out`, but its actual implementation
//! (`y4q1_tools.py:538-546`) omits the `H_out * W_out` factor entirely. This
//! port reproduces the reference's *executed* formula (the "trusted
//! reference" this WP's acceptance criterion names is the reference's
//! actual behavior, not its docstring) — see
//! [`LayerSpec::Conv2d`]'s own docs. No PRIN model currently uses `Conv2d`
//! (PhaseTracker/SlotAttention are MLP+GRU/oscillator architectures); this
//! variant exists for reference-formula completeness only.
//!
//! [`measure_wall_time`] is a direct structural port of the reference
//! function of the same name (`y4q1_tools.py:583-635`), generalized from "a
//! PyTorch model's forward call" to any closure — Burn has no `torch.cuda`
//! device-synchronization concept to port (this project's kernel-equivalence
//! tests already cover GPU-path correctness; wall-time comparison here is
//! host-side CPU timing only, consistent with `prin-kernels`'s own
//! documented prototype-timing caveat for `StepReport::wall_time_seconds`).

/// A single layer's shape, for [`count_flops`]'s closed-form FLOPs/params
/// formulas — see module docs for why this is caller-supplied rather than
/// introspected from a live `Module`.
#[derive(Clone, Debug, PartialEq)]
pub enum LayerSpec {
    /// A fully-connected layer: `y = x @ W + b` (`W: [in_features,
    /// out_features]`).
    Linear {
        /// Layer name, for [`LayerFlops::name`].
        name: String,
        /// Input feature count.
        in_features: usize,
        /// Output feature count.
        out_features: usize,
        /// Whether the layer has a bias term.
        bias: bool,
    },
    /// A 2D convolution. See module docs for the FLOPs-formula discrepancy
    /// this port intentionally preserves from the reference's actual
    /// (docstring-inconsistent) implementation: the FLOPs total does **not**
    /// scale with output spatial size (`H_out * W_out`). `params` assumes
    /// PyTorch `nn.Conv2d`'s default `bias=True`.
    Conv2d {
        /// Layer name.
        name: String,
        /// Input channel count.
        in_channels: usize,
        /// Output channel count.
        out_channels: usize,
        /// Kernel height.
        kernel_h: usize,
        /// Kernel width.
        kernel_w: usize,
    },
    /// A single-step GRU cell (3 gates). `params` assumes PyTorch
    /// `nn.GRUCell`'s default `bias=True` (`3 * hidden * (input + hidden +
    /// 2)`); the reference's own FLOPs formula (reproduced exactly here)
    /// does not add a separate bias term.
    GruCell {
        /// Layer name.
        name: String,
        /// Input feature count.
        input_size: usize,
        /// Hidden state size.
        hidden_size: usize,
    },
}

/// One layer's contribution to [`FlopsReport`], matching the reference's
/// `layer_flops` list-of-dicts entries.
#[derive(Clone, Debug, PartialEq)]
pub struct LayerFlops {
    /// Layer name (from the originating [`LayerSpec`]).
    pub name: String,
    /// Layer kind: `"Linear"`, `"Conv2d"`, or `"GruCell"`.
    pub layer_type: &'static str,
    /// Estimated FLOPs for one forward pass through this layer (unscaled by
    /// batch size — see [`FlopsReport::total_flops`]).
    pub flops: u64,
    /// Formula-derived parameter count for this layer (see module docs).
    pub params: u64,
}

/// Full FLOPs estimation result, matching the reference's return dict.
#[derive(Clone, Debug, PartialEq)]
pub struct FlopsReport {
    /// Total estimated FLOPs across all layers, scaled by `batch_size`.
    pub total_flops: u64,
    /// Total parameter count across all layers (unscaled by batch size — a
    /// parameter count does not depend on batch size).
    pub total_params: u64,
    /// Per-layer breakdown, in the order `layers` was given.
    pub layer_flops: Vec<LayerFlops>,
}

/// Estimate FLOPs for a forward pass through `layers`, scaled by
/// `batch_size`.
///
/// Direct port of `count_flops` (`y4q1_tools.py:498-580`) — see module docs
/// for the live-introspection-vs-declarative-spec correspondence and the
/// `Conv2d` formula discrepancy this reproduces intentionally.
pub fn count_flops(layers: &[LayerSpec], batch_size: usize) -> FlopsReport {
    let mut total_flops: u64 = 0;
    let mut total_params: u64 = 0;
    let mut layer_flops = Vec::with_capacity(layers.len());

    for layer in layers {
        let (name, layer_type, flops, params) = match layer {
            LayerSpec::Linear {
                name,
                in_features,
                out_features,
                bias,
            } => {
                let (i, o) = (*in_features as u64, *out_features as u64);
                let mut flops = 2 * i * o;
                let mut params = i * o;
                if *bias {
                    flops += o;
                    params += o;
                }
                (name.clone(), "Linear", flops, params)
            }
            LayerSpec::Conv2d {
                name,
                in_channels,
                out_channels,
                kernel_h,
                kernel_w,
            } => {
                let (ci, co, kh, kw) = (
                    *in_channels as u64,
                    *out_channels as u64,
                    *kernel_h as u64,
                    *kernel_w as u64,
                );
                let flops = 2 * ci * co * kh * kw;
                let params = ci * co * kh * kw + co; // PyTorch default bias=True.
                (name.clone(), "Conv2d", flops, params)
            }
            LayerSpec::GruCell {
                name,
                input_size,
                hidden_size,
            } => {
                let (i, h) = (*input_size as u64, *hidden_size as u64);
                let flops = 3 * 2 * (i + h) * h;
                let params = 3 * (i + h + 2) * h; // PyTorch default bias=True.
                (name.clone(), "GruCell", flops, params)
            }
        };
        total_flops += flops;
        total_params += params;
        layer_flops.push(LayerFlops {
            name,
            layer_type,
            flops,
            params,
        });
    }

    total_flops *= batch_size.max(1) as u64;

    FlopsReport {
        total_flops,
        total_params,
        layer_flops,
    }
}

/// Wall-time measurement summary, matching the reference's return dict.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct WallTimeStats {
    /// Mean elapsed time per run, in milliseconds.
    pub mean_ms: f64,
    /// Standard deviation of per-run elapsed time (`ddof=1`), in
    /// milliseconds.
    pub std_ms: f64,
    /// Minimum observed elapsed time, in milliseconds.
    pub min_ms: f64,
    /// Maximum observed elapsed time, in milliseconds.
    pub max_ms: f64,
}

/// Measure `f`'s wall-clock time: `n_warmup` untimed calls, then `n_runs`
/// timed calls.
///
/// Direct structural port of `measure_wall_time` (`y4q1_tools.py:583-635`),
/// generalized to any closure (see module docs). Returns all-zero stats if
/// `n_runs == 0`.
pub fn measure_wall_time<F: FnMut()>(mut f: F, n_warmup: usize, n_runs: usize) -> WallTimeStats {
    for _ in 0..n_warmup {
        f();
    }

    let mut times = Vec::with_capacity(n_runs);
    for _ in 0..n_runs {
        let t0 = std::time::Instant::now();
        f();
        times.push(t0.elapsed().as_secs_f64() * 1000.0);
    }

    if times.is_empty() {
        return WallTimeStats {
            mean_ms: 0.0,
            std_ms: 0.0,
            min_ms: 0.0,
            max_ms: 0.0,
        };
    }

    let mean = times.iter().sum::<f64>() / times.len() as f64;
    let var = times.iter().map(|t| (t - mean).powi(2)).sum::<f64>()
        / times.len().saturating_sub(1).max(1) as f64;
    let (mut min, mut max) = (times[0], times[0]);
    for &t in &times {
        if t < min {
            min = t;
        }
        if t > max {
            max = t;
        }
    }

    WallTimeStats {
        mean_ms: mean,
        std_ms: var.sqrt(),
        min_ms: min,
        max_ms: max,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    // --- count_flops ---

    #[test]
    fn linear_flops_hand_computed_with_bias() {
        let report = count_flops(
            &[LayerSpec::Linear {
                name: "l1".into(),
                in_features: 4,
                out_features: 8,
                bias: true,
            }],
            1,
        );
        // 2*4*8 + 8 = 72.
        assert_eq!(report.total_flops, 72);
        assert_eq!(report.total_params, 4 * 8 + 8);
        assert_eq!(report.layer_flops[0].layer_type, "Linear");
    }

    #[test]
    fn linear_flops_hand_computed_without_bias() {
        let report = count_flops(
            &[LayerSpec::Linear {
                name: "l1".into(),
                in_features: 4,
                out_features: 8,
                bias: false,
            }],
            1,
        );
        assert_eq!(report.total_flops, 64);
        assert_eq!(report.total_params, 32);
    }

    #[test]
    fn flops_scale_linearly_with_batch_size() {
        let layers = [LayerSpec::Linear {
            name: "l1".into(),
            in_features: 4,
            out_features: 8,
            bias: true,
        }];
        let single = count_flops(&layers, 1);
        let batched = count_flops(&layers, 8);
        assert_eq!(batched.total_flops, single.total_flops * 8);
        // Params never scale with batch size.
        assert_eq!(batched.total_params, single.total_params);
    }

    #[test]
    fn zero_batch_size_is_treated_as_one() {
        let layers = [LayerSpec::Linear {
            name: "l1".into(),
            in_features: 2,
            out_features: 2,
            bias: false,
        }];
        let zero = count_flops(&layers, 0);
        let one = count_flops(&layers, 1);
        assert_eq!(zero.total_flops, one.total_flops);
    }

    #[test]
    fn conv2d_flops_omits_output_spatial_size_matching_reference_behavior() {
        // 2 * C_in * C_out * K_h * K_w, no H_out*W_out factor (see module docs).
        let report = count_flops(
            &[LayerSpec::Conv2d {
                name: "c1".into(),
                in_channels: 3,
                out_channels: 16,
                kernel_h: 3,
                kernel_w: 3,
            }],
            1,
        );
        assert_eq!(report.total_flops, 2 * 3 * 16 * 3 * 3);
    }

    #[test]
    fn gru_cell_flops_hand_computed() {
        let report = count_flops(
            &[LayerSpec::GruCell {
                name: "g1".into(),
                input_size: 8,
                hidden_size: 16,
            }],
            1,
        );
        // 3 * 2 * (8 + 16) * 16 = 2304.
        assert_eq!(report.total_flops, 2304);
    }

    #[test]
    fn multi_layer_report_sums_and_preserves_order() {
        let report = count_flops(
            &[
                LayerSpec::Linear {
                    name: "a".into(),
                    in_features: 2,
                    out_features: 2,
                    bias: false,
                },
                LayerSpec::GruCell {
                    name: "b".into(),
                    input_size: 2,
                    hidden_size: 2,
                },
            ],
            1,
        );
        assert_eq!(report.layer_flops.len(), 2);
        assert_eq!(report.layer_flops[0].name, "a");
        assert_eq!(report.layer_flops[1].name, "b");
        assert_eq!(
            report.total_flops,
            report.layer_flops[0].flops + report.layer_flops[1].flops
        );
    }

    #[test]
    fn empty_layers_gives_zero_report() {
        let report = count_flops(&[], 4);
        assert_eq!(report.total_flops, 0);
        assert_eq!(report.total_params, 0);
        assert!(report.layer_flops.is_empty());
    }

    // --- measure_wall_time ---

    #[test]
    fn measure_wall_time_calls_warmup_and_runs_exact_counts() {
        let calls = Cell::new(0usize);
        let stats = measure_wall_time(|| calls.set(calls.get() + 1), 3, 5);
        assert_eq!(calls.get(), 8);
        assert!(stats.mean_ms >= 0.0);
        assert!(stats.min_ms <= stats.mean_ms);
        assert!(stats.mean_ms <= stats.max_ms);
        assert!(stats.std_ms >= 0.0);
    }

    #[test]
    fn measure_wall_time_zero_runs_gives_zeroed_stats() {
        let stats = measure_wall_time(|| (), 2, 0);
        assert_eq!(
            stats,
            WallTimeStats {
                mean_ms: 0.0,
                std_ms: 0.0,
                min_ms: 0.0,
                max_ms: 0.0
            }
        );
    }

    #[test]
    fn measure_wall_time_single_run_has_zero_std() {
        let stats = measure_wall_time(|| (), 0, 1);
        assert_eq!(stats.std_ms, 0.0);
    }
}
