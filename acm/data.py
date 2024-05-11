from typing import List

from pydantic import BaseModel


class Settings(BaseModel):
    temperature: int
    fan_speed: str
    mode: str


class CheckInRequest(BaseModel):
    user_id: str


class CheckInResponse(BaseModel):
    room_id: int


class Invoice(BaseModel):
    room_id: str
    start_time: str
    end_time: str
    settings: Settings
    cost: float


class ReportItem(BaseModel):
    room_id: int
    status: int
    settings: Settings


class ReportResponse(BaseModel):
    reports: List[Invoice]


class CheckoutRequest(BaseModel):
    user_id: str


class CheckoutResponse(BaseModel):
    cost: float
    invoices: List[Invoice]


class RoomRequest(BaseModel):
    room_id: int


class ACSwitchResponse(BaseModel):
    status: bool
    settings: Settings


class ACSettingRequest(BaseModel):
    room_id: int
    settings: Settings


class RoomCostResponse(BaseModel):
    cost: float


class RoomStatusResponse(BaseModel):
    status: bool
    settings: Settings


class UserRegisterRequest(BaseModel):
    name: str
    phone: str
    password: str


class UserRegisterResponse(BaseModel):
    user_id: str
