# NeuroHub


ex)

python services/agent/web_agent.py https://github.com/messpy --prompt "これいくら？" --output

# IP推定：引数なし
python services/agent/weather_agent.py
# 都市名
python services/agent/weather_agent.py "Osaka"
# 座標・温度単位・24時間予報
python services/agent/weather_agent.py --lat 35.68 --lon 139.76 --unit f --forecast hourly --hours 24



