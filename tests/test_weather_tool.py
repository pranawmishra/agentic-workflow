import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.tools.weather import weather_tool

# Sample response data for mocking
SAMPLE_WEATHER_RESPONSE = {
    "coord": {"lon": -0.1257, "lat": 51.5085},
    "weather": [{"id": 804, "main": "Clouds", "description": "overcast clouds", "icon": "04d"}],
    "base": "stations",
    "main": {
        "temp": 15.5,
        "feels_like": 14.9,
        "temp_min": 13.8,
        "temp_max": 16.5,
        "pressure": 1021,
        "humidity": 71
    },
    "visibility": 10000,
    "wind": {"speed": 3.6, "deg": 220},
    "clouds": {"all": 100},
    "dt": 1682084645,
    "sys": {
        "type": 2,
        "id": 2075535,
        "country": "GB",
        "sunrise": 1682055510,
        "sunset": 1682106821
    },
    "timezone": 3600,
    "id": 2643743,
    "name": "London",
    "cod": 200
}

def test_weather_tool_func():
    """Test that the weather_tool function has the correct attributes from the decorator."""
    assert hasattr(weather_tool, "name")
    assert weather_tool.name == "weather_tool"
    assert "location" in weather_tool.args

@patch('src.tools.weather.requests.get')
def test_weather_tool_successful_call(mock_get):
    """Test the weather_tool with a successful API call."""
    # Configure the mock to return a successful response
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_WEATHER_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Run the tool using invoke instead of direct calling
    result = weather_tool.invoke("London")
    
    # Assertions
    assert result["location"] == "London"
    assert result["country"] == "GB"
    assert result["weather"] == "overcast clouds"
    assert result["temperature"] == 15.5
    assert result["humidity"] == 71
    assert result["wind_speed"] == 3.6
    assert result["timestamp"] == 1682084645
    
    # Verify the API was called with the correct parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"]["q"] == "London"
    assert kwargs["params"]["appid"] == os.getenv("OPENWEATHER_API_KEY")
    assert kwargs["params"]["units"] == "metric"

@patch('src.tools.weather.requests.get')
def test_weather_tool_api_error(mock_get):
    """Test the weather_tool when the API returns an error."""
    # Configure the mock to raise a request exception
    mock_get.side_effect = Exception("API connection error")
    
    # Run the tool using invoke
    result = weather_tool.invoke("NonExistentCity")
    
    # Assertions
    assert "error" in result
    assert "API connection error" in result["error"]

@patch('src.tools.weather.requests.get')
def test_weather_tool_parse_error(mock_get):
    """Test the weather_tool when the response cannot be parsed correctly."""
    # Configure the mock to return an invalid response
    mock_response = MagicMock()
    mock_response.json.return_value = {"cod": 200}  # Missing required fields
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    
    # Run the tool using invoke
    result = weather_tool.invoke("London")
    
    # Assertions
    assert "error" in result
    assert "parse" in result["error"].lower() 