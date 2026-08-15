//! Cross-backend equivalence testing harness.
//!
//! Provides [`EquivalenceHarness`] which generates deterministic test cases
//! and verifies that all available backends produce matching results for the
//! mean-field RK4 step. The CPU reference (`step_cpu`) is the numerical
//! authority; GPU backends must match within documented `f32` tolerances.
//!
//! This module is always compiled (it depends only on the always-available CPU
//! reference). GPU-specific comparisons are gated by `#[cfg(feature)]` inside
//! the test methods.

use crate::mean_field_rk4::{step_cpu, MeanFieldRk4Output, MeanFieldRk4Params};

/// Default relative tolerance for cross-backend `f32` comparisons.
///
/// Matches the GPU-vs-CPU tolerance documented in the Testing Standards §3.
pub const DEFAULT_RTOL: f32 = 1e-5;

/// Default absolute tolerance for cross-backend `f32` comparisons.
pub const DEFAULT_ATOL: f32 = 1e-6;

/// A deterministic test case for kernel equivalence testing.
///
/// Contains oscillator state and parameters suitable for exercising all
/// code paths in the mean-field RK4 step.
#[derive(Clone, Debug)]
pub struct EquivalenceCase {
    /// Human-readable label for test output.
    pub label: String,
    /// Phase angles in radians, shape `(N,)`.
    pub phase: Vec<f32>,
    /// Amplitudes, shape `(N,)`.
    pub amplitude: Vec<f32>,
    /// Natural frequencies, shape `(N,)`.
    pub frequency: Vec<f32>,
    /// Model parameters.
    pub params: MeanFieldRk4Params,
}

/// Cross-backend equivalence testing harness.
///
/// Generates deterministic test cases and verifies that all available backends
/// produce matching results. The CPU reference is the numerical authority.
pub struct EquivalenceHarness {
    cases: Vec<EquivalenceCase>,
}

impl EquivalenceHarness {
    /// Create a new harness with the default test-case suite.
    ///
    /// The suite covers: small N, large N, zero coupling, strong coupling,
    /// single oscillator, and edge-case amplitudes.
    pub fn new() -> Self {
        Self {
            cases: Self::default_cases(),
        }
    }

    /// Create a harness with custom test cases.
    pub fn with_cases(cases: Vec<EquivalenceCase>) -> Self {
        Self { cases }
    }

    /// Return a reference to the test cases.
    pub fn cases(&self) -> &[EquivalenceCase] {
        &self.cases
    }

    /// Run the CPU reference on all cases and return the results.
    pub fn run_cpu_reference(&self) -> Vec<(EquivalenceCase, MeanFieldRk4Output)> {
        self.cases
            .iter()
            .map(|case| {
                let result = step_cpu(&case.phase, &case.amplitude, &case.frequency, &case.params)
                    .unwrap_or_else(|e| panic!("CPU reference failed for '{}': {e}", case.label));
                (case.clone(), result)
            })
            .collect()
    }

    /// Verify that a backend's output matches the CPU reference for all cases.
    ///
    /// Uses `rtol = DEFAULT_RTOL` and `atol = DEFAULT_ATOL`.
    ///
    /// # Returns
    ///
    /// `Ok(())` if all cases match within tolerance, or `Err(message)` with
    /// the first mismatch description.
    pub fn verify_against_reference(
        &self,
        backend_name: &str,
        backend_fn: impl Fn(
            &[f32],
            &[f32],
            &[f32],
            &MeanFieldRk4Params,
        ) -> Result<MeanFieldRk4Output, String>,
    ) -> Result<(), String> {
        self.verify_against_reference_with_tolerance(
            backend_name,
            backend_fn,
            DEFAULT_RTOL,
            DEFAULT_ATOL,
        )
    }

    /// Verify with custom tolerances.
    pub fn verify_against_reference_with_tolerance(
        &self,
        backend_name: &str,
        backend_fn: impl Fn(
            &[f32],
            &[f32],
            &[f32],
            &MeanFieldRk4Params,
        ) -> Result<MeanFieldRk4Output, String>,
        rtol: f32,
        atol: f32,
    ) -> Result<(), String> {
        for case in &self.cases {
            let (ref_p, ref_a, ref_f) =
                step_cpu(&case.phase, &case.amplitude, &case.frequency, &case.params)
                    .map_err(|e| format!("CPU reference failed for '{}': {e}", case.label))?;

            let (test_p, test_a, test_f) =
                backend_fn(&case.phase, &case.amplitude, &case.frequency, &case.params)?;

            assert_allclose(
                &test_p,
                &ref_p,
                rtol,
                atol,
                &format!("{backend_name} phase mismatch ({})", case.label),
            )?;
            assert_allclose(
                &test_a,
                &ref_a,
                rtol,
                atol,
                &format!("{backend_name} amplitude mismatch ({})", case.label),
            )?;
            assert_allclose(
                &test_f,
                &ref_f,
                rtol,
                atol,
                &format!("{backend_name} frequency mismatch ({})", case.label),
            )?;
        }
        Ok(())
    }

    /// Generate the default deterministic test-case suite.
    fn default_cases() -> Vec<EquivalenceCase> {
        let default_params = MeanFieldRk4Params {
            k: 2.0,
            decay: 0.1,
            gamma: 0.01,
            dt: 0.01,
        };

        vec![
            // Small N: basic functionality.
            EquivalenceCase {
                label: "small_n_16".into(),
                phase: (0..16).map(|i| 0.1 * i as f32).collect(),
                amplitude: vec![1.0; 16],
                frequency: (0..16).map(|i| 0.05 * (i as f32 - 8.0)).collect(),
                params: default_params,
            },
            // Medium N: typical workload.
            EquivalenceCase {
                label: "medium_n_256".into(),
                phase: (0..256)
                    .map(|i| (0.1 * i as f32).rem_euclid(core::f32::consts::TAU))
                    .collect(),
                amplitude: (0..256).map(|i| 0.5 + 0.5 * (i as f32 / 256.0)).collect(),
                frequency: (0..256).map(|i| 0.01 * (i as f32 - 128.0)).collect(),
                params: default_params,
            },
            // Zero coupling: free-running oscillators.
            EquivalenceCase {
                label: "zero_coupling".into(),
                phase: (0..32).map(|i| 0.2 * i as f32).collect(),
                amplitude: vec![1.0; 32],
                frequency: (0..32).map(|i| 0.1 * (i as f32 - 16.0)).collect(),
                params: MeanFieldRk4Params {
                    k: 0.0,
                    ..default_params
                },
            },
            // Strong coupling.
            EquivalenceCase {
                label: "strong_coupling".into(),
                phase: (0..64).map(|i| 0.1 * i as f32).collect(),
                amplitude: vec![1.0; 64],
                frequency: vec![0.0; 64],
                params: MeanFieldRk4Params {
                    k: 10.0,
                    ..default_params
                },
            },
            // Single oscillator.
            EquivalenceCase {
                label: "single_oscillator".into(),
                phase: vec![1.0],
                amplitude: vec![1.5],
                frequency: vec![0.5],
                params: default_params,
            },
            // Near-boundary amplitudes.
            EquivalenceCase {
                label: "boundary_amplitudes".into(),
                phase: vec![0.0, 1.0, 2.0, 3.0],
                amplitude: vec![1e-6, 0.5, 5.0, 10.0],
                frequency: vec![-0.5, 0.0, 0.5, 1.0],
                params: default_params,
            },
        ]
    }
}

impl Default for EquivalenceHarness {
    fn default() -> Self {
        Self::new()
    }
}

/// Check that two `f32` slices are element-wise close.
///
/// For each pair `(actual, expected)`:
/// `|actual - expected| <= atol + rtol * |expected|`
///
/// # Returns
///
/// `Ok(())` if all pairs are within tolerance, or `Err(description)` with the
/// first mismatch.
pub fn assert_allclose(
    actual: &[f32],
    expected: &[f32],
    rtol: f32,
    atol: f32,
    context: &str,
) -> Result<(), String> {
    if actual.len() != expected.len() {
        return Err(format!(
            "{context}: length mismatch (actual={}, expected={})",
            actual.len(),
            expected.len()
        ));
    }
    for (i, (a, e)) in actual.iter().zip(expected).enumerate() {
        let tol = atol + rtol * e.abs();
        if (a - e).abs() > tol {
            return Err(format!(
                "{context}: element {i}: actual={a}, expected={e}, tolerance={tol}"
            ));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn harness_default_cases_are_non_empty() {
        let harness = EquivalenceHarness::new();
        assert!(!harness.cases().is_empty());
    }

    #[test]
    fn harness_cpu_reference_runs_all_cases() {
        let harness = EquivalenceHarness::new();
        let results = harness.run_cpu_reference();
        assert_eq!(results.len(), harness.cases().len());
        for (case, (p, a, f)) in &results {
            assert_eq!(
                p.len(),
                case.phase.len(),
                "phase length mismatch: {}",
                case.label
            );
            assert_eq!(
                a.len(),
                case.amplitude.len(),
                "amp length mismatch: {}",
                case.label
            );
            assert_eq!(
                f.len(),
                case.frequency.len(),
                "freq length mismatch: {}",
                case.label
            );
        }
    }

    #[test]
    fn cpu_self_equivalence() {
        let harness = EquivalenceHarness::new();
        let result = harness.verify_against_reference("cpu-self", |p, a, f, params| {
            step_cpu(p, a, f, params).map_err(|e| e.to_string())
        });
        assert!(result.is_ok(), "CPU self-equivalence failed: {result:?}");
    }

    #[test]
    fn assert_allclose_exact_match() {
        let a = vec![1.0_f32, 2.0, 3.0];
        let b = vec![1.0_f32, 2.0, 3.0];
        assert!(assert_allclose(&a, &b, 0.0, 0.0, "test").is_ok());
    }

    #[test]
    fn assert_allclose_within_tolerance() {
        let a = vec![1.0_f32, 2.0, 3.0];
        let b = vec![1.0 + 1e-7, 2.0 - 1e-7, 3.0 + 1e-7];
        assert!(assert_allclose(&a, &b, 1e-5, 1e-6, "test").is_ok());
    }

    #[test]
    fn assert_allclose_detects_mismatch() {
        let a = vec![1.0_f32, 2.0, 3.0];
        let b = vec![1.0_f32, 2.1, 3.0];
        let result = assert_allclose(&a, &b, 1e-5, 1e-6, "test");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("element 1"));
    }

    #[test]
    fn assert_allclose_length_mismatch() {
        let a = vec![1.0_f32];
        let b = vec![1.0_f32, 2.0];
        let result = assert_allclose(&a, &b, 1e-5, 1e-6, "test");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("length mismatch"));
    }

    #[test]
    fn custom_cases_harness() {
        let case = EquivalenceCase {
            label: "custom".into(),
            phase: vec![0.5],
            amplitude: vec![1.0],
            frequency: vec![0.0],
            params: MeanFieldRk4Params {
                k: 1.0,
                decay: 0.0,
                gamma: 0.0,
                dt: 0.01,
            },
        };
        let harness = EquivalenceHarness::with_cases(vec![case]);
        assert_eq!(harness.cases().len(), 1);
        let result = harness.verify_against_reference("cpu-self", |p, a, f, params| {
            step_cpu(p, a, f, params).map_err(|e| e.to_string())
        });
        assert!(result.is_ok());
    }

    #[test]
    fn harness_default_impl() {
        let harness = EquivalenceHarness::default();
        assert!(!harness.cases().is_empty());
        assert_eq!(
            harness.cases().len(),
            EquivalenceHarness::new().cases().len()
        );
    }

    #[test]
    fn verify_detects_genuine_backend_mismatch() {
        let harness = EquivalenceHarness::with_cases(vec![EquivalenceCase {
            label: "mismatch_amp".into(),
            phase: vec![0.5],
            amplitude: vec![1.0],
            frequency: vec![0.0],
            params: MeanFieldRk4Params {
                k: 1.0,
                decay: 0.0,
                gamma: 0.0,
                dt: 0.01,
            },
        }]);
        let phase_ok_amp_wrong =
            |p: &[f32], _a: &[f32], f: &[f32], _params: &MeanFieldRk4Params| {
                let (ref_p, _ref_a, ref_f) = step_cpu(p, &[1.0], f, _params).unwrap();
                Ok((ref_p, vec![99.0], ref_f))
            };
        let result = harness.verify_against_reference("fake-amp", phase_ok_amp_wrong);
        assert!(result.is_err());
        let msg = result.unwrap_err();
        assert!(
            msg.contains("fake-amp"),
            "error should name the backend: {msg}"
        );
        assert!(
            msg.contains("amplitude"),
            "error should name amplitude: {msg}"
        );

        let phase_ok_freq_wrong =
            |p: &[f32], a: &[f32], _f: &[f32], _params: &MeanFieldRk4Params| {
                let (ref_p, ref_a, _ref_f) = step_cpu(p, a, &[0.0], _params).unwrap();
                Ok((ref_p, ref_a, vec![99.0]))
            };
        let result2 = harness.verify_against_reference("fake-freq", phase_ok_freq_wrong);
        assert!(result2.is_err());
        let msg2 = result2.unwrap_err();
        assert!(
            msg2.contains("frequency"),
            "error should name frequency: {msg2}"
        );
    }

    #[test]
    fn verify_with_tolerance_propagates_backend_error() {
        let harness = EquivalenceHarness::with_cases(vec![EquivalenceCase {
            label: "tiny".into(),
            phase: vec![0.5],
            amplitude: vec![1.0],
            frequency: vec![0.0],
            params: MeanFieldRk4Params {
                k: 1.0,
                decay: 0.0,
                gamma: 0.0,
                dt: 0.01,
            },
        }]);
        let failing_backend = |_p: &[f32], _a: &[f32], _f: &[f32], _params: &MeanFieldRk4Params| {
            Err("backend exploded".to_string())
        };
        let result = harness.verify_against_reference_with_tolerance(
            "bad-backend",
            failing_backend,
            DEFAULT_RTOL,
            DEFAULT_ATOL,
        );
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("backend exploded"));
    }
}
