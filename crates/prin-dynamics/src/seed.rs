//! Deterministic, counter-based seed authority for all PRIN randomness.
//!
//! Every stochastic entry point receives a [`Seed`]. A seed is a `(counter, key)`
//! pair that produces a reproducible stream of `u64` and `f64` values via
//! `Pcg64`. Counter jumps support parallel reproducible streams without shared
//! mutable state, and the design is forward-compatible with counter-mode
//! generators such as Philox.

use rand::{Error, RngCore};
use rand_pcg::Pcg64;
use serde::ser::SerializeStruct;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use thiserror::Error;

/// Errors that can arise from [`Seed`] operations.
#[derive(Debug, Error)]
pub enum SeedError {
    /// The seed's output counter would overflow `u128`.
    #[error("seed counter overflow")]
    CounterOverflow,

    /// The requested range is not valid for a uniform `f64` draw.
    #[error("invalid range for f64 draw: [{lo}, {hi}]")]
    InvalidRange {
        /// Lower bound.
        lo: f64,
        /// Upper bound.
        hi: f64,
    },
}

/// Snapshot used only for `Serialize`/`Deserialize` so the internal `Pcg64`
/// state is never persisted—only the logical `(counter, key)` pair is.
#[derive(Serialize, Deserialize)]
struct SeedSnapshot {
    counter: u128,
    key: u128,
}

/// Counter-based deterministic seed authority.
///
/// A `Seed` is identified by a `(counter, key)` pair. The `counter` selects the
/// starting position in the stream; the `key` selects an independent stream.
/// Drawing values advances the counter; [`Seed::jump`] advances without
/// consuming outputs, enabling reproducible parallel streams.
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Seed {
    counter: u128,
    key: u128,
    pcg: Pcg64,
}

impl Seed {
    /// Create a new seed at `counter` in the stream selected by `key`.
    ///
    /// The first call to a drawing method returns the `counter`-th output of the
    /// stream, so two seeds with the same `(counter, key)` produce identical
    /// sequences.
    pub fn new(counter: u128, key: u128) -> Self {
        let mut pcg = Pcg64::new(0, key);
        pcg.advance(counter);
        Self { counter, key, pcg }
    }

    /// The logical position of the next output in this stream.
    pub fn counter(&self) -> u128 {
        self.counter
    }

    /// The stream key.
    pub fn key(&self) -> u128 {
        self.key
    }

    /// Advance the seed by `delta` outputs without drawing them.
    ///
    /// This is the building block for parallel reproducible streams: each worker
    /// can jump to a disjoint counter range and then draw independently.
    pub fn jump(&mut self, delta: u128) -> Result<(), SeedError> {
        self.counter = self
            .counter
            .checked_add(delta)
            .ok_or(SeedError::CounterOverflow)?;
        self.pcg.advance(delta);
        Ok(())
    }

    /// Draw the next `f64` uniformly in `[0, 1)` with 53-bit precision.
    pub fn next_f64(&mut self) -> f64 {
        const SCALE: f64 = 1.0 / ((1u64 << 53) as f64);
        let v = self.pcg.next_u64();
        self.counter = self.counter.wrapping_add(1);
        ((v >> 11) as f64) * SCALE
    }

    /// Draw the next `f64` uniformly in the half-open interval `[lo, hi)`.
    ///
    /// The result is guaranteed to be strictly less than `hi`, even when the
    /// naive affine transform would round up to `hi` for the maximum 53-bit draw.
    ///
    /// # Errors
    ///
    /// Returns [`SeedError::InvalidRange`] if `lo` or `hi` is not finite, or if
    /// `lo >= hi`.
    pub fn next_f64_range(&mut self, lo: f64, hi: f64) -> Result<f64, SeedError> {
        if !(lo.is_finite() && hi.is_finite() && lo < hi) {
            return Err(SeedError::InvalidRange { lo, hi });
        }

        let mut scale = hi - lo;
        if !scale.is_finite() {
            return Err(SeedError::InvalidRange { lo, hi });
        }

        // Largest value that `next_f64()` can return: `(2^53 - 1) / 2^53`.
        const MAX_DRAW: f64 = 1.0 - 1.0 / ((1u64 << 53) as f64);

        // Decrease `scale` by one ulp until the maximum possible draw cannot
        // round up to `hi`. This preserves the half-open contract without
        // rejecting draws or changing the number of `u64` values consumed.
        while scale * MAX_DRAW + lo >= hi {
            scale = f64::from_bits(scale.to_bits() - 1);
        }

        Ok(lo + self.next_f64() * scale)
    }
}

impl RngCore for Seed {
    fn next_u32(&mut self) -> u32 {
        self.counter = self.counter.wrapping_add(1);
        self.pcg.next_u32()
    }

    fn next_u64(&mut self) -> u64 {
        self.counter = self.counter.wrapping_add(1);
        self.pcg.next_u64()
    }

    fn fill_bytes(&mut self, dest: &mut [u8]) {
        let mut chunks = dest.chunks_exact_mut(8);
        for chunk in &mut chunks {
            let v = self.next_u64();
            chunk.copy_from_slice(&v.to_le_bytes());
        }
        let rem = chunks.into_remainder();
        if !rem.is_empty() {
            let v = self.next_u64();
            rem.copy_from_slice(&v.to_le_bytes()[..rem.len()]);
        }
    }

    fn try_fill_bytes(&mut self, dest: &mut [u8]) -> Result<(), Error> {
        self.fill_bytes(dest);
        Ok(())
    }
}

impl Serialize for Seed {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut state = serializer.serialize_struct("Seed", 2)?;
        state.serialize_field("counter", &self.counter)?;
        state.serialize_field("key", &self.key)?;
        state.end()
    }
}

impl<'de> Deserialize<'de> for Seed {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let snapshot = SeedSnapshot::deserialize(deserializer)?;
        Ok(Self::new(snapshot.counter, snapshot.key))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::Rng;

    #[test]
    fn new_with_same_counter_and_key_is_reproducible() {
        let mut a = Seed::new(0, 0);
        let mut b = Seed::new(0, 0);
        assert_eq!(a.next_u64(), b.next_u64());
        assert_eq!(a.next_u64(), b.next_u64());
    }

    #[test]
    fn different_keys_produce_different_streams() {
        let mut a = Seed::new(0, 0);
        let mut b = Seed::new(0, 1);
        assert_ne!(a.next_u64(), b.next_u64());
    }

    #[test]
    fn different_counters_are_different_offsets() {
        let mut a = Seed::new(0, 0);
        let mut b = Seed::new(1, 0);
        let first = a.next_u64();
        let second = b.next_u64();
        assert_ne!(first, second);
    }

    #[test]
    fn counter_increments_per_draw() {
        let mut s = Seed::new(0, 0);
        assert_eq!(s.counter(), 0);
        s.next_u64();
        assert_eq!(s.counter(), 1);
        s.next_f64();
        assert_eq!(s.counter(), 2);
    }

    #[test]
    fn jump_matches_sequential_advance() {
        let mut s1 = Seed::new(0, 0);
        for _ in 0..100 {
            let _ = s1.next_u64();
        }
        let mut s2 = Seed::new(0, 0);
        s2.jump(100).unwrap();
        assert_eq!(s1.next_u64(), s2.next_u64());
    }

    #[test]
    fn next_f64_is_in_unit_interval() {
        let mut s = Seed::new(0, 0);
        for _ in 0..1000 {
            let v = s.next_f64();
            assert!(v >= 0.0);
            assert!(v < 1.0);
        }
    }

    #[test]
    fn next_f64_range_honours_bounds() {
        let mut s = Seed::new(0, 0);
        for _ in 0..1000 {
            let v = s.next_f64_range(0.1, 10.0).unwrap();
            assert!(v >= 0.1);
            assert!(v < 10.0);
        }
    }

    #[test]
    fn next_f64_range_rejects_invalid_range() {
        let mut s = Seed::new(0, 0);
        assert!(matches!(
            s.next_f64_range(1.0, 1.0),
            Err(SeedError::InvalidRange { lo: 1.0, hi: 1.0 })
        ));
        assert!(matches!(
            s.next_f64_range(2.0, 1.0),
            Err(SeedError::InvalidRange { lo: 2.0, hi: 1.0 })
        ));
        assert!(matches!(
            s.next_f64_range(f64::NAN, 1.0),
            Err(SeedError::InvalidRange { .. })
        ));
        assert!(matches!(
            s.next_f64_range(0.0, f64::INFINITY),
            Err(SeedError::InvalidRange { .. })
        ));
    }

    #[test]
    fn next_f64_range_0_1_matches_next_f64() {
        let mut a = Seed::new(42, 7);
        let mut b = Seed::new(42, 7);
        for _ in 0..1000 {
            let expected = a.next_f64();
            let got = b.next_f64_range(0.0, 1.0).unwrap();
            assert_eq!(expected, got);
        }
    }

    #[test]
    fn next_f64_range_max_draw_stays_strictly_below_hi() {
        // The maximum value `next_f64()` can return. The naive affine transform
        // `lo + max_draw * (hi - lo)` can round to exactly `hi` for ranges such
        // as `[1.0, 2.0)`; this is the regression case from WP006-F1.
        let max_draw = ((1u64 << 53) - 1) as f64 / (1u64 << 53) as f64;
        let lo = 1.0;
        let hi = 2.0;
        let naive = lo + max_draw * (hi - lo);
        assert!(naive >= hi, "naive affine transform rounds up to hi");

        // Run many draws to guard the actual implementation.
        let mut s = Seed::new(0, 0);
        for _ in 0..10_000 {
            let v = s.next_f64_range(lo, hi).unwrap();
            assert!(v >= lo && v < hi);
        }

        // Verify the internal scale-decrease logic directly: the maximum possible
        // scaled value must stay below `hi`.
        let mut scale = hi - lo;
        while scale * max_draw + lo >= hi {
            scale = f64::from_bits(scale.to_bits() - 1);
        }
        let max_scaled = lo + max_draw * scale;
        assert!(max_scaled < hi);
    }

    #[test]
    fn rng_gen_is_reproducible() {
        let mut a = Seed::new(123, 456);
        let mut b = Seed::new(123, 456);
        assert_eq!(a.gen::<f64>(), b.gen::<f64>());
        assert_eq!(a.gen::<u64>(), b.gen::<u64>());
    }

    #[test]
    fn serialization_round_trips() {
        let mut s = Seed::new(42, 7);
        s.next_u64();
        s.next_u64();
        let json = serde_json::to_string(&s).unwrap();
        let restored: Seed = serde_json::from_str(&json).unwrap();
        assert_eq!(s, restored);
        assert_eq!(s.counter(), restored.counter());
    }

    #[test]
    fn key_returns_stream_key() {
        let s = Seed::new(0, 42);
        assert_eq!(s.key(), 42);
    }

    #[test]
    fn next_u32_is_reproducible() {
        let mut a = Seed::new(0, 0);
        let mut b = Seed::new(0, 0);
        assert_eq!(a.next_u32(), b.next_u32());
        assert_eq!(a.next_u32(), b.next_u32());
    }

    #[test]
    fn fill_bytes_is_reproducible() {
        let mut a = Seed::new(0, 0);
        let mut b = Seed::new(0, 0);
        let mut buf_a = [0u8; 17];
        let mut buf_b = [0u8; 17];
        a.fill_bytes(&mut buf_a);
        b.fill_bytes(&mut buf_b);
        assert_eq!(buf_a, buf_b);
    }

    #[test]
    fn try_fill_bytes_is_reproducible() {
        let mut a = Seed::new(0, 0);
        let mut b = Seed::new(0, 0);
        let mut buf_a = [0u8; 11];
        let mut buf_b = [0u8; 11];
        a.try_fill_bytes(&mut buf_a).unwrap();
        b.try_fill_bytes(&mut buf_b).unwrap();
        assert_eq!(buf_a, buf_b);
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn next_f64_is_uniform_in_0_1(counter in any::<u128>(), key in any::<u128>()) {
            let mut s = Seed::new(counter, key);
            let v = s.next_f64();
            prop_assert!(v >= 0.0);
            prop_assert!(v < 1.0);
        }
    }

    proptest! {
        #[test]
        fn jump_preserves_counter_increments(delta in any::<u64>()) {
            let mut s = Seed::new(0, 0);
            s.jump(delta as u128).unwrap();
            prop_assert_eq!(s.counter(), delta as u128);
        }
    }
}
