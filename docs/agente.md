
# Preparación y uso del agente

## Entorno

- Editor: Visual Studio Code.
- Agente: GitHub Copilot Agent.
- Extensión: GitHub Copilot Chat.
- Lenguaje del proyecto: Python 3.14.7.
- Control de versiones: Git 2.53.0.windows.3.

## Modelo

- Modelo seleccionado: pendiente de verificar en VS Code.
- Versión o identificador: pendiente de verificar.
- Función: asistencia y delegación de tareas de programación.

## Instrucciones

Se utiliza el archivo AGENTS.md como contexto permanente del proyecto.

## Permisos y controles

El agente puede proponer y realizar modificaciones sobre los archivos del repositorio, ejecutar pruebas y solicitar autorización para acciones que requieran aprobación.

El usuario revisa los cambios antes de aceptarlos.

## Adaptación específica

Se establecieron instrucciones explícitas para:
- Permitir reservas consecutivas.
- Rechazar intervalos superpuestos.
- Mantener la persistencia de reservas canceladas.
- No eliminar registros al cancelar.

## Evidencias

Pendiente de incorporar:
- Primera interacción con el agente.
- Modelo utilizado, cuando sea visible.
- Instrucciones y resultados de las delegaciones.
- Revisiones humanas.

## Primera interacción documentada

**Objetivo:** verificar que el agente comprendiera las instrucciones del proyecto antes de comenzar el desarrollo.

**Contexto suministrado:** archivo AGENTS.md con descripción del sistema, funcionalidades, reglas de negocio, tecnologías y pruebas requeridas.

**Instrucción:** se solicitó leer y analizar AGENTS.md sin modificar archivos.

**Resultado:** el agente identificó correctamente las funcionalidades, reglas de superposición, persistencia y pruebas. También detectó ambigüedades técnicas y una diferencia en el nombre de la carpeta de pruebas.

**Decisión humana:** se aceptó el análisis y se decidió resolver las ambigüedades antes de autorizar el desarrollo.

**Evidencia:** primera interacción registrada en el historial de GitHub Copilot Chat.