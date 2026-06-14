"""Tests unitarios para simulate_battle.

Verifica invariantes deterministicos del caso de uso: consistencia
entre ganador y supervivientes, conservacion de tropas, limites de
rondas, reproducibilidad e inmutabilidad.
"""

from __future__ import annotations

import random

import pytest

from risk_simulator.core.entities import BattleState
from risk_simulator.core.use_cases import BattleResult, simulate_battle

# ---------------------------------------------------------------------------
# Reproducibilidad
# ---------------------------------------------------------------------------


class TestReproducibility:
    """Misma seed produce el mismo resultado."""

    def test_same_seed_same_result(self) -> None:
        state = BattleState(attacker=10, defender=5)
        result_a = simulate_battle(state, rng=random.Random(42))
        result_b = simulate_battle(state, rng=random.Random(42))
        assert result_a == result_b

    def test_default_rng_does_not_raise(self) -> None:
        """Si no se pasa rng, se crea uno interno sin error."""
        state = BattleState(attacker=5, defender=3)
        result = simulate_battle(state)
        assert isinstance(result, BattleResult)


# ---------------------------------------------------------------------------
# Consistencia ganador / supervivientes
# ---------------------------------------------------------------------------


class TestWinnerConsistency:
    """El ganador y los supervivientes deben ser coherentes."""

    def test_attacker_wins_means_defender_zero(self) -> None:
        """Si gana el atacante, el defensor tiene 0 tropas."""
        state = BattleState(attacker=10, defender=5)
        result = simulate_battle(state, rng=random.Random(42))
        if result.winner == "attacker":
            assert result.defender_survivors == 0

    def test_defender_wins_means_attacker_one(self) -> None:
        """Si gana el defensor, el atacante tiene exactamente 1 tropa."""
        state = BattleState(attacker=10, defender=5)
        result = simulate_battle(state, rng=random.Random(99))
        if result.winner == "defender":
            assert result.attacker_survivors == 1

    def test_winner_is_always_valid(self) -> None:
        """El ganador siempre es 'attacker' o 'defender'."""
        state = BattleState(attacker=8, defender=6)
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            assert result.winner in ("attacker", "defender")

    def test_attacker_survivors_at_least_one(self) -> None:
        """El atacante siempre conserva al menos 1 tropa (reserva)."""
        state = BattleState(attacker=5, defender=5)
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            assert result.attacker_survivors >= 1

    def test_defender_survivors_non_negative(self) -> None:
        """Las tropas del defensor nunca son negativas."""
        state = BattleState(attacker=5, defender=5)
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            assert result.defender_survivors >= 0


# ---------------------------------------------------------------------------
# Conservacion de tropas
# ---------------------------------------------------------------------------


class TestTroopConservation:
    """Las tropas totales nunca se crean, solo se destruyen."""

    def test_total_troops_do_not_increase(self) -> None:
        """La suma de supervivientes no supera la suma inicial."""
        state = BattleState(attacker=10, defender=8)
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            total_initial = state.attacker + state.defender
            total_final = result.attacker_survivors + result.defender_survivors
            assert total_final <= total_initial

    def test_attacker_does_not_gain_troops(self) -> None:
        """El atacante nunca termina con mas tropas de las iniciales."""
        state = BattleState(attacker=10, defender=5)
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            assert result.attacker_survivors <= state.attacker

    def test_defender_does_not_gain_troops(self) -> None:
        """El defensor nunca termina con mas tropas de las iniciales."""
        state = BattleState(attacker=10, defender=5)
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            assert result.defender_survivors <= state.defender


# ---------------------------------------------------------------------------
# Rondas
# ---------------------------------------------------------------------------


class TestRounds:
    """Limites y coherencia del numero de rondas."""

    def test_rounds_positive_for_active_battle(self) -> None:
        """Una batalla activa siempre tiene al menos 1 ronda."""
        state = BattleState(attacker=5, defender=3)
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            assert result.rounds >= 1

    def test_rounds_upper_bound(self) -> None:
        """Las rondas no superan la suma de tropas que pueden perderse.

        En cada ronda se pierde al menos 1 tropa en total, asi que el
        maximo teorico de rondas es (attacker - 1) + defender.
        """
        state = BattleState(attacker=10, defender=10)
        max_rounds = (state.attacker - 1) + state.defender
        for seed in range(50):
            result = simulate_battle(state, rng=random.Random(seed))
            assert result.rounds <= max_rounds


# ---------------------------------------------------------------------------
# Estados ya terminados (is_over)
# ---------------------------------------------------------------------------


class TestAlreadyFinished:
    """simulate_battle maneja estados que ya han terminado."""

    def test_attacker_cannot_attack_returns_defender_win(self) -> None:
        """Con attacker=1 la batalla ya termino: gana el defensor."""
        state = BattleState(attacker=1, defender=5)
        result = simulate_battle(state, rng=random.Random(42))
        assert result.winner == "defender"
        assert result.attacker_survivors == 1
        assert result.defender_survivors == 5
        assert result.rounds == 0

    def test_defender_zero_returns_attacker_win(self) -> None:
        """Con defender=0 la batalla ya termino: gana el atacante."""
        state = BattleState(attacker=5, defender=0)
        result = simulate_battle(state, rng=random.Random(42))
        assert result.winner == "attacker"
        assert result.attacker_survivors == 5
        assert result.defender_survivors == 0
        assert result.rounds == 0

    def test_attacker_one_defender_zero(self) -> None:
        """Caso limite: attacker=1, defender=0. Gana el atacante."""
        state = BattleState(attacker=1, defender=0)
        result = simulate_battle(state, rng=random.Random(42))
        assert result.winner == "attacker"
        assert result.rounds == 0


# ---------------------------------------------------------------------------
# Inmutabilidad del estado inicial
# ---------------------------------------------------------------------------


class TestImmutability:
    """El estado inicial no se modifica."""

    def test_initial_state_unchanged(self) -> None:
        """simulate_battle no muta el BattleState de entrada."""
        state = BattleState(attacker=10, defender=5)
        simulate_battle(state, rng=random.Random(42))
        assert state.attacker == 10
        assert state.defender == 5


# ---------------------------------------------------------------------------
# BattleResult es inmutable
# ---------------------------------------------------------------------------


class TestResultImmutability:
    """BattleResult es un modelo congelado."""

    def test_result_is_frozen(self) -> None:
        state = BattleState(attacker=5, defender=3)
        result = simulate_battle(state, rng=random.Random(42))
        with pytest.raises(Exception):
            result.rounds = 999  # type: ignore[misc]
