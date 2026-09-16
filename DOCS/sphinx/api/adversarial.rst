Adversarial API (``prin.adversarial_tools``)
============================================

FGSM and PGD attacks on input detection features, for evaluating the
adversarial robustness of :class:`prin.nn.temporal_compat.PhaseTracker`
against :class:`prin.nn.temporal_compat.TemporalSlotAttentionMOT`.

Faithful port of PRINet 3.0 ``prinet.utils.adversarial_tools`` (Testing
Standards §1.1). The attack construction is tensor arithmetic on the input;
the statistical evaluation harnesses that consume attack results
(``adversarial_evaluate_*``) live in :mod:`prin.experiments`.

Attacks are seeded explicitly — no hidden RNG (Project Plan §4 rule 4).

.. automodule:: prin.adversarial_tools
   :members:
