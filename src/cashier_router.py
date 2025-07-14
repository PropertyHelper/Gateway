import requests
from fastapi import APIRouter, HTTPException

from src.security import issue_token, AccessLevel
from src.settings import settings
from src.models import CashierLoginRequest, Cashier, LogInSuccessful

router = APIRouter(prefix="/cashier")

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
                                                            secret=settings.secret))
