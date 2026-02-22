from __future__ import annotations

from datetime import datetime
from html import escape
import json
from typing import Any
from urllib.parse import parse_qs, urlencode
from urllib.request import urlopen

from http.server import BaseHTTPRequestHandler, HTTPServer

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def fetch_json(url: str, params: dict[str, str]) -> dict[str, Any]:
    query = urlencode(params)
    with urlopen(f"{url}?{query}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def lookup_city(city: str) -> dict[str, Any] | None:
    payload = fetch_json(
        GEOCODING_URL,
        {"name": city, "count": "1", "language": "en", "format": "json"},
    )
    results = payload.get("results") or []
    return results[0] if results else None


def fetch_weather(latitude: float, longitude: float) -> dict[str, Any]:
    return fetch_json(
        WEATHER_URL,
        {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )


def render_page(city: str = "", weather: dict[str, Any] | None = None, error: str = "") -> str:
    error_html = f'<p class="error">{escape(error)}</p>' if error else ""

    weather_html = ""
    if weather:
        weather_html = f"""
        <section class="card">
          <h2>{escape(weather['city'])}, {escape(weather['country'])}</h2>
          <p class="temp">{weather['temperature']}°C</p>
          <ul>
            <li><strong>Condition:</strong> {escape(weather['description'])}</li>
            <li><strong>Feels like:</strong> {weather['feels_like']}°C</li>
            <li><strong>Humidity:</strong> {weather['humidity']}%</li>
            <li><strong>Wind speed:</strong> {weather['wind_speed']} km/h</li>
            <li><strong>Last updated:</strong> {escape(weather['updated_at'])}</li>
          </ul>
        </section>
        """

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Simple Weather App</title>
  <style>
    * {{ box-sizing: border-box; font-family: Arial, sans-serif; }}
    body {{ margin: 0; background: linear-gradient(145deg, #dfefff, #f8fbff); min-height: 100vh; display: grid; place-items: center; }}
    .container {{ width: min(95%, 580px); background: white; border-radius: 12px; padding: 24px; box-shadow: 0 6px 20px rgba(0,0,0,.08); }}
    .subtitle {{ color: #556; }}
    .weather-form {{ display: flex; gap: 10px; margin: 18px 0; }}
    input {{ flex: 1; padding: 10px; border: 1px solid #ccd; border-radius: 8px; }}
    button {{ padding: 10px 14px; border: none; border-radius: 8px; background: #2563eb; color: white; cursor: pointer; }}
    .temp {{ font-size: 2rem; margin: .5rem 0; }}
    .card {{ margin-top: 12px; border-top: 1px solid #e8eef7; padding-top: 12px; }}
    .error {{ color: #b00020; font-weight: 600; }}
  </style>
</head>
<body>
  <main class=\"container\">
    <h1>🌤️ Simple Weather App</h1>
    <p class=\"subtitle\">Check current weather for any city.</p>
    <form method=\"post\" class=\"weather-form\">
      <input type=\"text\" name=\"city\" placeholder=\"Enter city name (e.g., London)\" value=\"{escape(city)}\" required />
      <button type=\"submit\">Get Weather</button>
    </form>
    {error_html}
    {weather_html}
  </main>
</body>
</html>"""


class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self._send_html(render_page())

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        city = parse_qs(body).get("city", [""])[0].strip()

        if not city:
            self._send_html(render_page(error="Please enter a city name."))
            return

        try:
            location = lookup_city(city)
            if not location:
                self._send_html(render_page(city=city, error=f"Could not find weather data for '{city}'."))
                return

            forecast = fetch_weather(location["latitude"], location["longitude"])
            current = forecast.get("current", {})
            weather_code = current.get("weather_code")
            weather = {
                "city": str(location.get("name", city)),
                "country": str(location.get("country", "")),
                "temperature": current.get("temperature_2m", "N/A"),
                "feels_like": current.get("apparent_temperature", "N/A"),
                "humidity": current.get("relative_humidity_2m", "N/A"),
                "wind_speed": current.get("wind_speed_10m", "N/A"),
                "description": WEATHER_CODE_MAP.get(weather_code, "Unknown"),
                "updated_at": datetime.fromisoformat(current.get("time", datetime.now().isoformat())).strftime("%Y-%m-%d %H:%M"),
            }
            self._send_html(render_page(city=city, weather=weather))
        except Exception:
            self._send_html(render_page(city=city, error="Unable to fetch weather right now. Please try again in a moment."))

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 5000), WeatherHandler)
    print("Serving on http://0.0.0.0:5000")
    server.serve_forever()
