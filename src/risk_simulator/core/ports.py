"""Puertos (interfaces) del core de la aplicacion.

Define los metodos que los adaptadores (la base de datos)
deben implementar para comunicarse con el nucleo del simulador.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, Field

from risk_simulator.core.monte_carlo import MonteCarloResult

# ---------------------------------------------------------------------------
# Query tipado para consultas dinamicas
# ---------------------------------------------------------------------------

OrderByField = Literal[
    "attacker_win_prob DESC",
    "attacker_win_prob ASC",
    "attacker DESC",
    "attacker ASC",
    "expected_cost_if_win ASC",
    "expected_cost_if_win DESC",
    "expected_cost_per_success ASC",
    "expected_cost_per_success DESC",
    "avg_rounds DESC",
    "avg_rounds ASC",
]


class ScenarioQuery(BaseModel):
    """Filtros tipados para buscar escenarios en el repositorio.

    Todos los campos son opcionales. Los que se dejan en None se ignoran
    al construir la consulta.
    """

    attacker: int | None = Field(default=None, description="Fija el numero de atacantes exacto.")
    defender: int | None = Field(default=None, description="Fija el numero de defensores exacto.")
    min_attacker_win_prob: float | None = Field(
        default=None, description="Probabilidad minima de victoria (0.0 a 1.0).", ge=0.0, le=1.0
    )
    max_expected_cost_per_success: float | None = Field(
        default=None, description="Coste maximo esperado por exito en tropas."
    )
    order_by: OrderByField = Field(
        default="attacker_win_prob DESC",
        description="Criterio de ordenacion SQL para los resultados.",
    )
    limit: int = Field(default=5, description="Cantidad maxima de resultados a devolver.", le=20)


# ---------------------------------------------------------------------------
# Contrato del repositorio
# ---------------------------------------------------------------------------


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

    def query(self, filters: ScenarioQuery) -> list[MonteCarloResult]:
        """Busca escenarios aplicando filtros tipados.

        Args:
            filters: Objeto ScenarioQuery con los filtros deseados.

        Returns:
            Lista de escenarios que cumplen los filtros.
        """
        ...
