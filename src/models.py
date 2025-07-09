import uuid

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
    email: EmailStr
    date_of_birth: PastDate
    gender: str
    nationality: str


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
    user: User | None = None
    uid: uuid.UUID
    assummed_new: bool
