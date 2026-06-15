"""Implementacion del repositorio de escenarios usando SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, get_args

from risk_simulator.core.monte_carlo import MonteCarloResult
from risk_simulator.core.ports import OrderByField, ScenarioQuery, ScenarioRepository


class SQLiteScenarioRepository(ScenarioRepository):
    """Repositorio de escenarios respaldado por una base de datos SQLite."""

    def __init__(self, db_path: str | Path = "scenarios.db") -> None:
        """Inicializa el repositorio y crea la tabla si no existe.

        Args:
            db_path: Ruta al archivo SQLite. Usa ":memory:" para tests en RAM.
        """
        self.db_path = str(db_path)

        # Permite que múltiples hilos accedan a la misma conexión por que solo se leen datos.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Crea la tabla de escenarios desnormalizada."""
        query = """
        CREATE TABLE IF NOT EXISTS scenarios (
            attacker INTEGER NOT NULL,
            defender INTEGER NOT NULL,
            simulations INTEGER NOT NULL,

            attacker_win_prob REAL NOT NULL,
            defender_win_prob REAL NOT NULL,

            avg_attacker_survivors_if_win REAL NOT NULL,
            std_attacker_survivors_if_win REAL NOT NULL,
            avg_defender_survivors_if_win REAL NOT NULL,
            std_defender_survivors_if_win REAL NOT NULL,

            avg_attacker_losses REAL NOT NULL,
            avg_defender_losses REAL NOT NULL,

            avg_rounds REAL NOT NULL,
            std_rounds REAL NOT NULL,
            median_rounds INTEGER NOT NULL,
            p90_rounds INTEGER NOT NULL,

            expected_cost_if_win REAL NOT NULL,
            expected_cost_per_success REAL NOT NULL,

            PRIMARY KEY (attacker, defender)
        );
        """
        self._conn.execute(query)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def _row_to_result(self, row: sqlite3.Row) -> MonteCarloResult:
        """Convierte una fila de base de datos a MonteCarloResult."""
        return MonteCarloResult(
            attacker=row["attacker"],
            defender=row["defender"],
            simulations=row["simulations"],
            attacker_win_prob=row["attacker_win_prob"],
            defender_win_prob=row["defender_win_prob"],
            avg_attacker_survivors_if_win=row["avg_attacker_survivors_if_win"],
            std_attacker_survivors_if_win=row["std_attacker_survivors_if_win"],
            avg_defender_survivors_if_win=row["avg_defender_survivors_if_win"],
            std_defender_survivors_if_win=row["std_defender_survivors_if_win"],
            avg_attacker_losses=row["avg_attacker_losses"],
            avg_defender_losses=row["avg_defender_losses"],
            avg_rounds=row["avg_rounds"],
            std_rounds=row["std_rounds"],
            median_rounds=row["median_rounds"],
            p90_rounds=row["p90_rounds"],
            expected_cost_if_win=row["expected_cost_if_win"],
            expected_cost_per_success=row["expected_cost_per_success"],
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save(self, result: MonteCarloResult) -> None:
        """Guarda o actualiza un resultado usando upsert."""
        query = """
        INSERT OR REPLACE INTO scenarios (
            attacker, defender, simulations,
            attacker_win_prob, defender_win_prob,
            avg_attacker_survivors_if_win, std_attacker_survivors_if_win,
            avg_defender_survivors_if_win, std_defender_survivors_if_win,
            avg_attacker_losses, avg_defender_losses,
            avg_rounds, std_rounds, median_rounds, p90_rounds,
            expected_cost_if_win, expected_cost_per_success
        ) VALUES (
            ?, ?, ?,
            ?, ?,
            ?, ?,
            ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?
        )
        """
        params = (
            result.attacker,
            result.defender,
            result.simulations,
            result.attacker_win_prob,
            result.defender_win_prob,
            result.avg_attacker_survivors_if_win,
            result.std_attacker_survivors_if_win,
            result.avg_defender_survivors_if_win,
            result.std_defender_survivors_if_win,
            result.avg_attacker_losses,
            result.avg_defender_losses,
            result.avg_rounds,
            result.std_rounds,
            result.median_rounds,
            result.p90_rounds,
            result.expected_cost_if_win,
            result.expected_cost_per_success,
        )
        self._conn.execute(query, params)
        self._conn.commit()

    def get(self, attacker: int, defender: int) -> MonteCarloResult | None:
        """Recupera el escenario exacto para atacante y defensor."""
        query = """
        SELECT * FROM scenarios
        WHERE attacker = ? AND defender = ?
        """
        row = self._conn.execute(query, (attacker, defender)).fetchone()
        if row is None:
            return None
        return self._row_to_result(row)

    def list_all(self) -> list[MonteCarloResult]:
        """Lista todos los escenarios."""
        query = "SELECT * FROM scenarios ORDER BY attacker ASC, defender ASC"
        rows = self._conn.execute(query).fetchall()
        return [self._row_to_result(row) for row in rows]

    # ------------------------------------------------------------------
    # Consultas dinamicas
    # ------------------------------------------------------------------

    def query(self, filters: ScenarioQuery) -> list[MonteCarloResult]:
        """Busca con filtros dinamicos."""
        query = "SELECT * FROM scenarios WHERE 1=1"
        params: list[Any] = []

        # Filtros exactos
        if filters.attacker is not None:
            query += " AND attacker = ?"
            params.append(filters.attacker)

        if filters.defender is not None:
            query += " AND defender = ?"
            params.append(filters.defender)

        # Filtros de rango
        if filters.min_attacker_win_prob is not None:
            query += " AND attacker_win_prob >= ?"
            params.append(filters.min_attacker_win_prob)

        if filters.max_expected_cost_per_success is not None:
            query += " AND expected_cost_per_success <= ?"
            params.append(filters.max_expected_cost_per_success)

        # Orden y limite
        order_by = filters.order_by
        if order_by not in get_args(OrderByField):
            order_by = "attacker_win_prob DESC"

        query += f" ORDER BY {order_by}"

        limit = filters.limit
        if isinstance(limit, int):
            query += " LIMIT ?"
            params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_result(row) for row in rows]

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Cierra la conexion a la base de datos."""
        self._conn.close()
