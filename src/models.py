import uuid
import datetime

from pydantic import BaseModel, EmailStr, PastDate


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

class Transaction(TransactionCreate):
    tid: uuid.UUID
    total_cost: int
    points_allocated: int
    performed_at: datetime.datetime
    items: list[Item]

class TransactionResponse(BaseModel):
    transactions: list[Transaction]
