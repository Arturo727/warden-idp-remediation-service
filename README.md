# Warden Bundle v7 — Atomic Scenario Selection

Correcciones clave:
- Los 7 escenarios precargados ahora usan `workload_id` únicos para evitar contaminación de historial entre escenarios de prueba.
- El backend mantiene los guardrails:
  - critical => approval
  - confidence < 0.7 => approval
  - prod + rollback/scale_up => approval
- Si `final_safe_to_auto=false`, nunca ejecuta directo.
- `GET /preconfigured-scenarios` devuelve los 7 escenarios completos.


## Tests automatizados

El proyecto incluye tests unitarios y de integración para cubrir los flujos principales solicitados:

- **Validación del payload**
  - campos requeridos
  - severidad inválida
  - validación contra catálogo
  - validación de URLs en `context`
- **Aplicación de restricciones (`safe_to_auto`)**
  - `severity=critical` fuerza `safe_to_auto=false`
  - `confidence < 0.7` fuerza `safe_to_auto=false`
  - `prod + rollback/scale_up` fuerza `safe_to_auto=false`
- **Ejecución / mock de acciones**
  - ejecución automática de `restart`
  - creación de approval + notificación para `rollback` en prod
  - uso de mocks para orquestador / notificador
- **Cobertura usando los 7 escenarios preconfigurados**
  - restart
  - rollback
  - scale_up
  - notify_human
  - no_action
  - critical
  - baja confianza

### Cómo correr los tests

Desde `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Con cobertura:

```bash
pytest --cov=src --cov-report=term-missing
```

### Archivos de test relevantes

- `tests/test_payload_validation.py`
- `tests/test_rules.py`
- `tests/test_action_execution.py`
- `tests/test_event_flow.py`
- `tests/test_preconfigured_scenarios_matrix.py`


## Compatibilidad de Python

Esta versión fue ajustada para ser compatible con **Python 3.9+**.

Si estás en macOS y `python` no existe, usa:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```


## Tests automatizados

Los tests fueron ajustados para **mockear únicamente las dependencias externas durante la ejecución de pytest**:

- LLM (`LLMClient.decide`)
- Orchestrator (`restart`, `rollback`, `scale_up`)
- Notifier (`send`)

Esto permite validar los flujos principales sin cambiar el comportamiento real del backend fuera de los tests.

### Cobertura incluida

- **Validación del payload**
  - campo requerido faltante
  - severidad inválida
  - contexto inválido
  - URLs inválidas en `context`
- **Aplicación de restricciones (`safe_to_auto`)**
  - `severity=critical`
  - `confidence < 0.7`
  - `prod + rollback/scale_up`
- **Ejecución/mock de acciones**
  - `restart`
  - `rollback`
  - `scale_up`
  - `notify_human`
  - `no_action`
- **Matriz con los 7 escenarios preconfigurados**

### Cómo correr los tests

Desde `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Con cobertura:

```bash
python -m pytest --cov=src --cov-report=term-missing
```

### Nota

Los mocks viven solo en `tests/conftest.py`.  
El backend sigue funcionando con sus integraciones reales cuando se ejecuta normalmente.
