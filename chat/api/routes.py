import crud
import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnect as s_WebSocketDisconnect
from fastapi_pagination import Page, paginate
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select, col

from config.db import get_session, engine
from core.api.exceptions import NotFoundError
from core.api.deps import get_user, get_customer, get_customer_photo, get_chat
from core.api import responses
from chat.api.services import WSManager, ChatWorker, ws_error
from chat.schema import ChatMessageSchema, SendMessageSchema, ChatSchema
from models import CustomerRelation, Chat, Customer, ChatMessage


router = APIRouter()


@router.websocket("/")
async def chat(
    websocket: WebSocket,
    session: Session = Depends(get_session),
    customer: Customer = Depends(get_customer_ws),
):
    """
    Connect client to chat websocket
    """

    if not customer:
        await websocket.accept()
        return await ws_error(websocket, "Invalid credentials")

    await WSManager.run(ChatWorker, session, websocket, customer)


@router.get(
    "/{with_customer_id}/",
    responses=responses.CRUD_RESPONSES,
    response_model=Page[ChatMessageSchema],
    status_code=200,
)
async def get_chat(
    with_customer_id: int,
    session: Session = Depends(get_session),
    customer: Customer = Depends(get_customer),
    chat: Chat = Depends(get_chat),
):
    """
    Check if chat exists and if it does - return all its messages
    """

    customer_ids = (customer.id, with_customer_id)

    messages = list()
    for message in chat.messages:
        from_customer_id, to_customer_id = customer_ids
        if (
            (message.is_from_from_customer and chat.from_customer_id != from_customer_id) or
            (not message.is_from_from_customer and chat.to_customer_id != from_customer_id)
        ):
            from_customer_id, to_customer_id = to_customer_id, from_customer_id
        
        messages.append({
            "id": message.id,
            "message": message.message,
            "created_at": message.created_at,
            "from_customer_id": from_customer_id,
            "to_customer_id": to_customer_id,
            "is_viewed": message.is_viewed,
        })

    return paginate(sorted(messages, key = lambda item: item["created_at"], reverse=True))


@router.put(
    "/{with_customer_id}/view/",
    responses=responses.CRUD_RESPONSES,
    status_code=200,
)
async def view_chat_messages(
    with_customer_id: int,
    session: Session = Depends(get_session),
    customer: Customer = Depends(get_customer),
    chat: Chat = Depends(get_chat),
):
    """
    Mark all messages in a chat created after now as viewed
    """

    now = datetime.datetime.now()
    for message in chat.messages:
        to_customer = (
            (message.is_from_from_customer and chat.from_customer_id != customer.id) or
            (not message.is_from_from_customer and chat.from_customer_id == customer.id)
        )
        if to_customer and not message.is_viewed and message.created_at < now:
            crud.chat_message.update(session, message, data={"is_viewed": True}, commit=False)

    session.commit()


@router.get(
    "/",
    responses=responses.CRUD_RESPONSES,
    response_model=Page[ChatSchema],
    status_code=200,
)
async def get_chats(
    session: Session = Depends(get_session),
    customer: Customer = Depends(get_customer),
):
    """
    Get all customer's chats
    """

    chats = session.exec(
        select(Chat)
        .filter(
            or_(
                Chat.from_customer_id == customer.id,
                Chat.to_customer_id == customer.id
            ),
        )
    ).unique().all()

    res_chats = list()
    for chat in chats:
        with_customer, is_from_customer = chat.from_customer, True
        if chat.from_customer_id == customer.id:
            with_customer, is_from_customer = chat.to_customer, False

        messages_sorted = sorted(chat.messages, key = lambda item: item.created_at, reverse=True)
        last_message_text, last_message_sender_id, viewed_all_messages, last_message_created_at = None, None, None, None
        last_message_data = dict()
        if messages_sorted:
            last_message = messages_sorted[0]
            last_message_text = last_message.message
            last_message_sender_id = last_message.is_from_from_customer and chat.from_customer_id or chat.to_customer_id
            last_message_created_at = last_message.created_at
            last_message_data = {
                "last_message": last_message_text,
                "last_message_sender_id": last_message_sender_id,
                "last_message_created_at": last_message_created_at,
            }

            customer_messages = list(
                filter(
                    lambda x: (is_from_customer and x.is_from_from_customer) or
                    (not is_from_customer and not x.is_from_from_customer),
                    messages_sorted
                )
            )
            if customer_messages:
                viewed_all_messages = customer_messages[0].is_viewed

        res_chats.append({
            "id": chat.id,
            "name": with_customer.name,
            "with_customer_id": with_customer.id,
            "viewed_all_messages": viewed_all_messages,
            **last_message_data,
        })

    list_to_sort = [chat for chat in res_chats if chat.get("last_message_created_at")]
    list_not_to_sort = [chat for chat in res_chats if not chat.get("last_message_created_at")]
    sorted_list = sorted(list_to_sort, key = lambda item: item.get("last_message_created_at"), reverse=True)
    return paginate(sorted_list + list_not_to_sort)

    return paginate(sorted(res_chats, key = lambda item: item.get("last_message_created_at"), reverse=True))
