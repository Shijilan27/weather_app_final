from django.shortcuts import render
import json
import urllib.request
from datetime import datetime, timezone
import requests
import urllib.parse
import pytz
import os

def get_news(city, country_code):
    try:
        # Using NewsAPI to get local news
        news_api_key = os.environ.get("NEWS_API_KEY")  # Read from environment variable
        if not news_api_key:
            print("NEWS_API_KEY environment variable not set.")
            return None
        # Include both city and country in the search for more relevant results
        query = f"{city} {country_code}"
        encoded_query = urllib.parse.quote(query)
        news_url = f"https://newsapi.org/v2/everything?q={encoded_query}&sortBy=publishedAt&apiKey={news_api_key}&pageSize=5&language=en"
        news_response = requests.get(news_url)
        news_data = news_response.json()
        
        if news_response.status_code == 200 and news_data.get('articles'):
            # Filter out articles without images or descriptions
            valid_articles = [
                article for article in news_data['articles']
                if article.get('urlToImage') and article.get('description')
            ]
            return valid_articles[:5]  # Return top 5 valid news articles
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return None
    return None

def get_time_of_day(hour):
    if 6 <= hour < 11:
        return 'Morning'
    elif 11 <= hour < 16:
        return 'Afternoon'
    elif 16 <= hour < 19:
        return 'Evening'
    else:
        return 'Night'

def index(request):
    data = {}
    error_message = None
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')
    news_articles = None
    time_of_day = 'Day'
    
    if request.method == 'POST':
        city = request.POST['city']
        if city:
            try:
                openweather_api_key = os.environ.get("OPENWEATHER_API_KEY") # Read from environment variable
                if not openweather_api_key:
                    print("OPENWEATHER_API_KEY environment variable not set.")
                    error_message = "Weather API key not configured."
                    return render(request, 'index.html', {'error_message': error_message})

                encoded_city = urllib.parse.quote(city)
                res = urllib.request.urlopen(f'https://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={openweather_api_key}').read()
                json_data = json.loads(res)
                
                lat = json_data['coord']['lat']
                long = json_data['coord']['lon']

                timezonedb_api_key = os.environ.get("TIMEZONEDB_API_KEY") # Read from environment variable
                if not timezonedb_api_key:
                    print("TIMEZONEDB_API_KEY environment variable not set.")
                    error_message = "Timezone API key not configured."
                    return render(request, 'index.html', {'error_message': error_message})

                time_url = f"http://api.timezonedb.com/v2.1/get-time-zone?key={timezonedb_api_key}&format=json&by=position&lat={lat}&lng={long}"
                resp = requests.get(time_url)
                resp_json = resp.json()
                icon_code = json_data['weather'][0]['icon']
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                sunrise = json_data['sys']['sunrise']
                sunset = json_data['sys']['sunset']
                current_time = datetime.now(timezone.utc).timestamp() 

                is_daytime = sunrise <= current_time <= sunset
                day_or_night = "Day" if is_daytime else "Night"

                # Get news for the city
                news_articles = get_news(city, json_data['sys']['country'])

                # Get local time for city
                tz_name = resp_json.get('zoneName')
                if tz_name:
                    tz = pytz.timezone(tz_name)
                    local_dt = datetime.now(tz)
                    local_hour = local_dt.hour
                    time_of_day = get_time_of_day(local_hour)
                else:
                    # fallback: use UTC hour for time_of_day
                    utc_hour = datetime.utcnow().hour
                    time_of_day = get_time_of_day(utc_hour)

                data = {
                    'city': str(json_data['name']),
                    'country_code': str(json_data['sys']['country']),
                    'coordinate': str(json_data['coord']['lon'])+' N '+str(json_data['coord']['lat'])+' E',
                    'temp': str(int(json_data['main']['temp']) - int(273.15)) +' °C',
                    'pressure': str(json_data['main']['pressure'])+' '+'hPa',
                    'humidity': str(json_data['main']['humidity'])+' '+'%',
                    'icon_url': icon_url,
                    'desc': str(json_data['weather'][0]['description']),
                    'day_or_night': day_or_night,
                    'lat': lat,  # Add latitude for Google Maps
                    'lon': long,  # Add longitude for Google Maps
                    'rain_probability': str(json_data.get('rain', {}).get('1h', 0)) + '%' if 'rain' in json_data else '0%',  # Add rain probability
                    'feels_like': str(int(json_data['main']['feels_like']) - int(273.15)) + ' °C', # Add feels like temperature
                }
                date_time = resp_json.get("formatted")
                if date_time:
                    # Parse the datetime string from timezonedb.com
                    local_dt_obj = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
                    # Format date to dd-mm-yyyy
                    date = local_dt_obj.strftime('%d-%m-%Y')
                    # Format time to 12-hour clock with AM/PM
                    time = local_dt_obj.strftime('%I:%M:%S %p')
                else:
                    # Fallback to current UTC time if timezone API doesn't provide formatted time
                    date = datetime.now().strftime('%d-%m-%Y')
                    time = datetime.now().strftime('%I:%M:%S %p')

            except urllib.error.HTTPError as e:
                if e.code == 404:
                    error_message = "City not found. Please enter a valid city name."
                else:
                    error_message = "An error occurred while fetching weather data."
            except Exception as e:
                error_message = "An error occurred. Please try again."
        else:
            error_message = "City name cannot be empty"
            
    return render(request, 'index.html', {
        'data': data, 
        'error_message': error_message,
        'date': date,
        'time': time,
        'news_articles': news_articles,
        'google_maps_api_key': os.environ.get('GOOGLE_MAPS_API_KEY'),  # Read from environment variable
        'time_of_day': time_of_day
    })   