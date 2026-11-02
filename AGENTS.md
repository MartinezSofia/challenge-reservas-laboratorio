
# Instrucciones del agente - Sistema de reservas de laboratorio

## 1. Contexto del proyecto

Estamos desarrollando un sistema local de reservas para un laboratorio universitario.

Actualmente, la coordinación registra pedidos mediante mensajes y planillas, lo que puede provocar reservas superpuestas y horarios bloqueados por cancelaciones.

El objetivo es desarrollar una aplicación sencilla, verificable y persistente que permita administrar las reservas de los equipos disponibles.

## 2. Tecnologías

- Lenguaje: Python 3.
- Base de datos: SQLite.
- Interfaz: consola.
- Pruebas automáticas: pytest.
- Control de versiones: Git.

Priorizar las bibliotecas estándar de Python y evitar dependencias innecesarias.

## 3. Inventario inicial

El inventario es fijo y debe contener exactamente estas unidades:

| ID | Equipo |
|---|---|
| MIC-01 | Microscopio digital |
| MIC-02 | Microscopio digital |
| OSC-01 | Osciloscopio |
| MUL-01 | Multímetro |
| FUE-01 | Fuente de alimentación |

Cada identificador representa una unidad física independiente.

No implementar funciones para agregar, modificar o eliminar equipos.

## 4. Funcionalidades obligatorias

El sistema debe permitir:

1. Consultar las reservas y la disponibilidad de una unidad para un intervalo.
2. Crear reservas con identificador único, unidad, solicitante, fecha y horario de inicio y finalización.
3. Cancelar reservas conservando su identificador y todos sus datos.
4. Recuperar las reservas y sus estados después de cerrar y reiniciar la aplicación.

## 5. Reglas de negocio

- Una unidad no puede tener dos reservas activas cuyos intervalos se superpongan.
- Las reservas canceladas no bloquean la disponibilidad.
- Se permiten reservas consecutivas: si una termina a las 11:00, otra puede comenzar a las 11:00.
- Se permiten reservas simultáneas de unidades diferentes.
- El identificador de equipo debe existir en el inventario.
- El solicitante no puede estar vacío ni contener solamente espacios.
- Las fechas y horas deben ser válidas.
- El inicio debe ser estrictamente anterior al fin.
- La consulta de disponibilidad debe utilizar exactamente las mismas reglas de superposición que la creación de reservas.

Para detectar superposiciones, utilizar el criterio:

inicio_nuevo < fin_existente AND fin_nuevo > inicio_existente

Solamente deben considerarse reservas activas.

### Adaptación específica obligatoria

Prestar especial atención a los límites consecutivos.

Una reserva de 10:00 a 11:00 y otra de 11:00 a 12:00 para MIC-01 deben ser válidas.

Una reserva de 10:30 a 11:30 para MIC-01 debe rechazarse si existe una reserva activa de 10:00 a 11:00.

Esta regla también debe respetarse en las consultas de disponibilidad.

## 6. Persistencia

- Utilizar SQLite.
- Guardar las reservas y sus estados en una base de datos.
- No eliminar registros al cancelar una reserva.
- Mantener el historial de reservas.
- No borrar automáticamente la base de datos al iniciar la aplicación.
- Separar la inicialización de la base de datos de cualquier operación de reinicio de datos.

## 7. Validaciones y pruebas

Implementar pruebas automáticas para:

1. Creación de una reserva válida.
2. Rechazo de superposiciones.
3. Aceptación de reservas consecutivas.
4. Aceptación de reservas simultáneas en unidades diferentes.
5. Rechazo de unidades inexistentes.
6. Rechazo de solicitantes vacíos.
7. Rechazo de intervalos inválidos.
8. Cancelación que conserva el registro y libera el horario.
9. Persistencia de reservas activas y canceladas después de reiniciar.

Las pruebas no deben depender de datos reales ni de servicios externos.

## 8. Organización del código

Mantener responsabilidades separadas:

- app/main.py: punto de entrada e interfaz de consola.
- app/reservas.py: operaciones de creación y cancelación.
- app/disponibilidad.py: consultas y validaciones de disponibilidad.
- app/database.py: conexión e inicialización de SQLite.
- data/: inventario y archivos de datos.
- tests/: pruebas automáticas.
- docs/: documentación y registros del proyecto.

Se pueden proponer cambios en esta estructura si existe una justificación técnica.

## 9. Forma de trabajo del agente

- Trabajar sobre el repositorio existente.
- Antes de implementar, explicar brevemente el enfoque.
- Realizar cambios pequeños y verificables.
- No sobrescribir archivos existentes sin revisar su contenido.
- No eliminar datos ni ejecutar comandos destructivos sin autorización.
- Solicitar aprobación antes de instalar dependencias o ejecutar operaciones potencialmente destructivas.
- Ejecutar las pruebas pertinentes después de implementar cambios.
- Informar los archivos modificados y los resultados reales de las pruebas.
- No afirmar que una prueba pasó si no fue ejecutada.
- No inventar resultados, evidencias, decisiones humanas ni intervenciones.

## 10. Documentación y trazabilidad

Registrar las decisiones técnicas importantes en docs/.

Conservar las instrucciones, adaptaciones y decisiones relevantes para futuras sesiones.

Distinguir claramente entre:
- Acciones realizadas por el agente.
- Revisiones realizadas por el usuario.
- Correcciones aceptadas o rechazadas.
- Pruebas realmente ejecutadas y sus resultados.

No incluir contraseñas, tokens, credenciales ni información personal real.

## 11. Supuestos técnicos

Documentar explícitamente los supuestos adoptados sobre:

- Zona horaria.
- Formato de fechas y horas.
- Tratamiento de fechas pasadas.
- Duración de las reservas.
- Anticipación permitida.

No introducir restricciones arbitrarias sin documentarlas.

## 12. Prioridad

La prioridad es cumplir todos los requisitos funcionales y verificables de la consigna antes de implementar funcionalidades adicionales.

No agregar autenticación, pagos, notificaciones, integraciones externas ni interfaces gráficas complejas.
