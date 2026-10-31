import uuid

URL = "https://www.example.com/articulos/arquitectura-cloud"


def crear(client, url=URL):
    return client.post("/shorten", json={"original_url": url})


def test_shorten_genera_uuid_y_guarda_en_dynamodb(client, tabla):
    r = crear(client)
    assert r.status_code == 201
    cuerpo = r.json()
    assert uuid.UUID(cuerpo["short_code"]).version == 4
    assert cuerpo["original_url"] == URL
    assert cuerpo["short_url"] == f"http://api.test:8000/{cuerpo['short_code']}"
    item = tabla.get_item(Key={"short_code": cuerpo["short_code"]})["Item"]
    assert item["original_url"] == URL
    assert "created_at" in item


def test_cada_enlace_tiene_su_propio_uuid(client, tabla):
    a = crear(client).json()["short_code"]
    b = crear(client).json()["short_code"]
    assert a != b
    assert tabla.scan()["Count"] == 2


def test_url_invalida_da_422(client):
    assert crear(client, "no-es-una-url").status_code == 422
    assert crear(client, "ftp://archivos.com/x").status_code == 422
    assert client.post("/shorten", json={}).status_code == 422


def test_redireccion_307_al_destino(client):
    codigo = crear(client).json()["short_code"]
    r = client.get(f"/{codigo}")
    assert r.status_code == 307
    assert r.headers["location"] == URL


def test_head_tambien_redirige(client):
    codigo = crear(client).json()["short_code"]
    r = client.head(f"/{codigo}")
    assert r.status_code == 307
    assert r.headers["location"] == URL


def test_uuid_inexistente_da_404(client):
    assert client.get(f"/{uuid.uuid4()}").status_code == 404


def test_codigo_que_no_es_uuid_da_404(client):
    assert client.get("/hola").status_code == 404
    assert client.get("/urls/hola").status_code == 404


def test_consultar_enlace(client):
    creado = crear(client).json()
    r = client.get(f"/urls/{creado['short_code']}")
    assert r.status_code == 200
    info = r.json()
    assert info["short_code"] == creado["short_code"]
    assert info["original_url"] == URL
    assert info["created_at"].endswith("+00:00")


def test_consultar_inexistente_da_404(client):
    assert client.get(f"/urls/{uuid.uuid4()}").status_code == 404


def test_docs_y_estado_no_los_atrapa_la_redireccion(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/estado").json()["tabla_dynamodb"] == "links-test"


def test_cors_acepta_solo_el_frontend(client):
    pre = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
    ok = client.options("/shorten", headers={"Origin": "http://front.test", **pre})
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == "http://front.test"
    malo = client.options("/shorten", headers={"Origin": "http://malo.com", **pre})
    assert malo.status_code == 400
