import os
from fastapi import Request
from fastapi.responses import HTMLResponse
from pathlib import Path
from src.config.constants import BASE_DIR

async def get_welcome_page(request: Request):
    base_url = str(request.base_url).rstrip("/")
    query_key = request.query_params.get("API_KEY")
    
    # Simplesmente ecoamos o que vier na URL ou mostramos "sua-chave" se vazio.
    # Isso evita confirmar se a chave esta correta ou nao (seguranca contra brute-force).
    display_key = query_key if query_key else "sua-chave"
    
    template_path = Path(BASE_DIR) / "src" / "views" / "welcome.html"
    
    try:
        if not template_path.exists():
            return HTMLResponse("<h1>Template welcome.html não encontrado</h1>", status_code=500)
            
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
            
        html = html.replace("{{BASE_URL}}", base_url)
        html = html.replace("{{API_KEY}}", display_key)
        
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(f"<h1>Erro ao carregar página de boas-vindas</h1><p>{str(e)}</p>", status_code=500)
