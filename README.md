# Warden IDP Remediation Service API

## 1. Resumen 

**Warden IDP Remediation Service** es una API diseñada para recibir eventos operativos, analizarlos, tomar una decisión de remediación, aplicar restricciones de seguridad y gobernanza, ejecutar acciones mockeadas cuando sea seguro hacerlo, o escalar la decisión a aprobación humana cuando el riesgo operativo así lo requiera.

La solución fue construida para demostrar una arquitectura de remediación controlada donde una recomendación generada por lógica interna o por un modelo LLM **no se ejecuta automáticamente por defecto**, sino que pasa por un conjunto de guardrails obligatorios antes de convertirse en una acción final.

La API cubre de forma integral los siguientes aspectos:

- recepción y validación de eventos
- razonamiento con o sin LLM
- uso de contexto histórico por workload
- aplicación de reglas `safe_to_auto`
- ejecución mockeada de acciones
- approvals persistentes
- feedback loop a partir de decisiones humanas
- trazabilidad técnica detallada
- documentación interactiva con FastAPI + Swagger
- pruebas automatizadas de los flujos críticos

Esta implementación permite demostrar una solución moderna, explicable y auditable para remediación asistida, manteniendo una separación clara entre decisión, enforcement de políticas, ejecución y persistencia.

---

###  Levantar todo el entorno

Desde la raíz del repositorio:

```bash
docker compose up --build
```

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


## 2. Objetivo del servicio

El objetivo principal de Warden es proporcionar una API que permita **automatizar de forma controlada** la respuesta ante señales de degradación o incidentes operativos, asegurando que:

- la automatización solo ocurra cuando sea segura
- las reglas del negocio tengan prioridad sobre la recomendación del LLM
- las decisiones humanas también formen parte del contexto futuro
- exista evidencia suficiente para auditoría y troubleshooting

En otras palabras, la API busca demostrar cómo combinar:

- inteligencia asistida
- políticas obligatorias
- trazabilidad
- intervención humana
- persistencia histórica

dentro de un solo flujo de remediación.

---

## 3. Alcance

### Incluye

- API REST para procesamiento de eventos
- validación estructural del payload
- integración con LLM o lógica mock
- consulta de historial por workload
- reglas de negocio y guardrails
- ejecución mockeada de acciones
- approvals persistentes
- notificación mock a humano
- logging estructurado en JSON
- documentación OpenAPI/Swagger
- pruebas unitarias y de integración controlada

### No incluye

- integración real con orquestadores productivos
- ejecución real sobre Kubernetes o cloud
- mensajería real con Slack, PagerDuty o correo
- autenticación y autorización avanzadas
- multi-tenancy real
- hardening productivo completo
- políticas desacopladas tipo OPA
- motor de correlación avanzada de incidentes

---

## 4. Stack tecnológico y versiones utilizadas

La solución fue construida principalmente con tecnologías del ecosistema Python, utilizando un framework moderno para APIs y librerías orientadas a validación, persistencia, pruebas y observabilidad.

### 4.1 Lenguaje principal

- **Python 3.12**
- Validado localmente con **Python 3.12.13**

### 4.2 Framework de API

- **FastAPI 0.115.0**

### 4.3 Servidor ASGI

- **Uvicorn 0.30.6**

### 4.4 Persistencia y ORM

- **SQLAlchemy 2.0.35**

### 4.5 Validación y modelos de datos

- **Pydantic 2.9.2**
- **pydantic-settings 2.5.2**

### 4.6 Cliente HTTP

- **httpx 0.27.2**

### 4.7 Logging estructurado

- **python-json-logger 2.0.7**

### 4.8 Testing

- **pytest 8.3.3**
- **pytest-cov 5.0.0**

### 4.9 Documentación interactiva

- **OpenAPI / Swagger UI**
- **ReDoc**

### 4.10 Contenedorización

- **Docker**
- **Docker Compose**

---

## 5. Dependencias declaradas del proyecto

El archivo `requirements.txt` del backend contempla las siguientes versiones:

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
pydantic-settings==2.5.2
httpx==0.27.2
python-json-logger==2.0.7
pytest==8.3.3
pytest-cov==5.0.0
```

Estas versiones fueron seleccionadas para asegurar compatibilidad entre framework, validación, persistencia y pruebas automatizadas.

---

## 6. ¿Por qué se eligieron estas tecnologías?

### Python
Se eligió Python por su rapidez para prototipado, claridad sintáctica y fortaleza en integraciones, automatización, APIs y pruebas.

### FastAPI
Se eligió FastAPI porque permite:

- construir APIs modernas con poco boilerplate
- definir contratos de forma clara
- generar Swagger automáticamente
- validar payloads de forma robusta
- trabajar bien con tipado y pruebas

### SQLAlchemy
Se eligió SQLAlchemy para desacoplar la lógica del dominio de la persistencia y ofrecer una base sólida para almacenamiento estructurado.

### Pydantic
Se eligió Pydantic para garantizar contratos claros y validación fuerte del payload, algo clave en un sistema que procesa eventos operativos.

### httpx
Se eligió httpx por ser un cliente HTTP moderno, claro y adecuado para consumir mocks y servicios externos.

### pytest
Se eligió pytest por su flexibilidad, claridad y facilidad para mockear dependencias y validar flujos complejos.

### Docker Compose
Se eligió Docker Compose porque permite levantar rápidamente todo el entorno funcional de la prueba sin depender de instalaciones manuales complejas.

---

## 7. Tecnología base

La API fue desarrollada con **FastAPI**, un framework moderno de Python orientado a la construcción de APIs REST de alto desempeño, tipadas y autodocumentadas.

### ¿Por qué FastAPI?

FastAPI aporta ventajas importantes para este proyecto:

- validación automática de request y response
- definición clara de contratos mediante modelos tipados
- documentación interactiva generada automáticamente
- facilidad para pruebas automatizadas
- integración natural con OpenAPI
- estructura limpia para separar rutas, servicios, dominio y clientes externos

Gracias a esto, la API no solo funciona como motor de procesamiento, sino también como un servicio fácilmente entendible, consumible y demostrable.

---

## 8. Documentación interactiva de la API

Uno de los beneficios más importantes de FastAPI es la generación automática de documentación interactiva.

### Swagger UI

Una vez levantado el servicio, la documentación Swagger estará disponible en:

```text
http://localhost:8000/docs
```

Desde Swagger es posible:

- ver todos los endpoints
- revisar el contrato de entrada y salida
- probar llamadas directamente desde el navegador
- validar payloads
- observar responses y códigos HTTP
- explorar el comportamiento del servicio sin depender de un cliente externo

### ReDoc

FastAPI también expone documentación en formato ReDoc:

```text
http://localhost:8000/redoc
```

ReDoc es útil cuando se desea revisar la API con una presentación más documental.

---

## 9. Arquitectura funcional de la solución

La solución puede entenderse a través de los siguientes bloques:

### 9.1 Capa API
Expone endpoints REST para:

- health
- escenarios preconfigurados
- ingestión de eventos
- consulta de eventos
- consulta de approvals
- aprobación o rechazo de approvals

### 9.2 Capa de validación
Valida:

- estructura del payload
- campos obligatorios
- tipos de datos
- formatos inválidos
- URLs inválidas dentro del contexto, si aplica

### 9.3 Capa de razonamiento
Resuelve la decisión del evento usando:

- lógica mock
- proveedor LLM
- historial por workload
- modo de ejecución configurado

### 9.4 Capa de guardrails
Aplica restricciones obligatorias de seguridad y operación.

### 9.5 Capa de ejecución
Ejecuta acciones mockeadas cuando `final_safe_to_auto = true`.

### 9.6 Capa de approvals
Genera solicitudes persistentes de aprobación cuando la automatización no debe ocurrir directamente.

### 9.7 Capa de notificación
Simula el aviso al humano on-call.

### 9.8 Capa de persistencia
Guarda eventos, decisiones, approvals, resultados y feedback.

### 9.9 Capa de observabilidad
Produce logs estructurados y detalle técnico por evento.

---

## 10. Modos de ejecución

La API soporta distintos modos de razonamiento, usualmente definidos en `context.llm_mode`.

### 10.1 `without_llm`
No usa proveedor LLM. La decisión se toma mediante la lógica mock del sistema.

### 10.2 `with_llm`
Usa proveedor LLM sin agregar historial como contexto extendido.

### 10.3 `with_llm_context`
Usa proveedor LLM y agrega al prompt los últimos **N eventos del mismo workload**, donde `N` se define mediante el contexto recibido.

---

## 11. Modelo de entrada

La estructura base de un evento es la siguiente:

```json
{
  "project_id": "orders-api",
  "environment_id": "qa",
  "severity": "medium",
  "signal": "pod crash detected with OOM",
  "context": {
    "workload_id": "orders-api",
    "llm_mode": "with_llm_context",
    "simulated_context_count": 1
  },
  "timestamp": "2024-04-03T14:45:00Z"
}
```

### Campos principales

- **project_id**  
  Identificador lógico del proyecto o workload.

- **environment_id**  
  Ambiente del evento, por ejemplo `dev`, `qa`, `stg`, `prod`.

- **severity**  
  Severidad de la señal:
  - low
  - medium
  - high
  - critical

- **signal**  
  Descripción textual del síntoma observado.

- **context**  
  Diccionario flexible para enriquecer el evento con información adicional, como:
  - workload_id
  - last_deploy
  - cpu_usage
  - error_rate
  - llm_mode
  - simulated_context_count
  - metadatos de UI
  - referencias técnicas

- **timestamp**  
  Marca temporal del evento.

---

## 12. Acciones soportadas

La API soporta las siguientes acciones:

- `restart`
- `rollback`
- `scale_up`
- `notify_human`
- `no_action`

Estas acciones pueden ser sugeridas por el LLM o mock, pero su ejecución real depende de la evaluación de guardrails.

---

## 13. Reglas de negocio y guardrails

La recomendación del LLM o mock **no es la decisión final ejecutable**. Antes de ejecutar, Warden aplica reglas obligatorias que pueden forzar intervención humana.

### 13.1 Severidad crítica
Si `severity = critical`, entonces `safe_to_auto = false`, sin importar lo que recomiende el LLM.

### 13.2 Baja confianza
Si `confidence < 0.7`, entonces `safe_to_auto = false`.

### 13.3 Producción con rollback o scale_up
Si `environment_id = prod` y la acción es `rollback` o `scale_up`, entonces `safe_to_auto = false`.

Estas reglas aseguran que la automatización no ocurra en escenarios de mayor riesgo.

---

## 14. Flujo principal de procesamiento

El flujo principal del sistema ocurre así:

1. se recibe el evento por `POST /webhooks/events`
2. se valida la estructura del payload
3. se identifica el `workload_id` si existe
4. se obtiene historial del mismo workload
5. se decide la acción usando LLM o mock
6. se aplican guardrails
7. se calcula `final_safe_to_auto`
8. si `final_safe_to_auto = true`
   - se ejecuta acción mock
   - se persiste el resultado
9. si `final_safe_to_auto = false`
   - se crea approval
   - se notifica a humano
   - se persiste el estado pendiente
10. el evento y todos sus datos quedan disponibles para consulta futura

---

## 15. Historial por workload

Antes de consultar al LLM en modo contextual, Warden recupera los últimos **N eventos del mismo workload** y los incluye como contexto adicional.

### El historial conserva

- signal recibido
- decisión tomada
- confidence
- si se ejecutó automáticamente o requirió approval
- estado de approval
- feedback humano
- resultado conocido de la acción

### Comportamiento esperado

- si existe historial, se usa como contexto
- si no existe historial, el flujo funciona igual
- el valor de `N` es configurable
- el historial se limita al mismo workload

---

## 16. Feedback loop

Cuando una acción pendiente es aprobada o rechazada por un humano, esa resolución se guarda como parte del historial.

Esto permite que decisiones futuras puedan considerar:

- si recomendaciones previas fueron aprobadas
- si recomendaciones previas fueron rechazadas
- qué resultado tuvieron esas decisiones

La participación humana se convierte así en una señal adicional para decisiones futuras.

---

## 17. Persistencia

La API persiste los elementos clave del flujo:

### 17.1 Evento
Registro base del evento recibido.

### 17.2 Decisión
Incluye:

- acción
- confidence
- reasoning
- llm_safe_to_auto
- final_safe_to_auto
- restricciones aplicadas
- prompt
- response
- provider
- error del provider

### 17.3 Approval
Solicitud pendiente o resuelta.

### 17.4 Resultado de ejecución
Respuesta de la acción mock ejecutada.

### 17.5 Historial
Información acumulada por workload.

---

## 18. Observabilidad y trazabilidad

Cada evento guarda suficiente información para reconstruir el flujo completo:

- payload de entrada
- historial utilizado
- prompt enviado al LLM
- respuesta del LLM
- restricciones aplicadas
- approval asociado
- trazas de APIs
- trazas de handlers
- feedback humano
- resultado final

Esto hace que el sistema sea:

- auditable
- explicable
- depurable
- demostrable

---

## 19. Logs estructurados

El sistema genera logs estructurados en formato JSON para operaciones relevantes, por ejemplo:

- recepción de evento
- resolución de historial
- decisión del LLM o mock
- aplicación de guardrails
- ejecución de acción
- creación de approval
- notificación humana
- errores de integración
- errores de procesamiento

Estos logs ayudan a:

- troubleshooting
- observabilidad
- correlación de eventos
- auditoría

---

## 20. Endpoints principales

### 20.1 Health

#### GET `/health`

Valida que la API esté arriba.

**Ejemplo de respuesta:**

```json
{
  "status": "ok"
}
```

---

### 20.2 Escenarios preconfigurados

#### GET `/preconfigured-scenarios`

Devuelve la lista de escenarios usados para la validación funcional.

---

### 20.3 Ingestión de eventos

#### POST `/webhooks/events`

Endpoint principal del sistema.

**Ejemplo de payload:**

```json
{
  "project_id": "orders-api",
  "environment_id": "qa",
  "severity": "medium",
  "signal": "pod crash detected with OOM",
  "context": {
    "workload_id": "orders-api",
    "llm_mode": "with_llm"
  },
  "timestamp": "2024-04-03T14:45:00Z"
}
```

**Ejemplo de respuesta con ejecución automática:**

```json
{
  "event_id": 1,
  "status": "executed",
  "restrictions": [],
  "execution_result": {
    "status": "success",
    "action": "restart"
  },
  "history_items_used": 0
}
```

**Ejemplo de respuesta con approval:**

```json
{
  "event_id": 2,
  "status": "awaiting_approval",
  "approval_id": 1,
  "restrictions": [
    "prod + rollback/scale_up => safe_to_auto=false"
  ],
  "notification_result": {
    "status": "sent"
  },
  "history_items_used": 1
}
```

---

### 20.4 Listado de eventos

#### GET `/events`

Devuelve los eventos registrados.

---

### 20.5 Detalle de evento

#### GET `/events/{id}`

Devuelve el detalle técnico de un evento específico.

---

### 20.6 Listado de approvals

#### GET `/approvals`

Devuelve las solicitudes de aprobación registradas.

---

### 20.7 Aprobar acción

#### POST `/approvals/{id}/approve`

**Payload de ejemplo:**

```json
{
  "resolved_by": "human-on-call",
  "resolution_note": "approved from swagger"
}
```

---

### 20.8 Rechazar acción

#### POST `/approvals/{id}/reject`

**Payload de ejemplo:**

```json
{
  "resolved_by": "human-on-call",
  "resolution_note": "rejected from swagger"
}
```

---

## 21. Integraciones mockeadas

La solución utiliza integraciones mock para mantener el flujo demostrable sin depender de tecnología externa real.

### 21.1 Mock Orchestrator
Simula acciones como:

- restart
- rollback
- scale_up

### 21.2 Mock Notifier
Simula notificación al humano on-call.

### 21.3 Mock LLM
Cuando aplica fallback o modo controlado, la decisión es generada por lógica mock.

---

## 22. Ejecución del servicio

El servicio puede ejecutarse de dos maneras principales: con Docker Compose o de forma local con FastAPI/Uvicorn.

### 22.1 Ejecución recomendada con Docker Compose

La forma recomendada de levantar el sistema completo es usando `docker compose`, ya que permite iniciar:

- backend
- frontend
- mocks
- servicios auxiliares

#### Levantar todo el entorno

```bash
docker compose up --build
```

#### Levantar en segundo plano

```bash
docker compose up -d --build
```

#### Apagar el entorno

```bash
docker compose down
```

#### Reconstruir contenedores cuando existan cambios en código o dependencias

```bash
docker compose up --build --force-recreate
```

### 22.2 Ejecución local del backend

Si deseas levantar solo el backend localmente para desarrollo o validación:

#### Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

#### Exportar variables si aplica

```bash
export DATABASE_URL=sqlite:///./warden.db
export LOG_DIR=./logs
export ORCHESTRATOR_URL=http://localhost:8001
export NOTIFIER_URL=http://localhost:8002
export GROQ_API_KEY=tu_api_key
```

#### Levantar el servicio con Uvicorn

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

O bien:

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Una vez arriba, podrás acceder a:

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 23. Cómo usar Swagger para probar la API

Swagger es la forma más rápida de validar manualmente la API sin depender de frontend o Postman.

### Flujo recomendado de uso

1. levantar el entorno con Docker Compose o Uvicorn  
2. abrir `http://localhost:8000/docs`  
3. validar `GET /health`  
4. consultar `GET /preconfigured-scenarios`  
5. enviar un evento con `POST /webhooks/events`  
6. revisar `GET /events`  
7. inspeccionar `GET /events/{id}`  
8. si existe approval, aprobar o rechazar desde Swagger  

### ¿Qué puedes hacer desde Swagger?

- ejecutar endpoints directamente
- editar payloads
- revisar respuestas HTTP
- validar contratos
- probar escenarios manuales
- demostrar funcionalidad a evaluadores o stakeholders

### Ejemplo de prueba manual desde Swagger

#### Paso 1: validar salud del servicio

Usa `GET /health` y espera:

```json
{
  "status": "ok"
}
```

#### Paso 2: enviar un evento

Usa `POST /webhooks/events` con un payload como:

```json
{
  "project_id": "orders-api",
  "environment_id": "qa",
  "severity": "medium",
  "signal": "pod crash detected with OOM",
  "context": {
    "workload_id": "orders-api",
    "llm_mode": "with_llm"
  },
  "timestamp": "2024-04-03T14:45:00Z"
}
```

#### Paso 3: consultar resultado

- `GET /events`
- `GET /events/{id}`

#### Paso 4: si hubo approval

- `GET /approvals`
- `POST /approvals/{id}/approve`
- o `POST /approvals/{id}/reject`

### Cómo se consumen los servicios desde Swagger

Una vez abierto `http://localhost:8000/docs`, el consumo de endpoints se realiza directamente desde la interfaz.

#### Flujo general en Swagger

1. abrir el endpoint deseado  
2. presionar **Try it out**  
3. capturar o editar el payload si aplica  
4. presionar **Execute**  
5. revisar:
   - request URL
   - request body
   - response body
   - response code

### Servicios principales que pueden probarse desde Swagger

#### Validar salud del servicio

**Endpoint:** `GET /health`

**Uso:** Permite verificar rápidamente que la API está arriba y respondiendo.

#### Consultar escenarios preconfigurados

**Endpoint:** `GET /preconfigured-scenarios`

**Uso:** Permite obtener los escenarios de prueba preparados para validar el comportamiento funcional de la solución.

#### Enviar un evento al sistema

**Endpoint:** `POST /webhooks/events`

**Uso:** Es el endpoint principal de la API. Recibe el evento operativo, resuelve la decisión, aplica guardrails, ejecuta acción o genera approval según corresponda.

#### Consultar eventos registrados

**Endpoint:** `GET /events`

**Uso:** Devuelve la lista de eventos registrados en el sistema.

#### Consultar detalle de un evento

**Endpoint:** `GET /events/{id}`

**Uso:** Devuelve el detalle técnico completo de un evento específico.

#### Consultar approvals

**Endpoint:** `GET /approvals`

**Uso:** Permite listar las aprobaciones pendientes o resueltas.

#### Aprobar una acción pendiente

**Endpoint:** `POST /approvals/{id}/approve`

**Uso:** Permite aprobar una acción que no podía ejecutarse automáticamente por reglas del sistema.

#### Rechazar una acción pendiente

**Endpoint:** `POST /approvals/{id}/reject`

**Uso:** Permite rechazar una acción pendiente y registrar esa decisión como parte del feedback loop.

---

## 24. Variables de configuración

Según el entorno, la API puede utilizar variables como las siguientes:

```env
DATABASE_URL=sqlite:///./warden.db
LOG_DIR=./logs
GROQ_API_KEY=tu_api_key
ORCHESTRATOR_URL=http://mock-orchestrator:8001
NOTIFIER_URL=http://mock-notifier:8002
```

### Descripción general

- **DATABASE_URL**  
  Ubicación de la base de datos.

- **LOG_DIR**  
  Directorio donde se almacenan logs.

- **GROQ_API_KEY**  
  Clave del proveedor LLM cuando se use integración real.

- **ORCHESTRATOR_URL**  
  URL del mock o servicio de orquestación.

- **NOTIFIER_URL**  
  URL del mock o servicio de notificación.

---

## 25. Estructura del proyecto

Una estructura típica del backend incluye:

- `src/api/`  
  endpoints REST

- `src/clients/`  
  clientes hacia LLM, orchestrator y notifier

- `src/domain/`  
  enums, reglas, schemas, validadores, escenarios

- `src/models/`  
  modelos de persistencia

- `src/services/`  
  lógica principal del negocio

- `src/logging_config.py`  
  logging estructurado

- `src/main.py`  
  aplicación FastAPI

- `tests/`  
  pruebas automatizadas

- `mocks/`  
  mocks del ecosistema

- `logs/`  
  salida local de logs

---

## 26. Pruebas automatizadas

La API incluye pruebas automatizadas para validar los flujos más importantes del sistema.

### Cobertura funcional

Las pruebas cubren:

- validación del payload
- reglas de `safe_to_auto`
- ejecución/mock de acciones
- approvals
- feedback loop
- uso de historial por workload
- trazas de LLM/mock
- escenarios preconfigurados

### Tipos de pruebas incluidas

- pruebas unitarias
- pruebas de integración controlada
- pruebas con mocks de dependencias externas

### Dependencias mockeadas solo para tests

Durante la ejecución de tests se mockean dependencias externas como:

- `LLMClient.decide`
- `OrchestratorClient.restart`
- `OrchestratorClient.rollback`
- `OrchestratorClient.scale_up`
- `NotifierClient.send`

Esto permite validar el comportamiento del backend sin alterar su funcionamiento real fuera de pruebas.

---

## 27. Ejecución de pruebas unitarias

### Preparar entorno local

Desde la raíz del backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Ejecutar pruebas unitarias y funcionales

```bash
PYTHONPATH=. .venv/bin/pytest -q
```

### Ejecutar pruebas con coverage

```bash
PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing
```

### Guardar evidencia de ejecución de pruebas

```bash
PYTHONPATH=. .venv/bin/pytest -q | tee test-results.txt
PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing | tee coverage-results.txt
```

### Resultado de referencia validado

- **22 pruebas aprobadas**
- **80% de cobertura global**

### Evidencia esperada

Ejemplo de salida:

```text
22 passed in 0.37s
```

Y cobertura aproximada:

```text
TOTAL                                  645    126    80%
```

---

## 28. Escenarios preconfigurados cubiertos

La API contempla escenarios de referencia para validar el comportamiento esperado:

1. **QA · Restart automático por OOM**  
2. **PROD · Rollback requiere aprobación**  
3. **PROD · Scale up requiere aprobación**  
4. **Notify Human · Incidente ambiguo**  
5. **No Action · Evento informativo**  
6. **Critical · Nunca autoejecutar**  
7. **Baja confianza · Escalar a humano**

Estos escenarios son utilizados por frontend, pruebas automáticas y validación manual.

---

## 29. Seguridad y gobernanza

Aunque se trata de una implementación de prueba técnica, el diseño demuestra principios relevantes de seguridad:

- no ejecutar automáticamente lo que el LLM recomiende sin validación
- aplicar reglas rígidas antes de actuar
- exigir aprobación humana en escenarios de mayor riesgo
- dejar trazabilidad suficiente para auditoría
- separar recomendación de ejecución real

---

## 30. Manejo de errores

La API contempla manejo explícito de errores para casos como:

- payload inválido
- fallas de proveedor LLM
- fallas del mock orchestrator
- fallas del mock notifier
- approvals inexistentes
- errores de persistencia
- errores del flujo general

Los errores relevantes quedan registrados en logs estructurados.

---

## 31. Beneficios de la solución

### Técnicos
- arquitectura modular
- contratos claros
- facilidad de prueba
- observabilidad

### Operativos
- automatización controlada
- approvals en escenarios delicados
- trazabilidad de decisiones

### Arquitectónicos
- separación de responsabilidades
- posibilidad de ampliar guardrails
- posibilidad de reemplazar proveedor LLM

### De auditoría
- evidencia persistida
- logs estructurados
- detalle completo por evento

---

## 32. Limitaciones actuales

- acciones reales no ejecutadas sobre infraestructura productiva
- notifier real no integrado
- autenticación avanzada no implementada
- políticas desacopladas no implementadas
- multiusuario real fuera de alcance
- observabilidad distribuida no implementada
- sin hardening productivo completo

---

## 33. Posibles mejoras futuras

- integración real con Kubernetes
- integración con sistemas reales de notificación
- autenticación y RBAC
- políticas externas tipo OPA
- dashboards de métricas
- versionado de API
- trazabilidad distribuida
- correlación avanzada de eventos
- catálogo real de proyectos y ambientes
- modelo más sofisticado de aprendizaje con feedback

---

## 34. Conclusión

**Warden IDP Remediation Service API** demuestra una solución sólida para remediación asistida con control de riesgo. La API no se limita a proponer acciones, sino que incorpora un flujo más maduro:

- recomendación inteligente
- enforcement de políticas
- aprobación humana cuando corresponde
- persistencia histórica
- trazabilidad técnica
- pruebas automatizadas

Gracias al uso de **Python 3.12**, **FastAPI**, **Swagger**, **SQLAlchemy**, **Pydantic**, **httpx**, **pytest**, **Docker** y **Docker Compose**, el servicio resulta claro, demostrable, extensible y alineado con una arquitectura moderna de automatización segura.

---

## 35. Autor

Backend API desarrollado como parte de la solución **Warden IDP Remediation Service**, orientado a demostrar análisis, diseño, implementación, pruebas y trazabilidad de un sistema de remediación controlada.
