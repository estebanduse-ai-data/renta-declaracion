from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_liquidacion import router as router_liquidacion
from app.api.routes_ganancias_ocasionales import router as router_ganancias_ocasionales
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para el asistente de declaración de renta (Formulario 210, DIAN).",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_liquidacion)
app.include_router(router_ganancias_ocasionales)


@app.get("/salud", tags=["infraestructura"])
def salud():
    """Endpoint de verificación de disponibilidad (health check)."""
    return {"estado": "ok", "entorno": settings.entorno}
