from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import database
from routers.auth import verify_token

router = APIRouter()

class OrderUpdate(BaseModel):
    status: Optional[str] = None



@router.get("/")
async def get_orders(status_filter: Optional[str] = None, payload: dict = Depends(verify_token)):
    try:
        return database.list_orders({"status": status_filter} if status_filter else {})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка получения заявок: {exc}")

@router.get("/stats")
async def get_stats(payload: dict = Depends(verify_token)):
    return database.get_order_statistics()

@router.get("/{order_id}")
async def get_order(order_id: int, payload: dict = Depends(verify_token)):
    order = database.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return order

@router.put("/{order_id}")
async def update_order(order_id: int, order_update: OrderUpdate, payload: dict = Depends(verify_token)):
    if order_update.status:
        database.update_order_status(order_id, order_update.status)
    return {"ok": True}
