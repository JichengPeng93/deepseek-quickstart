# weather.py (最终修正版)

from typing import Any, Annotated
import httpx
from fastapi import Query
from mcp.server.fastmcp import FastMCP
import dateutil.parser
from datetime import datetime, timedelta
import pytz
import dateutil.parser

# 初始化 FastMCP 服务器
mcp = FastMCP("weather")

# --- 常量定义 ---
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
# 定义美国时区
ny_tz = pytz.timezone("America/New_York")
now = datetime.now(ny_tz)
today = now.date()
# --- 辅助函数 ---

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """一个通用的异步函数，用于向 NWS API 发起请求并处理常见的错误。"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """将单个天气预警的 JSON 数据格式化为人类可读的字符串。"""
    props = feature["properties"]
    return f"""
事件: {props.get('event', '未知')}
区域: {props.get('areaDesc', '未知')}
严重性: {props.get('severity', '未知')}
描述: {props.get('description', '无描述信息')}
指令: {props.get('instruction', '无具体指令')}
"""



# --- MCP 工具定义 ---

@mcp.tool()
async def get_alerts(
    state: Annotated[str, Query(description="需要查询的美国州代码，必须是两个大写字母，例如 'CA' 或 'NY'。")]
) -> str:
    """获取美国某个州当前生效的天气预警信息。"""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "无法获取预警信息或未找到相关数据。"

    if not data["features"]:
        return f"州代码 '{state}' 当前没有生效的天气预警。"

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(
    latitude: Annotated[float, Query(description="地理纬度坐标，北半球为正，南半球为负。例如：40.7128")],
    longitude: Annotated[float, Query(description="地理经度坐标，东半球为正，西半球为负。例如：-74.006")],
    days: Annotated[int, Query(description="从当前日期算起，几天之内的天气情况，例如：”3“，代表查询日期往后推3(包括查询当日)天之内的所有天气情况")] = 7
) -> str:
    """根据给定的经纬度获取天气预报。注意，如果不传days参数，那默认将查询从当前日期，到往后一周（7天）的时间段的天气"""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data or "properties" not in points_data or "forecast" not in points_data["properties"]:
        return f"无法为坐标 ({latitude}, {longitude}) 获取有效的预报网格点。"

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data or "properties" not in forecast_data or "periods" not in forecast_data["properties"]:
        return "无法获取详细的预报信息。"

    periods = forecast_data["properties"]["periods"]
    forecasts = []
    end_date = today + timedelta(days=days-1)
    for period in periods:
        start = dateutil.parser.isoparse(period['startTime']).astimezone(ny_tz).date()
        if start <= end_date:
            forecast = f"""
             {period['name']}:
                起始日期: {period['startTime']}
                终止日期: {period['endTime']}
                温度: {period['temperature']}°{period['temperatureUnit']}
                风力: {period['windSpeed']} {period['windDirection']}
                预报: {period['detailedForecast']}
                """
            forecasts.append(forecast)
        else:
            break
    return "\n---\n".join(forecasts)

# --- 服务器启动 ---

if __name__ == "__main__":
    mcp.run(transport='stdio')