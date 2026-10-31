"""Configuración leída de variables de entorno (.env).

Si falta una variable obligatoria, la API no arranca y dice cuál falta.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

OBLIGATORIAS = ("DYNAMODB_TABLE", "PUBLIC_BASE_URL")


@dataclass(frozen=True)
class Settings:
    table_name: str
    aws_region: str
    public_base_url: str
    cors_origins: list[str]


def load_settings() -> Settings:
    faltan = [n for n in OBLIGATORIAS if not os.getenv(n, "").strip()]
    if faltan:
        raise RuntimeError(f"Faltan variables de entorno: {', '.join(faltan)}")
    origenes = os.getenv("CORS_ORIGINS", "")
    return Settings(
        table_name=os.environ["DYNAMODB_TABLE"].strip(),
        aws_region=os.getenv("AWS_REGION", "us-east-1").strip(),
        public_base_url=os.environ["PUBLIC_BASE_URL"].strip().rstrip("/"),
        cors_origins=[o.strip().rstrip("/") for o in origenes.split(",") if o.strip()],
    )


settings = load_settings()
