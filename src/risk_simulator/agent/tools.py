"""Herramientas (tools) para que un agente LLM consulte la base de datos de escenarios."""

from typing import Any

from langchain_core.tools import tool

from risk_simulator.core.ports import ScenarioQuery
from risk_simulator.database.sqlite_repository import SQLiteScenarioRepository

# Instancia global por defecto conectada a la BD generada por populate.py
_repo = SQLiteScenarioRepository(db_path="scenarios.db")


@tool
def get_scenario(attacker: int, defender: int) -> dict[str, Any] | str:
    """Obtiene las estadisticas exactas de un combate especifico.

    Usar esta herramienta cuando el usuario pregunte por un enfrentamiento
    concreto.
    Ejemplo: "¿Que pasa si ataco con 8 tropas contra 5?" -> get_scenario(8, 5).

    Args:
        attacker: Numero de tropas iniciales del atacante.
        defender: Numero de tropas iniciales del defensor.

    Returns:
        Diccionario con las estadisticas del combate, o un mensaje de error
        si el escenario no existe.
    """
    result = _repo.get(attacker, defender)
    if result is None:
        return f"No se encontro el escenario de {attacker} atacantes vs {defender} defensores."
    return result.model_dump()


@tool
def search_scenarios(query: ScenarioQuery) -> list[dict[str, Any]]:
    """Busca combates que cumplan ciertos criterios estadisticos o filtros.

    Usar esta herramienta para preguntas abiertas inversas o condicionales.
    Ejemplo: "¿Cuantas tropas necesito para tener un 80% victoria contra 6 defensores?"
        -> search_scenarios(defender=6, min_attacker_win_prob=0.8, order_by="attacker ASC")

    Returns:
        Lista de diccionarios con los escenarios que cumplen los filtros.
    """
    results = _repo.query(query)
    return [r.model_dump() for r in results]
