import requests
from fastapi import APIRouter, HTTPException, Depends

from src.security import issue_token, AccessLevel, ValidateHeader
from src.settings import settings
from src.models import CashierLoginRequest, Cashier, LogInSuccessful, ShopInventoryItems, UserPublicProfile, \
    RenameUIDRequest, RenameResult, ConfusionUIRequest

router = APIRouter(prefix="/cashier")
cashier_access_level = AccessLevel("Cashier_Level")

@router.post("/login")
def login_cashier(login_request: CashierLoginRequest):
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
def get_user_by_user_name(user_name: str, token: dict = Depends(ValidateHeader(cashier_access_level, settings.secret))) -> UserPublicProfile:
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
    print(f'Cashier {token["entity_id"]} requested data rename of {rename_request.old_uid} to {rename_request.new_uid}')
    try:
        result_id_update = requests.post(settings.face_recognition_endpoint.encoded_string() + "/frontend/merge",
                                         json={"new_uid": str(rename_request.new_uid),
                                               "old_uid": str(rename_request.old_uid)},
                                         timeout=10)
    except (ConnectionError, TimeoutError) as e:
        print("merge_users", e)
        raise HTTPException(status_code=550, detail="Face recognition service not available")
    return result_id_update.json()

@router.post("/confused_users")
def note_user_confusion(confusion_request: ConfusionUIRequest,
                token: dict = Depends(ValidateHeader(cashier_access_level, settings.secret))) -> dict:
    print(f'Cashier {token["entity_id"]} reported confusion of recognised {confusion_request.recognised_uid} to '
          f'actual {confusion_request.found_uid}')
    return {}
