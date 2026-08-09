//! PyO3 bindings for `prin_dynamics::coupling` and `prin_dynamics::pac`.

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_dynamics::coupling::{CouplingError, CouplingMode, Topology};
use prin_dynamics::pac::{PacError, PhaseAmplitudeCoupling};

use super::state::PySeed;

fn coupling_err_to_py(err: CouplingError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

fn pac_err_to_py(err: PacError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

/// Coupling semantics for oscillator models.
#[pyclass(name = "CouplingMode", module = "prin._prin_core", skip_from_py_object)]
#[derive(Clone, Debug)]
pub struct PyCouplingMode {
    pub(crate) inner: CouplingMode,
}

#[pymethods]
impl PyCouplingMode {
    #[staticmethod]
    fn mean_field() -> Self {
        Self {
            inner: CouplingMode::MeanField,
        }
    }

    #[staticmethod]
    #[pyo3(signature = (matrix=None))]
    fn full(matrix: Option<PyReadonlyArray1<f64>>) -> PyResult<Self> {
        let mat = match matrix {
            Some(arr) => Some(
                arr.as_slice()
                    .map_err(|_| PyValueError::new_err("matrix must be contiguous"))?
                    .to_vec(),
            ),
            None => None,
        };
        Ok(Self {
            inner: CouplingMode::Full { matrix: mat },
        })
    }

    #[staticmethod]
    #[pyo3(signature = (k=None))]
    fn sparse_knn(k: Option<usize>) -> Self {
        Self {
            inner: CouplingMode::SparseKnn { k },
        }
    }

    fn variant(&self) -> &'static str {
        match &self.inner {
            CouplingMode::MeanField => "mean_field",
            CouplingMode::Full { .. } => "full",
            CouplingMode::SparseKnn { .. } => "sparse_knn",
        }
    }

    fn __repr__(&self) -> String {
        match &self.inner {
            CouplingMode::MeanField => "CouplingMode.mean_field()".into(),
            CouplingMode::Full { matrix } => if matrix.is_some() {
                "CouplingMode.full(matrix=...)"
            } else {
                "CouplingMode.full()"
            }
            .into(),
            CouplingMode::SparseKnn { k } => format!("CouplingMode.sparse_knn(k={k:?})"),
        }
    }
}

/// Structured coupling topology patterns producing N×N matrices.
#[pyclass(name = "Topology", module = "prin._prin_core", skip_from_py_object)]
#[derive(Clone, Debug)]
pub struct PyTopology {
    inner: Topology,
}

#[pymethods]
impl PyTopology {
    #[staticmethod]
    fn all_to_all() -> Self {
        Self {
            inner: Topology::AllToAll,
        }
    }

    #[staticmethod]
    fn ring(k_ring: usize) -> Self {
        Self {
            inner: Topology::Ring { k_ring },
        }
    }

    #[staticmethod]
    fn small_world(k_ring: usize, rewire_prob: f64, seed: &PySeed) -> PyResult<Self> {
        Ok(Self {
            inner: Topology::SmallWorld {
                k_ring,
                rewire_prob,
                seed: seed.inner.clone(),
            },
        })
    }

    fn build_matrix<'py>(
        &self,
        py: Python<'py>,
        n: usize,
        coupling_strength: f64,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let mat = self
            .inner
            .build_matrix(n, coupling_strength)
            .map_err(coupling_err_to_py)?;
        Ok(PyArray1::from_vec(py, mat))
    }

    fn __repr__(&self) -> String {
        match &self.inner {
            Topology::AllToAll => "Topology.all_to_all()".into(),
            Topology::Ring { k_ring } => format!("Topology.ring(k_ring={k_ring})"),
            Topology::SmallWorld {
                k_ring,
                rewire_prob,
                ..
            } => {
                format!("Topology.small_world(k_ring={k_ring}, rewire_prob={rewire_prob})")
            }
        }
    }
}

/// Phase–amplitude coupling between oscillator bands.
#[pyclass(
    name = "PhaseAmplitudeCoupling",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyPhaseAmplitudeCoupling {
    inner: PhaseAmplitudeCoupling,
}

#[pymethods]
impl PyPhaseAmplitudeCoupling {
    #[new]
    fn py_new(modulation_depth: f64) -> PyResult<Self> {
        Ok(Self {
            inner: PhaseAmplitudeCoupling::new(modulation_depth).map_err(pac_err_to_py)?,
        })
    }

    #[getter]
    fn modulation_depth(&self) -> f64 {
        self.inner.modulation_depth()
    }

    fn modulate<'py>(
        &self,
        py: Python<'py>,
        slow_phase: PyReadonlyArray1<f64>,
        fast_amplitude: PyReadonlyArray1<f64>,
        offset: f64,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let sp = slow_phase
            .as_slice()
            .map_err(|_| PyValueError::new_err("slow_phase must be contiguous"))?;
        let fa = fast_amplitude
            .as_slice()
            .map_err(|_| PyValueError::new_err("fast_amplitude must be contiguous"))?;
        let result = self.inner.modulate(sp, fa, offset).map_err(pac_err_to_py)?;
        Ok(PyArray1::from_vec(py, result))
    }

    fn __repr__(&self) -> String {
        format!(
            "PhaseAmplitudeCoupling(modulation_depth={})",
            self.inner.modulation_depth()
        )
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyCouplingMode>()?;
    m.add_class::<PyTopology>()?;
    m.add_class::<PyPhaseAmplitudeCoupling>()?;
    Ok(())
}
