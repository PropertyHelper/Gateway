import json

from fastapi import APIRouter, HTTPException, Depends
import requests

from src.models import UserLogInRequest, User, LogInSuccessful, UserCreate, TransactionResponse
from src.settings import settings
from src.security import issue_token, AccessLevel, ValidateHeader

router = APIRouter(prefix="/user")
user_access_level = AccessLevel("User_Level")

@router.post("/login")
def login_user(login_request: UserLogInRequest) -> LogInSuccessful:
    try:
        response = requests.post(settings.user_endpoint.unicode_string() + "/user/login",
                                 json=login_request.model_dump(),
                                 timeout=10)
    except TimeoutError as e:
        print("login timeout", e)
        raise HTTPException(status_code=550, detail="User service unavailable")
    if response.status_code == 403:
        raise HTTPException(status_code=403, detail="Invalid credentials or user does not exist")
    user = User.model_validate(response.json())
    return LogInSuccessful(msg="success", token=issue_token(entity_id=str(user.uid),
                                                            access_level=AccessLevel.USER_LEVEL,
                                                            secret=settings.secret))

@router.get("/")
def get_user(token: dict = Depends(ValidateHeader(user_access_level, settings.secret))) -> User:
    uid = token["entity_id"]
    try:
        response = requests.get(settings.user_endpoint.unicode_string() + f"/user/{uid}", timeout=10)
    except (TimeoutError, ConnectionError) as e:
        print("get user timeout", e)
        raise HTTPException(status_code=550, detail="User service unavailable")
    return response.json()

@router.get("/transactions")
def get_user_transactions(offset: int = 0,
                           limit: int = 100,
                          token: dict = Depends(ValidateHeader(user_access_level, settings.secret))) -> TransactionResponse:
    uid = token["entity_id"]
    try:
        response = requests.get(settings.transaction_endpoint.unicode_string() + f"/userdata/transactions/{uid}",
                                params={"offset": offset, "limit": limit},
                                timeout=10)
    except (TimeoutError, ConnectionError) as e:
        print("get user transaction timeout", e)
        raise HTTPException(status_code=550, detail="Transaction service unavailable")
    return response.json()

@router.post("/")
def create_user(user_create: UserCreate):
    try:
        response = requests.post(settings.user_endpoint.unicode_string() + "/user",
                                 json=json.loads(user_create.model_dump_json()),
                                 timeout=10)
    except (TimeoutError, ConnectionError) as e:
        print("login timeout", e)
        raise HTTPException(status_code=550, detail="User service unavailable")
    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Either the user exists, or the temporal user does not")
    user = User.model_validate(response.json())
    return LogInSuccessful(msg="success", token=issue_token(entity_id=str(user.uid),
                                                            access_level=AccessLevel.USER_LEVEL,
                                                            secret=settings.secret))
