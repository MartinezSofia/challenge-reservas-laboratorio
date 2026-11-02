from collections.abc import Callable
from pathlib import Path

from app.database import DEFAULT_DATABASE_PATH, initialize_database
from app.disponibilidad import (
    EquipoNoEncontradoError,
    consultar_disponibilidad,
)
from app.reservas import (
    ReservaNoEncontradaError,
    ReservaSuperpuestaError,
    ReservaYaCanceladaError,
    SolicitanteInvalidoError,
    cancelar_reserva,
    crear_reserva,
)
from app.validaciones import ValidacionTemporalError


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def _leer_intervalo(input_fn: InputFunction) -> tuple[str, str, str, str]:
    fecha_inicio = input_fn("Fecha de inicio (AAAA-MM-DD): ")
    hora_inicio = input_fn("Hora de inicio (HH:MM): ")
    fecha_fin = input_fn("Fecha de fin (AAAA-MM-DD): ")
    hora_fin = input_fn("Hora de fin (HH:MM): ")
    return fecha_inicio, hora_inicio, fecha_fin, hora_fin


def _mostrar_menu(output_fn: OutputFunction) -> None:
    output_fn("\nSistema de reservas de laboratorio")
    output_fn("1. Consultar disponibilidad")
    output_fn("2. Crear reserva")
    output_fn("3. Cancelar reserva")
    output_fn("0. Salir")


def _consultar(
    input_fn: InputFunction,
    output_fn: OutputFunction,
    database_path: str | Path,
) -> None:
    equipo_id = input_fn("Identificador del equipo: ").strip()
    intervalo = _leer_intervalo(input_fn)
    try:
        resultado = consultar_disponibilidad(
            equipo_id,
            *intervalo,
            database_path=database_path,
        )
    except (EquipoNoEncontradoError, ValidacionTemporalError) as error:
        output_fn(f"Error: {error}")
        return

    if resultado.disponible:
        output_fn(f"El equipo {equipo_id} está disponible para ese intervalo.")
    else:
        output_fn(
            f"El equipo {equipo_id} está ocupado. Reserva en conflicto: "
            f"{resultado.reserva_conflictiva_id}."
        )


def _crear(
    input_fn: InputFunction,
    output_fn: OutputFunction,
    database_path: str | Path,
) -> None:
    equipo_id = input_fn("Identificador del equipo: ").strip()
    solicitante = input_fn("Nombre del solicitante: ")
    intervalo = _leer_intervalo(input_fn)
    try:
        reserva_id = crear_reserva(
            equipo_id,
            solicitante,
            *intervalo,
            database_path=database_path,
        )
    except (
        EquipoNoEncontradoError,
        ReservaSuperpuestaError,
        SolicitanteInvalidoError,
        ValidacionTemporalError,
    ) as error:
        output_fn(f"Error: {error}")
        return

    output_fn(f"Reserva creada correctamente. Identificador: {reserva_id}")


def _cancelar(
    input_fn: InputFunction,
    output_fn: OutputFunction,
    database_path: str | Path,
) -> None:
    reserva_id = input_fn("Identificador de la reserva: ").strip()
    try:
        cancelar_reserva(reserva_id, database_path=database_path)
    except (ReservaNoEncontradaError, ReservaYaCanceladaError) as error:
        output_fn(f"Error: {error}")
        return

    output_fn(f"Reserva {reserva_id} cancelada correctamente.")


def run(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    input_fn: InputFunction | None = None,
    output_fn: OutputFunction | None = None,
) -> None:
    read_input = input if input_fn is None else input_fn
    write_output = print if output_fn is None else output_fn
    initialize_database(database_path)

    while True:
        _mostrar_menu(write_output)
        try:
            opcion = read_input("Seleccione una opción: ").strip()
            if opcion == "1":
                _consultar(read_input, write_output, database_path)
            elif opcion == "2":
                _crear(read_input, write_output, database_path)
            elif opcion == "3":
                _cancelar(read_input, write_output, database_path)
            elif opcion == "0":
                write_output("Saliendo del sistema.")
                return
            else:
                write_output("Opción inválida. Seleccione 1, 2, 3 o 0.")
        except EOFError:
            write_output("Entrada finalizada. Saliendo del sistema.")
            return


def main() -> None:
    run()


if __name__ == "__main__":
    main()