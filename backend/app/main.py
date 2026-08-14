from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_admin import router as router_admin
from app.api.routes_auth import router as router_auth
from app.api.routes_checklist import router as router_checklist
from app.api.routes_configuracion import (
    router as router_configuracion,
    router_publico as router_configuracion_publico,
)
from app.api.routes_declarantes import router as router_declarantes
from app.api.routes_ganancias_ocasionales import router as router_ganancias_ocasionales
from app.api.routes_liquidacion import router as router_liquidacion
from app.api.routes_roles import router as router_roles          # DT-4
from app.api.routes_usuarios import router as router_usuarios
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para el asistente de declaración de renta (Formulario 210, DIAN).",
    version="0.6.0",   # DT-4: roles múltiples por usuario
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_auth)
app.include_router(router_usuarios)
app.include_router(router_roles)                        # DT-4 — gestión de roles adicionales
app.include_router(router_admin)
app.include_router(router_declarantes)
app.include_router(router_configuracion)
app.include_router(router_configuracion_publico)
app.include_router(router_liquidacion)
app.include_router(router_ganancias_ocasionales)
app.include_router(router_checklist)


@app.get("/salud", tags=["infraestructura"])
def salud():
    """Endpoint de verificación de disponibilidad (health check)."""
    return {"estado": "ok", "entorno": settings.entorno}