# Sistema de reservas de laboratorio

Aplicación local de consola para consultar disponibilidad y administrar reservas de equipos de un laboratorio universitario. Usa SQLite para conservar las reservas entre ejecuciones.

## 1. Especificación breve

### Contexto y objetivo

La coordinación de equipos mediante mensajes y planillas puede generar reservas superpuestas y horarios que permanecen bloqueados después de una cancelación. Este sistema centraliza la disponibilidad y el ciclo básico de las reservas, con persistencia local.

El alcance incluye consultar disponibilidad por equipo e intervalo, crear reservas con UUID y cancelar reservas sin borrar sus registros. La interfaz es de consola y el inventario es fijo; no permite administrar equipos.

### Inventario

| ID | Equipo |
|---|---|
| `MIC-01` | Microscopio digital |
| `MIC-02` | Microscopio digital |
| `OSC-01` | Osciloscopio |
| `MUL-01` | Multímetro |
| `FUE-01` | Fuente de alimentación |

Cada identificador representa una unidad física independiente. El inventario debe contener exactamente estas cinco unidades.

### Reglas, validaciones y aceptación

- Las reservas se identifican con UUID y tienen estado `activa` o `cancelada`.
- Una unidad no puede tener dos reservas activas que se superpongan. El criterio es `inicio_nuevo < fin_existente AND fin_nuevo > inicio_existente`.
- Los intervalos consecutivos se permiten: una reserva que termina a las 11:00 no impide otra que comienza a las 11:00. Los horarios de unidades diferentes pueden coincidir.
- Las reservas canceladas no bloquean la disponibilidad; la cancelación conserva el registro y sus datos originales.
- El equipo debe existir y el solicitante no puede estar vacío ni contener solamente espacios.
- Las fechas deben usar `AAAA-MM-DD` y las horas `HH:MM` en formato de 24 horas. Se validan fechas y horas reales.
- Se solicitan fecha y hora separadas para inicio y fin; se admiten intervalos que atraviesan la medianoche.
- El inicio debe ser anterior al fin. Se rechazan inicios anteriores al momento actual; un inicio exactamente igual al momento actual se permite.
- Las reservas activas y canceladas deben conservarse al cerrar y reiniciar la aplicación.

## 2. Solución

### Arquitectura

```text
app/
  database.py       Conexión SQLite, esquema e inicialización del inventario
  validaciones.py   Validación temporal y normalización de instantes a UTC
  disponibilidad.py Consulta de disponibilidad y detección de conflictos
  reservas.py      Creación UUID y cancelación transaccional
  main.py          Interfaz y punto de entrada de consola
data/
  inventario.json  Inventario fijo
  reservas.sqlite3 Base de datos local creada al inicializar
 tests/             Pruebas automatizadas con bases temporales
 docs/              Decisiones, delegaciones y supuestos técnicos
```

La interfaz delega las reglas a `validaciones.py`, `disponibilidad.py` y `reservas.py`. La creación y cancelación usan transacciones SQLite; la detección de conflictos considera únicamente reservas activas.

### Tecnologías y dependencias

- Python 3; la preparación del agente registra Python **3.14.7**.
- SQLite mediante el módulo estándar `sqlite3`. La versión de SQLite del entorno no está registrada.
- `pytest` para las pruebas; `docs/decisiones.md` registra la versión **9.2.0** durante la verificación de la etapa 1.
- No se requieren dependencias externas para ejecutar la aplicación. El repositorio no incluye `requirements.txt` ni un manifiesto de paquetes.

### Requisitos previos e instalación

Se necesita Python 3 instalado y accesible como `python`. Desde la raíz del repositorio, se puede preparar un entorno virtual e instalar pytest para desarrollo:

```powershell
git clone https://github.com/MartinezSofia/challenge-reservas-laboratorio.git
cd challenge-reservas-laboratorio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pytest==9.2.0
```

La versión de pytest indicada es la registrada en la documentación del proyecto; si se usa otra versión, debe verificarse la compatibilidad localmente.

### Inicialización y ejecución

Desde la raíz del repositorio:

```powershell
python -m app.main
```

Al iniciar, la aplicación llama a `initialize_database()`. El menú ofrece consultar disponibilidad, crear reserva, cancelar reserva y salir. Después de cada operación vuelve al menú principal. Si la entrada termina durante una operación, muestra un mensaje de salida controlada.

Para ejecutar toda la suite:

```powershell
python -m pytest -v
```

Las pruebas del proyecto usan bases SQLite temporales; no necesitan servicios externos.

### Ejemplo de uso

Una consulta solicita el identificador de equipo y el intervalo completo:

```text
Seleccione una opción: 1
Identificador del equipo: MIC-01
Fecha de inicio (AAAA-MM-DD): 2090-05-10
Hora de inicio (HH:MM): 10:00
Fecha de fin (AAAA-MM-DD): 2090-05-10
Hora de fin (HH:MM): 11:00
El equipo MIC-01 está disponible para ese intervalo.
```

Ese resultado corresponde al caso en que el intervalo esté libre; si hay conflicto, la aplicación informa que el equipo está ocupado e identifica una reserva conflictiva. Para crear una reserva se ingresan también el solicitante y los mismos cuatro datos temporales; el sistema confirma la operación y muestra el UUID generado. Para cancelar, se ingresa el UUID y se informa el éxito o el motivo por el que no se pudo cancelar.

### Persistencia e inventario

La ruta predeterminada es `data/reservas.sqlite3`, calculada respecto de la ubicación del código y no del directorio desde el que se invoque Python. La inicialización crea las tablas si faltan y carga el inventario desde `data/inventario.json` de forma idempotente. No elimina reservas existentes. Los datos SQLite están excluidos de Git por `.gitignore` (`data/*.sqlite3`).

Las fechas y horas ingresadas se interpretan con offset fijo UTC-3. Los instantes se guardan en UTC como texto ISO 8601. Una cancelación cambia el estado a `cancelada` y registra `cancelada_utc`; no elimina físicamente la reserva.

### Limitaciones y fuera de alcance

El inventario es fijo. No hay autenticación, notificaciones, integraciones externas ni interfaz gráfica. La consola permite consultar disponibilidad por intervalo, pero no incluye una opción para listar todo el historial de reservas. La zona horaria se aplica como offset fijo UTC-3 y no se adapta automáticamente a eventuales cambios normativos. No hay límites adicionales de duración ni de anticipación.

## 3. Preparación del agente

- **Entorno registrado:** Visual Studio Code en Windows; Python 3.14.7 y Git 2.53.0.windows.3, según `docs/agente.md`.
- **Agente:** GitHub Copilot Agent, utilizado como asistente de análisis, implementación y ejecución de pruebas.
- **Contexto del proyecto:** `AGENTS.md` define tecnologías, estructura, inventario, reglas, persistencia, pruebas y límites de alcance.
- **Herramientas y permisos:** el agente puede proponer cambios, modificar archivos autorizados y ejecutar pruebas; las operaciones que requieren aprobación deben consultarse antes. No se registran permisos para acciones destructivas sin aprobación.
- **Control humano:** el usuario revisa los cambios y decide su aceptación. Las decisiones registradas distinguen instrucciones, resultados e incidencias.
- **Adaptaciones específicas:** se permiten intervalos consecutivos, se rechazan superposiciones entre reservas activas, la cancelación conserva el registro y libera el horario, y el inicio igual al momento actual se permite.
- **Modelo utilizado:** pendiente de verificar en VS Code; no se consigna un nombre ni una versión no confirmados.

## 4. Registro de decisiones y delegación

Las etapas de desarrollo, las instrucciones delegadas, los resultados y las incidencias, junto con las decisiones y revisiones humanas, se registran en [`docs/decisiones.md`](docs/decisiones.md).

Documentación relacionada:

- [Preparación y uso del agente](docs/agente.md)
- [Supuestos técnicos](docs/supuestos-tecnicos.md)
