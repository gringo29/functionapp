import logging
import azure.functions as func
import urllib.request
import urllib.parse
import tempfile
import zipfile
import os


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Procesando solicitud de certificado...")

    # Leer parámetros del request
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid body", status_code=400)

    hostname = req_body.get("hostname")
    if not hostname:
        return func.HttpResponse("Falta 'hostname'", status_code=400)

    # Configuración de la VM que genera certificados
    api_url = "http://172.171.221.176:5000/getcert"
    vm_user = "demo"
    vm_pass = "1234"

    try:
        # Preparar data del POST
        data = urllib.parse.urlencode({
            "user": vm_user,
            "pass": vm_pass,
            "hostname": hostname
        }).encode("utf-8")

        # Enviar request a la VM
        req_vm = urllib.request.Request(api_url, data=data, method="POST")
        with urllib.request.urlopen(req_vm, timeout=15) as resp:
            if resp.status != 200:
                return func.HttpResponse(
                    f"Error desde VM: {resp.status} {resp.reason}",
                    status_code=500
                )
            response_content = resp.read()

        # Guardar temporalmente el .tar.gz recibido
        temp_dir = tempfile.mkdtemp()
        tar_path = os.path.join(temp_dir, f"{hostname}.tar.gz")
        with open(tar_path, "wb") as f:
            f.write(response_content)

        # Crear un zip con el client.ovpn y los certificados
        zip_path = os.path.join(temp_dir, f"{hostname}.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(tar_path, arcname=f"{hostname}.tar.gz")

            ovpn_content = f"""
client
dev tun
proto udp
remote 172.171.221.176 1194
resolv-retry infinite
nobind
persist-key
persist-tun
ca ca.crt
cert {hostname}.crt
key {hostname}.key
remote-cert-tls server
cipher AES-256-CBC
auth SHA256
verb 3
"""
            ovpn_path = os.path.join(temp_dir, "client.ovpn")
            with open(ovpn_path, "w") as ovpn_file:
                ovpn_file.write(ovpn_content)
            zipf.write(ovpn_path, arcname="client.ovpn")

        # Devolver el zip
        with open(zip_path, "rb") as f:
            zip_bytes = f.read()

        headers = {
            "Content-Disposition": f"attachment; filename={hostname}.zip"
        }
        return func.HttpResponse(zip_bytes, headers=headers, mimetype="application/zip")

    except Exception as e:
        logging.error(f"Error en Function App: {e}")
        return func.HttpResponse(f"Internal error: {str(e)}", status_code=500)
