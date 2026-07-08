from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Renta Declaración API"
    entorno: str = "desarrollo"  # desarrollo | pruebas | produccion

    database_url: str = "postgresql+psycopg://renta:renta@db:5432/renta_declaracion"

    jwt_secret_key: str = "cambiar-en-produccion"
    jwt_algoritmo: str = "HS256"
    jwt_expiracion_minutos: int = 60

    # Se agregarán aquí los orígenes permitidos de CORS cuando exista el
    # frontend desplegado (Fase 1: solo red interna).
    origenes_permitidos: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
