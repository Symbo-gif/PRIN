"""Shared ``torch.autograd.Function`` glue for the Rust-backed bridges.

WP-025's ``ResonanceLayer``/``GatedPhaseActivation`` each hand-wrote a
dedicated ``torch.autograd.Function`` subclass for their single-input,
single-output ``forward``/``backward`` shape. Exec-WP-026 S1 adds ten more
differentiable entry points across seven modules, several with two tensor
inputs and/or two tensor outputs (see
``crates/prin-py/src/bindings/train_support.rs``'s module docs for the
Rust-side counterpart of this reuse). :func:`apply_rust_bridge` generalizes
the WP-025 pattern to arbitrary tensor input/output arity so each entry point
below is a few lines of glue instead of a bespoke subclass:

- `bridge_forward` is a callable — typically a bound PyO3 bridge method, or a
  small closure over one when the Rust signature also takes non-tensor
  arguments (e.g. a `prin._prin_core.Seed`) interleaved with the
  differentiable tensor arguments — that accepts exactly `len(tensors)`
  positional (detached) tensor arguments and returns
  `(*output_capsules, rust_ctx)`; each capsule is decoded via
  :func:`torch.utils.dlpack.from_dlpack` and `rust_ctx` is stashed on the
  autograd context.
- `backward` calls `rust_ctx.backward(*grad_output_capsules)`, which returns
  one gradient (a DLPack capsule, or ``None`` for a non-differentiable
  optional input such as an omitted `phase`/`prev_slots` argument) per
  tensor `apply_rust_bridge` was given.

Regular differentiable inputs must share dtype/device. Canonical module
parameters may follow those inputs from ``parameter_start`` onward; each
parameter keeps its own output/VJP dtype and device so a ``float64`` parameter
can accompany a ``float32`` activation. Every tensor is marshalled as
contiguous ``float64`` CPU storage for Rust while Burn retains numerical
authority.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import torch
from torch.utils.dlpack import from_dlpack

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: list[str] = ["apply_rust_bridge"]


class _RustBridgeFunction(torch.autograd.Function):
    """Generic ``torch.autograd.Function`` over an arity-erased Rust bridge method.

    See the module docs for the ``forward``/``backward`` contract.
    """

    @staticmethod
    def forward(
        ctx: torch.autograd.function.FunctionCtx,
        bridge_forward: Callable[..., tuple[Any, ...]],
        n_tensor_inputs: int,
        parameter_start: int,
        *tensors: torch.Tensor | None,
    ) -> Any:
        """Call `bridge_forward` and decode every DLPack capsule it returns.

        Decodes every output capsule `bridge_forward` returns except the
        trailing Rust context object. `n_tensor_inputs` is unused beyond
        documenting the arity `tensors` must match; PyTorch itself infers it
        from `*tensors`. `parameter_start` separates regular inputs, which must
        share dtype/device, from canonical parameters with independent specs.
        """
        del n_tensor_inputs
        specs = tuple(
            None if tensor is None else (tensor.dtype, tensor.device)
            for tensor in tensors
        )
        regular_specs = tuple(
            spec for spec in specs[:parameter_start] if spec is not None
        )
        output_spec = regular_specs[0]
        if any(spec != output_spec for spec in regular_specs[1:]):
            raise ValueError("Rust bridge tensor inputs must share dtype and device")
        detached = tuple(
            None
            if tensor is None
            else tensor.detach().to(dtype=torch.float64, device="cpu").contiguous()
            for tensor in tensors
        )
        *out_capsules, rust_ctx = bridge_forward(*detached)
        outputs = tuple(
            from_dlpack(cap).to(dtype=output_spec[0], device=output_spec[1])
            for cap in out_capsules
        )
        ctx.rust_ctx = rust_ctx  # type: ignore[attr-defined]
        ctx.input_specs = specs  # type: ignore[attr-defined]
        return outputs if len(outputs) > 1 else outputs[0]

    @staticmethod
    def backward(
        ctx: torch.autograd.function.FunctionCtx, *grad_outputs: torch.Tensor
    ) -> tuple[torch.Tensor | None, ...]:
        """Run the saved Rust context's ``backward`` and decode its gradients.

        Calls it with the (contiguous) upstream cotangents and decodes each
        returned gradient capsule (or passes through ``None`` for a
        non-differentiable input).
        """
        rust_ctx = ctx.rust_ctx  # type: ignore[attr-defined]
        input_specs = ctx.input_specs  # type: ignore[attr-defined]
        grads = rust_ctx.backward(
            *(
                gradient.detach().to(dtype=torch.float64, device="cpu").contiguous()
                for gradient in grad_outputs
            )
        )
        if isinstance(grads, list):
            grads = tuple(grads)
        elif not isinstance(grads, tuple):
            grads = (grads,)
        decoded: tuple[torch.Tensor | None, ...] = tuple(
            None
            if gradient is None or spec is None
            else from_dlpack(gradient).to(dtype=spec[0], device=spec[1])
            for gradient, spec in zip(grads, input_specs, strict=True)
        )
        # Three leading `None`s for the non-tensor `bridge_forward`,
        # `n_tensor_inputs`, and `parameter_start` arguments `forward`
        # received.
        return (None, None, None, *decoded)


def apply_rust_bridge(
    bridge_forward: Callable[..., tuple[Any, ...]],
    tensors: Sequence[torch.Tensor | None],
    *,
    parameter_start: int | None = None,
) -> Any:
    """Apply a Rust bridge's ``forward`` method as a differentiable call.

    Args:
        bridge_forward: A callable accepting exactly `len(tensors)`
            positional (DLPack-compatible) tensor arguments and returning
            `(*output_capsules, rust_ctx)`. Typically a bound PyO3 bridge
            method (e.g. `bridge.encode`) directly; when the Rust method also
            takes non-tensor arguments interleaved with the differentiable
            ones (e.g. a `prin._prin_core.Seed`), pass a small closure that
            captures them and forwards `tensors` at the right positions
            (e.g. ``lambda d, p: bridge.process_frame(d, seed, p)``).
        tensors: The differentiable tensor inputs, in the order
            `bridge_forward` expects them. A ``None`` entry marks an absent
            optional differentiable input (e.g. `OscillatoryAttention`'s
            `phase` when not supplied) and is passed through as ``None``
            rather than detached.
        parameter_start: Index of the first canonical parameter tensor, if any.
            Entries before this index are regular inputs and must share
            dtype/device; entries from this index onward retain independent
            output/VJP dtype/device specs.

    Returns:
        A single output tensor, or a tuple of tensors if the bridge method
        returns more than one.
    """
    first_parameter = len(tensors) if parameter_start is None else parameter_start
    if not 0 < first_parameter <= len(tensors):
        raise ValueError("parameter_start must identify a suffix of tensors")
    result: Any = _RustBridgeFunction.apply(  # type: ignore[no-untyped-call, unused-ignore]
        bridge_forward, len(tensors), first_parameter, *tensors
    )
    return result
