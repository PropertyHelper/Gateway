import json

from fastapi import APIRouter, HTTPException, Depends
import requests

from src.models import UserLogInRequest, User, LogInSuccessful, UserCreate, TransactionResponse, FrontendUserBalances, \
    UserBalances, FrontendTransactionResponse, FrontendTransaction, ShopNames
from src.settings import settings
from src.security import issue_token, AccessLevel, ValidateHeader

router = APIRouter(prefix="/user")
user_access_level = AccessLevel("User_Level")  # access level for users

@router.post("/login")
def login_user(login_request: UserLogInRequest) -> LogInSuccessful:
    """
    Authorise the user and issue JWT.

    Flow:
        1. Check whether login is allowed on the user data service side
        2. Issue JWT or throw 403 exception
    :param login_request: credentials
    :return: LogInSuccessful object

    :raise HTTPException with 550 code if user service times out
    :raise HTTPException with 403 code if the credentials are wrong
    """
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
    """
    Get user details by a token.

    :param token: dict, received from DI system with data from jwt token.
    :return: user domain model
    :raise HTTPException with 550 code if user server times out
    """
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
                          token: dict = Depends(ValidateHeader(user_access_level, settings.secret))) -> FrontendTransactionResponse:
    """
    Get user most recent transactions.

    :param offset: skip int transactions
    :param limit: show up to this number of transactions
    :param token: dict, received from DI system with data from jwt token.
    :return: FrontendTransactionResponse object
    :raise HTTPException with code 550 if services time out

    Flow:
        1. Get recent transactions
        2. Saturate the response by adding shop names from the shop data service
    """
    uid = token["entity_id"]
    try:
        response = requests.get(settings.transaction_endpoint.unicode_string() + f"/userdata/transactions/{uid}",
                                params={"offset": offset, "limit": limit},
                                timeout=10)
    except (TimeoutError, ConnectionError) as e:
        print("get user transaction timeout", e)
        raise HTTPException(status_code=550, detail="Transaction service unavailable")
    transactions = TransactionResponse.model_validate(response.json())
    try:
        shop_names_response = requests.post(settings.shop_endpoint.unicode_string() + f"/shop/names",
                                json=[str(transaction.shop_id) for transaction in transactions.transactions],
                                timeout=10)
    except (TimeoutError, ConnectionError) as e:
        print("get shop transaction timeout", e)
        raise HTTPException(status_code=550, detail="Shop service unavailable")
    shop_names = ShopNames.model_validate(shop_names_response.json())
    return FrontendTransactionResponse(transactions=[FrontendTransaction(**transaction.model_dump(),
                                                                         shop_name=shop_name) for transaction, shop_name in
                                                     zip(transactions.transactions, shop_names.names)])

@router.get("/balance")
def get_user_balance(token: dict = Depends(ValidateHeader(user_access_level, settings.secret))) -> FrontendUserBalances:
    """
    Get user balances for shop
    :param token: dict, received from DI system with data from jwt token.
    :return: FrontendUserBalances object
    :raise HTTPException if any service times out

    Flow:
        1. Get user balances
        2. Saturate the response by adding shop names from the shop data service
    """
    uid = token["entity_id"]
    try:
        response = requests.get(settings.transaction_endpoint.unicode_string() + f"/userdata/{uid}",
                                timeout=10)
    except (TimeoutError, ConnectionError) as e:
        print("get user transaction timeout", e)
        raise HTTPException(status_code=550, detail="Transaction service unavailable")
    user_balances = UserBalances.model_validate(response.json())
    sids = [str(record[0]) for record in user_balances.shops]
    balances = [record[1] for record in user_balances.shops]
    try:
        shop_names_response = requests.post(settings.shop_endpoint.unicode_string() + f"/shop/names",
                                json=sids,
                                timeout=10)
    except (TimeoutError, ConnectionError) as e:
        print("get shop transaction timeout", e)
        raise HTTPException(status_code=550, detail="Shop service unavailable")
    shop_names = ShopNames.model_validate(shop_names_response.json())
    front_user_balance = FrontendUserBalances(user_id=uid, shops=list(zip(shop_names.names, balances)))
    return front_user_balance

@router.post("/")
def create_user(user_create: UserCreate) -> LogInSuccessful:
    """
    Create a new user.

    :param user_create: user creation model
    :return: LogInSuccessful object
    :raise HTTPException with code 550 if the service is unavailable
    :raise HTTPException with code 400 if parameters for user creation were invalid
    """
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
