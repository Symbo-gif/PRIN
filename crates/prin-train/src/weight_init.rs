//! Oscillator-aware parameter initialization.
//!
//! Coupling matrices are symmetrized, scaled, and stripped of self-coupling;
//! projection matrices use deterministic Xavier-uniform initialization; biases
//! are zeroed. Random draws are threaded through [`prin_dynamics::Seed`].

use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::support::{seeded_uniform, validate_finite, xavier_bound};

/// Initialization role for a two-dimensional parameter tensor.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OscillatoryWeightKind {
    /// Symmetric zero-diagonal oscillator coupling.
    Coupling,
    /// Xavier-uniform linear projection weight.
    Projection,
}

/// Initialize a two-dimensional oscillator-network parameter.
///
/// `Coupling` uses the reference transform
/// `(parameter + parameterᵀ) / 2 * coupling_scale` and zeros the diagonal.
/// `Projection` replaces the tensor with a deterministic Xavier-uniform draw
/// using `proj_gain` and the supplied project [`Seed`].
///
/// # Errors
///
/// Returns [`TrainError::ShapeMismatch`] for a non-square coupling matrix or
/// [`TrainError::NonFiniteParameter`] for a non-finite scale/gain.
pub fn oscillatory_weight_init<B: Backend>(
    parameter: Tensor<B, 2>,
    kind: OscillatoryWeightKind,
    coupling_scale: f64,
    proj_gain: f64,
    seed: &mut Seed,
) -> Result<Tensor<B, 2>, TrainError> {
    validate_finite("coupling_scale", coupling_scale)?;
    validate_finite("proj_gain", proj_gain)?;
    let [rows, cols] = parameter.dims();
    match kind {
        OscillatoryWeightKind::Coupling => {
            if rows != cols {
                return Err(TrainError::ShapeMismatch {
                    name: "coupling",
                    expected: vec![rows, rows],
                    got: vec![rows, cols],
                });
            }
            let device = parameter.device();
            let mask =
                Tensor::<B, 2>::ones([rows, rows], &device) - Tensor::<B, 2>::eye(rows, &device);
            Ok(
                ((parameter.clone() + parameter.transpose()) / 2.0).mul_scalar(coupling_scale)
                    * mask,
            )
        }
        OscillatoryWeightKind::Projection => {
            let device = parameter.device();
            let bound = xavier_bound(rows, cols, proj_gain);
            Ok(seeded_uniform([rows, cols], -bound, bound, &device, seed))
        }
    }
}

/// Replace a one-dimensional bias parameter with zeros.
pub fn zero_bias<B: Backend>(parameter: Tensor<B, 1>) -> Tensor<B, 1> {
    Tensor::zeros(parameter.dims(), &parameter.device())
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::NdArray;
    use burn::tensor::TensorData;

    type TestBackend = NdArray<f64>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    #[test]
    fn coupling_matches_reference_symmetry_scale_and_zero_diagonal() {
        let parameter = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![1.0, 2.0, 3.0, 4.0], vec![2, 2]),
            &device(),
        );
        let mut seed = Seed::new(0, 0);
        let got = oscillatory_weight_init(
            parameter,
            OscillatoryWeightKind::Coupling,
            0.1,
            0.5,
            &mut seed,
        )
        .unwrap()
        .to_data()
        .to_vec::<f64>()
        .unwrap();
        assert_eq!(got, vec![0.0, 0.25, 0.25, 0.0]);
    }

    #[test]
    fn projection_is_deterministic_and_within_xavier_bound() {
        let parameter = Tensor::<TestBackend, 2>::zeros([3, 5], &device());
        let mut first_seed = Seed::new(7, 11);
        let first = oscillatory_weight_init(
            parameter.clone(),
            OscillatoryWeightKind::Projection,
            0.1,
            0.5,
            &mut first_seed,
        )
        .unwrap()
        .to_data()
        .to_vec::<f64>()
        .unwrap();
        let mut second_seed = Seed::new(7, 11);
        let second = oscillatory_weight_init(
            parameter,
            OscillatoryWeightKind::Projection,
            0.1,
            0.5,
            &mut second_seed,
        )
        .unwrap()
        .to_data()
        .to_vec::<f64>()
        .unwrap();
        assert_eq!(first, second);
        let bound = xavier_bound(3, 5, 0.5);
        assert!(first.iter().all(|value| value.abs() <= bound));
    }

    #[test]
    fn bias_is_zeroed_and_bad_coupling_shape_is_rejected() {
        let bias = Tensor::<TestBackend, 1>::ones([4], &device());
        assert_eq!(
            zero_bias(bias).to_data().to_vec::<f64>().unwrap(),
            vec![0.0; 4]
        );
        let mut seed = Seed::new(0, 0);
        let nonsquare = Tensor::<TestBackend, 2>::zeros([2, 3], &device());
        assert!(matches!(
            oscillatory_weight_init(
                nonsquare,
                OscillatoryWeightKind::Coupling,
                0.1,
                0.5,
                &mut seed,
            )
            .unwrap_err(),
            TrainError::ShapeMismatch {
                name: "coupling",
                ..
            }
        ));
    }
}
