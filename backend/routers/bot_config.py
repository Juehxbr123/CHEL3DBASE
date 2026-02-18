from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import database
from routers.auth import verify_token

router = APIRouter()

class BotConfigUpdate(BaseModel):
    key: str
    value: str

@router.get("/")
async def get_config(payload: dict = Depends(verify_token)):
    return database.get_bot_config()

@router.put("/")
async def put_config(config_update: BotConfigUpdate, payload: dict = Depends(verify_token)):
    database.set_bot_config(config_update.key, config_update.value)
    return {"ok": True}
