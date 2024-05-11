from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from acm import Manager
from acm.data import Invoice, Settings

app = FastAPI()
manager = Manager()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


class UserRegisterRequest(BaseModel):
    name: str
    phone: str
    password: str


class UserRegisterResponse(BaseModel):
    user_id: str


@app.post("/user/register", response_model = UserRegisterResponse)
async def register_user(user_request: UserRegisterRequest):
    # 将用户注册逻辑放在这里，包括密码哈希等操作
    # 返回包含用户ID的响应
    user_id = "123456789"  # 替换为实际的用户ID生成逻辑
    return {"user_id": user_id}


class CheckInRequest(BaseModel):
    user_id: str


class CheckInResponse(BaseModel):
    room_id: int


@app.post("/checkin", response_model = CheckInResponse)
def check_in(check_in_request: CheckInRequest):
    # 将签到逻辑放在这里，包括根据用户ID获取房间ID等操作
    # 返回包含房间ID的响应
    room_id = 1  # 替换为实际的房间ID生成逻辑
    return {"room_id": room_id}


class CheckoutRequest(BaseModel):
    user_id: str


class CheckoutResponse(BaseModel):
    cost: float
    invoices: List[Invoice]


@app.post("/checkout", response_model = CheckoutResponse)
def checkout(checkout_request: CheckoutRequest):
    # 结账逻辑放在这里，包括根据用户ID计算费用、生成详单等操作
    # 返回包含待支付金额和详单的响应
    cost = 100.0  # 替换为实际的费用计算逻辑
    invoices = [
        Invoice(room_id = "123456", start_time = "2022-01-01 10:00:00", end_time = "2022-01-01 12:00:00",
                settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool"), cost = 50.0),
        Invoice(room_id = "789012", start_time = "2022-01-01 13:00:00", end_time = "2022-01-01 15:00:00",
                settings = Settings(temperature = 22, fan_speed = "Low", mode = "Heat"), cost = 50.0)
    ]  # 替换为实际的详单生成逻辑
    return {"cost": cost, "invoices": invoices}


class RoomRequest(BaseModel):
    room_id: int


class ACSwitchResponse(BaseModel):
    status: bool
    settings: Settings


@app.post("/ac/on", response_model = ACSwitchResponse)
def turn_on_ac(ac_on_request: RoomRequest):
    # 开启空调逻辑放在这里，包括根据房间ID执行相应操作，如设置参数等
    # 返回包含操作状态和空调参数的响应
    room_id = ac_on_request.room_id
    status = True  # 替换为实际的开启空调逻辑
    settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool")  # 替换为实际的空调参数
    return {"status": status, "settings": settings}


@app.post("/ac/off", response_model = ACSwitchResponse)
def turn_off_ac(ac_off_request: RoomRequest):
    # 关闭空调逻辑放在这里，包括根据房间ID执行相应操作，如设置参数等
    # 返回包含操作状态和空调参数的响应
    room_id = ac_off_request.room_id
    status = False
    settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool")
    return {"status": status, "settings": settings}


class ACSettingRequest(BaseModel):
    room_id: int
    settings: Settings


@app.post("/ac/settings", response_model = ACSwitchResponse)
def set_ac(ac_set_request: ACSettingRequest):
    # 设置空调参数逻辑放在这里，包括根据房间ID和参数执行相应操作
    # 返回包含操作状态和空调参数的响应
    room_id = ac_set_request.room_id
    settings = ac_set_request.settings
    status = True
    return {"status": status, "settings": settings}


class RoomCostResponse(BaseModel):
    cost: float


@app.post("/ac/cost", response_model = RoomCostResponse)
def get_cost(room_query_request: RoomRequest):
    return {"cost": 100.0}


class RoomStatusResponse(BaseModel):
    status: bool
    settings: Settings


@app.get("/ac/status", response_model = RoomStatusResponse)
def get_ac_status(room_query_request: RoomRequest):
    return {"status": True, "settings": Settings(temperature = 25, fan_speed = "High", mode = "Cool")}


class ReportItem(BaseModel):
    room_id: int
    status: int
    settings: Settings


class ReportResponse(BaseModel):
    reports: List[Invoice]


@app.get("/ac/reports", response_model = ReportResponse)
def get_reports():
    return {"reports": [
        ReportItem(room_id = 1, status = 1, settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool"))]}
