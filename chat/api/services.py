import asyncio
import async_timeout
import crud
import json
import redis
import os

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnect as s_WebSocketDisconnect
from starlette.concurrency import run_until_first_complete
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, load_only, contains_eager
from sqlmodel import Session, select
from typing import List, TYPE_CHECKING

from config.db import redis_manager
from config.settings import settings
from core.api.deps import get_chat
from models import Customer, ChatMessage


class WSWorker():
    channel_type = None

    @staticmethod
    async def validate_message(session: Session, websocket: WebSocket, customer: Customer, message_str: str):
        raise NotImplementedError("Override process_data method")

    @staticmethod
    async def process_and_enhance_message(session: Session, websocket: WebSocket, customer: Customer, message_str: str):
        raise NotImplementedError("Override process_and_enhance_message method")


class ChatWorker(WSWorker):
    channel_type = 'chat'

    @staticmethod
    async def validate_message(session: Session, websocket: WebSocket, customer: Customer, message_str: str):
        try:
            data = json.loads(message_str)
        except Exception:
            return None, "Not a JSON"

        to_customer_id = data.get("to_customer_id")
        if not to_customer_id:
            return None, "No to_customer_id in data"
        
        message = data.get("message")
        if not message:
            return None, "No message in data"

        chat = await get_chat(to_customer_id, session, customer)
        if not chat:
            chat = crud.chat.create(
                session, {"from_customer_id": customer.id, "to_customer_id": to_customer_id}
            )

        return {
            "to_customer_id": int(to_customer_id),
            "message": message,
            "is_from_from_customer": chat.from_customer_id == customer.id,
            "chat_id": chat.id,

        }, None

    @staticmethod
    async def process_and_enhance_message(session: Session, customer: Customer, data: dict):
        chat_message = ChatMessage(**data)

        session.add(chat_message)
        session.commit()

        return {
            "message": data["message"],
            "to_customer_id": data["to_customer_id"],
            "created_at": chat_message.created_at.isoformat(),
            "from_customer_id": customer.id,
            "id": chat_message.id
        }


class WSManager():
    @staticmethod
    async def run(worker: WSWorker, session: Session, websocket: WebSocket, customer: Customer):
        await websocket.accept()

        async def callback(message_str):
            await websocket.send_json(message_str)

        channel = f"ws_{worker.channel_type}_{customer.id}"
        await redis_manager.subscribe(channel, callback)

        await WSManager.ws_receiver(worker, session, websocket, customer)
        
        await redis_manager.unsubscribe(channel)

    @staticmethod
    async def ws_receiver(worker: WSWorker, session: Session, websocket: WebSocket, customer: Customer):
        async for message_str in websocket.iter_json():
            data, err = await worker.validate_message(session, websocket, customer, message_str)
            if err:
                await ws_error(websocket, err, close_ws=False)
                continue               

            res_message = await worker.process_and_enhance_message(session, customer, data)

            await websocket.send_json(json.dumps(res_message))
            
            channel = f"ws_{worker.channel_type}_{data['to_customer_id']}"
            await redis_manager.publish(channel, json.dumps(res_message))

    @staticmethod
    async def ws_sender(worker: WSWorker, session: Session, websocket: WebSocket, customer: Customer):
        while True:
            try:
                async with async_timeout.timeout(1):
                    message = await redis_manager.get_message()
                    if message is not None:
                        message_str = message["data"].decode("utf-8")
                        if message_str == STOPWORD:
                            break
                        await websocket.send_json(message_str)
                    await asyncio.sleep(0.01)
            except asyncio.TimeoutError:
                pass


async def ws_error(websocket: WebSocket, err: str, close_ws: bool=True):
    await websocket.send_text(err)
    if close_ws:
        await websocket.close()
