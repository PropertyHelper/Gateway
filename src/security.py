import binascii
import typing
import enum
import jwt
import base64
import json

from fastapi import Header, HTTPException


class AccessLevel(enum.Enum):
    USER_LEVEL = "User_Level"
    CASHIER_LEVEL = "Cashier_Level"
    STORE_MANAGEMENT_LEVEL = "Store_Management_Level"


def issue_token(
    entity_id: str, access_level: AccessLevel, secret: str, **kwargs
) -> str:
    """
    Generate a token signed by secret.

    :param entity_id: str
    :param access_level: AccessLevel
    :param secret: str
    :return: str
    """
    return jwt.encode(
        {"entity_id": entity_id, "access_level": access_level.value, **kwargs},
        secret,
        algorithm="HS256",
    )


def verify_token(token: str, supposed_secret: str) -> dict[str, str]:
    return jwt.decode(token, supposed_secret, algorithms="HS256")


def decode_segment(segment: str) -> None | dict[str, str]:
    """
    Decode a given segment of the JWT.

    :param segment: str
    :return: decoded JWT - dict
    """
    try:
        binary_decoded = base64.b64decode(segment + "==")
        jsonned_data = json.loads(binary_decoded.decode())
    except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return jsonned_data


def token_has_access(token: str, access_level: AccessLevel, secret: str) -> bool:
    """
    Verify that the token has required access level.

    The function is expected to be used for the FastApi header check.
    :param token: str
    :param access_level: AccessLevel
    :param secret: str
    :return: bool
    """
    try:
        payload = decode_segment(token.split(".")[1])
    except IndexError:
        return False
    if payload is None or payload.get("entity_id") is None:
        return False
    try:
        decoded_payload = verify_token(token, secret)
    except jwt.PyJWTError:
        return False
    return decoded_payload["access_level"] == access_level.value


class ValidateHeader:
    """
    Validate Header with an instance of a class.
    use case:
    https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/
    Specify security level for a router:
    >>> from fastapi import APIRouter, Depends
    >>> read_only_access_level = AccessLevel("Can_Read")
    >>> router = APIRouter(
    >>>     prefix="/items",
    >>>     tags=["items"],
    >>>     dependencies=[Depends(ValidateHeader(read_only_access_level))],
    >>>     responses={404: {"description": "Not found"}},
    >>>     )
    """

    def __init__(self, required_access_level: AccessLevel, secret: str):
        self.required_access_level = required_access_level
        self.secret = secret

    async def __call__(
        self, token: typing.Annotated[str | None, Header()] = None
    ):
        if token is None:
            raise HTTPException(status_code=401)
        if not token_has_access(token, self.required_access_level, self.secret):
            raise HTTPException(status_code=403)
        return decode_segment(token.split(".")[1])