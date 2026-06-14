"""Reusable local-first engines for Paideia-style AI growth systems.

The orchestration engine is imported lazily so that individual engines remain
usable even if optional modules are not present in a partial checkout.
"""

from __future__ import annotations

from importlib.util import find_spec

if find_spec("paideia_engines.orchestration") is not None:
    from .orchestration import PaideiaEngineSuite  # pragma: no cover
    __all__ = ["PaideiaEngineSuite"]
else:
    __all__ = []
