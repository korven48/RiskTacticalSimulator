"""Motor de simulacion Monte Carlo.

Ejecuta miles de batallas con los mismos parametros y agrega
los resultados en un informe estadistico completo.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from pydantic import BaseModel

from risk_simulator.core.entities import BattleState
from risk_simulator.core.use_cases import BattleResult, simulate_battle


class MonteCarloResult(BaseModel):
    """Informe estadistico completo de un escenario (N, M).

    Attributes:
        attacker: Tropas iniciales del atacante.
        defender: Tropas iniciales del defensor.
        simulations: Numero de simulaciones ejecutadas.
        attacker_win_prob: Probabilidad estimada de victoria del atacante.
        defender_win_prob: Probabilidad estimada de victoria del defensor.
        avg_attacker_survivors_if_win: Media de supervivientes del atacante
            condicionada a que el atacante gane.
        std_attacker_survivors_if_win: Desviacion estandar de supervivientes
            del atacante condicionada a que el atacante gane.
        avg_defender_survivors_if_win: Media de supervivientes del defensor
            condicionada a que el defensor gane.
        std_defender_survivors_if_win: Desviacion estandar de supervivientes
            del defensor condicionada a que el defensor gane.
        avg_attacker_losses: Bajas medias del atacante (incondicional).
        avg_defender_losses: Bajas medias del defensor (incondicional).
        avg_rounds: Media de rondas por batalla.
        std_rounds: Desviacion estandar de rondas por batalla.
        median_rounds: Mediana de rondas.
        p90_rounds: Percentil 90 de rondas.
        expected_cost_if_win: Coste esperado en tropas si el atacante gana.
        expected_cost_per_success: Coste por conquista exitosa
            (expected_cost_if_win / attacker_win_prob).
    """

    attacker: int
    defender: int
    simulations: int

    # --- Probabilidades ---
    attacker_win_prob: float
    defender_win_prob: float

    # --- Supervivientes condicionados ---
    avg_attacker_survivors_if_win: float
    std_attacker_survivors_if_win: float
    avg_defender_survivors_if_win: float
    std_defender_survivors_if_win: float

    # --- Bajas ---
    avg_attacker_losses: float
    avg_defender_losses: float

    # --- Duracion ---
    avg_rounds: float
    std_rounds: float
    median_rounds: int
    p90_rounds: int

    # --- Decision ---
    expected_cost_if_win: float
    expected_cost_per_success: float

    model_config = {
        "frozen": True,
    }


def _percentile(sorted_data: list[int], p: float) -> int:
    """Calcula el percentil p de una lista ya ordenada.

    Usa el metodo de interpolacion 'nearest'.

    Args:
        sorted_data: Lista de valores ordenados de menor a mayor.
        p: Percentil deseado, entre 0 y 100.

    Returns:
        Valor del percentil.
    """
    k = int(math.ceil(p / 100 * len(sorted_data))) - 1
    return sorted_data[max(0, k)]


def _std(values: Sequence[int | float], mean: float) -> float:
    """Calcula la desviacion estandar poblacional.

    Args:
        values: Lista de valores.
        mean: Media ya calculada.

    Returns:
        Desviacion estandar poblacional. 0.0 si la lista esta vacia.
    """
    if not values:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def run_monte_carlo(
    initial_state: BattleState,
    simulations: int = 10_000,
    rng: random.Random | None = None,
) -> MonteCarloResult:
    """Ejecuta K simulaciones Monte Carlo y agrega los resultados.

    Args:
        initial_state: Estado inicial de la batalla.
        simulations: Numero de simulaciones a ejecutar.
        rng: Generador de numeros aleatorios. Si es None, se crea
            uno nuevo por defecto.

    Returns:
        MonteCarloResult con el informe estadistico completo.
    """
    if rng is None:
        rng = random.Random()

    results: list[BattleResult] = []
    for _ in range(simulations):
        result = simulate_battle(initial_state, rng=rng)
        results.append(result)

    # --- Clasificar resultados por ganador ---
    attacker_wins: list[BattleResult] = []
    defender_wins: list[BattleResult] = []
    for r in results:
        if r.winner == "attacker":
            attacker_wins.append(r)
        else:
            defender_wins.append(r)

    n_att_wins = len(attacker_wins)
    n_def_wins = len(defender_wins)

    # --- Probabilidades ---
    attacker_win_prob = n_att_wins / simulations
    defender_win_prob = n_def_wins / simulations

    # --- Supervivientes condicionados al ganador ---
    att_survivors = [r.attacker_survivors for r in attacker_wins]
    def_survivors = [r.defender_survivors for r in defender_wins]

    avg_att_surv = sum(att_survivors) / n_att_wins if n_att_wins else 0.0
    std_att_surv = _std(att_survivors, avg_att_surv)

    avg_def_surv = sum(def_survivors) / n_def_wins if n_def_wins else 0.0
    std_def_surv = _std(def_survivors, avg_def_surv)

    # --- Bajas incondicionales ---
    att_n = initial_state.attacker
    def_n = initial_state.defender
    avg_att_losses = sum(att_n - r.attacker_survivors for r in results) / simulations
    avg_def_losses = sum(def_n - r.defender_survivors for r in results) / simulations

    # --- Duracion ---
    all_rounds = [r.rounds for r in results]
    avg_rounds = sum(all_rounds) / simulations
    std_rounds = _std(all_rounds, avg_rounds)

    sorted_rounds = sorted(all_rounds)
    median_rounds = _percentile(sorted_rounds, 50)
    p90_rounds = _percentile(sorted_rounds, 90)

    # --- Metricas de decision ---
    cost_if_win = (att_n - avg_att_surv) if avg_att_surv > 0 else 0.0
    cost_per_success = cost_if_win / attacker_win_prob if attacker_win_prob > 0 else float("inf")

    return MonteCarloResult(
        attacker=att_n,
        defender=def_n,
        simulations=simulations,
        attacker_win_prob=attacker_win_prob,
        defender_win_prob=defender_win_prob,
        avg_attacker_survivors_if_win=avg_att_surv,
        std_attacker_survivors_if_win=std_att_surv,
        avg_defender_survivors_if_win=avg_def_surv,
        std_defender_survivors_if_win=std_def_surv,
        avg_attacker_losses=avg_att_losses,
        avg_defender_losses=avg_def_losses,
        avg_rounds=avg_rounds,
        std_rounds=std_rounds,
        median_rounds=median_rounds,
        p90_rounds=p90_rounds,
        expected_cost_if_win=cost_if_win,
        expected_cost_per_success=cost_per_success,
    )
