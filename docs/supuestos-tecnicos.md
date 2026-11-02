# Supuestos técnicos

- Lenguaje: Python 3; persistencia: SQLite; pruebas: pytest.
- La zona horaria de entrada y salida es UTC-3, correspondiente al horario local acordado para Argentina. Los instantes se almacenan normalizados en UTC.
- Las fechas se ingresan como `AAAA-MM-DD` y las horas como `HH:MM` en formato de 24 horas.
- Se solicitan fecha y hora por separado para el inicio y para el fin, lo que permite reservas que atraviesan la medianoche.
- Se rechazan nuevas reservas cuyo inicio sea anterior al momento actual.
- No se imponen límites adicionales de duración ni de anticipación. El inicio debe ser anterior al fin.
- Las reservas se identifican con UUID y tienen estado `activa` o `cancelada`.
- La inicialización de la base de datos crea el esquema y carga el inventario fijo de cinco equipos de forma idempotente; no elimina reservas existentes.