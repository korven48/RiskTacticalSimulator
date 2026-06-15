"""Script para poblar la base de datos con escenarios comunes de Risk."""

import argparse
import sys
import time
from pathlib import Path

# Anadir el directorio src al path si se ejecuta directamente
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from risk_simulator.core.entities import BattleState
from risk_simulator.core.monte_carlo import run_monte_carlo
from risk_simulator.database.sqlite_repository import SQLiteScenarioRepository


def main() -> None:
    """Ejecuta la simulacion para todos los escenarios y los guarda en SQLite."""
    parser = argparse.ArgumentParser(description="Poblar la base de datos de escenarios de Risk.")
    parser.add_argument(
        "--simulations", type=int, default=10000, help="Numero de simulaciones por escenario."
    )
    parser.add_argument(
        "--db-path", type=str, default="scenarios.db", help="Ruta de la base de datos SQLite."
    )
    args = parser.parse_args()

    repo = SQLiteScenarioRepository(db_path=args.db_path)

    # Risk: atacantes desde 2 hasta 20 (minimo 2 para atacar), defensores 1 hasta 20
    attackers = range(2, 21)
    defenders = range(1, 21)

    total_scenarios = len(attackers) * len(defenders)
    count = 0

    print(f"Poblando {total_scenarios} escenarios con {args.simulations} simulaciones cada uno...")
    start_time = time.time()

    for attacker in attackers:
        for defender in defenders:
            initial_state = BattleState(attacker=attacker, defender=defender)
            result = run_monte_carlo(initial_state, simulations=args.simulations)
            repo.save(result)
            count += 1
            if count % 50 == 0:
                print(f"Progreso: {count}/{total_scenarios} escenarios completados.")

    elapsed = time.time() - start_time
    print(f"Completado exitosamente en {elapsed:.2f} segundos.")


if __name__ == "__main__":
    main()
