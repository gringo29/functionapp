import logging
import requests
import tempfile
import tarfile
import os
import io
import zipfile
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Function triggered")

    # Recibir hostname
    hostname = req.params.get("hostname")
    if not hostname:
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse("Falta parámetro hostname", status_code=400)
        hostname = req_body.get("hostname")

    if not hostname:
        return func.HttpResponse("Debe especificar hostname", status_code=400)

    # Usuario, password y API URL de la VM
    vm_user = os.environ.get("VM_USER", "demo")
    vm_pass = os.environ.get("VM_PASS", "1234")
    api_url = os.environ.get("VM_API_URL", "http://172.171.221.176:5000/getcert")

    # POST a la VM
    files = {
        "user": (None, vm_user),
        "pass": (None, vm_pass),
        "hostname": (None, hostname)
    }

    try:
        response = requests.post(api_url, files=files, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return func.HttpResponse(f"Error conectando a la VM: {str(e)}", status_code=502)

    # Guardar tar.gz recibido en temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp_tar:
        tmp_tar.write(response.content)
        tmp_tar_path = tmp_tar.name

    # Extraer tar.gz a temp dir
    extract_dir = tempfile.mkdtemp()
    try:
        with tarfile.open(tmp_tar_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)
    except Exception as e:
        return func.HttpResponse(f"Error extrayendo el certificado: {str(e)}", status_code=500)

    # Crear archivo client.ovpn
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
tls-auth ./tacloud.key 1
cipher AES-256-GCM
auth SHA256
verb 3
"""
    ovpn_path = os.path.join(extract_dir, "client.ovpn")
    with open(ovpn_path, "w") as f:
        f.write(ovpn_content)

    # Crear zip en memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Agregar todos los archivos del extract_dir
        for root, _, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, extract_dir)
                zipf.write(file_path, arcname)

    zip_buffer.seek(0)

    # Devolver zip como response
    headers = {
        "Content-Disposition": f"attachment; filename={hostname}_certs.zip"
    }
    return func.HttpResponse(zip_buffer.read(), mimetype="application/zip", headers=headers)
