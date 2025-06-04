from django.shortcuts import render
import json
import urllib.request
from datetime import datetime, timezone
import requests
import urllib.parse
import pytz

def get_news(city, country_code):
    try:
        # Using NewsAPI to get local news
        news_api_key = "f1d407ba55d04b089e355373cf1708f5"  # Updated NewsAPI key
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
                encoded_city = urllib.parse.quote(city)
                res = urllib.request.urlopen('https://api.openweathermap.org/data/2.5/weather?q='+encoded_city+'&appid=4843294ed54d8db19afda2ecfd556d58').read()
                json_data = json.loads(res)
                api_key = 'GQjHMX4tvtHatHs08b3+EQ==XmNODG7RykC4hzJP'
                lat = json_data['coord']['lat']
                long = json_data['coord']['lon']
                time_url = "http://api.timezonedb.com/v2.1/get-time-zone?key=H3E525G4N9Q2&format=json&by=position&lat={}&lng={}".format(lat,long)
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
                }
                date_time = resp_json.get("formatted")
                date_time = str(date_time)
                date = date_time[:10]
                time = date_time[11:]

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
        'google_maps_api_key': 'AIzaSyBzdYVLbv2_z2OAm7cDaGPyRrkjXZteXWM',  # Updated Google Maps API key
        'time_of_day': time_of_day
    })   