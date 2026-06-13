"""Casos de uso del dominio de combate.

Orquesta la logica de negocio combinando entidades y servicios
para resolver batallas completas.
"""

from __future__ import annotations

import random
from typing import Literal

from pydantic import BaseModel, Field

from risk_simulator.core.entities import BattleState
from risk_simulator.core.round_resolver import resolve_round


class BattleResult(BaseModel):
    """Resultado de una batalla completa.

    Attributes:
        winner: Bando ganador ("attacker" o "defender").
        attacker_survivors: Tropas restantes del atacante al finalizar.
        defender_survivors: Tropas restantes del defensor al finalizar.
        rounds: Numero total de rondas disputadas.
    """

    winner: Literal["attacker", "defender"]
    attacker_survivors: int = Field(..., ge=1)
    defender_survivors: int = Field(..., ge=0)
    rounds: int = Field(..., ge=0)

    model_config = {
        "frozen": True,
    }


def simulate_battle(
    initial_state: BattleState,
    rng: random.Random | None = None,
) -> BattleResult:
    """Simula una batalla completa hasta que un bando gane.

    Ejecuta rondas sucesivas llamando a resolve_round hasta
    alcanzar la condicion de victoria. Si el estado inicial ya
    ha terminado, devuelve el resultado directamente con 0 rondas.

    Args:
        initial_state: Estado inicial de la batalla.
        rng: Generador de numeros aleatorios. Si es None, se crea
            uno nuevo por defecto.

    Returns:
        BattleResult con el ganador, supervivientes y numero de rondas.
    """
    if rng is None:
        rng = random.Random()

    state = initial_state
    rounds = 0

    while not state.is_over():
        state = resolve_round(state, rng)
        rounds += 1

    winner = state.winner
    if winner is None:
        msg = "Estado inconsistente: is_over() es True pero winner es None."
        raise AssertionError(msg)

    return BattleResult(
        winner=winner,
        attacker_survivors=state.attacker,
        defender_survivors=state.defender,
        rounds=rounds,
    )
