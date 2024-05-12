from fastapi import FastAPI

from acm import Manager
from acm.acmdb import ACMDatabase
from acm.data import *

app = FastAPI()
manager = Manager()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/user/register", response_model = UserRegisterResponse)
async def register_user(user_request: UserRegisterRequest):
    # 将用户注册逻辑放在这里，包括密码哈希等操作
    # 返回包含用户ID的响应
    # user_id = "123456789"  # 替换为实际的用户ID生成逻辑
    # return {"user_id": user_id}
    acm_db = ACMDatabase()  # 创建 ACMDatabase 类的实例
    # 调用 register_user 方法
    user_id = acm_db.register_user(user_request.username, user_request.phone, user_request.password)
    if user_id is not None:
        return {"message": "User registered successfully", "user_id": user_id}
    else:
        return {"message": "Failed to register user"}

@app.post("/checkin", response_model = CheckInResponse)
def check_in(check_in_request: CheckInRequest):
    # 将签到逻辑放在这里，包括根据用户ID获取房间ID等操作
    # 返回包含房间ID的响应
    #room_id = 1  # 替换为实际的房间ID生成逻辑
    #return {"room_id": room_id}
    acm_db = ACMDatabase()  # 创建 ACMDatabase 类的实例
    # 调用 checkin 方法
    room_id = acm_db.checkin(check_in_request.user_id)
    if room_id == -1:
        return {"room_id": -1}
    else:
        return {"room_id": room_id}


@app.post("/checkout", response_model = CheckoutResponse)
def checkout(checkout_request: CheckoutRequest):
    # 结账逻辑放在这里，包括根据用户ID计算费用、生成详单等操作
    # 返回包含待支付金额和详单的响应
    # cost = 100.0  # 替换为实际的费用计算逻辑
    # invoices = [
    #     Invoice(room_id = "123456", start_time = "2022-01-01 10:00:00", end_time = "2022-01-01 12:00:00",
    #             settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool"), cost = 50.0),
    #     Invoice(room_id = "789012", start_time = "2022-01-01 13:00:00", end_time = "2022-01-01 15:00:00",
    #             settings = Settings(temperature = 22, fan_speed = "Low", mode = "Heat"), cost = 50.0)
    # ]  # 替换为实际的详单生成逻辑
    acm_db = ACMDatabase()
    # 调用 checkout 方法
    cost, invoices = acm_db.checkout(checkout_request.user_id)
    return {"cost": cost, "invoices": invoices}

@app.post("/ac/on", response_model = ACSwitchResponse)
def turn_on_ac(ac_on_request: RoomRequest):
    # 开启空调逻辑放在这里，包括根据房间ID执行相应操作，如设置参数等
    # 返回包含操作状态和空调参数的响应
    # room_id = ac_on_request.room_id
    # status = True  # 替换为实际的开启空调逻辑
    # settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool")  # 替换为实际的空调参数
    # return {"status": status, "settings": settings}
    room_id = RoomRequest.room_id
    # 创建 ACMDatabase 类的实例
    acm_db = ACMDatabase()
    # 调用 turn_on_ac 方法
    status = acm_db.turn_on_ac(room_id)
    # 根据返回的状态构建响应
    if status == -1:
        return {"status": -1, "message": "Room not found or not available"}
    elif status == -2:
        return {"status": -2, "message": "AC is already turned on in this room"}
    else:
        return {"status": 0, "message": "AC turned on successfully"}



@app.post("/ac/off", response_model = ACSwitchResponse)
def turn_off_ac(ac_off_request: RoomRequest):
    # 关闭空调逻辑放在这里，包括根据房间ID执行相应操作，如设置参数等
    # 返回包含操作状态和空调参数的响应
    # room_id = ac_off_request.room_id
    # status = False
    # settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool")
    # return {"status": status, "settings": settings}
    # 解析请求体数据
    room_id = RoomRequest.room_id
    # 创建 ACMDatabase 类的实例
    acm_db = ACMDatabase()
    # 调用 turn_off_ac 方法
    status, settings = acm_db.turn_off_ac(room_id)
    # 根据返回的状态构建响应
    if status == -1:
        return {"status": -1, "message": "Room not found or not available", "settings": settings.dict()}
    elif status == -2:
        return {"status": -2, "message": "AC is already turned off in this room", "settings": settings.dict()}
    else:
        return {"status": 0, "message": "AC turned off successfully", "settings": settings.dict()}



@app.post("/ac/settings", response_model = ACSwitchResponse)
def set_ac(ac_set_request: ACSettingRequest):
    # 设置空调参数逻辑放在这里，包括根据房间ID和参数执行相应操作
    # 返回包含操作状态和空调参数的响应
    # room_id = ac_set_request.room_id
    # settings = ac_set_request.settings
    # status = True
    # return {"status": status, "settings": settings}
    acm_db = ACMDatabase()
    # 从请求中获取房间ID和设置
    room_id = ac_set_request.room_id
    settings = ac_set_request.settings
    # 调用set_ac方法
    status, new_settings = acm_db.set_ac(room_id, settings)
    # 根据返回值生成响应
    if status == 0:
        return {"status": "success", "settings": new_settings}
    elif status == -1:
        return {"status": "error", "message": "Room not found"}
    elif status == -2:
        return {"status": "error", "message": "AC is turned off"}
    else:
        return {"status": "error", "message": "Unknown error"}



@app.post("/ac/cost", response_model = RoomCostResponse)
def get_cost(room_query_request:UserRegisterResponse):
    acm_db = ACMDatabase()  # 创建 ACMDatabase 类的实例
    cost = acm_db.get_cost(room_query_request.user_id)  # 调用 get_cost 方法
    return {"cost": cost}



@app.get("/ac/status", response_model = RoomStatusResponse)
def get_ac_status(room_query_request: RoomRequest):
    acm_db = ACMDatabase()  # 创建 ACMDatabase 类的实例
    statuses = acm_db.check_status(room_query_request.room_id)  # 调用 fetch_all_ac_statuses 方法
    return {"status": True, "settings": statuses}
    #return {"status": True, "settings": Settings(temperature = 25, fan_speed = "High", mode = "Cool")}


@app.get("/ac/reports", response_model = List[ReportItem])
def get_report_item(room_query_request: RoomRequest):
    acm_db = ACMDatabase()  # 创建 ACMDatabase 类的实例
    total_cost, report = acm_db.generate_report(room_query_request.room_id)  # 调用 generate_report 方法
    # 这里假设 ReportItem 是你定义的报告项数据模型
    return {"total_cost": total_cost, "report": report}
    # return [
    #     ReportItem(room_id = 1, status = 1, settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool")),
    #     ReportItem(room_id = 2, status = 0, settings = Settings(temperature = 25, fan_speed = "High", mode = "Cool"))
    # ]
