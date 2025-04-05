import os
import requests
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel, Field
# from langchain.tools import BaseTool
from langchain_core.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    raise ValueError("OpenWeather API key not found in environment variables")

class WeatherInput(BaseModel):
    """Input for the weather tool."""
    location: str = Field(..., description="The city name to get weather for")

# class WeatherTool(BaseTool):
#     """Tool that fetches weather information from OpenWeatherMap API."""
    
#     name: str = "weather_tool"
#     description: str = "Useful for getting current weather information for a city."
#     args_schema: Type[WeatherInput] = WeatherInput

@tool
def weather_tool(location: str) -> Dict[str, Any]:
    """Tool that fetches weather information for the provided location"""
    print("Using tool weather_tool")
    try:
        # API endpoint for OpenWeatherMap
        url = f"https://api.openweathermap.org/data/2.5/weather"
        
        # Parameters for the API request
        params = {
            "q": location,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"  # For temperature in Celsius
        }
        
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response
        data = response.json()
        
        # Extract relevant weather information
        weather_info = {
            "location": data["name"],
            "country": data["sys"]["country"],
            "weather": data["weather"][0]["description"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "timestamp": data["dt"]
        }
        
        return weather_info
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    except (KeyError, IndexError) as e:
        return {"error": f"Failed to parse weather data: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"} 