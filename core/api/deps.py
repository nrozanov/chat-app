from fastapi import Depends

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.operators import is_
from sqlalchemy.sql import column
from sqlmodel import Session, select, col

from config.db import get_session
from core.api.exceptions import PermissionDeniedError, UnauthorizedError, NotFoundError
from core.api.security import JWTBearer, JWTBearerWS
from core.token import Token, TokenError
from user.tokens import UserAccessToken
from models.user import User
from models.customer import Customer, CustomerPhoto
from models.chat import Chat


class _UserDependency:
    def __init__(self, *, token_class: type[Token]):
        self.token_class = token_class

    async def __call__(
        self,
        session: Session = Depends(get_session),
        token: str = Depends(JWTBearer(scheme_name="Bearer")),
    ) -> User:
        try:
            user = self.token_class.from_string(token, session).user
        except TokenError:
            raise UnauthorizedError
        return user


class _UserDependencyWS:
    def __init__(self, *, token_class: type[Token]):
        self.token_class = token_class

    async def __call__(
        self,
        session: Session = Depends(get_session),
        token: str = Depends(JWTBearerWS(scheme_name="Bearer")),
    ) -> User:
        if not token:
            return None
        
        try:
            user = self.token_class.from_string(token, session).user
        except TokenError:
            return None
        return user


async def get_user(
    user: User = Depends(_UserDependency(token_class=UserAccessToken)),
) -> User:
    return user


async def get_customer(
    user: User = Depends(_UserDependency(token_class=UserAccessToken)),
) -> Customer:
    return user.customer


async def get_customer_ws(
    user: User = Depends(_UserDependencyWS(token_class=UserAccessToken)),
) -> Customer:
    if not user:
        return None
    return user.customer


async def get_customer_photo(
    photo_id: int,
    session: Session = Depends(get_session),
) -> CustomerPhoto:
    customer_photo = session.exec(select(CustomerPhoto).where(CustomerPhoto.id == photo_id)).one_or_none()
    if not customer_photo:
        raise NotFoundError
    return customer_photo


async def _get_relation_w_chat(with_customer_id: int, session: Session, customer: Customer) -> CustomerRelation:
    customer_ids = [customer.id, with_customer_id]
    relation_w_chat = session.exec(
        select(CustomerRelation)
        .options(joinedload(CustomerRelation.chat).joinedload(Chat.messages))
        .where(
            col(CustomerRelation.from_customer_id).in_(customer_ids),
            col(CustomerRelation.to_customer_id).in_(customer_ids),
            CustomerRelation.chat,
            CustomerRelation.relation != 'block'
        )
    ).unique().one_or_none()
    if not relation_w_chat:
        raise NotFoundError
    return relation_w_chat


async def get_relation_w_chat(
    with_customer_id: int,
    session: Session = Depends(get_session),
    customer: Customer = Depends(get_customer),
) -> CustomerRelation:
    return await _get_relation_w_chat(with_customer_id, session, customer)


async def get_relation_w_chat_ws(
    with_customer_id: int,
    session: Session = Depends(get_session),
    customer: Customer = Depends(get_customer_ws),
) -> CustomerRelation | None:
    try :
        res = await _get_relation_w_chat(with_customer_id, session, customer)
    except Exception:
        return None
    return res


async def get_chat(
    with_customer_id: int,
    session: Session = Depends(get_session),
    customer: Customer = Depends(get_customer_ws),
) -> Chat | None:
    return session.exec(
        select(Chat)
        .filter(
            or_(
                and_(
                    Chat.from_customer_id == customer.id,
                    Chat.to_customer_id == with_customer_id
                ),
                and_(
                    Chat.from_customer_id == with_customer_id,
                    Chat.to_customer_id == customer.id
                )
            ),
        )
    ).one_or_none()

