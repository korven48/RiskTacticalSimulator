"""Motor de resolucion de rondas.

Implementa la mecanica de una ronda de combate.
"""

from __future__ import annotations

import random

from risk_simulator.core.entities import BattleState


def dice_count(attacker: int, defender: int) -> tuple[int, int]:
    """Calcula el numero de dados que lanza cada bando.

    El atacante lanza min(a-1, 3) dados (reserva obligatoria de 1 tropa).
    El defensor lanza min(b, 2) dados.

    Args:
        attacker: Tropas actuales del atacante (a >= 2).
        defender: Tropas actuales del defensor (b >= 1).

    Returns:
        Tupla (alpha, delta) con el numero de dados de atacante y defensor.

    Raises:
        ValueError: Si el atacante no puede atacar (< 2) o el defensor
            no tiene tropas (< 1).
    """
    if attacker < 2:
        raise ValueError(f"El atacante necesita al menos 2 tropas para atacar, tiene: {attacker}")
    if defender < 1:
        raise ValueError(f"El defensor necesita al menos 1 tropa, tiene: {defender}")

    alpha = min(attacker - 1, 3)
    delta = min(defender, 2)
    return alpha, delta


def roll_dice(n: int, rng: random.Random) -> list[int]:
    """Lanza n dados de 6 caras usando el generador de numeros aleatorios dado.

    Args:
        n: Numero de dados a lanzar (>= 1).
        rng: Generador de numeros aleatorios inyectado para reproducibilidad.

    Returns:
        Lista de n resultados, cada uno entre 1 y 6 (inclusive).
    """
    return [rng.randint(1, 6) for _ in range(n)]


def resolve_pairs(attacker_dice: list[int], defender_dice: list[int]) -> tuple[int, int]:
    """Resuelve los pares de dados y calcula las bajas de cada bando.

    Ambas colecciones se ordenan de mayor a menor. Se forman
    min(alpha, delta) pares, emparejando el i-esimo mayor dado
    de cada bando. Para cada par (a_i, d_i):
    - Si d_i >= a_i: el atacante pierde una tropa (empate favorece defensor).
    - Si d_i < a_i: el defensor pierde una tropa.

    Args:
        attacker_dice: Dados lanzados por el atacante.
        defender_dice: Dados lanzados por el defensor.

    Returns:
        Tupla (bajas_atacante, bajas_defensor).
    """
    sorted_attack = sorted(attacker_dice, reverse=True)
    sorted_defend = sorted(defender_dice, reverse=True)

    attacker_losses = 0
    defender_losses = 0

    pairs = min(len(sorted_attack), len(sorted_defend))
    for i in range(pairs):
        if sorted_defend[i] >= sorted_attack[i]:
            attacker_losses += 1
        else:
            defender_losses += 1

    return attacker_losses, defender_losses


def resolve_round(state: BattleState, rng: random.Random) -> BattleState:
    """Resuelve una ronda completa de combate.

    Dado un estado de batalla donde el atacante puede atacar (>= 2 tropas)
    y el defensor tiene tropas (>= 1), lanza los dados de ambos bandos,
    resuelve los pares y devuelve el nuevo estado con las bajas aplicadas.

    Args:
        state: Estado actual de la batalla (inmutable).
        rng: Generador de numeros aleatorios inyectado.

    Returns:
        Nuevo BattleState con las bajas de la ronda aplicadas.

    Raises:
        ValueError: Si la batalla ya ha terminado.
    """
    if state.is_over():
        raise ValueError("No se puede resolver una ronda: la batalla ya ha terminado.")

    alpha, delta = dice_count(state.attacker, state.defender)

    attacker_dice = roll_dice(alpha, rng)
    defender_dice = roll_dice(delta, rng)

    attacker_losses, defender_losses = resolve_pairs(attacker_dice, defender_dice)

    return BattleState(
        attacker=state.attacker - attacker_losses,
        defender=state.defender - defender_losses,
    )
