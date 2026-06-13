"""Entidades puras del dominio de combate.

Este modulo define las estructuras de datos fundamentales que representan
el estado de una batalla.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Limite superior de tropas definido en la especificacion.
MAX_TROOPS = 20


class BattleState(BaseModel):
    """Estado inmutable de una batalla entre atacante y defensor.

    Attributes:
        attacker: Numero de tropas del atacante (N). Debe ser >= 1 y <= 20.
        defender: Numero de tropas del defensor (M). Debe ser >= 0 y <= 20.
    """

    attacker: int = Field(..., ge=1, le=MAX_TROOPS)
    defender: int = Field(..., ge=0, le=MAX_TROOPS)

    model_config = {
        "frozen": True,
    }


    def attacker_can_attack(self) -> bool:
        """El atacante puede lanzar dados si tiene al menos 2 tropas.

        La reserva obligatoria consume 1 tropa, por lo que con solo
        1 tropa el atacante no puede atacar.
        """
        return self.attacker >= 2

    def defender_is_defeated(self) -> bool:
        """El defensor ha sido eliminado (0 tropas restantes)."""
        return self.defender == 0

    def is_over(self) -> bool:
        """La batalla ha terminado.

        Condiciones de finalizacion:
        - Victoria del atacante: el defensor llega a 0 tropas.
        - Victoria del defensor: el atacante llega a 1 tropa y ya no
          puede lanzar dados (reserva obligatoria).
        """
        return self.defender_is_defeated() or not self.attacker_can_attack()

    @property
    def winner(self) -> str | None:
        """Devuelve el bando ganador, o None si la batalla no ha terminado.

        Returns:
            "attacker" si el defensor fue eliminado,
            "defender" si el atacante no puede seguir atacando,
            None si la batalla sigue en curso.
        """
        if not self.is_over():
            return None
        if self.defender_is_defeated():
            return "attacker"
        return "defender"
