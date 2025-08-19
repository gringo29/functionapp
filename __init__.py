import logging
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hola, {name}. La Function en Azure respondió OK.", status_code=200)
    else:
        return func.HttpResponse(
            "Pasa un parámetro 'name' en la query string o en el cuerpo de la petición.",
            status_code=400
        )
