from apps.FastAPI.app.routers.products import router as products_router

from fastapi import FastAPI

app = FastAPI(title="Ecommerce API", version="0.1.0")

app.include_router(products_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
