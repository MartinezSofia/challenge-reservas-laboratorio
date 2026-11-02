# Registro de decisiones y delegaciones

## Etapa 1: base de datos e inventario

- **Objetivo:** implementar el esquema SQLite, la conexión con claves foráneas, la carga idempotente del inventario y pruebas de persistencia durante la reinicialización.
- **Instrucción:** ejecutar solamente la etapa 1; usar bases SQLite temporales en pruebas; documentar los supuestos técnicos y no avanzar a etapas posteriores sin autorización.
- **Resultado:** implementación de la etapa 1 realizada por el agente. Se verificó la creación del esquema SQLite, la carga de las cinco unidades, la activación de claves foráneas y la conservación de reservas al reinicializar la base de datos.
- **Pruebas ejecutadas:** `python -m pytest tests/test_database.py -v`
- **Resultado de las pruebas:** 4 pruebas aprobadas, 0 fallidas. Ejecución realizada con Python 3.14.7 y pytest 9.2.0 en Windows.
- **Aceptación humana:** etapa 1 revisada y aceptada. Se autoriza continuar con la etapa 2.

## Etapa 2: validaciones temporales y disponibilidad

- **Objetivo:** validar fechas, horas e intervalos en UTC-3, normalizar los instantes a UTC y consultar disponibilidad según reservas activas.
- **Instrucción:** implementar exclusivamente `app/validaciones.py`, `app/disponibilidad.py`, sus pruebas y este registro; permitir inicio igual al momento actual; diferenciar intervalo inválido, equipo inexistente, equipo ocupado y disponible; no implementar creación, cancelación ni interfaz.
- **Resultado:** implementados los validadores temporales y la consulta SQLite con el criterio de superposición acordado. Se rechazó explícitamente `24:00` después de que la primera ejecución de pruebas detectara que `time.fromisoformat()` lo aceptaba. La aceptación humana queda pendiente de revisión.
- **Pruebas ejecutadas:** `python -m pytest -q tests/test_validaciones.py tests/test_disponibilidad.py` (primera ejecución: 1 fallida y 27 aprobadas; repetición tras la corrección: 28 aprobadas; ejecución final: 28 aprobadas).
- **Pruebas de etapa 1:** `python -m pytest -q tests/test_database.py`; 4 pruebas aprobadas.
- **Aceptación humana:** etapa 2 revisada y aceptada. Las 32 pruebas de las etapas 1 y 2 fueron ejecutadas conjuntamente y aprobadas.

### Etapa 3: creación y cancelación de reservas

- **Objetivo:** implementar las operaciones de creación y cancelación de reservas, respetando las reglas de disponibilidad y conservando el historial.
- **Delegación al agente:** se solicitó analizar la implementación existente y proponer una solución antes de modificar archivos. Luego de revisar la propuesta, se autorizó la implementación con precisiones sobre el esquema, la conservación de datos y el manejo de errores.
- **Archivos modificados o creados:** `app/reservas.py`, `app/disponibilidad.py` y `tests/test_reservas.py`.
- **Resultado:** se implementó la creación de reservas con identificador UUID, validación del solicitante, verificación transaccional de disponibilidad y cancelación lógica con registro del instante en UTC. Se extrajo un helper compartido para detectar superposiciones sin duplicar la consulta SQL.
- **Adaptación específica:** se utilizó `BEGIN IMMEDIATE` para mantener dentro de una misma transacción la comprobación de conflictos y la inserción de una reserva. La cancelación conserva los datos originales y actualiza únicamente el estado y el instante de cancelación.
- **Incidencias durante el desarrollo:** las primeras ejecuciones detectaron errores de indentación y problemas en algunas pruebas. El agente realizó correcciones y volvió a ejecutar las pruebas hasta obtener resultados satisfactorios.
- **Verificación ejecutada:** `python -m pytest -v`.
- **Resultado de verificación:** 14 pruebas específicas de reservas aprobadas y 46 pruebas totales aprobadas.
- **Base de datos:** no se modificó el esquema ni se reinició la base local. Las pruebas se ejecutaron utilizando bases de datos temporales.
- **Decisión humana:** etapa 3 revisada y aceptada después de inspeccionar los tres archivos y verificar los resultados finales de las pruebas.

### Etapa 4: integración de la interfaz de consola

- **Objetivo:** integrar las funcionalidades desarrolladas en las etapas anteriores mediante una interfaz de consola que permita utilizar el sistema de reservas.
- **Delegación al agente:** se solicitó analizar la arquitectura existente y proponer una solución antes de autorizar modificaciones. Luego de revisar la propuesta, se autorizó la creación de una interfaz de consola y sus pruebas automatizadas.
- **Archivos creados:** `app/main.py` y `tests/test_main.py`.
- **Resultado:** se implementó un menú interactivo que permite consultar disponibilidad, crear reservas, cancelar reservas y salir del sistema. La interfaz reutiliza las operaciones de los módulos existentes, sin duplicar las reglas de negocio.
- **Adaptaciones específicas:** se incorporó la posibilidad de inyectar la ruta de la base de datos y las funciones de entrada y salida para facilitar las pruebas. También se agregó el manejo de finalización de entrada (`EOFError`) durante cualquier operación.
- **Incidencias durante el desarrollo:** una primera ejecución de las pruebas detectó una diferencia de capitalización en una aserción de fecha inválida. Se corrigió la comparación y se volvieron a ejecutar las pruebas.
- **Verificación ejecutada:** `python -m pytest -q tests/test_main.py` y `python -m pytest -v`.
- **Resultado de verificación:** 14 pruebas de consola aprobadas y 60 pruebas totales aprobadas.
- **Decisión humana:** etapa 4 revisada y aceptada luego de inspeccionar el código, las pruebas y los resultados de ejecución.