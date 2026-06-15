"""Tests unitarios para el motor de resolucion de rondas.

Verifica la mecanica de combate: calculo de dados, resolucion de pares
y rondas completas con RNG determinista.
"""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from risk_simulator.core.entities import BattleState
from risk_simulator.core.round_resolver import (
    dice_count,
    resolve_pairs,
    resolve_round,
    roll_dice,
)

# ---------------------------------------------------------------------------
# dice_count: tabla completa de la especificacion
# ---------------------------------------------------------------------------


class TestDiceCount:
    """Verifica las 5 configuraciones de la tabla de la especificacion."""

    def test_2v1(self) -> None:
        """a=2, b=1 -> alpha=1, delta=1."""
        assert dice_count(2, 1) == (1, 1)

    def test_2v2(self) -> None:
        """a=2, b>=2 -> alpha=1, delta=2."""
        assert dice_count(2, 2) == (1, 2)

    def test_3v1(self) -> None:
        """a=3, b=1 -> alpha=2, delta=1."""
        assert dice_count(3, 1) == (2, 1)

    def test_3v2(self) -> None:
        """a=3, b>=2 -> alpha=2, delta=2."""
        assert dice_count(3, 2) == (2, 2)

    def test_4plus_v2(self) -> None:
        """a>=4, b>=2 -> alpha=3, delta=2."""
        assert dice_count(4, 2) == (3, 2)
        assert dice_count(10, 5) == (3, 2)
        assert dice_count(20, 20) == (3, 2)

    def test_4plus_v1(self) -> None:
        """a>=4, b=1 -> alpha=3, delta=1."""
        assert dice_count(4, 1) == (3, 1)
        assert dice_count(20, 1) == (3, 1)

    def test_attacker_below_2_raises(self) -> None:
        """El atacante necesita al menos 2 tropas."""
        with pytest.raises(ValueError, match="al menos 2 tropas"):
            dice_count(1, 1)

    def test_defender_below_1_raises(self) -> None:
        """El defensor necesita al menos 1 tropa."""
        with pytest.raises(ValueError, match="al menos 1 tropa"):
            dice_count(2, 0)


# ---------------------------------------------------------------------------
# roll_dice
# ---------------------------------------------------------------------------


class TestRollDice:
    """Verifica el lanzamiento de dados con RNG inyectado."""

    def test_returns_correct_count(self) -> None:
        rng = random.Random(42)
        result = roll_dice(3, rng)
        assert len(result) == 3

    def test_values_in_range(self) -> None:
        rng = random.Random(42)
        for _ in range(100):
            result = roll_dice(1, rng)
            assert 1 <= result[0] <= 6

    def test_deterministic_with_seed(self) -> None:
        """Misma seed produce mismos resultados."""
        result_a = roll_dice(5, random.Random(123))
        result_b = roll_dice(5, random.Random(123))
        assert result_a == result_b


# ---------------------------------------------------------------------------
# resolve_pairs
# ---------------------------------------------------------------------------


class TestResolvePairs:
    """Verifica la resolucion de pares segun las reglas del Risk."""

    def test_ties_favor_defender(self) -> None:
        """Empate: d_i >= a_i -> atacante pierde."""
        attacker_losses, defender_losses = resolve_pairs([4], [4])
        assert attacker_losses == 1
        assert defender_losses == 0

    def test_attacker_wins_pair(self) -> None:
        """Dado atacante mayor -> defensor pierde."""
        attacker_losses, defender_losses = resolve_pairs([6], [3])
        assert attacker_losses == 0
        assert defender_losses == 1

    def test_defender_wins_with_higher(self) -> None:
        """Dado defensor estrictamente mayor -> atacante pierde."""
        attacker_losses, defender_losses = resolve_pairs([2], [5])
        assert attacker_losses == 1
        assert defender_losses == 0

    def test_two_pairs_mixed(self) -> None:
        """Dos pares: el atacante gana uno, el defensor gana otro."""
        attacker_losses, defender_losses = resolve_pairs([6, 2], [3, 5])
        assert attacker_losses == 1
        assert defender_losses == 1

    def test_only_min_pairs_resolved(self) -> None:
        """Config 3v2: solo se resuelven 2 pares, el 3er dado no cuenta."""
        attacker_losses, defender_losses = resolve_pairs([6, 5, 1], [3, 2])
        assert attacker_losses == 0
        assert defender_losses == 2

    def test_all_ties_two_pairs(self) -> None:
        """Todos los empates: defensor gana ambos pares."""
        attacker_losses, defender_losses = resolve_pairs([4, 3], [4, 3])
        assert attacker_losses == 2
        assert defender_losses == 0

    def test_attacker_wins_all_two_pairs(self) -> None:
        """Atacante gana todos los pares."""
        attacker_losses, defender_losses = resolve_pairs([6, 5], [1, 1])
        assert attacker_losses == 0
        assert defender_losses == 2


# ---------------------------------------------------------------------------
# resolve_round: ronda completa con RNG determinista
# ---------------------------------------------------------------------------


class TestResolveRound:
    """Verifica la resolucion de una ronda completa."""

    def test_deterministic_with_seed(self) -> None:
        """Misma seed produce el mismo resultado."""
        state = BattleState(attacker=10, defender=5)
        result_a = resolve_round(state, random.Random(42))
        result_b = resolve_round(state, random.Random(42))
        assert result_a == result_b

    def test_troops_decrease(self) -> None:
        """Despues de una ronda, al menos un bando pierde tropas."""
        state = BattleState(attacker=10, defender=5)
        result = resolve_round(state, random.Random(42))
        total_before = state.attacker + state.defender
        total_after = result.attacker + result.defender
        assert total_after < total_before

    def test_original_state_unchanged(self) -> None:
        """BattleState es inmutable (frozen); resolve_round crea uno nuevo."""
        state = BattleState(attacker=10, defender=5)
        result = resolve_round(state, random.Random(42))
        assert state.attacker == 10
        assert state.defender == 5
        assert result is not state

    def test_raises_when_battle_over_attacker_1(self) -> None:
        """No se puede resolver ronda si el atacante solo tiene 1 tropa."""
        state = BattleState(attacker=1, defender=5)
        with pytest.raises(ValueError, match="ya ha terminado"):
            resolve_round(state, random.Random(42))

    def test_raises_when_battle_over_defender_0(self) -> None:
        """No se puede resolver ronda si el defensor tiene 0 tropas."""
        state = BattleState(attacker=5, defender=0)
        with pytest.raises(ValueError, match="ya ha terminado"):
            resolve_round(state, random.Random(42))

    def test_attacker_min_2_defender_min_1(self) -> None:
        """Caso limite: 2 vs 1 (configuracion minima valida)."""
        state = BattleState(attacker=2, defender=1)
        result = resolve_round(state, random.Random(42))
        # Solo 1 par (alpha=1, delta=1), alguien pierde 1 tropa
        assert (result.attacker == 1) or (result.defender == 0)

    def test_resolve_round_with_mocked_dice(self) -> None:
        """Verifica resultado exacto controlando los dados."""
        state = BattleState(attacker=5, defender=3)
        # alpha=3, delta=2 -> atacante lanza 3, defensor lanza 2
        # Mock: atacante saca [6, 4, 1], defensor saca [5, 4]
        # Ordenados: atk [6, 4, 1], def [5, 4]
        # Par 1: 6 vs 5 -> defensor pierde
        # Par 2: 4 vs 4 -> atacante pierde (empate)
        rng = random.Random(0)
        with patch.object(rng, "randint", side_effect=[6, 4, 1, 5, 4]):
            result = resolve_round(state, rng)

        assert result.attacker == 4  # 5 - 1 = 4
        assert result.defender == 2  # 3 - 1 = 2
