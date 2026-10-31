"""API del acortador de enlaces: crea enlaces cortos, los consulta y redirige."""
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

from app.config import settings
from app.repository import RepoDep

app = FastAPI(
    title="Acortador de enlaces",
    version="1.0.0",
    description="Crea enlaces cortos con UUID, los guarda en Amazon DynamoDB y redirige con 307.",
)

# La interfaz vive en otro origen (bucket S3), por eso la API debe permitirlo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ShortenRequest(BaseModel):
    original_url: HttpUrl = Field(description="URL http o https que se quiere acortar")


class ShortenResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str


class LinkInfo(BaseModel):
    short_code: str
    original_url: str
    created_at: str


def _short_url(short_code: str) -> str:
    return f"{settings.public_base_url}/{short_code}"


def _buscar(repo, short_code: str) -> dict:
    # Un código que ni siquiera es UUID tampoco existe: 404, no 422.
    try:
        codigo = str(uuid.UUID(short_code))
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El enlace no existe")
    item = repo.find(codigo)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El enlace no existe")
    return item


@app.get("/", tags=["Estado"])
def raiz():
    return {"mensaje": "API del acortador de enlaces", "documentacion": "/docs"}


@app.get("/estado", tags=["Estado"])
def estado(repo: RepoDep):
    return {
        "tabla_dynamodb": settings.table_name,
        "region": settings.aws_region,
        "iam_role": repo.role_name(),
    }


@app.post("/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED, tags=["Enlaces"])
def shorten(data: ShortenRequest, repo: RepoDep):
    short_code = str(uuid.uuid4())  # el UUID se genera aquí, en el backend
    original_url = str(data.original_url)
    repo.save(
        {
            "short_code": short_code,
            "original_url": original_url,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
    return ShortenResponse(short_code=short_code, original_url=original_url, short_url=_short_url(short_code))


@app.get("/urls/{short_code}", response_model=LinkInfo, tags=["Enlaces"])
def link_info(short_code: str, repo: RepoDep):
    item = _buscar(repo, short_code)
    return LinkInfo(**item)


# Va al final: atrapa cualquier ruta de un solo segmento que no se haya definido antes.
@app.api_route("/{short_code}", methods=["GET", "HEAD"], tags=["Enlaces"])
def redirect(short_code: str, repo: RepoDep):
    item = _buscar(repo, short_code)
    return RedirectResponse(item["original_url"], status_code=status.HTTP_307_TEMPORARY_REDIRECT)
