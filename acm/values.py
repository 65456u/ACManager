from .data import Settings

default_ac_setting = Settings(temperature = 25, fan_speed = "High", mode = "Cool")

invalid_ac_setting = Settings(temperature = -1, fan_speed = "Invalid", mode = "Invalid")
