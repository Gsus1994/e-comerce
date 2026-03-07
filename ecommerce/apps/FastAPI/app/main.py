from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.FastAPI.app.routers.auth import router as auth_router
from apps.FastAPI.app.routers.cart import router as cart_router
from apps.FastAPI.app.routers.orders import router as orders_router
from apps.FastAPI.app.routers.products import router as products_router
from apps.FastAPI.app.settings import get_settings

app = FastAPI(title="Ecommerce API", version="0.1.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(products_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
