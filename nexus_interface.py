from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict

# استيراد المكونات السيادية المرنة
from sovereign_foundation import db, settings
from sovereign_core import core

app = FastAPI(title="Sovereign Nexus Elite v6.0-FLEX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Sovereign Command Center | Flex</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&display=swap" rel="stylesheet">
        <style>
            body {{ 
                background: #05070a;
                color: #f1f5f9; 
                font-family: 'Space Grotesk', sans-serif;
            }}
            /* نفس الأنماط من قبل */
        </style>
    </head>
    <body class="p-8">
        <div class="max-w-[1700px] mx-auto">
            <div class="flex flex-col lg:flex-row justify-between items-center mb-12 p-8 rounded-lg bg-gray-800">
                <div>
                    <h1 class="text-5xl font-bold text-white">SOVEREIGN ELITE <span class="text-amber-500">v6.0-FLEX</span></h1>
                    <p class="text-slate-400 mt-2">Dynamic Slot Management via Helius gRPC Streaming</p>
                </div>
                <div class="flex gap-4 mt-6 lg:mt-0">
                    <input id="manual-mint" type="text" placeholder="Mint Address for manual override..." 
                           class="bg-gray-900 border border-gray-700 px-6 py-3 rounded-lg w-[400px] text-white">
                    <button onclick="addManual()" class="bg-amber-600 hover:bg-amber-500 text-white px-8 py-3 rounded-lg font-bold">Engage Manually</button>
                </div>
            </div>

            <div id="nexus-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- سيتم ملء البطاقات هنا ديناميكيًا -->
            </div>
        </div>

        <script>
            async function addManual() {{
                const mint = document.getElementById('manual-mint').value;
                if(!mint) return;
                await fetch('/api/slots/manual', {{ 
                    method: 'POST', 
                    headers: {{ 'Content-Type': 'application/json' }}, 
                    body: JSON.stringify({{ mint: mint }}) 
                }});
                document.getElementById('manual-mint').value = '';
                updateUI();
            }}

            async function updateUI() {{
                try {{
                    const response = await fetch('/api/pulse');
                    const data = await response.json();
                    
                    const grid = document.getElementById('nexus-grid');
                    grid.innerHTML = data.active_slots.map(slot => `
                        <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h3 class="text-xl font-bold text-amber-500">${{slot}}</h3>
                            <p class="text-slate-400 mt-2">Status: Currently Monitored</p>
                        </div>
                    `).join('');

                }} catch (e) {{ console.error("Nexus Refresh Error", e); }}
            }}

            setInterval(updateUI, 3000);
            updateUI();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/slots/manual")
async def add_manual_slot(request: Request):
    data = await request.json()
    mint = data.get("mint")
    if not mint: raise HTTPException(status_code=400)
    core.add_manual_token(mint)
    return {"status": "success"}

@app.get("/api/pulse")
async def get_system_pulse():
    try:
        return {
            "status": "online",
            "active_slots": core.active_slots,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
