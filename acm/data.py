from pydantic import BaseModel


class Settings(BaseModel):
    temperature: int
    fan_speed: str
    mode: str


class Invoice(BaseModel):
    room_id: str
    start_time: str
    end_time: str
    settings: Settings
    cost: float
