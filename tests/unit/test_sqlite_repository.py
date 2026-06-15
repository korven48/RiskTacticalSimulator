"""Tests unitarios para el repositorio SQLite de escenarios."""

from __future__ import annotations

from pathlib import Path

import pytest

from risk_simulator.core.monte_carlo import MonteCarloResult
from risk_simulator.core.ports import ScenarioQuery
from risk_simulator.database.sqlite_repository import SQLiteScenarioRepository


@pytest.fixture
def repo(tmp_path: Path) -> SQLiteScenarioRepository:
    """Proporciona un repositorio con un archivo DB temporal para cada test."""
    db_file = tmp_path / "test_scenarios.db"
    return SQLiteScenarioRepository(db_file)


def create_dummy_result(
    attacker: int = 10,
    defender: int = 5,
    simulations: int = 100,
    attacker_win_prob: float = 0.8,
) -> MonteCarloResult:
    """Crea un MonteCarloResult de prueba."""
    return MonteCarloResult(
        attacker=attacker,
        defender=defender,
        simulations=simulations,
        attacker_win_prob=attacker_win_prob,
        defender_win_prob=1.0 - attacker_win_prob,
        avg_attacker_survivors_if_win=3.0,
        std_attacker_survivors_if_win=1.0,
        avg_defender_survivors_if_win=0.0,
        std_defender_survivors_if_win=0.0,
        avg_attacker_losses=4.0,
        avg_defender_losses=5.0,
        avg_rounds=4.5,
        std_rounds=1.2,
        median_rounds=4,
        p90_rounds=6,
        expected_cost_if_win=2.0,
        expected_cost_per_success=2.5,
    )


class TestSQLiteScenarioRepository:
    """Tests para SQLiteScenarioRepository."""

    def test_save_and_get(self, repo: SQLiteScenarioRepository) -> None:
        """Puede guardar y recuperar un resultado identico."""
        result = create_dummy_result()
        repo.save(result)

        saved = repo.get(10, 5)
        assert saved is not None
        assert saved == result

    def test_get_not_found(self, repo: SQLiteScenarioRepository) -> None:
        """get() devuelve None si no existe el escenario."""
        assert repo.get(99, 99) is None

    def test_upsert(self, repo: SQLiteScenarioRepository) -> None:
        """save() actualiza si ya existe la misma clave primaria."""
        res1 = create_dummy_result(simulations=100, attacker_win_prob=0.8)
        repo.save(res1)

        # Mismo attacker, defender -> debe reemplazar
        res2 = create_dummy_result(simulations=100, attacker_win_prob=0.9)
        repo.save(res2)

        saved = repo.get(10, 5)
        assert saved is not None
        assert saved.attacker_win_prob == 0.9

        # Diferente simulations -> TAMBIEN reemplaza la fila existente
        res3 = create_dummy_result(simulations=1000, attacker_win_prob=0.95)
        repo.save(res3)

        saved_highest = repo.get(10, 5)
        assert saved_highest is not None
        assert saved_highest.simulations == 1000
        assert saved_highest.attacker_win_prob == 0.95

        all_records = repo.list_all()
        assert len(all_records) == 1

    def test_list_all(self, repo: SQLiteScenarioRepository) -> None:
        """list_all() devuelve todos los escenarios ordenados."""
        repo.save(create_dummy_result(attacker=5, defender=5))
        repo.save(create_dummy_result(attacker=10, defender=5))
        repo.save(create_dummy_result(attacker=2, defender=2))

        all_records = repo.list_all()
        assert len(all_records) == 3
        assert all_records[0].attacker == 2
        assert all_records[1].attacker == 5
        assert all_records[2].attacker == 10

    def test_query_exact_match(self, repo: SQLiteScenarioRepository) -> None:
        """query() filtra exactamente por attacker y defender."""
        repo.save(create_dummy_result(attacker=10, defender=5))
        repo.save(create_dummy_result(attacker=10, defender=6))

        results = repo.query(ScenarioQuery(attacker=10, defender=5))
        assert len(results) == 1
        assert results[0].defender == 5

    def test_query_filters_and_ordering(self, repo: SQLiteScenarioRepository) -> None:
        """query() aplica rangos y orden."""
        repo.save(create_dummy_result(attacker=5, defender=5, attacker_win_prob=0.4))
        repo.save(create_dummy_result(attacker=10, defender=5, attacker_win_prob=0.8))
        repo.save(create_dummy_result(attacker=15, defender=5, attacker_win_prob=0.95))

        # min_attacker_win_prob
        res1 = repo.query(ScenarioQuery(min_attacker_win_prob=0.5))
        assert len(res1) == 2

        # Orden y limite
        res2 = repo.query(ScenarioQuery(order_by="attacker_win_prob ASC", limit=1))
        assert len(res2) == 1
        assert res2[0].attacker_win_prob == 0.4
