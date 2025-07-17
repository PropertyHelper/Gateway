import shutil
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
import pandas as pd

from src.handle_excel import transform_file_into_request_objects
from src.models import ShopLogInRequest, Shop, LogInSuccessful, AnalyticalView, ShopUsers, CashierCreate, Cashier, \
    ItemInventory
from src.security import issue_token, AccessLevel, ValidateHeader
from src.settings import settings

router = APIRouter(prefix="/shop")
shop_access_level = AccessLevel("Store_Management_Level")  # access level for shop management

# upload dirs for excel catalogues
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/login")
def login_shop(login_request: ShopLogInRequest) -> LogInSuccessful:
    """
    Authenticate a shop and generate a JWT for it.

    :param login_request: credentials
    :return: LogInSuccessful object

    :raise HTTPException with 550 code if shop service times out
    :raise HTTPException with 403 code if the credentials are wrong
    """
    try:
        response = requests.post(settings.shop_endpoint.unicode_string() + "/shop/login",
                                 json=login_request.model_dump(),
                                 timeout=10)
    except TimeoutError as e:
        print("login timeout", e)
        raise HTTPException(status_code=550, detail="Shop service unavailable")
    if response.status_code == 403:
        raise HTTPException(status_code=403, detail="Invalid credentials or shop does not exist")
    shop = Shop.model_validate(response.json())
    return LogInSuccessful(msg="success", token=issue_token(entity_id=str(shop.sid),
                                                            access_level=AccessLevel.STORE_MANAGEMENT_LEVEL,
                                                            secret=settings.secret))

@router.get("/stats")
def get_stats(token: dict = Depends(ValidateHeader(shop_access_level, settings.secret))) -> AnalyticalView:
    """
    Get the shop anonimised statistics of customers.

    :param token: dict from the DI system with data from jwt token.
    :return: AnalyticalView
    :raise HTTPException with code 550 if any service times out
    :raise HTTPException with code 400 if to few user visited the shop to preserve privacy

    Flow:
        1. Get customer ids from the transactional service
        2. Supply customer ids to the customer data service and get the AnalyticalView
    """
    shop_id = token["entity_id"]
    try:
        response = requests.get(settings.transaction_endpoint.unicode_string() + f"/shopdata/{shop_id}",
                                 timeout=10)
    except TimeoutError as e:
        print("get_stats shopdata timeout", e)
        raise HTTPException(status_code=550, detail="Transaction service unavailable")
    shop_users = ShopUsers.model_validate(response.json())
    try:
        response = requests.post(settings.user_endpoint.unicode_string() + f"/users/stats_report",
                                 json=[str(uid) for uid in shop_users.users],
                                 timeout=10)
    except TimeoutError as e:
        print("get_stats stats_report timeout", e)
        raise HTTPException(status_code=550, detail="Transaction service unavailable")
    try:
        view = AnalyticalView.model_validate(response.json())
    except ValueError:
        raise HTTPException(status_code=400)
    return view

@router.post("/cashier")
def create_cashier(potential_cashier: CashierCreate, token: dict = Depends(ValidateHeader(shop_access_level, settings.secret))) -> Cashier:
    """
    Create a new cashier account.

    :param potential_cashier: data for creating cashier account
    :param token: dict from the DI system with data from jwt token.
    :raise HTTPException with code 550 if any service times out
    :raise HTTPException with code 400 if cashier account already exists
    :return: cashier domain model
    """
    shop_id = token["entity_id"]
    try:
        response = requests.post(settings.shop_endpoint.unicode_string() + f"/cashier/",
                                json={"account_name": potential_cashier.account_name,
                                      "shop_id": str(shop_id),
                                      "password": potential_cashier.password},
                                timeout=10)
    except TimeoutError as e:
        print("create_cashier timeout", e)
        raise HTTPException(status_code=550, detail="Shop service unavailable")
    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Account Already Exists")
    return response.json()

@router.post("/add_inventory")
async def add_inventory(file: UploadFile = File(...),
                              token: dict = Depends(ValidateHeader(shop_access_level, settings.secret))) -> list[ItemInventory]:
    """
    Add inventory to the shop catalogue by the excel file.

    The gateway preprocesses the file and then uses shop service to upload catalogue.
    Expects the file to have following columns:
        - name,
        - description,
        - photo_url,
        - price,
        - percent_point_allocation
    :param file: excel file to get the data from
    :param token: dict from the DI system with data from jwt token.
    :return: list of shop service inventory domain model
    :raise HTTPException with code 550 if any service times out
    """
    if file.filename is None:
        raise HTTPException(400, "Invalid file")
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(400, "Invalid file")
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    shop_id = token["entity_id"]
    df = pd.read_excel(file_path)
    items = transform_file_into_request_objects(df, shop_id)  # transform excel file to domain objects
    items_dict = [item.model_dump() for item in items]
    for item in items_dict:
        item["shop_id"] = str(item["shop_id"])
    try:
        response = requests.post(settings.shop_endpoint.unicode_string() + f"/items/",
                                json=items_dict,
                                timeout=10)
    except TimeoutError as e:
        print("create_cashier timeout", e)
        raise HTTPException(status_code=550, detail="Shop service unavailable")
    return response.json()
