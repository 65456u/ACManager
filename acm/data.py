from typing import List

from pydantic import BaseModel


class Settings(BaseModel):
    temperature: int
    fan_speed: str
    mode: str


class CheckInRequest(BaseModel):
    user_id: int


class CheckInResponse(BaseModel):
    room_id: int


class Invoice(BaseModel):
    room_id: int
    start_time: str
    end_time: str
    settings: Settings
    cost: float


class ReportItem(BaseModel):
    room_id: int
    user_id: int
    start_time: str
    end_time: str
    cost: float
    settings: Settings


class ReportResponse(BaseModel):
    reports: List[ReportItem]


class CheckoutRequest(BaseModel):
    user_id: int


class CheckoutResponse(BaseModel):
    cost: float
    invoices: List[Invoice]


class RoomRequest(BaseModel):
    room_id: int


class ACSwitchResponse(BaseModel):
    status: int
    settings: Settings


class ACSettingRequest(BaseModel):
    room_id: int
    settings: Settings


class RoomCostResponse(BaseModel):
    cost: float


class RoomStatusResponse(BaseModel):
    busy: int
    ac_on: int
    settings: Settings
    start_time: str


class UserRegisterRequest(BaseModel):
    name: str
    phone: str
    password: str


class GetUserIdRequest(BaseModel):
    name: str


class UserRegisterResponse(BaseModel):
    user_id: int


class UserLoginResponse(BaseModel):
    status: int
    room_id: int
    user_id: int


class UserLoginRequest(BaseModel):
    name: str
    password: str
