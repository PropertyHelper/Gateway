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
    """
    Use the model to demonstrate user providers to cashier system.
    Does not contain any sensitive information to identify the user
    beyond the system.
    Preserves user privacy.
    """
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
    """
    A model to return a jwt token on successful login.
    """
    msg: str
    token: str

class RecognitionResult(BaseModel):
    """
    User recognition results returned to frontend.
    """
    user: UserPublicProfile | None = None
    uid: uuid.UUID
    assummed_new: bool

class Cashier(BaseModel):
    """Use to represent the cashier domain model"""
    cid: uuid.UUID
    account_name: str
    shop_id: uuid.UUID

class CashierLoginRequest(BaseModel):
    """Use to authenticate the cashier"""
    shop_nickname: str
    account_name: str
    password: str

class ItemCreate(BaseModel):
    """Use to create an item in TransactioonService"""
    item_id: uuid.UUID
    quantity: int
    unit_cost: int
    point_allocation_percentage: int

class Item(ItemCreate):
    """Use to represent an item in TransactioonService"""
    total_cost: int

class TransactionCreate(BaseModel):
    """Use to create a transaction in TransactioonService"""
    user_id: uuid.UUID
    shop_id: uuid.UUID
    items: list[ItemCreate]

class UserBalances(BaseModel):
    """Use to represent user balances in TransactioonService"""
    user_id: uuid.UUID
    shops: list[tuple[uuid.UUID, int]]

class FrontendUserBalances(BaseModel):
    """
    Use to return balances to the frontend.

    Saturates initial UserBalances from TransactioonService
    by changing shop ids to names.
    """
    user_id: uuid.UUID
    shops: list[tuple[str, int]]

class Transaction(TransactionCreate):
    """Represent a transaction in TransactioonService"""
    tid: uuid.UUID
    total_cost: int
    points_allocated: int
    performed_at: datetime.datetime
    items: list[Item]

class FrontendTransaction(Transaction):
    """
    Represent a transaction for frontend.

    Saturates the response of TransactioonService by adding shop name.
    """
    shop_name: str

class TransactionResponse(BaseModel):
    """Represent multiple transactions from TransactioonService"""
    transactions: list[Transaction]

class FrontendTransactionResponse(BaseModel):
    """Represent multiple transactions to return to frontend"""
    transactions: list[FrontendTransaction]

class ShopNames(BaseModel):
    """Represent shop names to return to frontend"""
    names: list[str]

class ItemCreateIventory(BaseModel):
    """Represent an item creation object in ShopDataService"""
    name: str
    description: str
    photo_url: str | None = None
    price: int = Field(gt=0)
    percent_point_allocation: int = Field(ge=0)
    shop_id: uuid.UUID

class ItemInventory(ItemCreateIventory):
    """Represent an item object in ShopDataService"""
    iid: uuid.UUID

class ShopInventoryItems(BaseModel):
    """Represent inventory of the shop from the ShopDataService"""
    items: list[ItemInventory]
    total: int

class RenameUIDRequest(BaseModel):
    """Use to merge users in face recognition service"""
    old_uid: uuid.UUID
    new_uid: uuid.UUID

class RenameResult(BaseModel):
    """Returned for merge from face recognition service"""
    new_uid: uuid.UUID

class ConfusionUIRequest(BaseModel):
    """Get the user confusion feedback from UI"""
    recognised_uid: uuid.UUID
    found_uid: uuid.UUID
    timestamp: int

class SelectedItems(BaseModel):
    """Represent selected items from frontend to fetch data about them"""
    item_id_list: list[uuid.UUID]

class TransactionCreateFromFrontend(BaseModel):
    """Represent frontend transaction creation data"""
    user_id: uuid.UUID
    item_id_quantity: list[tuple[uuid.UUID, int]]

class ShopLogInRequest(BaseModel):
    """Use to get shop credentials"""
    nickname: str
    password: str

class Shop(BaseModel):
    """Use to represent the shop from the ShopDataService"""
    sid: uuid.UUID
    nickname: str

class ShopUsers(BaseModel):
    """Use to represent users of a shop"""
    shop_id: uuid.UUID
    users: list[uuid.UUID]

class AnalyticalView(BaseModel):
    """
    Data transfer object for user analytics reports.

    Contains aggregated user statistics including gender and nationality
    distributions, along with total valid user count for the analysis.
    """
    gender_groupby: list[tuple[str, int]]
    nationality_groupby: list[tuple[str, int]]
    valid_users: int

class CashierCreate(BaseModel):
    """Use to add a new cashier in the system"""
    account_name: str
    password: str
