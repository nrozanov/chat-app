from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Session, select

from auth.api.services import get_code, send_code
from config.db import get_session
from core.api import responses

router = APIRouter()

@router.head(
    "/signup/{email}/",
    responses=responses.CONFLICT,
    status_code=200,
)
async def check_no_user_with_email(
    email: str,
    session: Session = Depends(get_session),
):
    """
    Check if user with this email already exists
    """
    email_exists = bool(session.exec(select(User).filter(User.email == email)).one_or_none())

    if email_exists:
        return JSONResponse(status_code=409, content=None)


@router.get(
    "/signup/{phone_number}/",
    responses=responses.CONFLICT, 
    status_code=200,
)
async def get_signup_code(
    phone_number: str,
    session: Session = Depends(get_session),
):
    """
    Check if user with this phone already exists and if not, send verification code
    """
    phone_exists = bool(
        session.exec(select(User).filter(User.phone_number == phone_number)).one_or_none()
    )

    if phone_exists:
        return JSONResponse(status_code=409, content=None)

    await send_code(phone_number)


@router.post(
    "/signup/{phone_number}/",
    responses=responses.INVALID_CODE,
    response_model=schema.TokenPairSchema,
    status_code=201,
)
async def check_signup_code(
    phone_number: str,
    data: schema.GetSignupCodeSchema,
    session: Session = Depends(get_session),
):
    """
    Check if code is valid and if it is, create user and reply with his token
    """
    sent_code = await get_code(phone_number)
    if sent_code is None or sent_code != data.code:
        return JSONResponse(status_code=400, content={"detail": "Code is invalid or expired"})

    user = User(phone_number=phone_number, **data.dict())
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return JSONResponse(
            status_code=409,
            content={"detail": "User with this email or phone number already exists"}
        )

    access, refresh = get_token_pair_for_user(
        session,
        user,
        access_token_class=UserAccessToken,
        refresh_token_class=UserRefreshToken
    )

    return {
        "access_token": str(access),
        "refresh_token": str(refresh),
    }


@router.get(
    "/signin/{phone_number}/",
    status_code=200,
)
async def get_signin_code(
    phone_number: str,
    session: Session = Depends(get_session),
):
    """
    Find user in db and send verification code
    """
    user = session.exec(select(User).filter(User.phone_number == phone_number)).one_or_none()
    if not user:
        raise NotFoundError

    await send_code(phone_number)


@router.post(
    "/signin/{phone_number}/",
    responses=responses.INVALID_CODE | responses.NOT_FOUND,
    response_model=schema.TokenPairSchema,
    status_code=200,
)
async def check_signin_code(
    phone_number: str,
    data: schema.GetSigninCodeSchema,
    session: Session = Depends(get_session),
):
    """
    Check if code is valid and if it is, get user from db and reply with his token
    """
    sent_code = await get_code(phone_number)
    if sent_code is None or sent_code != data.code:
        return JSONResponse(status_code=400, content={"detail": "Code is invalid or expired"})

    user = session.exec(select(User).filter(User.phone_number == phone_number)).one_or_none()
    if not user:
        raise NotFoundError

    access, refresh = get_token_pair_for_user(
        session,
        user,
        access_token_class=UserAccessToken,
        refresh_token_class=UserRefreshToken
    )

    return {
        "access_token": str(access),
        "refresh_token": str(refresh),
    }


@router.post(
    "/refresh_token/",
    responses=responses.INVALID_TOKEN,
    response_model=schema.TokenPairSchema,
    status_code=200,
)
async def refresh_token(
    data: schema.k,
    session: Session = Depends(get_session),
):
    """
    Get new token pair using refresh token
    """
    try:
        access, refresh = refresh_token_pair(
            session,
            token=data.token,
            access_token_class=UserAccessToken,
            refresh_token_class=UserRefreshToken,
        )
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Token is invalid or expired"})

    return {
        "access_token": str(access),
        "refresh_token": str(refresh),
    }
