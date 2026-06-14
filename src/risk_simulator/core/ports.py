"""Puertos (interfaces) del core de la aplicación.

Define los métodos que los adaptadores (la base de datos)
deben implementar para comunicarse con el núcleo del simulador.
"""

from __future__ import annotations

from typing import Any, Protocol

from risk_simulator.core.monte_carlo import MonteCarloResult


class ScenarioRepository(Protocol):
    """Repositorio para almacenar y consultar resultados de escenarios."""

    def save(self, result: MonteCarloResult) -> None:
        """Guarda o actualiza un resultado en el repositorio."""
        ...

    def get(self, attacker: int, defender: int) -> MonteCarloResult | None:
        """Recupera el resultado exacto de un escenario.

        Args:
            attacker: Tropas iniciales del atacante.
            defender: Tropas iniciales del defensor.

        Returns:
            El resultado si existe, None en caso contrario.
        """
        ...

    def list_all(self) -> list[MonteCarloResult]:
        """Devuelve todos los escenarios guardados."""
        ...

    def query(self, filters: dict[str, Any]) -> list[MonteCarloResult]:
        """Busca escenarios aplicando filtros dinamicos.

        Args:
            filters: Diccionario de filtros (ej. {"min_attacker_win_prob": 0.8}).

        Returns:
            Lista de escenarios que cumplen los filtros.
        """
        ...
