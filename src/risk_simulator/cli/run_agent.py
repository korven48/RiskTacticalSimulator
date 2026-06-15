"""Script de demostración interactiva del Agente Táctico."""

import argparse
import os
import sys

from langchain_core.messages import HumanMessage

from risk_simulator.agent.react_agent import get_agent


def run_examples(agent) -> None:
    """Ejecuta los ejemplos automáticos solicitados por el usuario."""
    print("\n" + "=" * 50)
    print("EJECUTANDO EJEMPLOS PREDEFINIDOS")
    print("=" * 50 + "\n")

    examples = [
        "Tengo 8 tropas y quiero atacar una región defendida por 5. ¿Me compensa?",
        (
            "¿Cuántas tropas necesito para tener más de un 80% de probabilidad "
            "de victoria contra 6 defensores?"
        ),
        "Compara atacar con 10 tropas contra 4 defensores frente a atacar con 7 contra 3.",
    ]

    for i, prompt in enumerate(examples, 1):
        print(f"--- EJEMPLO {i} ---")
        print(f"COMANDANTE: {prompt}")

        # Invocamos al agente
        messages = [HumanMessage(content=prompt)]
        result = agent.invoke({"messages": messages})

        # Imprimimos la última respuesta
        ai_message = result["messages"][-1].content
        print(f"\nASESOR TÁCTICO:\n{ai_message}\n")
        print("-" * 50 + "\n")


def interactive_loop(agent) -> None:
    """Inicia un bucle de chat interactivo con el agente."""
    print("\n" + "=" * 50)
    print("SISTEMA DE COMUNICACIÓN ABIERTO")
    print("Escribe 'salir', 'exit' o 'quit' para terminar.")
    print("=" * 50 + "\n")

    # Mantenemos el historial de la conversación (memoria)
    messages = []

    while True:
        try:
            user_input = input("\nCOMANDANTE> ")
            if user_input.lower() in ("salir", "exit", "quit"):
                print("Conexión terminada. ¡Buena suerte, Comandante!")
                break
            if not user_input.strip():
                continue

            messages.append(HumanMessage(content=user_input))

            # Pasamos el historial al agente
            result = agent.invoke({"messages": messages})

            # Actualizamos nuestro historial con la respuesta
            messages = result["messages"]
            ai_response = messages[-1].content

            print(f"\nASESOR TÁCTICO>\n{ai_response}")

        except KeyboardInterrupt:
            print("\nConexión terminada por el usuario.")
            break
        except Exception as e:
            print(f"\nError de comunicación: {e}")


def main() -> None:
    """Función principal."""
    parser = argparse.ArgumentParser(description="Ejecuta el Agente Táctico de Risk.")
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "ollama"],
        default="ollama",
        help="Proveedor de LLM a usar (openai o ollama).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen3:14b",
        help="Nombre del modelo (ej. gpt-4o-mini, llama3.1).",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["loop", "examples"],
        default="loop",
        help="Modo de ejecución: interactivo (loop) o ejemplos predefinidos (examples).",
    )
    args = parser.parse_args()

    if args.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: La variable de entorno OPENAI_API_KEY no está configurada.")
        print("Por favor, configúrala antes de ejecutar el agente con OpenAI.")
        print("Ejemplo en PowerShell: $env:OPENAI_API_KEY='tu-clave-aqui'")
        sys.exit(1)

    print(f"Iniciando conexión con el Cuartel General (Proveedor: {args.provider})...")
    agent = get_agent(provider=args.provider, model_name=args.model)

    if args.mode == "examples":
        # Ejecutar ejemplos automáticos
        run_examples(agent)
    elif args.mode == "loop":
        # Entrar en modo interactivo para seguir hablando con él
        interactive_loop(agent)


if __name__ == "__main__":
    main()
