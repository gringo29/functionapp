# __init__.py dentro de tu Function
import logging
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HelloFunction ha sido invocada.')

    # Leer parámetro "name" del query string o body JSON
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        name = req_body.get('name')

    # Responder siempre con JSON
    return func.HttpResponse(
        json.dumps({"message": f"Hola {name} desde Azure Function!"}),
        mimetype="application/json",
        status_code=200
    )
