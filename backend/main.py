import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, bot_config, orders

app = FastAPI(title="Chel3D API", description="API админки и сайта Chel3D")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(bot_config.router, prefix="/api/bot-config", tags=["bot-config"])

@app.get("/")
async def root():
    return {"message": "CRM API для токарных работ"}
	return {"message": "Chel3D API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("API_PORT", "45556")), reload=True)
