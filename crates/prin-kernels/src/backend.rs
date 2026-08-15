//! Compute backend abstraction for `prin-kernels`.
//!
//! The [`Device`] enum identifies the available compute backends (CUDA, wgpu,
//! CPU). [`backend_priority`] returns the dispatch order for a requested device,
//! enabling graceful fallback when the preferred backend is unavailable.
//!
//! This module is independent of CubeCL — it defines *what* backends exist and
//! their priority, not *how* they are instantiated. Runtime instantiation
//! happens in the `cubecl` submodule of `mean_field_rk4` (gated by `cuda` /
//! `wgpu` features).

use thiserror::Error;

/// A compute backend device.
///
/// The variant order reflects the performance preference: CUDA (fastest,
/// requires NVIDIA GPU) > wgpu (portable GPU via Vulkan/Metal/DX12) > CPU
/// (always available, used as the numerical authority and fallback).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Device {
    /// NVIDIA CUDA GPU via `cubecl-cuda`.
    Cuda,
    /// Portable GPU via `cubecl-wgpu` (Vulkan / Metal / DX12).
    Wgpu,
    /// CPU via `cubecl-cpu` or the native Rust reference path.
    Cpu,
}

/// Errors raised by backend selection and dispatch.
#[derive(Debug, Error)]
pub enum BackendError {
    /// No backend could be initialised.
    #[error("no compute backend available: {message}")]
    NoBackendAvailable {
        /// Human-readable description of why all backends failed.
        message: String,
    },
}

/// Return the backend priority list for `preferred`, most-preferred first.
///
/// The caller tries each entry in order; the first backend that initialises
/// successfully is used. This decouples *preference* from *availability*:
/// the caller handles the instantiation and fallback logic.
///
/// # Examples
///
/// ```
/// use prin_kernels::backend::{backend_priority, Device};
///
/// let order = backend_priority(Device::Cuda);
/// assert_eq!(order[0], Device::Cuda);
/// assert_eq!(order[1], Device::Wgpu);
/// assert_eq!(order[2], Device::Cpu);
///
/// let order = backend_priority(Device::Cpu);
/// assert_eq!(order, [Device::Cpu]);
/// ```
pub fn backend_priority(preferred: Device) -> Vec<Device> {
    match preferred {
        Device::Cuda => vec![Device::Cuda, Device::Wgpu, Device::Cpu],
        Device::Wgpu => vec![Device::Wgpu, Device::Cpu],
        Device::Cpu => vec![Device::Cpu],
    }
}

/// Return the default auto-detection order: CUDA → wgpu → CPU.
///
/// Use this when the caller has no preference and wants the fastest available
/// backend. CPU is always last and always available (it is the numerical
/// authority).
pub fn auto_detect_order() -> Vec<Device> {
    vec![Device::Cuda, Device::Wgpu, Device::Cpu]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cuda_priority_includes_all_backends() {
        let order = backend_priority(Device::Cuda);
        assert_eq!(order, vec![Device::Cuda, Device::Wgpu, Device::Cpu]);
    }

    #[test]
    fn wgpu_priority_falls_back_to_cpu_only() {
        let order = backend_priority(Device::Wgpu);
        assert_eq!(order, vec![Device::Wgpu, Device::Cpu]);
    }

    #[test]
    fn cpu_priority_is_cpu_only() {
        let order = backend_priority(Device::Cpu);
        assert_eq!(order, vec![Device::Cpu]);
    }

    #[test]
    fn auto_detect_starts_with_cuda() {
        let order = auto_detect_order();
        assert_eq!(order[0], Device::Cuda);
        assert_eq!(order[1], Device::Wgpu);
        assert_eq!(order[2], Device::Cpu);
    }

    #[test]
    fn auto_detect_always_ends_with_cpu() {
        let order = auto_detect_order();
        assert_eq!(*order.last().unwrap(), Device::Cpu);
    }

    #[test]
    fn device_clone_and_eq() {
        let d = Device::Cuda;
        let d2 = d;
        assert_eq!(d, d2);
        assert_ne!(Device::Cuda, Device::Wgpu);
    }

    #[test]
    fn device_debug_format() {
        assert_eq!(format!("{:?}", Device::Cuda), "Cuda");
        assert_eq!(format!("{:?}", Device::Wgpu), "Wgpu");
        assert_eq!(format!("{:?}", Device::Cpu), "Cpu");
    }

    #[test]
    fn backend_error_display() {
        let err = BackendError::NoBackendAvailable {
            message: "test failure".into(),
        };
        assert!(err.to_string().contains("test failure"));
    }

    #[test]
    fn priority_lists_are_non_empty() {
        for device in [Device::Cuda, Device::Wgpu, Device::Cpu] {
            assert!(!backend_priority(device).is_empty());
        }
    }

    #[test]
    fn priority_lists_always_end_with_cpu() {
        for device in [Device::Cuda, Device::Wgpu, Device::Cpu] {
            let order = backend_priority(device);
            assert_eq!(*order.last().unwrap(), Device::Cpu);
        }
    }
}
