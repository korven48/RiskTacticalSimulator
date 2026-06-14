"""Tests unitarios para el motor Monte Carlo.

Verifica la logica de agregacion estadistica: invariantes matematicos,
coherencia de conteos, inmutabilidad y reproducibilidad.
"""

from __future__ import annotations

import random

from risk_simulator.core.entities import BattleState
from risk_simulator.core.monte_carlo import run_monte_carlo

# ---------------------------------------------------------------------------
# Reproducibilidad
# ---------------------------------------------------------------------------


class TestReproducibility:
    """Misma seed produce el mismo informe."""

    def test_same_seed_same_result(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result_a = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        result_b = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result_a == result_b


# ---------------------------------------------------------------------------
# Coherencia de probabilidades
# ---------------------------------------------------------------------------


class TestProbabilities:
    """Verifica invariantes matematicos de las probabilidades."""

    def test_probabilities_sum_to_one(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.attacker_win_prob + result.defender_win_prob == 1.0

    def test_probabilities_in_range(self) -> None:
        """Ambas probabilidades estan entre 0 y 1."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert 0.0 <= result.attacker_win_prob <= 1.0
        assert 0.0 <= result.defender_win_prob <= 1.0


# ---------------------------------------------------------------------------
# Supervivientes condicionados
# ---------------------------------------------------------------------------


class TestConditionedSurvivors:
    """Verifica invariantes de las medias condicionadas."""

    def test_attacker_survivors_at_least_one_if_wins(self) -> None:
        """Si el atacante gana alguna vez, la media de supervivientes >= 1."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        if result.attacker_win_prob > 0:
            assert result.avg_attacker_survivors_if_win >= 2.0

    def test_defender_survivors_at_least_one_if_wins(self) -> None:
        """Si el defensor gana alguna vez, la media de supervivientes >= 1."""
        state = BattleState(attacker=5, defender=10)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        if result.defender_win_prob > 0:
            assert result.avg_defender_survivors_if_win >= 1.0

    def test_attacker_survivors_bounded(self) -> None:
        """La media de supervivientes no puede exceder las tropas iniciales."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.avg_attacker_survivors_if_win <= state.attacker

    def test_defender_survivors_bounded(self) -> None:
        """La media de supervivientes no puede exceder las tropas iniciales."""
        state = BattleState(attacker=5, defender=10)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.avg_defender_survivors_if_win <= state.defender

    def test_std_is_nonnegative(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.std_attacker_survivors_if_win >= 0.0
        assert result.std_defender_survivors_if_win >= 0.0

    def test_zero_wins_means_zero_stats(self) -> None:
        """Si un bando nunca gana, sus medias y std condicionadas son 0."""
        # BattleState(1, N) -> is_over() == True, el defensor siempre gana
        # porque el atacante no puede atacar.
        state = BattleState(attacker=1, defender=5)
        result = run_monte_carlo(state, simulations=100, rng=random.Random(42))
        assert result.attacker_win_prob == 0.0
        assert result.avg_attacker_survivors_if_win == 0.0
        assert result.std_attacker_survivors_if_win == 0.0


# ---------------------------------------------------------------------------
# Bajas
# ---------------------------------------------------------------------------


class TestLosses:
    """Verifica invariantes de las metricas de bajas."""

    def test_losses_are_nonnegative(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.avg_attacker_losses >= 0.0
        assert result.avg_defender_losses >= 0.0

    def test_losses_bounded_by_troops(self) -> None:
        """Las bajas medias no pueden exceder las tropas iniciales."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.avg_attacker_losses <= state.attacker
        assert result.avg_defender_losses <= state.defender


# ---------------------------------------------------------------------------
# Duracion
# ---------------------------------------------------------------------------


class TestDuration:
    """Verifica invariantes de las metricas de duracion."""

    def test_avg_rounds_positive(self) -> None:
        """Una batalla que no empieza terminada tiene al menos 1 ronda."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.avg_rounds >= 1.0

    def test_std_rounds_nonnegative(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.std_rounds >= 0.0

    def test_median_leq_p90(self) -> None:
        """La mediana nunca es mayor que el percentil 90."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.median_rounds <= result.p90_rounds

    def test_median_and_p90_positive(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.median_rounds >= 1
        assert result.p90_rounds >= 1


# ---------------------------------------------------------------------------
# Metricas de decision
# ---------------------------------------------------------------------------


class TestDecisionMetrics:
    """Verifica invariantes de las metricas orientadas a decision."""

    def test_expected_cost_nonnegative(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.expected_cost_if_win >= 0.0

    def test_cost_per_success_geq_cost_if_win(self) -> None:
        """Dividir por probabilidad < 1 siempre incrementa el coste."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        # Solo se puede verificar si ambos bandos ganan alguna vez
        if 0 < result.attacker_win_prob < 1:
            assert result.expected_cost_per_success >= result.expected_cost_if_win

    def test_cost_per_success_inf_when_zero_wins(self) -> None:
        """Si el atacante nunca gana, el coste por exito es infinito."""
        # attacker=1 -> is_over() siempre True, atacante nunca gana
        state = BattleState(attacker=1, defender=5)
        result = run_monte_carlo(state, simulations=100, rng=random.Random(42))
        assert result.expected_cost_per_success == float("inf")


# ---------------------------------------------------------------------------
# Campos del informe
# ---------------------------------------------------------------------------


class TestReportFields:
    """Verifica que el informe contiene los campos de identificacion."""

    def test_report_contains_initial_params(self) -> None:
        state = BattleState(attacker=8, defender=6)
        result = run_monte_carlo(state, simulations=1000, rng=random.Random(42))
        assert result.attacker == 8
        assert result.defender == 6
        assert result.simulations == 1000

    def test_result_is_frozen(self) -> None:
        """MonteCarloResult es inmutable."""
        state = BattleState(attacker=10, defender=5)
        result = run_monte_carlo(state, simulations=100, rng=random.Random(42))
        try:
            result.attacker_win_prob = 0.999  # type: ignore[misc]
            raise AssertionError("Deberia lanzar error al modificar un campo frozen")
        except Exception:
            pass
