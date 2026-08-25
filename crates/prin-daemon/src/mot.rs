//! Multi-object-tracking (MOT) evaluation: IoU distances, the CLEAR-MOT/IDF1
//! event accumulator, and deterministic synthetic sequence generators.
//!
//! Rebuild of PRINet 3.0 `prinet.nn.mot_evaluation`, scoped to the metrics
//! themselves rather than the reference module's end-to-end
//! `evaluate_tracking(sequence, tracker, ...)` loop: this crate cannot
//! depend on `prin-train` (the workspace layering in `crates/README.md`
//! places `prin-train` and `prin-daemon` at the same tier), so wiring a real
//! tracker's per-frame hypotheses into this accumulator is a Python
//! orchestration concern (`python/prin/eval`), not a Rust one. What lives
//! here is the reusable, tracker-agnostic core: given ground-truth and
//! hypothesis identities plus a distance matrix for each frame, compute
//! MOTA/MOTP/IDF1/identity-switch counts exactly as `py-motmetrics` does.
//!
//! # Reference algorithm
//!
//! [`MotAccumulator::update`] reproduces `motmetrics.mot.MOTAccumulator.update`'s
//! four-step per-frame procedure (hysteresis carry-forward of established
//! pairings, Kuhn–Munkres assignment of the remainder via the crate-private
//! `assignment::solve_assignment`, then miss/false-positive bookkeeping) and
//! [`MotAccumulator::summary`] reproduces
//! `motmetrics.metrics`'s MOTA/MOTP/IDF1 formulas, including the IDF1
//! global min-cost identity assignment (`id_global_assignment` /
//! `idtp`/`idfn`/`idfp`/`idf1` in `motmetrics/metrics.py`). Event subtypes
//! the reference tracks but this crate's four target metrics never consume
//! — `TRANSFER`, `ASCEND`, `MIGRATE`, and the full per-event `RAW` log — are
//! intentionally not reproduced; only the running counts MOTA/MOTP/IDF1/
//! switches actually need survive per frame.
//!
//! `crates/prin-daemon/tests/parity_mot.rs` replays fixed oid/hid/distance
//! sequences (including several run through the real `motmetrics` package)
//! and checks this accumulator's summary against the recorded reference
//! output.

use std::collections::{HashMap, HashSet};

use prin_dynamics::Seed;

use crate::assignment::solve_assignment;
use crate::error::DaemonError;

// ---------------------------------------------------------------------------
// Bounding boxes and IoU distance
// ---------------------------------------------------------------------------

/// An axis-aligned bounding box in `(x, y, width, height)` form.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct BBox {
    /// Left edge.
    pub x: f64,
    /// Top edge.
    pub y: f64,
    /// Width (non-negative in well-formed boxes).
    pub w: f64,
    /// Height (non-negative in well-formed boxes).
    pub h: f64,
}

impl BBox {
    /// Construct a box from `(x, y, w, h)`.
    #[must_use]
    pub fn new(x: f64, y: f64, w: f64, h: f64) -> Self {
        Self { x, y, w, h }
    }

    /// Intersection-over-union with `other`, in `[0, 1]`.
    ///
    /// Matches `motmetrics.distances.boxiou`: zero when the intersection
    /// area is zero (including for degenerate zero-area boxes, where the
    /// reference's `0 / 0` would otherwise be `nan`).
    #[must_use]
    pub fn iou(&self, other: &BBox) -> f64 {
        let a_min = (self.x, self.y);
        let a_max = (self.x + self.w, self.y + self.h);
        let b_min = (other.x, other.y);
        let b_max = (other.x + other.w, other.y + other.h);

        let i_min = (a_min.0.max(b_min.0), a_min.1.max(b_min.1));
        let i_max = (a_max.0.min(b_max.0), a_max.1.min(b_max.1));
        let i_size = ((i_max.0 - i_min.0).max(0.0), (i_max.1 - i_min.1).max(0.0));
        let i_vol = i_size.0 * i_size.1;

        let a_size = ((a_max.0 - a_min.0).max(0.0), (a_max.1 - a_min.1).max(0.0));
        let b_size = ((b_max.0 - b_min.0).max(0.0), (b_max.1 - b_min.1).max(0.0));
        let a_vol = a_size.0 * a_size.1;
        let b_vol = b_size.0 * b_size.1;
        let u_vol = a_vol + b_vol - i_vol;

        if i_vol == 0.0 {
            0.0
        } else {
            i_vol / u_vol
        }
    }
}

/// Build a `objs.len() x hyps.len()` IoU distance matrix, `1 - IoU`, with
/// entries beyond `max_iou_distance` marked as forbidden (`NaN`).
///
/// Matches `motmetrics.distances.iou_matrix`. Returns an empty matrix (zero
/// rows) if either input is empty.
#[must_use]
pub fn iou_distance_matrix(objs: &[BBox], hyps: &[BBox], max_iou_distance: f64) -> Vec<Vec<f64>> {
    if objs.is_empty() || hyps.is_empty() {
        return Vec::new();
    }
    objs.iter()
        .map(|o| {
            hyps.iter()
                .map(|h| {
                    let dist = 1.0 - o.iou(h);
                    if dist > max_iou_distance {
                        f64::NAN
                    } else {
                        dist
                    }
                })
                .collect()
        })
        .collect()
}

// ---------------------------------------------------------------------------
// MOTAccumulator
// ---------------------------------------------------------------------------

/// Ground-truth object identity.
pub type ObjId = u64;
/// Hypothesis (predicted track) identity.
pub type HypId = u64;

/// Accumulates per-frame tracking events and computes CLEAR-MOT/IDF1
/// summary metrics.
///
/// Rebuild of `motmetrics.mot.MOTAccumulator` restricted to the events that
/// feed MOTA, MOTP, IDF1, and the identity-switch count (see the module
/// docs for exactly which reference event subtypes are out of scope).
///
/// # Examples
///
/// ```
/// use prin_daemon::mot::MotAccumulator;
///
/// let mut acc = MotAccumulator::new();
/// // Frame 0: object 1 <-> hypothesis 1, distance 0.1.
/// acc.update(0, &[1], &[1], &[vec![0.1]]).unwrap();
/// // Frame 1: same pairing continues.
/// acc.update(1, &[1], &[1], &[vec![0.1]]).unwrap();
///
/// let summary = acc.summary();
/// assert_eq!(summary.num_switches, 0);
/// assert_eq!(summary.mota, 1.0);
/// assert!((summary.motp - 0.1).abs() < 1e-12);
/// assert_eq!(summary.idf1, 1.0);
/// ```
#[derive(Debug, Clone)]
pub struct MotAccumulator {
    max_switch_time: Option<u64>,
    matched: HashMap<ObjId, HypId>,
    last_occurrence: HashMap<ObjId, u64>,
    num_matches: u64,
    num_switches: u64,
    num_misses: u64,
    num_false_positives: u64,
    sum_match_distance: f64,
    oid_frame_count: HashMap<ObjId, u64>,
    hid_frame_count: HashMap<HypId, u64>,
    pair_frame_count: HashMap<(ObjId, HypId), u64>,
}

impl Default for MotAccumulator {
    fn default() -> Self {
        Self::new()
    }
}

impl MotAccumulator {
    /// Create an empty accumulator with no upper bound on the frame span
    /// over which a re-appearing object may still trigger an identity
    /// switch (`motmetrics`' `max_switch_time=float('inf')` default).
    #[must_use]
    pub fn new() -> Self {
        Self {
            max_switch_time: None,
            matched: HashMap::new(),
            last_occurrence: HashMap::new(),
            num_matches: 0,
            num_switches: 0,
            num_misses: 0,
            num_false_positives: 0,
            sum_match_distance: 0.0,
            oid_frame_count: HashMap::new(),
            hid_frame_count: HashMap::new(),
            pair_frame_count: HashMap::new(),
        }
    }

    /// Create an accumulator that only counts a re-assignment as an identity
    /// switch when the object was last seen within `max_switch_time` frames.
    #[must_use]
    pub fn with_max_switch_time(max_switch_time: u64) -> Self {
        Self {
            max_switch_time: Some(max_switch_time),
            ..Self::new()
        }
    }

    /// Record one frame's ground-truth/hypothesis identities and their
    /// pairwise distance matrix.
    ///
    /// `dists[i][j]` is the cost of pairing `oids[i]` with `hids[j]`; `NaN`
    /// or infinite marks a forbidden pairing (see [`iou_distance_matrix`]).
    /// Frames must be supplied in non-decreasing `frame_id` order for
    /// `max_switch_time` bookkeeping to be meaningful, but this is not
    /// validated — an accumulator has no way to distinguish "out of order"
    /// from "a legitimately sparse frame numbering".
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::MotShapeMismatch`] unless `dists` has exactly
    /// `oids.len()` rows, each with exactly `hids.len()` columns.
    pub fn update(
        &mut self,
        frame_id: u64,
        oids: &[ObjId],
        hids: &[HypId],
        dists: &[Vec<f64>],
    ) -> Result<(), DaemonError> {
        let no = oids.len();
        let nh = hids.len();
        if dists.len() != no || dists.iter().any(|row| row.len() != nh) {
            return Err(DaemonError::MotShapeMismatch {
                oids: no,
                hids: nh,
                rows: dists.len(),
                cols: dists.first().map_or(0, Vec::len),
            });
        }

        self.record_raw_presence(oids, hids, dists);

        let mut oids_masked = vec![false; no];
        let mut hids_masked = vec![false; nh];

        if no > 0 && nh > 0 {
            let mut working: Vec<Vec<f64>> = dists.to_vec();

            // Step 1: carry forward already-established pairings.
            for i in 0..no {
                let Some(&hprev) = self.matched.get(&oids[i]) else {
                    continue;
                };
                let Some(j) = (0..nh).find(|&j| !hids_masked[j] && hids[j] == hprev) else {
                    continue;
                };
                if working[i][j].is_finite() {
                    oids_masked[i] = true;
                    hids_masked[j] = true;
                    self.record_match(oids[i], hids[j], working[i][j], frame_id);
                }
            }

            // Step 2: forbid re-use of already-matched rows/columns, then
            // solve the remainder.
            for (i, masked) in oids_masked.iter().enumerate() {
                if *masked {
                    working[i].iter_mut().for_each(|v| *v = f64::NAN);
                }
            }
            for (j, masked) in hids_masked.iter().enumerate() {
                if *masked {
                    for row in &mut working {
                        row[j] = f64::NAN;
                    }
                }
            }

            for (i, j) in solve_assignment(&working) {
                self.record_match(oids[i], hids[j], dists[i][j], frame_id);
                oids_masked[i] = true;
                hids_masked[j] = true;
            }
        }

        self.num_misses += oids_masked.iter().filter(|&&m| !m).count() as u64;
        self.num_false_positives += hids_masked.iter().filter(|&&m| !m).count() as u64;

        for &o in oids {
            self.last_occurrence.insert(o, frame_id);
        }

        Ok(())
    }

    fn record_raw_presence(&mut self, oids: &[ObjId], hids: &[HypId], dists: &[Vec<f64>]) {
        let unique_oids: HashSet<ObjId> = oids.iter().copied().collect();
        for o in unique_oids {
            *self.oid_frame_count.entry(o).or_insert(0) += 1;
        }
        let unique_hids: HashSet<HypId> = hids.iter().copied().collect();
        for h in unique_hids {
            *self.hid_frame_count.entry(h).or_insert(0) += 1;
        }

        let mut seen_pairs: HashSet<(ObjId, HypId)> = HashSet::new();
        for (i, &o) in oids.iter().enumerate() {
            for (j, &h) in hids.iter().enumerate() {
                if dists[i][j].is_finite() && seen_pairs.insert((o, h)) {
                    *self.pair_frame_count.entry((o, h)).or_insert(0) += 1;
                }
            }
        }
    }

    fn record_match(&mut self, o: ObjId, h: HypId, dist: f64, frame_id: u64) {
        let is_switch = match self.matched.get(&o) {
            Some(&prev) if prev != h => match self.max_switch_time {
                None => true,
                Some(max_span) => {
                    let last = self.last_occurrence.get(&o).copied().unwrap_or(frame_id);
                    frame_id.saturating_sub(last) <= max_span
                }
            },
            _ => false,
        };
        if is_switch {
            self.num_switches += 1;
        } else {
            self.num_matches += 1;
        }
        self.sum_match_distance += dist;
        self.matched.insert(o, h);
    }

    /// Compute the CLEAR-MOT/IDF1 summary over every frame recorded so far.
    #[must_use]
    pub fn summary(&self) -> MotSummary {
        let num_objects: u64 = self.oid_frame_count.values().sum();
        let num_detections = self.num_matches + self.num_switches;

        let mota = 1.0
            - (self.num_misses + self.num_switches + self.num_false_positives) as f64
                / num_objects as f64;
        let motp = self.sum_match_distance / num_detections as f64;
        let idf1 = self.compute_idf1(num_objects);

        MotSummary {
            mota,
            motp,
            idf1,
            num_matches: self.num_matches,
            num_switches: self.num_switches,
            num_misses: self.num_misses,
            num_false_positives: self.num_false_positives,
            num_objects,
        }
    }

    /// Global min-cost identity assignment (`motmetrics` `id_global_assignment`
    /// plus `idtp`/`idfn`/`idf1`).
    fn compute_idf1(&self, num_objects: u64) -> f64 {
        let mut oids: Vec<ObjId> = self.oid_frame_count.keys().copied().collect();
        oids.sort_unstable();
        let mut hids: Vec<HypId> = self.hid_frame_count.keys().copied().collect();
        hids.sort_unstable();
        let no = oids.len();
        let nh = hids.len();
        let num_predictions: u64 = self.hid_frame_count.values().sum();

        let size = no + nh;
        let mut fp = vec![vec![0.0_f64; size]; size];
        let mut fnv = vec![vec![0.0_f64; size]; size];

        for row in fp.iter_mut().skip(no) {
            row[..nh].fill(f64::NAN);
        }
        for row in fnv.iter_mut().take(no) {
            row[nh..].fill(f64::NAN);
        }

        for (idx, &o) in oids.iter().enumerate() {
            let oc = self.oid_frame_count[&o] as f64;
            fnv[idx][..nh].fill(oc);
            fnv[idx][nh + idx] = oc;
        }
        for (idx, &h) in hids.iter().enumerate() {
            let hc = self.hid_frame_count[&h] as f64;
            for row in fp.iter_mut().take(no) {
                row[idx] = hc;
            }
            fp[no + idx][idx] = hc;
        }
        for (&(o, h), &tp) in &self.pair_frame_count {
            if let (Ok(r), Ok(c)) = (oids.binary_search(&o), hids.binary_search(&h)) {
                fp[r][c] -= tp as f64;
                fnv[r][c] -= tp as f64;
            }
        }

        let costs: Vec<Vec<f64>> = (0..size)
            .map(|r| (0..size).map(|c| fp[r][c] + fnv[r][c]).collect())
            .collect();

        let pairs = solve_assignment(&costs);
        let idfn: f64 = pairs.iter().map(|&(r, c)| fnv[r][c]).sum();
        let idtp = num_objects as f64 - idfn;

        (2.0 * idtp) / (num_objects as f64 + num_predictions as f64)
    }
}

/// CLEAR-MOT/IDF1 summary produced by [`MotAccumulator::summary`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct MotSummary {
    /// Multiple object tracking accuracy, `1 - (misses + switches + FP) / objects`.
    ///
    /// Unbounded below; `1.0` is perfect.
    pub mota: f64,
    /// Multiple object tracking precision: mean distance over matched pairs
    /// (including switches). `NaN` when there were no matches.
    pub motp: f64,
    /// Global min-cost identity F1 score, in `[0, 1]`.
    pub idf1: f64,
    /// Total `MATCH` events (a pairing consistent with the previous frame).
    pub num_matches: u64,
    /// Total `SWITCH` events (a pairing inconsistent with the previous frame).
    pub num_switches: u64,
    /// Total unmatched ground-truth objects across all frames.
    pub num_misses: u64,
    /// Total unmatched hypotheses across all frames.
    pub num_false_positives: u64,
    /// Total ground-truth object-frame occurrences (the MOTA denominator).
    pub num_objects: u64,
}

// ---------------------------------------------------------------------------
// Synthetic sequence generators
// ---------------------------------------------------------------------------

/// Default bounding-box half-extent used by the synthetic generators below
/// (PRINet 3.0 `mot_evaluation` uses the same fixed `[0.05, 0.1]` size).
const DEFAULT_BOX_SIZE: (f64, f64) = (0.05, 0.1);

/// One ground-truth detection in a synthetic sequence frame.
///
/// `obj_id: None` marks a distractor: a detection with no ground-truth
/// identity, injected to test whether an identity-assignment procedure
/// spuriously latches onto it (PRINet 3.0's `obj_id = -1` sentinel,
/// represented here as `Option` rather than a magic number).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Detection {
    /// Ground-truth identity, or `None` for a distractor.
    pub obj_id: Option<ObjId>,
    /// Detection bounding box.
    pub bbox: BBox,
}

/// Draw a standard-normal value from `seed` via the Box–Muller transform.
///
/// [`Seed`] exposes uniform draws only; this is the one derived distribution
/// the synthetic sequence generators need, kept local to this module rather
/// than promoted to `prin-dynamics` because it is test/evaluation-fixture
/// scaffolding, not part of the dynamics numerical core.
fn standard_normal(seed: &mut Seed) -> f64 {
    let u1 = seed.next_f64().max(f64::MIN_POSITIVE);
    let u2 = seed.next_f64();
    (-2.0 * u1.ln()).sqrt() * (std::f64::consts::TAU * u2).cos()
}

/// Generate a synthetic sequence of `n_objects` moving in straight lines
/// with Gaussian position noise, each frame optionally missing a detection.
///
/// Rebuild of PRINet 3.0 `generate_linear_mot_sequence`. Deterministic in
/// `seed`: the same [`Seed`] state always produces the same sequence.
///
/// # Errors
///
/// Returns [`DaemonError::InvalidParameter`] if `n_objects` or `n_frames`
/// is `0`, `noise_std` is negative or non-finite, or `miss_rate` is outside
/// `[0, 1]`.
pub fn generate_linear_sequence(
    n_objects: usize,
    n_frames: usize,
    noise_std: f64,
    miss_rate: f64,
    seed: &mut Seed,
) -> Result<Vec<Vec<Detection>>, DaemonError> {
    validate_sequence_params(n_objects, n_frames, noise_std, miss_rate)?;

    let mut positions: Vec<(f64, f64)> = (0..n_objects)
        .map(|_| (seed.next_f64(), seed.next_f64()))
        .collect();
    let velocities: Vec<(f64, f64)> = (0..n_objects)
        .map(|_| {
            (
                (seed.next_f64() - 0.5) * 0.03,
                (seed.next_f64() - 0.5) * 0.03,
            )
        })
        .collect();

    let mut frames = Vec::with_capacity(n_frames);
    for _ in 0..n_frames {
        let mut frame = Vec::with_capacity(n_objects);
        #[allow(clippy::needless_range_loop)]
        // obj_id is also the emitted identity, not just an index
        for obj_id in 0..n_objects {
            if seed.next_f64() < miss_rate {
                continue;
            }
            let (px, py) = positions[obj_id];
            let x = px + noise_std * standard_normal(seed);
            let y = py + noise_std * standard_normal(seed);
            frame.push(Detection {
                obj_id: Some(obj_id as ObjId),
                bbox: BBox::new(x, y, DEFAULT_BOX_SIZE.0, DEFAULT_BOX_SIZE.1),
            });
        }
        frames.push(frame);

        for (pos, vel) in positions.iter_mut().zip(&velocities) {
            pos.0 = (pos.0 + vel.0).clamp(0.0, 1.0);
            pos.1 = (pos.1 + vel.1).clamp(0.0, 1.0);
        }
    }
    Ok(frames)
}

/// Generate a crowded synthetic sequence: linear trajectories plus random
/// occlusion windows (an object vanishes for 1–3 frames) and distractor
/// injections (extra no-identity detections).
///
/// Rebuild of PRINet 3.0 `generate_crowded_mot_sequence`. Deterministic in
/// `seed`.
///
/// # Errors
///
/// Returns [`DaemonError::InvalidParameter`] under the same conditions as
/// [`generate_linear_sequence`], plus if `occlusion_rate` or
/// `distractor_rate` is outside `[0, 1]`.
#[allow(clippy::too_many_arguments)]
pub fn generate_crowded_sequence(
    n_objects: usize,
    n_frames: usize,
    noise_std: f64,
    miss_rate: f64,
    occlusion_rate: f64,
    distractor_rate: f64,
    seed: &mut Seed,
) -> Result<Vec<Vec<Detection>>, DaemonError> {
    validate_sequence_params(n_objects, n_frames, noise_std, miss_rate)?;
    validate_unit_rate("occlusion_rate", occlusion_rate)?;
    validate_unit_rate("distractor_rate", distractor_rate)?;

    let mut positions: Vec<(f64, f64)> = (0..n_objects)
        .map(|_| (seed.next_f64(), seed.next_f64()))
        .collect();
    let velocities: Vec<(f64, f64)> = (0..n_objects)
        .map(|_| {
            (
                (seed.next_f64() - 0.5) * 0.02,
                (seed.next_f64() - 0.5) * 0.02,
            )
        })
        .collect();

    // Occlusion schedule: for every object/frame, roll for the start of a
    // 1-3 frame occlusion window.
    let mut occluded = vec![vec![false; n_frames]; n_objects];
    for obj_occluded in occluded.iter_mut() {
        #[allow(clippy::needless_range_loop)] // t is also used to size the occlusion window below
        for t in 0..n_frames {
            if seed.next_f64() < occlusion_rate {
                let duration = (1 + (seed.next_f64() * 3.0) as usize).min(n_frames - t);
                obj_occluded
                    .iter_mut()
                    .skip(t)
                    .take(duration)
                    .for_each(|o| *o = true);
            }
        }
    }

    let mut frames = Vec::with_capacity(n_frames);
    #[allow(clippy::needless_range_loop)]
    // t indexes the per-object occlusion column occluded[obj_id][t]
    for t in 0..n_frames {
        let mut frame = Vec::with_capacity(n_objects);
        for obj_id in 0..n_objects {
            if occluded[obj_id][t] || seed.next_f64() < miss_rate {
                continue;
            }
            let (px, py) = positions[obj_id];
            let x = px + noise_std * standard_normal(seed);
            let y = py + noise_std * standard_normal(seed);
            frame.push(Detection {
                obj_id: Some(obj_id as ObjId),
                bbox: BBox::new(x, y, DEFAULT_BOX_SIZE.0, DEFAULT_BOX_SIZE.1),
            });
        }

        for _ in 0..n_objects {
            if seed.next_f64() < distractor_rate {
                let dx = seed.next_f64();
                let dy = seed.next_f64();
                frame.push(Detection {
                    obj_id: None,
                    bbox: BBox::new(dx, dy, DEFAULT_BOX_SIZE.0, DEFAULT_BOX_SIZE.1),
                });
            }
        }

        frames.push(frame);
        for (pos, vel) in positions.iter_mut().zip(&velocities) {
            pos.0 = (pos.0 + vel.0).clamp(0.0, 1.0);
            pos.1 = (pos.1 + vel.1).clamp(0.0, 1.0);
        }
    }
    Ok(frames)
}

fn validate_sequence_params(
    n_objects: usize,
    n_frames: usize,
    noise_std: f64,
    miss_rate: f64,
) -> Result<(), DaemonError> {
    if n_objects == 0 {
        return Err(DaemonError::InvalidParameter {
            param: "n_objects",
            value: 0.0,
        });
    }
    if n_frames == 0 {
        return Err(DaemonError::InvalidParameter {
            param: "n_frames",
            value: 0.0,
        });
    }
    if !(noise_std.is_finite() && noise_std >= 0.0) {
        return Err(DaemonError::InvalidParameter {
            param: "noise_std",
            value: noise_std,
        });
    }
    validate_unit_rate("miss_rate", miss_rate)
}

fn validate_unit_rate(param: &'static str, value: f64) -> Result<(), DaemonError> {
    if !(value.is_finite() && (0.0..=1.0).contains(&value)) {
        return Err(DaemonError::InvalidParameter { param, value });
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // -- BBox / IoU -----------------------------------------------------

    #[test]
    fn identical_boxes_have_iou_one() {
        let a = BBox::new(0.0, 0.0, 1.0, 1.0);
        assert!((a.iou(&a) - 1.0).abs() < 1e-15);
    }

    #[test]
    fn disjoint_boxes_have_iou_zero() {
        let a = BBox::new(0.0, 0.0, 1.0, 1.0);
        let b = BBox::new(5.0, 5.0, 1.0, 1.0);
        assert_eq!(a.iou(&b), 0.0);
    }

    #[test]
    fn half_overlap_iou_matches_hand_computed_value() {
        let a = BBox::new(0.0, 0.0, 2.0, 2.0);
        let b = BBox::new(1.0, 0.0, 2.0, 2.0);
        // Intersection area 2 (1x2), union area 4+4-2=6 -> IoU = 1/3.
        assert!((a.iou(&b) - 1.0 / 3.0).abs() < 1e-12);
    }

    #[test]
    fn iou_distance_matrix_marks_low_overlap_as_forbidden() {
        let objs = [BBox::new(0.0, 0.0, 1.0, 1.0)];
        let hyps = [BBox::new(10.0, 10.0, 1.0, 1.0)];
        let dists = iou_distance_matrix(&objs, &hyps, 0.99);
        assert!(dists[0][0].is_nan());
    }

    #[test]
    fn iou_distance_matrix_keeps_distances_within_the_threshold() {
        let objs = [BBox::new(0.0, 0.0, 1.0, 1.0)];
        let hyps = [BBox::new(0.0, 0.0, 1.0, 1.0), BBox::new(0.5, 0.0, 1.0, 1.0)];
        let dists = iou_distance_matrix(&objs, &hyps, 1.0);
        assert_eq!(dists[0][0], 0.0); // identical boxes: distance 0
        assert!((dists[0][1] - (1.0 - 1.0 / 3.0)).abs() < 1e-12);
    }

    #[test]
    fn accumulator_default_matches_new() {
        // Both are empty accumulators, so mota/motp/idf1 are all `0.0 / 0.0`
        // (`NaN`); compare via `Debug` formatting rather than `PartialEq`,
        // since `NaN != NaN`.
        let default_acc = MotAccumulator::default();
        let new_acc = MotAccumulator::new();
        assert_eq!(
            format!("{:?}", default_acc.summary()),
            format!("{:?}", new_acc.summary())
        );
    }

    #[test]
    fn iou_distance_matrix_empty_inputs_yield_empty_matrix() {
        assert_eq!(
            iou_distance_matrix(&[], &[BBox::new(0.0, 0.0, 1.0, 1.0)], 1.0),
            Vec::<Vec<f64>>::new()
        );
        assert_eq!(
            iou_distance_matrix(&[BBox::new(0.0, 0.0, 1.0, 1.0)], &[], 1.0),
            Vec::<Vec<f64>>::new()
        );
    }

    // -- MotAccumulator basic bookkeeping --------------------------------

    #[test]
    fn shape_mismatch_is_rejected() {
        let mut acc = MotAccumulator::new();
        let err = acc.update(0, &[1, 2], &[1], &[vec![0.1]]).unwrap_err();
        assert!(matches!(
            err,
            DaemonError::MotShapeMismatch {
                oids: 2,
                hids: 1,
                rows: 1,
                cols: 1,
            }
        ));
    }

    #[test]
    fn empty_frame_is_a_no_op() {
        let mut acc = MotAccumulator::new();
        acc.update(0, &[], &[], &[]).unwrap();
        let summary = acc.summary();
        assert_eq!(summary.num_matches, 0);
        assert_eq!(summary.num_objects, 0);
    }

    #[test]
    fn perfect_single_object_tracking_has_mota_one() {
        let mut acc = MotAccumulator::new();
        for t in 0..5u64 {
            acc.update(t, &[1], &[1], &[vec![0.2]]).unwrap();
        }
        let s = acc.summary();
        assert_eq!(s.num_matches, 5);
        assert_eq!(s.num_switches, 0);
        assert_eq!(s.num_misses, 0);
        assert_eq!(s.num_false_positives, 0);
        assert_eq!(s.mota, 1.0);
        assert!((s.motp - 0.2).abs() < 1e-12);
        assert_eq!(s.idf1, 1.0);
    }

    #[test]
    fn unmatched_object_counts_as_miss_and_lowers_mota() {
        let mut acc = MotAccumulator::new();
        // Object present but no hypothesis at all.
        acc.update(0, &[1], &[], &[vec![]]).unwrap();
        let s = acc.summary();
        assert_eq!(s.num_misses, 1);
        assert_eq!(s.num_objects, 1);
        assert_eq!(s.mota, 0.0);
    }

    #[test]
    fn unmatched_hypothesis_counts_as_false_positive() {
        let mut acc = MotAccumulator::new();
        acc.update(0, &[], &[1], &[]).unwrap();
        let s = acc.summary();
        assert_eq!(s.num_false_positives, 1);
        // No ground-truth objects ever appeared: MOTA denominator is 0, so
        // the nonzero false-positive numerator drives MOTA to -infinity
        // (matching `motmetrics.math_util.quiet_divide`'s plain IEEE-754
        // division, not a "clamped to 0" convention).
        assert_eq!(s.mota, f64::NEG_INFINITY);
    }

    #[test]
    fn reassignment_to_a_different_hypothesis_is_a_switch() {
        let mut acc = MotAccumulator::new();
        acc.update(0, &[1], &[1, 2], &[vec![0.1, f64::NAN]])
            .unwrap();
        // Force the previous pairing (oid1<->hid1) to become invalid so the
        // Hungarian step must pick hid2 instead.
        acc.update(1, &[1], &[1, 2], &[vec![f64::NAN, 0.1]])
            .unwrap();
        let s = acc.summary();
        assert_eq!(s.num_matches, 1);
        assert_eq!(s.num_switches, 1);
    }

    #[test]
    fn reappearance_with_the_same_hypothesis_after_a_miss_is_not_a_switch() {
        let mut acc = MotAccumulator::new();
        acc.update(0, &[1], &[1], &[vec![0.1]]).unwrap();
        // Frame 1: object occluded (absent entirely).
        acc.update(1, &[], &[], &[]).unwrap();
        // Frame 2: reappears with the *same* hypothesis id.
        acc.update(2, &[1], &[1], &[vec![0.1]]).unwrap();
        let s = acc.summary();
        assert_eq!(s.num_switches, 0);
        assert_eq!(s.num_matches, 2);
    }

    #[test]
    fn max_switch_time_suppresses_switches_beyond_the_window() {
        let mut acc = MotAccumulator::with_max_switch_time(1);
        acc.update(0, &[1], &[1, 2], &[vec![0.1, f64::NAN]])
            .unwrap();
        // Object absent for two frames (span 3 > max_switch_time 1 once it reappears).
        acc.update(1, &[], &[], &[]).unwrap();
        acc.update(2, &[], &[], &[]).unwrap();
        acc.update(3, &[1], &[1, 2], &[vec![f64::NAN, 0.1]])
            .unwrap();
        let s = acc.summary();
        // Span from frame 0 to frame 3 is 3, which exceeds max_switch_time=1,
        // so the reassignment is a plain MATCH, not a SWITCH.
        assert_eq!(s.num_switches, 0);
    }

    #[test]
    fn rectangular_frame_more_objects_than_hypotheses() {
        let mut acc = MotAccumulator::new();
        acc.update(
            0,
            &[1, 2, 3],
            &[1],
            &[vec![0.1], vec![f64::NAN], vec![f64::NAN]],
        )
        .unwrap();
        let s = acc.summary();
        assert_eq!(s.num_matches, 1);
        assert_eq!(s.num_misses, 2);
        assert_eq!(s.num_false_positives, 0);
    }

    #[test]
    fn distractor_hypothesis_is_a_false_positive_every_frame() {
        let mut acc = MotAccumulator::new();
        for t in 0..3u64 {
            acc.update(t, &[1], &[1, 99], &[vec![0.1, f64::NAN]])
                .unwrap();
        }
        let s = acc.summary();
        assert_eq!(s.num_false_positives, 3);
        assert_eq!(s.num_matches, 3);
    }

    #[test]
    fn idf1_is_one_for_a_permanently_consistent_two_object_sequence() {
        let mut acc = MotAccumulator::new();
        for t in 0..4u64 {
            acc.update(
                t,
                &[1, 2],
                &[1, 2],
                &[vec![0.05, f64::NAN], vec![f64::NAN, 0.05]],
            )
            .unwrap();
        }
        assert_eq!(acc.summary().idf1, 1.0);
    }

    #[test]
    fn idf1_drops_when_hypotheses_never_correspond_to_ground_truth() {
        let mut acc = MotAccumulator::new();
        for t in 0..3u64 {
            // Every frame: a GT object with no valid hypothesis, and a
            // hypothesis with no valid GT pairing.
            acc.update(t, &[1], &[99], &[vec![f64::NAN]]).unwrap();
        }
        assert_eq!(acc.summary().idf1, 0.0);
    }

    // -- Synthetic sequence generators -----------------------------------

    #[test]
    fn linear_sequence_rejects_invalid_parameters() {
        let mut seed = Seed::new(0, 0);
        assert!(generate_linear_sequence(0, 5, 0.01, 0.0, &mut seed).is_err());
        assert!(generate_linear_sequence(5, 0, 0.01, 0.0, &mut seed).is_err());
        assert!(generate_linear_sequence(5, 5, -0.1, 0.0, &mut seed).is_err());
        assert!(generate_linear_sequence(5, 5, 0.01, 1.5, &mut seed).is_err());
        assert!(generate_linear_sequence(5, 5, 0.01, -0.1, &mut seed).is_err());
    }

    #[test]
    fn linear_sequence_is_deterministic_for_a_fixed_seed() {
        let mut a = Seed::new(7, 3);
        let mut b = Seed::new(7, 3);
        let seq_a = generate_linear_sequence(5, 10, 0.01, 0.1, &mut a).unwrap();
        let seq_b = generate_linear_sequence(5, 10, 0.01, 0.1, &mut b).unwrap();
        assert_eq!(seq_a, seq_b);
    }

    #[test]
    fn linear_sequence_has_expected_shape_and_no_distractors() {
        let mut seed = Seed::new(0, 0);
        let seq = generate_linear_sequence(4, 6, 0.01, 0.0, &mut seed).unwrap();
        assert_eq!(seq.len(), 6);
        for frame in &seq {
            assert!(frame.len() <= 4);
            for det in frame {
                assert!(det.obj_id.is_some());
                assert!(det.obj_id.unwrap() < 4);
            }
        }
    }

    #[test]
    fn linear_sequence_zero_miss_rate_keeps_every_object_every_frame() {
        let mut seed = Seed::new(1, 1);
        let seq = generate_linear_sequence(3, 8, 0.0, 0.0, &mut seed).unwrap();
        for frame in &seq {
            assert_eq!(frame.len(), 3);
        }
    }

    #[test]
    fn crowded_sequence_is_deterministic_for_a_fixed_seed() {
        let mut a = Seed::new(11, 5);
        let mut b = Seed::new(11, 5);
        let seq_a = generate_crowded_sequence(6, 10, 0.02, 0.05, 0.1, 0.05, &mut a).unwrap();
        let seq_b = generate_crowded_sequence(6, 10, 0.02, 0.05, 0.1, 0.05, &mut b).unwrap();
        assert_eq!(seq_a, seq_b);
    }

    #[test]
    fn crowded_sequence_rejects_invalid_rates() {
        let mut seed = Seed::new(0, 0);
        assert!(generate_crowded_sequence(3, 5, 0.01, 0.0, 1.5, 0.0, &mut seed).is_err());
        assert!(generate_crowded_sequence(3, 5, 0.01, 0.0, 0.0, -0.5, &mut seed).is_err());
    }

    #[test]
    fn crowded_sequence_contains_distractors_when_rate_is_one() {
        let mut seed = Seed::new(2, 2);
        let seq = generate_crowded_sequence(3, 4, 0.0, 0.0, 0.0, 1.0, &mut seed).unwrap();
        // distractor_rate=1.0 injects n_objects distractor rolls per frame,
        // each always firing.
        for frame in &seq {
            let distractors = frame.iter().filter(|d| d.obj_id.is_none()).count();
            assert_eq!(distractors, 3);
        }
    }

    #[test]
    fn crowded_sequence_has_no_live_detections_when_occlusion_rate_is_one() {
        let mut seed = Seed::new(3, 3);
        let seq = generate_crowded_sequence(4, 5, 0.0, 0.0, 1.0, 0.0, &mut seed).unwrap();
        // occlusion_rate=1.0 (guaranteed fire, since draws are < 1.0) and
        // distractor_rate=0.0: every object starts an occlusion window on
        // frame 0, so frame 0 has no detections of any kind.
        assert!(seq[0].is_empty());
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn accumulator_never_panics_on_well_formed_frames(
            frames in prop::collection::vec(
                (1usize..4, 1usize..4),
                1..8,
            ),
        ) {
            let mut acc = MotAccumulator::new();
            for (t, (no, nh)) in frames.into_iter().enumerate() {
                let oids: Vec<ObjId> = (0..no as u64).collect();
                let hids: Vec<HypId> = (0..nh as u64).collect();
                let dists = vec![vec![0.5; nh]; no];
                acc.update(t as u64, &oids, &hids, &dists).unwrap();
            }
            let s = acc.summary();
            prop_assert!(s.num_objects > 0);
            prop_assert!(s.mota.is_finite() || s.mota.is_nan());
        }

        #[test]
        fn mota_denominator_equals_total_object_occurrences(
            per_frame_objects in prop::collection::vec(0usize..5, 1..10),
        ) {
            let mut acc = MotAccumulator::new();
            let mut expected_objects = 0u64;
            for (t, no) in per_frame_objects.iter().enumerate() {
                let oids: Vec<ObjId> = (0..*no as u64).collect();
                let dists = vec![vec![]; *no];
                acc.update(t as u64, &oids, &[], &dists).unwrap();
                expected_objects += *no as u64;
            }
            prop_assert_eq!(acc.summary().num_objects, expected_objects);
        }
    }
}
