from datetime import datetime

fan_speed_mapping = {
    "low": 1.0,
    "mid": 1.2,
    "high": 1.5
}

mode_mapping = {
    "cool": 1.0,
    "heat": 1.2
}


def calculate_cost(start_time, end_time, temperature, fan_speed, mode):
    """
    计价标准：
    end_time-start_time: 每1小时记10
    temperature: 以28度为基准，每相差一度加收2%
    fan_speed: "低" "中" "高" 依次乘上1.0/1.2/1.5
    mode: "制冷" "制热" 依次乘1.0/1.2
    """
    # convert string to lower case
    fan_speed = fan_speed.lower()
    mode = mode.lower()

    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    time_diff = end_time - start_time
    time = time_diff.total_seconds() / 3600
    print(time, temperature, fan_speed_mapping.get(fan_speed), mode_mapping.get(mode))
    # 计算花费
    cost = 10 * time * (abs(temperature - 26) * 0.02 + 1) * fan_speed_mapping.get(fan_speed) * mode_mapping.get(mode)
    return cost
