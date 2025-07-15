import uuid
import datetime

from pydantic import BaseModel, EmailStr, PastDate, Field


class UserCreate(BaseModel):
    """
    Data transfer object for user creation requests.

    Enforces business rules through Pydantic validation:
    - Email must be valid format
    - Date of birth must be in the past
    - Required fields ensure data completeness
    - Optional UUID for linking to temporal user
    """
    uid: uuid.UUID | None = None
    first_name: str
    last_name: str
    user_name: str
    email: EmailStr
    date_of_birth: PastDate
    gender: str
    nationality: str
    password: str


class User(BaseModel):
    """
    Domain entity representing a registered user account.

    Contains user profile information without sensitive data like passwords.
    Used for API responses and domain operations.
    """
    uid: uuid.UUID
    first_name: str
    last_name: str
    user_name: str
    email: EmailStr
    date_of_birth: PastDate
    gender: str
    nationality: str

class UserPublicProfile(BaseModel):
    uid: uuid.UUID
    first_name: str
    user_name: str

class UserLogInRequest(BaseModel):
    """
    Data transfer object for user authentication requests.

    Contains login credentials for user authentication.
    Password is validated against stored hash in service layer.
    """
    email: EmailStr
    password: str


class LogInSuccessful(BaseModel):
    msg: str
    token: str

class RecognitionResult(BaseModel):
    user: UserPublicProfile | None = None
    uid: uuid.UUID
    assummed_new: bool

class Cashier(BaseModel):
    cid: uuid.UUID
    account_name: str
    shop_id: uuid.UUID

class CashierLoginRequest(BaseModel):
    shop_nickname: str
    account_name: str
    password: str

class ItemCreate(BaseModel):
    item_id: uuid.UUID
    quantity: int
    unit_cost: int
    point_allocation_percentage: int

class Item(ItemCreate):
    total_cost: int

class TransactionCreate(BaseModel):
    user_id: uuid.UUID
    shop_id: uuid.UUID
    items: list[ItemCreate]

class UserBalances(BaseModel):
    user_id: uuid.UUID
    shops: list[tuple[uuid.UUID, int]]

class FrontendUserBalances(BaseModel):
    user_id: uuid.UUID
    shops: list[tuple[str, int]]

class Transaction(TransactionCreate):
    tid: uuid.UUID
    total_cost: int
    points_allocated: int
    performed_at: datetime.datetime
    items: list[Item]

class FrontendTransaction(Transaction):
    shop_name: str

class TransactionResponse(BaseModel):
    transactions: list[Transaction]

class FrontendTransactionResponse(BaseModel):
    transactions: list[FrontendTransaction]

class ShopNames(BaseModel):
    names: list[str]

class ItemCreateIventory(BaseModel):
    name: str
    description: str
    photo_url: str | None = None
    price: int = Field(gt=0)
    percent_point_allocation: int = Field(ge=0)
    shop_id: uuid.UUID

class ItemInventory(ItemCreateIventory):
    iid: uuid.UUID

class ShopInventoryItems(BaseModel):
    items: list[ItemInventory]
    total: int

class RenameUIDRequest(BaseModel):
    old_uid: uuid.UUID
    new_uid: uuid.UUID

class RenameResult(BaseModel):
    new_uid: uuid.UUID

class ConfusionUIRequest(BaseModel):
    recognised_uid: uuid.UUID
    found_uid: uuid.UUID
    timestamp: int
