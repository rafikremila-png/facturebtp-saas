"""
Minimal backend server - Health check only.
All data operations are handled by Supabase directly from the frontend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BTP Facture - Health Check")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "supabase-only"}

@app.get("/api/{path:path}")
def catch_all(path: str):
    return {
        "error": "This endpoint is no longer available.",
        "message": "L'application utilise désormais Supabase directement.",
        "mode": "supabase-only"
    }
