from fastapi import FastAPI, Response
from pydantic import BaseModel
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import time
import os

# Creo una app per visualizzare le metriche prometheus
app = FastAPI(
      title="API Platform Demo",
      description="Servizio dimostrativo per la pipeline CI/CD + Kubernetes",
      version=os.getenv("APP_VERSION", "0.1.0"),
)

# Metriche base di Prometheus
REQUEST_COUNT = Counter("api_requests_total", "Numero totale di richieste ricevute", ["endpoint"])

START_TIME = time.time()

class Item(BaseModel):
      name: str
      description: str | None = None

# In-memory store, solo a scopo dimostrativo (non persistente)
_items_db: dict[int, Item] = {}
_next_id = 1

@app.get("/")
def read_root():
    REQUEST_COUNT.labels(endpoint="/").inc()
    return {
        "message": "API Platform Demo attiva",
        "version": os.getenv("APP_VERSION", "0.1.0"),
    }

@app.get("/items")
def list_items():
    REQUEST_COUNT.labels(endpoint="/items").inc()
    return _items_db

@app.post("/items", status_code=201)
def create_item(item: Item):
    global _next_id
    REQUEST_COUNT.labels(endpoint="/items").inc()
    _items_db[_next_id] = item
    created_id = _next_id
    _next_id += 1
    return {"id": created_id, **item.model_dump()}

@app.get("/items/{item_id}")
def get_item(item_id: int, response: Response):
    REQUEST_COUNT.labels(endpoint="/items/{id}").inc()
    item = _items_db.get(item_id)
    if item is None:
        response.status_code = 404
        return {"error": "Item non trovato"}
    return item

# --- Health checks (usati della probe Kubernetes)

@app.get("/healthz/live")
def liveness():
    return {"status" : "alive"}

@app.get("/healthz/ready")
def readiness():
    uptime = time.time() - START_TIME
    if uptime < 2:
        return Response(status_code=503, content='{"status": "starting"}')
    return {"status": "ready", "uptime_seconds": round(uptime, 2)}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
