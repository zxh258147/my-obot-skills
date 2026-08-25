import json
import sys

def get_weather(city):
    # 这里是你的业务逻辑，现在先用模拟数据
    data = {
        "Beijing": "Sunny, 25°C",
        "Shanghai": "Rainy, 22°C",
        "New York": "Cloudy, 18°C"
    }
    return data.get(city, f"Unknown weather for {city}")

if __name__ == "__main__":
    # Obot/GPTScript 会通过环境变量或参数传递输入
    # 简单起见，我们从命令行参数读取
    try:
        input_data = json.loads(sys.argv[1])
        city = input_data.get("city", "Beijing")
        result = get_weather(city)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)