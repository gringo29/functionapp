# __init__.py de tu función HelloFunction
import logging
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HelloFunction ha sido invocada.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        name = req_body.get('name')

    if name:
        mensaje = {"message": f"Hola {name}, tu Function ha sido invocada correctamente!"}
    else:
        mensaje = {"message": "Hola, no enviaste nombre."}

    return func.HttpResponse(
        json.dumps(mensaje),
        mimetype="application/json",
        status_code=200
    )
