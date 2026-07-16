# prin-dynamics

Fundamental oscillator dynamics for PRIN: oscillator state (struct-of-arrays),
Kuramoto / Stuart–Landau / Hopf models, Euler / RK4 / RK45 / exponential /
multi-rate integrators, phase–amplitude coupling, coupling topologies,
continuous hierarchical band networks, and temporal propagation.

Rebuild target for PRINet 3.0 modules:
`core/propagation/{oscillator_state,oscillator_models,integrators,coupling,networks,temporal}.py`.

See `DOCS/PRIN_Project_Plan.md` §6 for the full module mapping and §7 for the
numerical invariants this crate must preserve.
