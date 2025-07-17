import requests
from fastapi import APIRouter, HTTPException, Depends

from src.db_ops import record_recognition_event
from src.metrics import total_merged_recognitions, total_confused_recognitions
from src.security import issue_token, AccessLevel, ValidateHeader
from src.settings import settings
from src.models import CashierLoginRequest, Cashier, LogInSuccessful, ShopInventoryItems, UserPublicProfile, \
    RenameUIDRequest, RenameResult, ConfusionUIRequest, SelectedItems, TransactionCreateFromFrontend, Transaction

router = APIRouter(prefix="/cashier")
cashier_access_level = AccessLevel("Cashier_Level")  # cashier level access


@router.post("/login")
def login_cashier(login_request: CashierLoginRequest) -> LogInSuccessful:
    """
    Authenticate a cashier and issue a token.

    :param login_request: credentials
    :return: LogInSuccessful object

    :raise HTTPException with 550 code if cashier service times out
    :raise HTTPException with 403 code if the credentials are wrong
    """
    try:
        response = requests.post(settings.shop_endpoint.unicode_string() + "/cashier/login",
                                 json=login_request.model_dump(),
                                 timeout=10)
    except TimeoutError as e:
        print("login timeout", e)
        raise HTTPException(status_code=550, detail="Cashier service unavailable")
    if response.status_code == 403:
        raise HTTPException(status_code=403, detail="Invalid credentials or cashier/shop does not exist")
    cashier = Cashier.model_validate(response.json())
    return LogInSuccessful(msg="success", token=issue_token(entity_id=str(cashier.cid),
                                                            access_level=AccessLevel.CASHIER_LEVEL,
                                                            secret=settings.secret,
                                                            shop_id=str(cashier.shop_id)))


@router.get("/inventory")
def get_inventory(token: dict = Depends(ValidateHeader(cashier_access_level, settings.secret))) -> ShopInventoryItems:
    """
    Get inventory available in the shop to display in cashier system.

    :param token: dict from the DI system with data from jwt token.
    :return: ShopInventoryItems object
    :raise HTTPException with status code 401 if the shop id is not included in jwt (should not happen)
    :raise HTTPException with status code 500 if the external service timed out.
    """
    shop_id = token.get("shop_id")
    if not shop_id:
        raise HTTPException(status_code=401, detail="No shop_id included in token")
    try:
        response = requests.get(settings.shop_endpoint.unicode_string() + f"/shop/{shop_id}/items",
                                timeout=10)
    except TimeoutError as e:
        print("login timeout", e)
        raise HTTPException(status_code=550, detail="Shop service unavailable")
    return response.json()


@router.get("/get_user_by_user_name/{user_name}")
def get_user_by_user_name(user_name: str, token: dict = Depends(
    ValidateHeader(cashier_access_level, settings.secret))) -> UserPublicProfile:
    """
    Fetch a user by username.

    Endpoint logs this cashier's action to ensure cashier does not abuse the system.
    :param user_name: unique user name within the system
    :param token: dict from the DI system with data from jwt token.
    :return: UserPublicProfile object that does not contain sensitive data
    """
    print(f'Cashier {token["entity_id"]} requested data about {user_name}')
    try:
        user_details = requests.get(settings.user_endpoint.encoded_string() + f"/user/by_user_name/{user_name}",
                                    timeout=10)
    except (ConnectionError, TimeoutError) as e:
        print("handle_face_recognition 4", e)
        raise HTTPException(status_code=550, detail="User service not available")
    if user_details.status_code == 404:
        raise HTTPException(status_code=404)
    if user_details.status_code != 200:
        print("get_user_by_user_name unusual code", user_details.status_code, user_details.text)
        raise HTTPException(status_code=500, detail="something went wrong")
    jsonned_user_details = user_details.json()
    return UserPublicProfile.model_validate(jsonned_user_details)


@router.post("/merge_users")
def merge_users(rename_request: RenameUIDRequest,
                token: dict = Depends(ValidateHeader(cashier_access_level, settings.secret))) -> RenameResult:
    """
    Merge a new user with existing one.

    Use in case of confusion between new and existing user.
    Cashier action is logged
    :param rename_request: RenameUIDRequest object
    :param token: dict from the DI system with data from jwt token.
    :return: RenameResult
    :raise HTTPException with code 550 if the external service times out
    """
    print(f'Cashier {token["entity_id"]} requested data rename of {rename_request.old_uid} to {rename_request.new_uid}')
    try:
        result_id_update = requests.post(settings.face_recognition_endpoint.encoded_string() + "/frontend/merge",
                                         json={"new_uid": str(rename_request.new_uid),
                                               "old_uid": str(rename_request.old_uid)},
                                         timeout=10)
    except (ConnectionError, TimeoutError) as e:
        print("merge_users", e)
        raise HTTPException(status_code=550, detail="Face recognition service not available")
    total_merged_recognitions.inc()
    record_recognition_event("merge")
    return result_id_update.json()


@router.post("/confused_users")
def note_user_confusion(confusion_request: ConfusionUIRequest,
                        token: dict = Depends(ValidateHeader(cashier_access_level, settings.secret))) -> dict:
    """
    Log the system's confusion on 2 existing users. Record it to prometheus and the database.

    :param confusion_request: ConfusionUIRequest object
    :param token: dict from the DI system with data from jwt token.
    :return: empty dict - as the endpoint is for further analysis of ML engineers
    """
    print(f'Cashier {token["entity_id"]} reported confusion of recognised {confusion_request.recognised_uid} to '
          f'actual {confusion_request.found_uid}')
    total_confused_recognitions.inc()
    record_recognition_event("confusion")
    return {}


@router.post("/get_items_details")
def get_items_details(selected_items: SelectedItems,
                      token: dict = Depends(ValidateHeader(cashier_access_level, settings.secret))) -> ShopInventoryItems:
    """
    Get data on items based on their ids.

    :param selected_items: list of item ids
    :param token: dict from the DI system with data from jwt token.
    :return: list of item objects from the shop service
    """
    shop_id = token.get("shop_id")
    if not shop_id:
        raise HTTPException(status_code=401, detail="No shop_id included in token")
    try:
        response = requests.post(settings.shop_endpoint.unicode_string() + f"/items/get",
                                 json={"item_id_list": [str(iid) for iid in selected_items.item_id_list]},
                                 timeout=10)
    except TimeoutError as e:
        print("login timeout", e)
        raise HTTPException(status_code=550, detail="Shop service unavailable")
    jsonned = response.json()
    return ShopInventoryItems(items=jsonned, total=len(jsonned))


@router.post("/record_transaction")
def record_transaction(transaction_create: TransactionCreateFromFrontend,
                       token: dict = Depends(ValidateHeader(cashier_access_level, settings.secret))) -> Transaction:
    """
    Record a transaction into the system

    :param transaction_create: TransactionCreateFromFrontend object
    :param token: dict from the DI system with data from jwt token.
    :return: Transaction domain object
    """
    iids = [record[0] for record in transaction_create.item_id_quantity]
    item_details = get_items_details(SelectedItems(item_id_list=iids), token)
    shop_id = token.get("shop_id")
    data = {
        "shop_id": str(shop_id),
        "user_id": str(transaction_create.user_id),
        "items": [{"item_id": str(item.iid), "quantity": id_quantity[1], "unit_cost": item.price, "point_allocation_percentage": item.percent_point_allocation} for item, id_quantity in zip(item_details.items, transaction_create.item_id_quantity)]
    }
    try:
        response = requests.post(settings.transaction_endpoint.unicode_string() + f"/userdata/transaction",
                                 json=data,
                                 timeout=10)
    except TimeoutError as e:
        print("record_transaction timeout", e)
        raise HTTPException(status_code=550, detail="Transaction service unavailable")
    return response.json()
