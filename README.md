# Risk Tactical Simulator

Motor de simulación táctica de combate basado en las reglas del juego de mesa Risk, integrado con un Agente de Inteligencia Artificial (ReAct) que actúa como tu asesor táctico. Está diseñado para que puedas hacerle preguntas en lenguaje natural sobre si te compensa atacar o defender una región, cuántas tropas necesitas, y calcular tus probabilidades de victoria en el juego real.

## Instalación

Este proyecto utiliza `uv` como gestor de paquetes. Para instalar el entorno y todas las herramientas:

```bash
uv sync
```

## Comandos Disponibles

Al instalar el proyecto, se habilitan automáticamente los siguientes comandos de consola:

### 1. El Agente Táctico (`risk-agent`)
Inicia el chat interactivo con el asesor de IA. El agente es capaz de consultar la base de datos de escenarios de batalla para darte probabilidades de victoria exactas.

```bash
uv run risk-agent
```

**Opciones disponibles:**
- `--provider`: Elige el motor de IA. Opciones: `ollama` (por defecto) u `openai`.
- `--model`: El modelo específico a usar. Por defecto es `qwen3:14b` para ollama. (Ej. `gpt-4o-mini` si usas openai).
- `--mode`: Modo de ejecución. Opciones: `loop` (chat interactivo, por defecto) o `examples` (imprime ejemplos de prueba y sale).

### 2. Generador de Base de Datos (`populate-db`)
Ejecuta miles de simulaciones de Monte Carlo para todas las combinaciones posibles de combates de Risk y guarda las probabilidades pre-calculadas en una base de datos local para que el agente las consulte al instante.

```bash
uv run populate-db
```

**Opciones disponibles:**
- `--db-path`: Ruta donde se guardará la base de datos. Por defecto: `scenarios.db`.
- `--simulations`: Número de simulaciones de Monte Carlo por cada combate posible. Por defecto: `100000`.
- `--seed`: Semilla aleatoria (número entero) para garantizar resultados idénticos y reproducibles en las simulaciones.