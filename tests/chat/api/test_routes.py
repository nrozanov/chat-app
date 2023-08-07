import json
import datetime
import pytest

from fastapi import WebSocketDisconnect
from starlette.testclient import TestClient
from sqlmodel import Session, select
from unittest.mock import MagicMock

from models import User, Customer, ChatMessage, Chat
from tests import factories, asserts


class TestChatWS():
    url = "/chat/"

    @pytest.fixture
    def setup(self, customer: Customer, other_customer: Customer):
        chat = factories.ChatFactory(from_customer_id=customer.id, to_customer_id=other_customer.id)
        messages = factories.ChatMessageFactory.create_batch(3, chat=chat)

        return (messages, chat)

    @pytest.mark.anyio
    async def test_ok_have_chat(
        self,
        session: Session,
        as_user: TestClient,
        other_customer: Customer,
        as_other_customer: TestClient,
        customer: Customer,
        setup: tuple,
        assert_num_queries
    ):
        _, chat = setup
        with as_user.websocket_connect(self.url) as websocket:
            message = {"to_customer_id": other_customer.id, "message": "some message"}
            websocket.send_json(json.dumps(message))
            data = json.loads(websocket.receive_json())
            message["from_customer_id"] = customer.id
            for key in ('message', 'from_customer_id', 'to_customer_id'):
                assert message[key] == data[key]

            with as_other_customer.websocket_connect(self.url) as other_websocket:
                other_message = {"to_customer_id": customer.id, "message": "other message"}
                other_websocket.send_json(json.dumps(other_message))
                data = other_websocket.receive_json()

                db_message = session.exec(select(ChatMessage).where(ChatMessage.message == "other message")).one_or_none()
                other_message["created_at"] = db_message.created_at.isoformat()
                other_message["from_customer_id"] = other_customer.id
                other_message["id"] = db_message.id
                assert json.loads(data) == other_message
                assert db_message.is_from_from_customer == False
                assert db_message.chat_id == chat.id

                data_for_from_customer = websocket.receive_json()
                data_for_from_customer = json.loads(data_for_from_customer)
                assert data_for_from_customer == other_message


    @pytest.mark.anyio
    async def test_invalid_cases(
        self,
        session: Session,
        as_user: TestClient,
        customer: Customer,
        other_customer: Customer,
        setup: tuple,
        assert_num_queries
    ):
        messages, chat = setup
        with as_user.websocket_connect(self.url) as websocket:
            message = "not a json"
            websocket.send_json(message)
            data = websocket.receive_text()
            assert data == "Not a JSON"

            message = {"message": "no to_customer_id"}
            websocket.send_json(json.dumps(message))
            data = websocket.receive_text()
            assert data == "No to_customer_id in data"

            message = {"to_customer_id": other_customer.id}
            websocket.send_json(json.dumps(message))
            data = websocket.receive_text()
            assert data == "No message in data"

            message = {"to_customer_id": 999, "message": "some"}
            websocket.send_json(json.dumps(message))
            data = websocket.receive_text()
            assert data == "No chat found"


class TestGetChat():
    url = "/chat/{}/"

    @pytest.fixture
    def setup(self, customer: Customer):
        other_customer = factories.CustomerFactory()
        chat = factories.ChatFactory(from_customer_id=customer.id, to_customer_id=other_customer.id)
        messages = factories.ChatMessageFactory.create_batch(3, chat=chat)

        return (other_customer, messages)

    @pytest.fixture
    def expect_response(self, customer: Customer, setup: tuple):
        other_customer, messages = setup
        messages.reverse()
        return [{
            "id": message.id,
            "message": message.message,
            "from_customer_id": customer.id,
            "to_customer_id": other_customer.id,
            "created_at": message.created_at.isoformat(),
            "is_viewed": False,
        } for message in messages]

    @pytest.mark.anyio
    async def test_ok(
        self,
        session: Session,
        as_user: TestClient,
        customer: Customer,
        setup: tuple,
        assert_num_queries,
        expect_response
    ):
        other_customer, messages = setup
        with assert_num_queries(2):
            response = as_user.get(self.url.format(other_customer.id))

        assert response.status_code == 200
        assert response.json()["items"] == expect_response


class TestViewChatMessages():
    url = "/chat/{}/view/"

    @pytest.fixture
    def setup(self, customer: Customer):
        other_customer = factories.CustomerFactory()
        chat = factories.ChatFactory(from_customer_id=customer.id, to_customer_id=other_customer.id)
        
        messages_data = [
            {"is_from_from_customer": True, "created_at": datetime.datetime(2018, 5, 3)},
            {"is_from_from_customer": False, "created_at": datetime.datetime(2018, 5, 3)},
            {"is_from_from_customer": False, "created_at": datetime.datetime(2018, 5, 3)},
            {"is_from_from_customer": False, "created_at": datetime.datetime(2028, 5, 3)},
        ]
        messages = [factories.ChatMessageFactory(chat=chat, **data) for data in messages_data]

        return (other_customer, messages)

    @pytest.mark.anyio
    async def test_ok(
        self,
        session: Session,
        as_user: TestClient,
        customer: Customer,
        setup: tuple,
        assert_num_queries,
    ):
        other_customer, messages = setup
        with assert_num_queries(3):
            response = as_user.put(self.url.format(other_customer.id))

        assert response.status_code == 200
        
        viewed_messages = session.exec(select(ChatMessage).where(ChatMessage.is_viewed)).all()
        assert len(viewed_messages) == 2
        for message in viewed_messages:
            assert message.is_from_from_customer == False
            assert message.created_at == datetime.datetime(2018, 5, 3)


class TestGetChats():
    url = "/chat/"

    @staticmethod
    def _setup(
        customer: Customer, is_viewed: bool = True, have_to_messages: bool = True, have_messages: bool = True
    ):
        other_customer = factories.CustomerFactory()
        chat = factories.ChatFactory(from_customer_id=customer.id, to_customer_id=other_customer.id)
        if not have_messages:
            return (other_customer, [], chat)

        messages_data = [
            {"is_from_from_customer": True, "created_at": datetime.datetime(2018, 5, 3)},
        ]
        if have_to_messages:
            messages_data.extend([
                {"is_from_from_customer": False, "created_at": datetime.datetime(2018, 5, 3)},
                {"is_from_from_customer": False, "created_at": datetime.datetime(2019, 5, 3), "is_viewed": is_viewed},
            ])
        messages = [factories.ChatMessageFactory(chat=chat, **data) for data in messages_data]

        return (other_customer, messages, chat)

    @staticmethod
    def expect_response(
        customer: Customer, other_customer: Customer, chat: Chat, messages: list,
        is_viewed: bool = True, have_to_messages: bool = True
    ):
        if not messages:
            return [{
                "id": chat.id,
                "name": other_customer.name,
                "with_customer_id": other_customer.id,
                "last_message": None,
                "last_message_sender_id": None,
                "viewed_all_messages": None,
                "last_message_created_at": None,
            }]

        last_message = messages[-1]
        last_message_sender_id = other_customer.id
        if not have_to_messages:
            is_viewed = None
            last_message_sender_id = customer.id
        return [{
            "id": chat.id,
            "name": other_customer.name,
            "with_customer_id": other_customer.id,
            "last_message": last_message.message,
            "last_message_sender_id": last_message_sender_id,
            "viewed_all_messages": is_viewed,
            "last_message_created_at": last_message.created_at.isoformat(),
        }]
        
    @pytest.mark.anyio
    async def test_ok_viewed(
        self,
        session: Session,
        as_user: TestClient,
        customer: Customer,
        assert_num_queries,
    ):
        setup = self._setup(customer)
        other_customer, messages, chat = setup
        with assert_num_queries(2):
            response = as_user.get(self.url)

        assert response.status_code == 200
        assert response.json()["items"] == self.expect_response(customer, other_customer, chat, messages)

    @pytest.mark.anyio
    async def test_ok_not_viewed(
        self,
        session: Session,
        as_user: TestClient,
        customer: Customer,
        assert_num_queries,
    ):
        setup = self._setup(customer, is_viewed=False)
        other_customer, messages, chat = setup
        with assert_num_queries(2):
            response = as_user.get(self.url)

        assert response.status_code == 200
        assert response.json()["items"] == self.expect_response(
            customer, other_customer, chat, messages, is_viewed=False
        )

    @pytest.mark.anyio
    async def test_no_to_message(
        self,
        session: Session,
        as_user: TestClient,
        customer: Customer,
        assert_num_queries,
    ):
        setup = self._setup(customer, have_to_messages=False)
        other_customer, messages, chat = setup
        with assert_num_queries(2):
            response = as_user.get(self.url)

        assert response.status_code == 200
        assert response.json()["items"] == self.expect_response(
            customer, other_customer, chat, messages, have_to_messages=False
        )

    @pytest.mark.anyio
    async def test_no_messages(
        self,
        session: Session,
        as_user: TestClient,
        customer: Customer,
        assert_num_queries,
    ):
        setup = self._setup(customer, have_messages=False)
        other_customer, messages, chat = setup
        with assert_num_queries(2):
            response = as_user.get(self.url)

        assert response.status_code == 200
        assert response.json()["items"] == self.expect_response(
            customer, other_customer, chat, messages, have_to_messages=False
        )
        