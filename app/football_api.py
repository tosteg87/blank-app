import json
import logging
import csv
import requests
from redislite import Redis
from io import StringIO
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, filename="py_log.log", filemode="w", format="%(asctime)s %(levelname)s %(message)s")

base_api_url = "https://api.sstats.net"
api_key = "608sqlko14ddrypq"

redis_client = Redis('/tmp/redis.db')

payload={}
headers = {}

def get_countries():
    url = f"{base_api_url}/leagues"
    countries_response = get_api_data(url)
    
    countries = {}

    if countries_response['data']:
        for item in countries_response['data']:
            if item['country']['name'] in countries:
                countries[item['country']['name']].append({
                    'id': item['id'],
                    'name': item['name'],
                })
            else:
                countries[item['country']['name']] = []
                countries[item['country']['name']].append({
                    'id': item['id'],
                    'name': item['name'],
                })
    
    return countries

def get_leagues(country):
    countries = get_countries()
    
    return countries[country]

def get_teams(league):
    league_teams = {}
    all_teams = {}
    cached_teams = redis_client.get('teams')

    if cached_teams:
        all_teams = json.loads(cached_teams)
    
    url = f"{base_api_url}/games/season-table"
    params = {
        'league': league,
        'format':'csv',
        'fields': 'Rank,TeamName,TeamId',
        'orderField': 'Rank',
        'year': datetime.now().year
    }
    
    teams_response = get_api_data(url, params, 'csv', league)
    
    if teams_response:
        data = StringIO(teams_response)
        file_reader = csv.reader(data, delimiter=',')

        count = 0
    
        for row in file_reader:
            if count != 0:
                league_teams[row[2]] = row[1]
                all_teams[row[2]] = row[1]
            count += 1
            
    redis_client.setex('teams', 86400, json.dumps(all_teams))
    
    return league_teams

def get_team_name(team_id):
    cached_teams = redis_client.get('teams')
    teams = json.loads(cached_teams)

    if cached_teams:
        return teams[team_id]

    return []

def get_team_games(team_id):
    url = f"{base_api_url}/games/list"
    date_to = datetime.now() + timedelta(days=1)
    
    params = {
        'Year': datetime.now().year,
        'HomeTeam': team_id,
        'Upcoming': 'true',
        'To': f'{date_to.year}-{date_to.month}-{date_to.day}'
    }
    
    games_response = get_api_data(url, params, 'json', f'{url}-{team_id}')

    if games_response and games_response['count'] > 0:
        if games_response['data']:
            match = games_response['data'][0]
            match_date = match['date']
            match_team_name = match['homeTeam']['name']

            return {'team_name': match_team_name, 'match_date': match_date}

    return []

def get_api_data(api_url, params = None, format = 'json', cacheId = ''):
    #redis_client.flushall()
    cached_data = redis_client.get(api_url + cacheId)

    if cached_data:
        if format == 'json':
            data = json.loads(cached_data)
            return data
        else:
            return cached_data
    else:
        try:
            if params is None:
                params = {}
            
            params['apikey'] = api_key
            response = requests.request("GET", f"{api_url}", params=params, headers=headers, data=payload)

            response.raise_for_status()

            redis_client.setex(api_url + cacheId, 86400, response.text)

            if format == 'json':
                return response.json()
            else:
                return response.text

        except requests.RequestException as e:
            logging.error(e)
            return None
