import datetime
from datetime import date
from faker.proxy import Faker
import json
import pytest
from typing import Any
from unittest.mock import MagicMock, ANY
from starlette.testclient import TestClient
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import InvalidRequestError

from auth.tokens import JWTToken
from config.settings import settings
from models import User
from models.customer import Customer
from models.chat import Chat
from routes import router
from tests import factories, asserts
from user.tokens import UserAccessToken, UserRefreshToken


class AccessDummyToken(JWTToken):
    token_type = "access_dummy"
    lifetime = datetime.timedelta(days=1)


class RefreshDummyToken(JWTToken):
    token_type = "refresh_dummy"
    lifetime = datetime.timedelta(days=11)


class TestCheckNoUserWithEmail():
    url = "/auth/signup/{}/"

    def test_user_does_not_exist(
        self,
        session: Session,
        client: TestClient,
        user: User,
        assert_num_queries
    ):
        with assert_num_queries(1):
            response = client.head(self.url.format('some-email'))

        assert response.status_code == 200

    def test_user_exists(
        self,
        session: Session,
        client: TestClient,
        user: User,
        assert_num_queries
    ):
        with assert_num_queries(1):
            response = client.head(self.url.format(user.email))

        assert response.status_code == 409


class TestGetSignupCode():
    url = "/auth/signup/{}/"

    def test_user_does_not_exist(
        self,
        session: Session,
        client: TestClient,
        user: User,
        mock_send_code: MagicMock,
        assert_num_queries
    ):
        mock_send_code.side_effect = (1,)

        with assert_num_queries(1):
            response = client.get(self.url.format('phone_num'))

        assert response.status_code == 200

        mock_send_code.assert_called_once_with('phone_num')

    def test_user_exists(
        self,
        session: Session,
        client: TestClient,
        user: User,
        assert_num_queries
    ):
        with assert_num_queries(1):
            response = client.get(self.url.format(user.phone_number))

        assert response.status_code == 409


class TestCheckSignupCode():
    url = "/auth/signup/{}/"

    @pytest.fixture
    def post_data(self, user: User):
        return {
            "code": "some-code",
            "email": str(user.email)
        }

    def test_ok(
        self,
        session: Session,
        client: TestClient,
        mock_get_code: MagicMock,
        assert_num_queries
    ):
        mock_get_code.side_effect = ("some-code",)
        user_data = {"email": "some-email", "phone_number": "some-phone-number"}
        post_data = {"code": "some-code", "email": user_data["email"]}
        with assert_num_queries(4):
            response = client.post(
                self.url.format(user_data["phone_number"]), json=post_data
            )

        user = session.exec(select(User)).one_or_none()
        assert user.email == user_data["email"]
        assert user.phone_number == user_data["phone_number"]
        
        assert response.status_code == 201

        result = response.json()

        assert UserAccessToken.from_string(result["access_token"], session).user == user
        assert (
            UserRefreshToken.from_string(result["refresh_token"], session).user == user
        )

    def test_invalid_code(
        self,
        post_data,
        session: Session,
        client: TestClient,
        user: User,
        mock_get_code: MagicMock,
        assert_num_queries
    ):
        mock_get_code.side_effect =  None
        with assert_num_queries(0):
            response = client.post(
                self.url.format(user.phone_number), json=post_data
            )

        assert response.status_code == 400

    def test_user_exists(
        self,
        post_data,
        session: Session,
        client: TestClient,
        user: User,
        mock_get_code: MagicMock,
        assert_num_queries
    ):
        mock_get_code.side_effect = ("some-code",)
        with assert_num_queries(1):
            response = client.post(
                self.url.format(user.phone_number), json=post_data
            )

        assert response.status_code == 409


class TestGetSigninCode():
    url = "/auth/signin/{}/"

    def test_ok(
        self,
        session: Session,
        client: TestClient,
        user: User,
        mock_send_code: MagicMock,
        assert_num_queries
    ):
        mock_send_code.side_effect = (1,)

        with assert_num_queries(1):
            response = client.get(self.url.format(user.phone_number))

        assert response.status_code == 200

        mock_send_code.assert_called_once_with(user.phone_number)

    def test_user_does_not_exist(
        self,
        session: Session,
        client: TestClient,
        assert_num_queries
    ):
        with assert_num_queries(1):
            response = client.get(self.url.format('some'))

        assert response.status_code == 404


class TestCheckSigninCode():
    url = "/auth/signin/{}/"

    @pytest.fixture
    def post_data(self):
        return {
            "code": "some-code",
        }

    def test_ok(
        self,
        session: Session,
        client: TestClient,
        user: User,
        post_data: dict,
        mock_get_code,
        assert_num_queries
    ):
        mock_get_code.return_value = 'some-code'
        with assert_num_queries(2):
            response = client.post(
                self.url.format(user.phone_number), json=post_data
            )

        assert response.status_code == 200

        result = response.json()

        assert UserAccessToken.from_string(result["access_token"], session).user == user
        assert (
            UserRefreshToken.from_string(result["refresh_token"], session).user == user
        )

    def test_invalid_code(
        self,
        post_data,
        session: Session,
        client: TestClient,
        user: User,
        mock_get_code: MagicMock,
        assert_num_queries
    ):
        mock_get_code.side_effect =  None
        with assert_num_queries(0):
            response = client.post(
                self.url.format(user.phone_number), json=post_data
            )

        assert response.status_code == 400

    def test_user_does_not_exist(
        self,
        post_data,
        session: Session,
        client: TestClient,
        mock_get_code: MagicMock,
        assert_num_queries
    ):
        mock_get_code.side_effect = ("some-code",)
        with assert_num_queries(1):
            response = client.post(
                self.url.format("123456"), json=post_data
            )

        assert response.status_code == 404


class TestRefreshToken:
    url = "/refresh_token/"

    @pytest.fixture
    def refresh_token(self, user: User):
        return UserRefreshToken.for_user(user)

    def test_ok(
        self,
        session: Session,
        client: TestClient,
        refresh_token: UserRefreshToken,
        user: User,
        assert_num_queries,
    ):
        with assert_num_queries(2):
            response = client.post(self.url, json={"token": str(refresh_token)})

        result = response.json()

        assert response.status_code == 200
        assert result["refresh_token"] != str(refresh_token)
        assert UserAccessToken.from_string(result["access_token"], session).user == user
        assert (
            UserRefreshToken.from_string(result["refresh_token"], session).user == user
        )

    def test_invalid_token(
        self,
        client: TestClient,
        assert_num_queries,
    ):
        with assert_num_queries(0):
            response = client.post(self.url, json={"token": "qqq"})

        assert response.status_code == 400
        assert response.json() == {"detail": "Token is invalid or expired"}
