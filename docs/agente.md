# Preparación y uso del agente

## 1. Entorno

- **Editor:** Visual Studio Code.
- **Agente:** GitHub Copilot Agent.
- **Extensión:** GitHub Copilot Chat.
- **Lenguaje del proyecto:** Python 3.14.7.
- **Sistema de control de versiones:** Git 2.53.0.windows.3.
- **Sistema operativo:** Windows 11.

## 2. Modelo utilizado

- **Modelo seleccionado:** no se pudo verificar el nombre desde la información disponible en el entorno.
- **Versión o identificador:** no disponible.
- **Función:** asistencia en el análisis, implementación, corrección y verificación del sistema de reservas.

No se atribuye al agente un modelo o versión que no haya podido comprobarse.

## 3. Instrucciones y contexto suministrado

Se utilizó el archivo `AGENTS.md` como contexto permanente del proyecto. Este archivo establece:

- Objetivo y alcance del sistema.
- Inventario fijo de equipos.
- Tecnologías y estructura de carpetas.
- Reglas de disponibilidad y superposición de reservas.
- Validaciones requeridas.
- Persistencia mediante SQLite.
- Requisitos de pruebas automatizadas.
- Restricciones para evitar modificaciones no autorizadas.

El agente recibió instrucciones para trabajar por etapas, realizar cambios acotados, ejecutar las pruebas correspondientes y no inventar resultados. También se estableció que debía solicitar autorización antes de realizar cambios fuera del alcance acordado o acciones destructivas.

## 4. Permisos y controles humanos

El agente trabajó en modo Agent desde Visual Studio Code, con capacidad para leer y modificar archivos del repositorio y ejecutar comandos de terminal.

El trabajo se organizó en etapas. Antes de implementar cada una, se revisó la propuesta del agente y se autorizaron los archivos y cambios correspondientes.

Los controles humanos incluyeron:

- Revisar las propuestas antes de autorizar la implementación.
- Inspeccionar los archivos modificados.
- Comprobar que se respetaran las reglas de negocio.
- Ejecutar y revisar las pruebas automatizadas.
- Realizar pruebas manuales de los flujos principales.
- Decidir la aceptación de cada etapa antes de continuar.

Las operaciones de Git, como los commits y los envíos al repositorio remoto, fueron realizadas y verificadas por el usuario.

## 5. Adaptaciones específicas del proyecto

Durante el desarrollo se establecieron y verificaron las siguientes adaptaciones:

- Permitir reservas consecutivas en una misma unidad.
- Rechazar reservas activas con intervalos superpuestos.
- Permitir reservas simultáneas en unidades diferentes.
- Conservar los registros y datos originales al cancelar una reserva.
- Liberar el intervalo de una reserva cancelada.
- Utilizar `BEGIN IMMEDIATE` para mantener la comprobación de disponibilidad y la inserción dentro de una misma transacción.
- Permitir el inicio de una reserva exactamente en el momento actual.
- Manejar `EOFError` durante las operaciones de consola para finalizar la aplicación de manera controlada.
- Utilizar bases de datos temporales en las pruebas para evitar modificar la base de datos local.

## 6. Episodios de delegación y revisión

### Episodio 1. Análisis inicial y definición técnica

**Objetivo:** comprobar que el agente comprendiera el alcance y las reglas del proyecto antes de comenzar el desarrollo.

**Contexto suministrado:** archivo `AGENTS.md`, con las funcionalidades, reglas de negocio, tecnologías, estructura y pruebas requeridas.

**Instrucción y acción del agente:** se solicitó leer y analizar las instrucciones sin modificar archivos. El agente identificó las funcionalidades principales, las reglas de superposición y persistencia, y aspectos técnicos que necesitaban definirse antes de implementar.

**Resultado:** se obtuvo un análisis inicial y se identificó la necesidad de precisar los supuestos técnicos.

**Decisión humana:** se aceptó el análisis y se resolvieron los supuestos antes de autorizar la implementación.

**Evidencias:** `AGENTS.md`, `docs/supuestos-tecnicos.md` y registro de la primera interacción en el historial de GitHub Copilot Chat.

### Episodio 2. Implementación de creación y cancelación

**Objetivo:** implementar las operaciones de creación y cancelación de reservas, respetando las reglas de disponibilidad y la conservación del historial.

**Contexto suministrado:** módulos existentes de base de datos, validaciones temporales y consulta de disponibilidad.

**Instrucción y acción del agente:** primero se solicitó analizar la implementación existente y proponer una solución. Después de revisar la propuesta, se autorizó trabajar sobre los archivos acordados, sin modificar el esquema de la base de datos.

**Resultado:** se implementó la creación de reservas con UUID, la verificación transaccional de disponibilidad y la cancelación lógica. Se incorporó un helper compartido para detectar conflictos y se agregaron pruebas específicas.

**Decisión humana:** se aprobaron las precisiones sobre la conservación de datos, el manejo de errores y el uso de transacciones. La etapa fue aceptada después de revisar los archivos y comprobar las pruebas.

**Evidencias:** `app/reservas.py`, `app/disponibilidad.py`, `tests/test_reservas.py` y `docs/decisiones.md`.

### Episodio 3. Corrección del manejo de fin de entrada en la consola

**Objetivo:** asegurar que la aplicación pudiera finalizar de manera controlada cuando se produjera un fin de entrada durante una operación, no solamente al seleccionar una opción del menú.

**Contexto suministrado:** implementación de la interfaz de consola y pruebas existentes de `app/main.py` y `tests/test_main.py`.

**Instrucción y acción del agente:** se solicitó ampliar el manejo de `EOFError` alrededor del despacho completo de las operaciones y fortalecer las pruebas, manteniendo los cambios limitados a los dos archivos autorizados.

**Resultado:** el agente incorporó el manejo de fin de entrada durante las operaciones y agregó pruebas para comprobar ese comportamiento, además de mejorar otros casos de prueba de la interfaz.

**Incidencias:** una primera ejecución detectó una diferencia de capitalización en una aserción de fecha inválida. Se corrigió y se repitieron las pruebas.

**Decisión humana:** se revisaron los cambios y los resultados. Se aceptó la etapa después de obtener 14 pruebas específicas de consola aprobadas y 60 pruebas totales aprobadas.

**Evidencias:** `app/main.py`, `tests/test_main.py` y `docs/decisiones.md`.

## 7. Documentación relacionada

- [Registro de decisiones y delegaciones](decisiones.md).
- [Supuestos técnicos](supuestos-tecnicos.md).
- [Instrucciones permanentes del proyecto](../AGENTS.md).
- [README del proyecto](../README.md).