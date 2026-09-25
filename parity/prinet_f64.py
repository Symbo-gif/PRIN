"""Test-local float64 evaluation of PRINet 3.0's DV-007 ``complex64`` paths.

PRINet 3.0 builds its oscillator models with ``dtype=torch.float64`` but
evaluates three derivative paths in ``torch.complex64`` (float32 precision):

* ``StuartLandauOscillator.compute_derivatives`` — ``exp(±iφ)``, ``ω`` and
  ``r²`` are cast to ``complex64`` (``oscillator_models.py`` lines 575-593);
* ``KuramotoOscillator._compute_derivatives_mean_field`` and
* ``HopfOscillator._compute_derivatives_mean_field`` — the complex order
  parameter is formed from ``phase.to(torch.complex64)`` and its modulus and
  angle are narrowed with ``.float()`` (lines 362-364 and 732-734).

PRIN evaluates the same equations in float64. Deferred Validation item DV-007
accepts the difference as a reference-implementation hazard. The EXP-001 D1
correction (campaign plan §10.4 item 3) must go further and *positively
demonstrate* that a PRIN-vs-reference breach on these paths is explained by
exactly this arithmetic and nothing else — the amendment #25 pattern. It does
so by re-evaluating the reference with only those casts widened.

:func:`f64_corrected_reference` temporarily replaces exactly the three methods
above with statement-for-statement copies in which every ``complex64`` becomes
``complex128`` and every ``.float()`` becomes ``.to(self._dtype)``. Nothing
else in PRINet 3.0 changes: integrators, amplitude guards, coupling matrices,
k-NN selection, and metrics are the archived code as-is. The replacement is
process-local and undone on exit, so it cannot leak into a test that compares
against the unmodified reference.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import torch
from prin.parity.schema import Coupling, Model
from prinet.core.propagation import oscillator_models as _om

_Derivatives = tuple[torch.Tensor, torch.Tensor, torch.Tensor]


def on_dv007_path(model: str, coupling: str) -> bool:
    """Return whether PRINet 3.0 evaluates this case's derivatives in complex64.

    Stuart-Landau is affected for every coupling (PRINet 3.0 implements only
    the dense coupling matrix for it); Kuramoto and Hopf are affected only in
    mean-field mode.
    """
    return model == Model.STUART_LANDAU.value or (
        coupling == Coupling.MEAN_FIELD.value
        and model in (Model.KURAMOTO.value, Model.HOPF.value)
    )


def _stuart_landau_f64(self: Any, state: Any) -> _Derivatives:
    """``StuartLandauOscillator.compute_derivatives`` with complex128 casts."""
    phase = state.phase
    amp = state.amplitude
    freq = state.frequency
    z = amp * torch.exp(1j * phase.to(torch.float64)).to(torch.complex128)
    coupling = self.coupling_matrix
    z_diff = z.unsqueeze(-2) - z.unsqueeze(-1)
    coupling_term = (coupling * z_diff).sum(dim=-1)
    dz = (
        (self._mu + 1j * freq.to(torch.complex128)) * z
        - (amp**2).to(torch.complex128) * z
        + coupling_term
    )
    dz_rotated = dz * torch.exp(-1j * phase.to(torch.float64)).to(torch.complex128)
    dr = dz_rotated.real.to(self._dtype)
    dphi_raw = dz_rotated.imag.to(self._dtype)
    safe_amp = torch.clamp(amp, min=1e-8)
    dphi = dphi_raw / safe_amp
    domega = torch.zeros_like(freq)
    return dphi, dr, domega


def _kuramoto_mean_field_f64(self: Any, state: Any) -> _Derivatives:
    """``KuramotoOscillator._compute_derivatives_mean_field`` in float64."""
    phase = state.phase
    amp = state.amplitude
    freq = state.frequency
    z = (amp * torch.exp(1j * phase.to(torch.complex128))).mean(dim=-1)
    R = z.abs().to(self._dtype)
    psi = z.angle().to(self._dtype)
    K = self._K
    dphi = freq + K * R.unsqueeze(-1) * torch.sin(psi.unsqueeze(-1) - phase)
    dr = -self._decay * amp + K * R.unsqueeze(-1) * torch.cos(psi.unsqueeze(-1) - phase)
    domega = (
        self._gamma
        * K
        * R.unsqueeze(-1)
        * torch.sin(psi.unsqueeze(-1) - phase)
        / self._n
    )
    return dphi, dr, domega


def _hopf_mean_field_f64(self: Any, state: Any) -> _Derivatives:
    """``HopfOscillator._compute_derivatives_mean_field`` in float64."""
    phase = state.phase
    amp = state.amplitude
    freq = state.frequency
    z = (amp * torch.exp(1j * phase.to(torch.complex128))).mean(dim=-1)
    R = z.abs().to(self._dtype)
    psi = z.angle().to(self._dtype)
    K = self._K
    safe_amp = torch.clamp(amp, min=1e-8)
    dphi = freq + K * R.unsqueeze(-1) * torch.sin(psi.unsqueeze(-1) - phase) / safe_amp
    dr = (
        self._mu * amp
        - amp**3
        + K * R.unsqueeze(-1) * torch.cos(psi.unsqueeze(-1) - phase)
    )
    domega = (
        self._gamma
        * K
        * R.unsqueeze(-1)
        * torch.sin(psi.unsqueeze(-1) - phase)
        / self._n
    )
    return dphi, dr, domega


_REPLACEMENTS: tuple[tuple[type[Any], str, Any], ...] = (
    (_om.StuartLandauOscillator, "compute_derivatives", _stuart_landau_f64),
    (
        _om.KuramotoOscillator,
        "_compute_derivatives_mean_field",
        _kuramoto_mean_field_f64,
    ),
    (_om.HopfOscillator, "_compute_derivatives_mean_field", _hopf_mean_field_f64),
)


@contextmanager
def f64_corrected_reference() -> Iterator[None]:
    """Evaluate PRINet 3.0's three DV-007 paths in float64 inside the block.

    Every other PRINet 3.0 behaviour is unchanged. The original methods are
    restored on exit, including when the block raises.
    """
    originals = [(cls, name, cls.__dict__[name]) for cls, name, _ in _REPLACEMENTS]
    try:
        for cls, name, replacement in _REPLACEMENTS:
            setattr(cls, name, replacement)
        yield
    finally:
        for cls, name, original in originals:
            setattr(cls, name, original)
