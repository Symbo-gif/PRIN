//! Preallocated buffer pools for kernel computations.
//!
//! Buffer pools eliminate per-step heap allocations by reusing working memory
//! across repeated kernel invocations. Two pool types are provided:
//!
//! - [`MeanFieldRk4Buffers`] — CPU-side `Vec<f32>` buffers for the mean-field
//!   RK4 step. Eliminates 15+ per-step allocations (k1–k4 intermediates,
//!   stage states, output buffers, and derivative temporaries).
//! - `CubeclBufferPool` — GPU-side CubeCL `Handle`s for working and output
//!   buffers. Eliminates 15 per-step `client.empty()` calls; only the 4 input
//!   handles (which carry fresh host data) are created per step.
//!
//! Both pools grow to the required size on first use and reuse their capacity
//! for all subsequent steps with the same or smaller oscillator count.

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
use cubecl::prelude::*;
#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
use cubecl::server::Handle;

// ── CPU buffer pool ──────────────────────────────────────────────────────

/// Preallocated CPU buffers for the mean-field RK4 step.
///
/// Holds all intermediate `Vec<f32>` buffers that `step_cpu` would otherwise
/// allocate fresh on every call. The pool grows to the required size on first
/// use and reuses its capacity for all subsequent steps.
///
/// # Invariants
///
/// After [`clear`](Self::clear), every buffer has `len() == 0` and
/// `capacity() >= n` (where `n` is the oscillator count from the first call).
/// The `step_cpu` function pushes exactly `n` elements into each buffer before
/// reading, so stale data from a previous call is never observed.
pub struct MeanFieldRk4Buffers {
    /// Current capacity (oscillator count this pool was sized for).
    n: usize,
    // k1 intermediates
    pub(crate) k1_phase: Vec<f32>,
    pub(crate) k1_amp: Vec<f32>,
    pub(crate) k1_freq: Vec<f32>,
    // k2 intermediates
    pub(crate) k2_phase: Vec<f32>,
    pub(crate) k2_amp: Vec<f32>,
    pub(crate) k2_freq: Vec<f32>,
    // k3 intermediates
    pub(crate) k3_phase: Vec<f32>,
    pub(crate) k3_amp: Vec<f32>,
    pub(crate) k3_freq: Vec<f32>,
    // k4 intermediates
    pub(crate) k4_phase: Vec<f32>,
    pub(crate) k4_amp: Vec<f32>,
    pub(crate) k4_freq: Vec<f32>,
    // Stage intermediate state (s = base + dt_scale * k_prev)
    pub(crate) stage_phase: Vec<f32>,
    pub(crate) stage_amp: Vec<f32>,
    pub(crate) stage_freq: Vec<f32>,
    // Output buffers
    pub(crate) out_phase: Vec<f32>,
    pub(crate) out_amp: Vec<f32>,
    pub(crate) out_freq: Vec<f32>,
}

impl MeanFieldRk4Buffers {
    /// Create a new buffer pool sized for `n` oscillators.
    ///
    /// All internal buffers are allocated with capacity `n` and length 0.
    pub fn new(n: usize) -> Self {
        Self {
            n,
            k1_phase: Vec::with_capacity(n),
            k1_amp: Vec::with_capacity(n),
            k1_freq: Vec::with_capacity(n),
            k2_phase: Vec::with_capacity(n),
            k2_amp: Vec::with_capacity(n),
            k2_freq: Vec::with_capacity(n),
            k3_phase: Vec::with_capacity(n),
            k3_amp: Vec::with_capacity(n),
            k3_freq: Vec::with_capacity(n),
            k4_phase: Vec::with_capacity(n),
            k4_amp: Vec::with_capacity(n),
            k4_freq: Vec::with_capacity(n),
            stage_phase: Vec::with_capacity(n),
            stage_amp: Vec::with_capacity(n),
            stage_freq: Vec::with_capacity(n),
            out_phase: Vec::with_capacity(n),
            out_amp: Vec::with_capacity(n),
            out_freq: Vec::with_capacity(n),
        }
    }

    /// Clear all intermediate buffers, preserving allocated capacity.
    ///
    /// After this call every buffer has `len() == 0`. Call before each
    /// `step_cpu` invocation to ensure a clean slate.
    pub fn clear(&mut self) {
        self.k1_phase.clear();
        self.k1_amp.clear();
        self.k1_freq.clear();
        self.k2_phase.clear();
        self.k2_amp.clear();
        self.k2_freq.clear();
        self.k3_phase.clear();
        self.k3_amp.clear();
        self.k3_freq.clear();
        self.k4_phase.clear();
        self.k4_amp.clear();
        self.k4_freq.clear();
        self.stage_phase.clear();
        self.stage_amp.clear();
        self.stage_freq.clear();
        self.out_phase.clear();
        self.out_amp.clear();
        self.out_freq.clear();
    }

    /// The oscillator count this pool was sized for.
    pub fn capacity(&self) -> usize {
        self.n
    }
}

// ── CubeCL GPU buffer pool ───────────────────────────────────────────────

/// Preallocated CubeCL device handles for the mean-field RK4 step.
///
/// Holds the 15 working + output device [`Handle`]s that would otherwise be
/// created via `client.empty()` on every step. Only the 4 input handles
/// (base_phase, base_amp, base_freq, k_zero) are created fresh each step
/// because they carry host data via `client.create_from_slice`.
///
/// # Safety
///
/// All handles are allocated with `byte_len = n * size_of::<f32>()` bytes.
/// The caller must ensure that kernel launches use `n` as the element count
/// when constructing `ArrayArg` from these handles.
#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
pub struct CubeclBufferPool<R: Runtime> {
    /// Oscillator count this pool was sized for.
    n: usize,
    // k1 intermediates
    pub(crate) k1_phase: Handle,
    pub(crate) k1_amp: Handle,
    pub(crate) k1_freq: Handle,
    // k2 intermediates
    pub(crate) k2_phase: Handle,
    pub(crate) k2_amp: Handle,
    pub(crate) k2_freq: Handle,
    // k3 intermediates
    pub(crate) k3_phase: Handle,
    pub(crate) k3_amp: Handle,
    pub(crate) k3_freq: Handle,
    // k4 intermediates
    pub(crate) k4_phase: Handle,
    pub(crate) k4_amp: Handle,
    pub(crate) k4_freq: Handle,
    // Stage intermediate state
    pub(crate) stage_phase: Handle,
    pub(crate) stage_amp: Handle,
    pub(crate) stage_freq: Handle,
    // Output
    pub(crate) out_phase: Handle,
    pub(crate) out_amp: Handle,
    pub(crate) out_freq: Handle,
    /// Marker for the runtime type.
    _runtime: core::marker::PhantomData<R>,
}

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
impl<R: Runtime> CubeclBufferPool<R> {
    /// Allocate all 18 working + output device handles.
    ///
    /// Each handle has `n * size_of::<f32>()` bytes.
    pub fn new(client: &ComputeClient<R>, n: usize) -> Self {
        let byte_len = n * core::mem::size_of::<f32>();
        let empty = || client.empty(byte_len);
        Self {
            n,
            k1_phase: empty(),
            k1_amp: empty(),
            k1_freq: empty(),
            k2_phase: empty(),
            k2_amp: empty(),
            k2_freq: empty(),
            k3_phase: empty(),
            k3_amp: empty(),
            k3_freq: empty(),
            k4_phase: empty(),
            k4_amp: empty(),
            k4_freq: empty(),
            stage_phase: empty(),
            stage_amp: empty(),
            stage_freq: empty(),
            out_phase: empty(),
            out_amp: empty(),
            out_freq: empty(),
            _runtime: core::marker::PhantomData,
        }
    }

    /// The oscillator count this pool was sized for.
    pub fn capacity(&self) -> usize {
        self.n
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cpu_pool_new_allocates_correct_capacity() {
        let pool = MeanFieldRk4Buffers::new(1024);
        assert_eq!(pool.capacity(), 1024);
        assert_eq!(pool.k1_phase.len(), 0);
        assert!(pool.k1_phase.capacity() >= 1024);
        assert!(pool.out_freq.capacity() >= 1024);
    }

    #[test]
    fn cpu_pool_clear_resets_lengths() {
        let mut pool = MeanFieldRk4Buffers::new(8);
        pool.k1_phase.extend_from_slice(&[1.0; 8]);
        pool.out_phase.extend_from_slice(&[2.0; 8]);
        assert_eq!(pool.k1_phase.len(), 8);
        assert_eq!(pool.out_phase.len(), 8);

        pool.clear();
        assert_eq!(pool.k1_phase.len(), 0);
        assert_eq!(pool.out_phase.len(), 0);
        // Capacity is preserved.
        assert!(pool.k1_phase.capacity() >= 8);
        assert!(pool.out_phase.capacity() >= 8);
    }

    #[test]
    fn cpu_pool_reuse_after_clear() {
        let mut pool = MeanFieldRk4Buffers::new(4);

        // Simulate a step: push data, then clear.
        pool.k1_phase.extend_from_slice(&[1.0, 2.0, 3.0, 4.0]);
        pool.out_phase.extend_from_slice(&[5.0, 6.0, 7.0, 8.0]);
        pool.clear();

        // Reuse: push different data.
        pool.k1_phase.extend_from_slice(&[10.0, 20.0, 30.0, 40.0]);
        assert_eq!(pool.k1_phase, &[10.0, 20.0, 30.0, 40.0]);
    }

    #[test]
    fn cpu_pool_zero_sized() {
        let pool = MeanFieldRk4Buffers::new(0);
        assert_eq!(pool.capacity(), 0);
    }

    #[test]
    fn cpu_pool_all_buffers_have_same_capacity() {
        let pool = MeanFieldRk4Buffers::new(256);
        let caps = [
            pool.k1_phase.capacity(),
            pool.k1_amp.capacity(),
            pool.k1_freq.capacity(),
            pool.k2_phase.capacity(),
            pool.k2_amp.capacity(),
            pool.k2_freq.capacity(),
            pool.k3_phase.capacity(),
            pool.k3_amp.capacity(),
            pool.k3_freq.capacity(),
            pool.k4_phase.capacity(),
            pool.k4_amp.capacity(),
            pool.k4_freq.capacity(),
            pool.stage_phase.capacity(),
            pool.stage_amp.capacity(),
            pool.stage_freq.capacity(),
            pool.out_phase.capacity(),
            pool.out_amp.capacity(),
            pool.out_freq.capacity(),
        ];
        for cap in &caps {
            assert!(*cap >= 256);
        }
    }
}
