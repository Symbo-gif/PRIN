//! Rust-vs-PRINet 3.0.0 parity tests for continuous hierarchical band networks.
//!
//! WP-013 acceptance requires band golden trajectories and capacity invariants.
//! These tests compare [`BandNetwork`] against hard-coded reference values
//! produced by `prinet==3.0.0` (`torch==2.13.0+cpu`, `dtype=torch.float64`) and
//! embedded here, so the test needs neither a Python subprocess nor a PyO3
//! bridge (the `parity_models.rs` / `parity_integrators.rs` precedent).
//!
//! # What is compared, and against what
//!
//! PRIN's `BandNetwork` is a single continuous ODE right-hand side, while
//! PRINet 3.0's `ThetaGammaNetwork`/`DeltaThetaGammaNetwork` are steppers with
//! an embedded `MultiRateIntegrator` (Project Plan amendment #19). The
//! reference values are therefore assembled from the PRINet primitives the
//! networks are built out of:
//!
//! 1. **Intra-band derivatives** — `prinet ... KuramotoOscillator
//!    .compute_derivatives` on each band's sub-state, per `coupling_mode`
//!    (`mean_field`, `full`, and the reference networks' `sparse_knn`).
//! 2. **Composed right-hand side** — the above plus, for each PAC pair,
//!    `decay_fast · (prinet ... PhaseAmplitudeCoupling.modulate(...) − A_fast)`.
//! 3. **Golden trajectories** — RK4 over (2) in PRIN's stage semantics,
//!    computed independently in Python from the PRINet primitives.
//! 4. **Capacity** — `BandNetwork::theoretical_capacity` against the sub-step
//!    count `max(1, int(f_fast / f_slow))` that PRINet's `ThetaGammaNetwork`
//!    gives its `MultiRateIntegrator`.
//!
//! # Tolerances
//!
//! - `CouplingMode::MeanField` evaluates PRINet's order parameter through
//!   `torch.complex64` (f32), the preserved numerical hazard of amendment #14.
//!   Measured worst-case drift on these fixtures: `1.19e-7` absolute
//!   (derivatives) and `9.03e-8` absolute (10-step trajectories).
//! - `CouplingMode::Full` is real f64 on both sides but differs by torch's
//!   pairwise reduction order; measured worst case `2.74e-9` absolute.
//! - `CouplingMode::SparseKnn` — the mode the reference band networks use — is
//!   real f64 with the same reduction order: measured worst case `2.22e-16`
//!   absolute, i.e. ~1 ulp, including the 10-step golden trajectories.
//!
//! Each constant below records the measured figure it was set from.
//!
//! Reference generation: `DOCS/test_and_benchmark_results/`
//! `wp013_generate_prinet_references.py` (ad-hoc, gitignored, WP-009/WP-010
//! precedent), run against the repository venv's `prinet==3.0.0`.

use prin_dynamics::bands::{delta_theta_gamma_network, theta_gamma_network, BandNetwork};
use prin_dynamics::{
    integrate_fixed, BandParams, CouplingMode, Dynamics, OscillatorState, PhaseAmplitudeCoupling,
    RK4Integrator,
};

/// f32-complex mean-field hazard (amendment #14). Measured worst case on
/// these fixtures: `1.19e-7` absolute, `2.87e-6` relative — the relative figure
/// is inflated by near-zero amplitude derivatives, so the absolute bound is the
/// meaningful one and carries ~4× margin.
const MF_RTOL: f64 = 1e-6;
const MF_ATOL: f64 = 5e-7;
/// Multi-step accumulation of the same hazard. Measured worst case: `9.03e-8`
/// absolute at `n = 10`.
const MF_TRAJ_RTOL: f64 = 1e-5;
const MF_TRAJ_ATOL: f64 = 5e-7;
/// Dense pairwise path: real f64 on both sides, but torch's pairwise reduction
/// order differs from the Rust accumulation loop. Measured worst case:
/// `2.74e-9` absolute, `2.61e-8` relative.
const FULL_RTOL: f64 = 1e-7;
const FULL_ATOL: f64 = 1e-8;
/// Sparse k-NN path: real f64 with identical reduction order. Measured worst
/// case: `2.22e-16` absolute (~1 ulp).
const F64_RTOL: f64 = 1e-10;
const F64_ATOL: f64 = 1e-12;

fn assert_close(actual: &[f64], expected: &[f64], rtol: f64, atol: f64) {
    assert_eq!(actual.len(), expected.len());
    for (i, (a, e)) in actual.iter().zip(expected.iter()).enumerate() {
        assert!(
            (a - e).abs() <= atol || (a - e).abs() <= rtol * e.abs(),
            "index {i}: actual {a:.17e} vs expected {e:.17e} \
             (abs {:.3e} > atol {atol:.3e}, rel {:.3e} > rtol {rtol:.3e})",
            (a - e).abs(),
            (a - e).abs() / e.abs()
        );
    }
}

// ------------------------------------------------------------------
// Shared fixtures — identical to the reference generator
// ------------------------------------------------------------------

const THETA_PHASE: [f64; 4] = [0.10, 1.30, 2.70, 4.90];
const THETA_AMP: [f64; 4] = [1.00, 1.20, 0.80, 1.10];
const THETA_FREQ: [f64; 4] = [5.0, 5.5, 6.5, 7.0];
const GAMMA_PHASE: [f64; 8] = [0.20, 0.90, 1.70, 2.40, 3.10, 3.90, 4.60, 5.80];
const GAMMA_AMP: [f64; 8] = [1.00, 0.90, 1.10, 1.05, 0.95, 1.15, 0.85, 1.00];
const GAMMA_FREQ: [f64; 8] = [35.0, 36.5, 38.0, 40.0, 41.0, 42.5, 44.0, 45.0];

const DELTA_PHASE: [f64; 3] = [0.40, 2.20, 5.10];
const DELTA_AMP: [f64; 3] = [1.00, 1.30, 0.70];
const DELTA_FREQ: [f64; 3] = [1.5, 2.0, 2.5];

const K_BAND: f64 = 2.0;
const DECAY: f64 = 0.1;
const GAMMA_ADAPT: f64 = 0.01;
const PAC_DEPTH: f64 = 0.3;
const PAC_OFFSET: f64 = 0.25;

fn tg_state() -> OscillatorState {
    let mut phase = THETA_PHASE.to_vec();
    phase.extend_from_slice(&GAMMA_PHASE);
    let mut amp = THETA_AMP.to_vec();
    amp.extend_from_slice(&GAMMA_AMP);
    let mut freq = THETA_FREQ.to_vec();
    freq.extend_from_slice(&GAMMA_FREQ);
    let mut bands = vec![0u32; 4];
    bands.extend(vec![1u32; 8]);
    OscillatorState::new(phase, amp, freq, Some(bands)).unwrap()
}

fn dtg_state() -> OscillatorState {
    let mut phase = DELTA_PHASE.to_vec();
    phase.extend_from_slice(&THETA_PHASE);
    phase.extend_from_slice(&GAMMA_PHASE);
    let mut amp = DELTA_AMP.to_vec();
    amp.extend_from_slice(&THETA_AMP);
    amp.extend_from_slice(&GAMMA_AMP);
    let mut freq = DELTA_FREQ.to_vec();
    freq.extend_from_slice(&THETA_FREQ);
    freq.extend_from_slice(&GAMMA_FREQ);
    let mut bands = vec![0u32; 3];
    bands.extend(vec![1u32; 4]);
    bands.extend(vec![2u32; 8]);
    OscillatorState::new(phase, amp, freq, Some(bands)).unwrap()
}

fn tg_network(mode: CouplingMode, pac_depth: f64, offset: f64) -> BandNetwork {
    theta_gamma_network(
        4,
        8,
        BandParams::with_coupling(K_BAND, DECAY, GAMMA_ADAPT, mode.clone()).unwrap(),
        BandParams::with_coupling(K_BAND, DECAY, GAMMA_ADAPT, mode).unwrap(),
        PhaseAmplitudeCoupling::new(pac_depth).unwrap(),
        offset,
    )
    .unwrap()
}

fn dtg_network() -> BandNetwork {
    let params =
        || BandParams::with_coupling(K_BAND, DECAY, GAMMA_ADAPT, CouplingMode::MeanField).unwrap();
    delta_theta_gamma_network(
        3,
        4,
        8,
        params(),
        params(),
        params(),
        PhaseAmplitudeCoupling::new(0.2).unwrap(),
        PhaseAmplitudeCoupling::new(PAC_DEPTH).unwrap(),
        0.0,
        0.0,
    )
    .unwrap()
}

// ==================================================================
// 1. Intra-band derivatives per coupling mode (PAC depth 0)
// ==================================================================

#[test]
fn parity_intra_band_mean_field_matches_prinet_kuramoto() {
    let net = tg_network(CouplingMode::MeanField, 0.0, 0.0);
    let d = net.compute_derivatives(&tg_state()).unwrap();

    let expected_dphase = [
        5.217533469451431,
        5.184774022473835,
        6.095652448210613,
        7.44019609918461,
        35.175952174933414,
        36.67244752040135,
        38.07108648763356,
        39.943981338915414,
        40.84322264182107,
        42.319627272946065,
        43.88998191433744,
        45.099351987402784,
    ];
    let expected_damplitude = [
        0.3227836825439335,
        0.2359486418707898,
        -0.3301397807605088,
        -0.28970600106740796,
        -0.15878738634172299,
        -0.021611569954296486,
        0.06135295717498776,
        0.07185314322052577,
        0.004176532602859842,
        -0.15836823713058856,
        -0.23436915840907518,
        -0.25666622882997825,
    ];
    let expected_dfrequency = [
        0.0005438336438018357,
        -0.0007880649005937248,
        -0.0010108688240320215,
        0.0011004901876047655,
        0.00021994021480222363,
        0.00021555939671411703,
        8.885810798063504e-05,
        -7.002332512536091e-05,
        -0.0001959716942802629,
        -0.0002254659048557886,
        -0.00013752260466180525,
        0.00012418998207134924,
    ];

    assert_close(&d.dphase, &expected_dphase, MF_RTOL, MF_ATOL);
    assert_close(&d.damplitude, &expected_damplitude, MF_RTOL, MF_ATOL);
    assert_close(&d.dfrequency, &expected_dfrequency, MF_RTOL, MF_ATOL);
}

#[test]
fn parity_intra_band_full_matches_prinet_kuramoto() {
    let net = tg_network(CouplingMode::Full { matrix: None }, 0.0, 0.0);
    let d = net.compute_derivatives(&tg_state()).unwrap();

    let expected_dphase = [
        5.217533465449209,
        5.184774105199602,
        6.095652498196967,
        7.440196008866996,
        35.175952131954766,
        36.672447502296734,
        38.071086507458745,
        39.9439813827414,
        40.843222689035805,
        42.319627297250925,
        43.88998190573281,
        45.09935193959961,
    ];
    let expected_damplitude = [
        -0.17721640776987876,
        -0.36405139458534763,
        -0.7301397054347694,
        -0.8397060049829027,
        -0.40878740926452195,
        -0.24661161517422608,
        -0.21364708731749377,
        -0.19064687803746452,
        -0.23332345542267427,
        -0.4458681949181206,
        -0.44686911046557415,
        -0.5066662194771319,
    ];
    let expected_dfrequency = [
        0.0005438336636230226,
        -0.0007880647370009953,
        -0.001010868754507584,
        0.0011004900221674896,
        0.00021994016494345577,
        0.00021555937787092112,
        8.885813432343487e-05,
        -7.002327157325305e-05,
        -0.0001959716387052401,
        -0.00022546587843634027,
        -0.00013752261783398788,
        0.00012418992449951172,
    ];

    // PRINet's dense path is real f64 throughout; the residual difference is
    // torch's pairwise reduction order, not an f32 truncation.
    assert_close(&d.dphase, &expected_dphase, FULL_RTOL, FULL_ATOL);
    assert_close(&d.damplitude, &expected_damplitude, FULL_RTOL, FULL_ATOL);
    assert_close(&d.dfrequency, &expected_dfrequency, FULL_RTOL, FULL_ATOL);
}

#[test]
fn parity_intra_band_sparse_knn_matches_prinet_kuramoto() {
    // sparse_knn is the coupling mode PRINet's ThetaGammaNetwork and
    // DeltaThetaGammaNetwork give their per-band KuramotoOscillator.
    let net = tg_network(CouplingMode::SparseKnn { k: Some(2) }, 0.0, 0.0);
    let d = net.compute_derivatives(&tg_state()).unwrap();

    let expected_dphase = [
        5.022665833441247,
        5.356320698023542,
        6.206806368215397,
        7.349367485780168,
        34.9485292806416,
        36.644874012751785,
        38.03080808979001,
        39.903367346914344,
        41.148530932934875,
        42.36609674779749,
        44.191188745643885,
        44.83903341480018,
    ];
    let expected_damplitude = [
        0.43107818715540036,
        0.3783314687968663,
        -0.5233906575005915,
        -0.4933019103648294,
        1.3639238470662893,
        1.4412195675663704,
        1.3201203350611619,
        1.4629264839332012,
        1.509297012397953,
        1.1969872330716225,
        1.1569262698538352,
        0.983569969815422,
    ];
    let expected_dfrequency = [
        0.0001133291672062331,
        -0.0007183965098822903,
        -0.0014659681589230152,
        0.0017468374289008421,
        -0.0002573535967919982,
        0.0007243700637589201,
        0.0001540404489500258,
        -0.0004831632654282675,
        0.0007426546646743759,
        -0.0006695162610125466,
        0.00095594372821941,
        -0.0008048329259991039,
    ];

    assert_close(&d.dphase, &expected_dphase, F64_RTOL, F64_ATOL);
    assert_close(&d.damplitude, &expected_damplitude, F64_RTOL, F64_ATOL);
    assert_close(&d.dfrequency, &expected_dfrequency, F64_RTOL, F64_ATOL);
}

// ==================================================================
// 2. Composed right-hand side (intra-band + PAC relaxation)
// ==================================================================

#[test]
fn parity_composed_theta_gamma_mean_field() {
    let net = tg_network(CouplingMode::MeanField, PAC_DEPTH, PAC_OFFSET);
    let d = net.compute_derivatives(&tg_state()).unwrap();

    let expected_damplitude = [
        0.3227836825439335,
        0.2359486418707898,
        -0.3301397807605088,
        -0.28970600106740796,
        -0.182821694808131,
        -0.0432424475740637,
        0.034915217861938935,
        0.046617119330797346,
        -0.018656060440227773,
        -0.18600769186695779,
        -0.254798320605522,
        -0.2807005372963863,
    ];
    assert_close(&d.damplitude, &expected_damplitude, MF_RTOL, MF_ATOL);
}

#[test]
fn parity_composed_theta_gamma_sparse_knn() {
    let net = tg_network(
        CouplingMode::SparseKnn { k: Some(2) },
        PAC_DEPTH,
        PAC_OFFSET,
    );
    let d = net.compute_derivatives(&tg_state()).unwrap();

    let expected_damplitude = [
        0.43107818715540036,
        0.3783314687968663,
        -0.5233906575005915,
        -0.4933019103648294,
        1.3398895385998812,
        1.4195886899466033,
        1.293682595748113,
        1.4376904600434728,
        1.4864644193548653,
        1.1693477783352533,
        1.1364971076573884,
        0.959535661349014,
    ];
    assert_close(&d.damplitude, &expected_damplitude, F64_RTOL, F64_ATOL);
}

#[test]
fn parity_composed_delta_theta_gamma_cascade() {
    let net = dtg_network();
    let d = net.compute_derivatives(&dtg_state()).unwrap();

    let expected_dphase = [
        1.8773703524441654,
        1.4624180515727827,
        2.959265982901415,
        5.217533469451431,
        5.184774022473835,
        6.095652448210613,
        7.44019609918461,
        35.175952174933414,
        36.67244752040135,
        38.07108648763356,
        39.943981338915414,
        40.84322264182107,
        42.319627272946065,
        43.88998191433744,
        45.099351987402784,
    ];
    let expected_damplitude = [
        0.3639767039011762,
        0.1320847446762785,
        -0.4530894433633359,
        0.30599903152376823,
        0.21580706064659141,
        -0.34356750157664107,
        -0.30816911718958984,
        -0.17763259502340517,
        -0.03857225776781045,
        0.04062322762513736,
        0.052065674104759485,
        -0.01372641564473823,
        -0.18004022711452305,
        -0.25038758578850506,
        -0.2755114375116604,
    ];

    assert_close(&d.dphase, &expected_dphase, MF_RTOL, MF_ATOL);
    assert_close(&d.damplitude, &expected_damplitude, MF_RTOL, MF_ATOL);
}

// ==================================================================
// 3. Golden RK4 trajectories
// ==================================================================

fn rk4_trajectory(net: &BandNetwork, state: &OscillatorState, n: usize) -> OscillatorState {
    let mut rk4 = RK4Integrator::new();
    integrate_fixed(&mut rk4, net, state, n, 0.01, false)
        .unwrap()
        .0
}

#[test]
fn parity_golden_trajectory_theta_gamma_mean_field_1_step() {
    let net = tg_network(CouplingMode::MeanField, PAC_DEPTH, PAC_OFFSET);
    let out = rk4_trajectory(&net, &tg_state(), 1);
    let expected_phase = [
        0.1521740882270373,
        1.3517827878611899,
        2.7609329206491795,
        4.974491042947392,
        0.5516650017737521,
        1.2665805727231463,
        2.080578383978682,
        2.7993746767634273,
        3.508476677288848,
        4.323349620417573,
        5.0390897283865295,
        6.251052065754424,
    ];
    let expected_amplitude = [
        1.0032960636755406,
        1.202383026817632,
        0.7966218622287828,
        1.0971619832316584,
        0.9982705198156993,
        0.8995923799751396,
        1.1002641516561769,
        1.0503086513310818,
        0.9496437666302127,
        1.1480402416647182,
        0.8474686676285599,
        0.9973799144422247,
    ];
    assert_close(&out.phase, &expected_phase, MF_RTOL, MF_ATOL);
    assert_close(&out.amplitude, &expected_amplitude, MF_RTOL, MF_ATOL);
}

#[test]
fn parity_golden_trajectory_theta_gamma_mean_field_10_steps() {
    let net = tg_network(CouplingMode::MeanField, PAC_DEPTH, PAC_OFFSET);
    let out = rk4_trajectory(&net, &tg_state(), 10);
    let expected_phase = [
        0.6219368598970039,
        1.8117824100145257,
        3.3070759757460384,
        5.652922336435722,
        3.7121055526578988,
        4.554947896148268,
        5.494228861041258,
        0.10522894779233205,
        0.90618010352081,
        1.8641767700157907,
        2.7225683302996444,
        4.027214279977153,
    ];
    let expected_amplitude = [
        1.039508328802522,
        1.22648354408921,
        0.758987733637268,
        1.0779047538644146,
        0.9924166777205515,
        0.9003737449328589,
        1.0970977310986447,
        1.0401122910588647,
        0.9327033125122811,
        1.1243222295782398,
        0.8299024375541004,
        0.9898383453347086,
    ];
    let expected_frequency = [
        5.000054835331001,
        5.499904467260983,
        6.499892703087724,
        7.000132290225853,
        35.00001513090876,
        36.50000618419614,
        37.99999278619945,
        39.99998551857639,
        40.999986707733775,
        42.49999670320157,
        44.00000719199618,
        45.00001299860862,
    ];
    assert_close(&out.phase, &expected_phase, MF_TRAJ_RTOL, MF_TRAJ_ATOL);
    assert_close(
        &out.amplitude,
        &expected_amplitude,
        MF_TRAJ_RTOL,
        MF_TRAJ_ATOL,
    );
    assert_close(
        &out.frequency,
        &expected_frequency,
        MF_TRAJ_RTOL,
        MF_TRAJ_ATOL,
    );
}

#[test]
fn parity_golden_trajectory_theta_gamma_sparse_knn_1_step() {
    let net = tg_network(
        CouplingMode::SparseKnn { k: Some(2) },
        PAC_DEPTH,
        PAC_OFFSET,
    );
    let out = rk4_trajectory(&net, &tg_state(), 1);
    let expected_phase = [
        0.15028763309615223,
        1.353516410698619,
        2.7619839259734507,
        4.973553013939325,
        0.5499512792102169,
        1.2664406727395712,
        2.080335073533645,
        2.7990066561928764,
        3.511479570048223,
        4.323663001304227,
        5.041851183116645,
        6.247976124168858,
    ];
    let expected_amplitude = [
        1.0044219588052994,
        1.2037363293703098,
        0.7946850424231111,
        1.0951660404014543,
        1.013727950429609,
        0.9141695310954103,
        1.112917606006096,
        1.064362732180393,
        0.9648525300021003,
        1.1616825135055218,
        0.8613182377809624,
        1.0099326866701188,
    ];
    assert_close(&out.phase, &expected_phase, F64_RTOL, F64_ATOL);
    assert_close(&out.amplitude, &expected_amplitude, F64_RTOL, F64_ATOL);
}

#[test]
fn parity_golden_trajectory_theta_gamma_sparse_knn_10_steps() {
    let net = tg_network(
        CouplingMode::SparseKnn { k: Some(2) },
        PAC_DEPTH,
        PAC_OFFSET,
    );
    let out = rk4_trajectory(&net, &tg_state(), 10);
    let expected_phase = [
        0.6086174391601085,
        1.8304033486199924,
        3.3123836218677947,
        5.640747159626389,
        3.7025290638725927,
        4.567422222841996,
        5.505622275705788,
        0.10476794979702042,
        0.9309382888593791,
        1.8534375270096035,
        2.729449365705425,
        3.995681190365639,
    ];
    let expected_amplitude = [
        1.054100539897697,
        1.233714393652547,
        0.7392936612324414,
        1.060958303275761,
        1.1477239872506262,
        1.0415544403783346,
        1.2260004120198555,
        1.1909984323253455,
        1.0963515104593213,
        1.2646957131523104,
        0.9632835257511372,
        1.1321605424045829,
    ];
    let expected_frequency = [
        5.000043079126406,
        5.49990203893065,
        6.499811961688106,
        7.00020368725968,
        35.000012625405446,
        36.50008709261594,
        38.00002810537273,
        39.999939780423595,
        41.00007059999049,
        42.49993313086302,
        44.00006315431714,
        44.99989437571008,
    ];
    assert_close(&out.phase, &expected_phase, F64_RTOL, F64_ATOL);
    assert_close(&out.amplitude, &expected_amplitude, F64_RTOL, F64_ATOL);
    assert_close(&out.frequency, &expected_frequency, F64_RTOL, F64_ATOL);
}

#[test]
fn parity_golden_trajectory_delta_theta_gamma_10_steps() {
    let net = dtg_network();
    let out = rk4_trajectory(&net, &dtg_state(), 10);
    let expected_phase = [
        0.5902134389907785,
        2.340761905094757,
        5.403849651522379,
        0.6219171858231298,
        1.811818692263936,
        3.307116171723409,
        5.652871492829644,
        3.712107853946659,
        4.554948310465399,
        5.49422698467149,
        0.10522623232105399,
        0.9061781809681102,
        1.8641770644581839,
        2.7225703847562457,
        4.027216319004962,
    ];
    let expected_amplitude = [
        1.0419277725776799,
        1.315678995708501,
        0.6554561422621198,
        1.0376574276816433,
        1.2243001265995044,
        0.7576382949226368,
        1.0759867837537302,
        0.992746258385054,
        0.9006728181692892,
        1.0974621507250284,
        1.0404577414942244,
        0.9330130162086601,
        1.1246954986904607,
        0.8301779498020178,
        0.9901670718031294,
    ];
    assert_close(&out.phase, &expected_phase, MF_TRAJ_RTOL, MF_TRAJ_ATOL);
    assert_close(
        &out.amplitude,
        &expected_amplitude,
        MF_TRAJ_RTOL,
        MF_TRAJ_ATOL,
    );
}

// ==================================================================
// 4. Capacity invariant vs PRINet's MultiRateIntegrator sub-step count
// ==================================================================

#[test]
fn parity_capacity_matches_prinet_sub_step_count() {
    // PRINet `ThetaGammaNetwork.__init__` builds
    // `MultiRateIntegrator(sub_steps=max(1, int(gamma_freq / max(theta_freq, 1e-6))))`.
    // PRIN exposes the same ratio as `theoretical_capacity`.
    let cases: [(f64, f64, usize); 4] = [
        (6.0, 40.0, 6),
        (4.0, 30.0, 7),
        (8.0, 50.0, 6),
        (2.0, 45.0, 22),
    ];
    let net = tg_network(CouplingMode::MeanField, PAC_DEPTH, PAC_OFFSET);
    for (theta_freq, gamma_freq, expected) in cases {
        let mut freq = vec![theta_freq; 4];
        freq.extend(vec![gamma_freq; 8]);
        let mut bands = vec![0u32; 4];
        bands.extend(vec![1u32; 8]);
        let state = OscillatorState::new(vec![0.0; 12], vec![1.0; 12], freq, Some(bands)).unwrap();
        assert_eq!(
            net.theoretical_capacity(&state).unwrap(),
            expected,
            "capacity mismatch for f_theta={theta_freq}, f_gamma={gamma_freq}"
        );
    }
}
