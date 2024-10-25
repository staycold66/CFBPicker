import requests
import json
from datetime import datetime
import os
from typing import Dict, List, Any, Optional

class CFBDataAPI:
    def __init__(self):
        self.base_url = "https://api.collegefootballdata.com"
        self.config_file = "config.json"
        self.headers = {
            "Authorization": f"Bearer {self.get_api_key()}",
            "accept": "application/json"
        }

    def get_api_key(self) -> str:
        """Get API key from config file or environment variable"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('api_key', '')
        return os.getenv('CFBD_API_KEY', '')

    def set_api_key(self, api_key: str) -> None:
        """Save API key to config file"""
        config = {'api_key': api_key}
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        self.headers["Authorization"] = f"Bearer {api_key}"
        print("API key saved successfully!")

    def test_api_key(self, api_key: str) -> bool:
        """Test if API key is valid"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json"
        }
        try:
            response = requests.get(
                f"{self.base_url}/teams/fbs",
                headers=headers
            )
            return response.status_code == 200
        except:
            return False

    def safe_api_call(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """Make a safe API call with error handling"""
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params
            )
            data = response.json()
            # Only return first item if it's a list and the endpoint isn't 'calendar'
            if isinstance(data, list) and endpoint != 'calendar' and len(data) > 0:
                return data[0]
            return data
        except (IndexError, KeyError, requests.RequestException) as e:
            print(f"Warning: Failed to fetch data from {endpoint}: {str(e)}")
            return None

    def get_current_week(self) -> Dict[str, Any]:
        """Get the current week information"""
        year = datetime.now().year
        try:
            response = requests.get(
                f"{self.base_url}/calendar",
                headers=self.headers,
                params={"year": year}
            )
            calendar = response.json()
            
            if not calendar or not isinstance(calendar, list):
                return {"year": year, "week": 1, "seasonType": "regular"}
            
            now = datetime.now()
            for week in calendar:
                try:
                    start = datetime.strptime(week["firstGameStart"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    end = datetime.strptime(week["lastGameStart"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    if start <= now <= end:
                        return {
                            "year": year,
                            "week": week["week"],
                            "seasonType": week["seasonType"]
                        }
                except (KeyError, ValueError) as e:
                    continue
            
            # If we're before the season starts, return first week
            first_week = calendar[0]
            first_start = datetime.strptime(first_week["firstGameStart"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if now < first_start:
                return {
                    "year": year,
                    "week": first_week["week"],
                    "seasonType": first_week["seasonType"]
                }
            
            # If we're after the season ends, return last week
            last_week = calendar[-1]
            return {
                "year": year,
                "week": last_week["week"],
                "seasonType": last_week["seasonType"]
            }
            
        except Exception as e:
            print(f"Warning: Failed to get calendar data: {str(e)}")
            return {"year": year, "week": 1, "seasonType": "regular"}

    def get_games(self, year: int, week: int, season_type: str) -> List[Dict[str, Any]]:
        """Get games for specified week"""
        try:
            response = requests.get(
                f"{self.base_url}/games",
                headers=self.headers,
                params={
                    "year": year,
                    "week": week,
                    "seasonType": season_type
                }
            )
            return response.json()
        except Exception as e:
            print(f"Warning: Failed to get games: {str(e)}")
            return []

    def get_team_records(self, team: str, year: int) -> Optional[Dict[str, Any]]:
        """Get team's season records"""
        return self.safe_api_call("records", {
            "year": year,
            "team": team
        })

    def get_team_talent(self, year: int) -> Optional[Dict[str, Any]]:
        """Get team talent composite rankings"""
        return self.safe_api_call("talent", {
            "year": year
        })

    def get_returning_production(self, team: str, year: int) -> Optional[Dict[str, Any]]:
        """Get team's returning production metrics"""
        return self.safe_api_call("player/returning", {
            "year": year,
            "team": team
        })

    def get_fpi_ratings(self, team: str, year: int) -> Optional[Dict[str, Any]]:
        """Get team's FPI ratings"""
        return self.safe_api_call("ratings/fpi", {
            "year": year,
            "team": team
        })

    def get_elo_ratings(self, team: str, year: int) -> Optional[Dict[str, Any]]:
        """Get team's ELO ratings"""
        return self.safe_api_call("ratings/elo", {
            "year": year,
            "team": team
        })

    def get_srs_ratings(self, team: str, year: int) -> Optional[Dict[str, Any]]:
        """Get team's SRS ratings"""
        return self.safe_api_call("ratings/srs", {
            "year": year,
            "team": team
        })

    def get_pregame_win_prob(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get pregame win probability"""
        return self.safe_api_call("metrics/wp/pregame", {
            "gameId": game_id
        })

    def get_weather(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get game weather information"""
        return self.safe_api_call("games/weather", {
            "gameId": game_id
        })

    def get_matchup_history(self, team1: str, team2: str) -> Optional[Dict[str, Any]]:
        """Get historical matchup data"""
        return self.safe_api_call("teams/matchup", {
            "team1": team1,
            "team2": team2
        })

    def get_advanced_box_score(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get advanced box score metrics"""
        return self.safe_api_call("game/box/advanced", {
            "gameId": game_id
        })

    def get_betting_lines(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get betting lines for a game"""
        return self.safe_api_call("lines", {
            "gameId": game_id
        })

    def get_team_season_stats(self, team: str, year: int) -> Optional[Dict[str, Any]]:
        """Get team's season statistics"""
        return self.safe_api_call("stats/season/advanced", {
            "year": year,
            "team": team
        })

    def get_sp_ratings(self, team: str, year: int) -> Optional[Dict[str, Any]]:
        """Get team's SP+ ratings"""
        return self.safe_api_call("ratings/sp", {
            "year": year,
            "team": team
        })

    def get_matchup_data(self, game: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive matchup data"""
        year = game["season"]
        home_team = game["home_team"]
        away_team = game["away_team"]
        game_id = game["id"]

        print(f"\nGathering comprehensive data for {away_team} @ {home_team}...")
        
        # Basic game info and betting
        print("Retrieving betting lines and weather data...")
        betting = self.get_betting_lines(game_id)
        weather = self.get_weather(game_id)
        pregame_wp = self.get_pregame_win_prob(game_id)
        
        # Team performance metrics
        print("Retrieving team performance metrics...")
        home_stats = self.get_team_season_stats(home_team, year)
        away_stats = self.get_team_season_stats(away_team, year)
        
        # Advanced ratings
        print("Retrieving advanced ratings...")
        home_sp = self.get_sp_ratings(home_team, year)
        away_sp = self.get_sp_ratings(away_team, year)
        home_fpi = self.get_fpi_ratings(home_team, year)
        away_fpi = self.get_fpi_ratings(away_team, year)
        home_elo = self.get_elo_ratings(home_team, year)
        away_elo = self.get_elo_ratings(away_team, year)
        home_srs = self.get_srs_ratings(home_team, year)
        away_srs = self.get_srs_ratings(away_team, year)
        
        # Team records and talent
        print("Retrieving team records and talent data...")
        home_record = self.get_team_records(home_team, year)
        away_record = self.get_team_records(away_team, year)
        talent_rankings = self.get_team_talent(year)
        
        # Returning production
        print("Retrieving returning production metrics...")
        home_returning = self.get_returning_production(home_team, year)
        away_returning = self.get_returning_production(away_team, year)
        
        # Historical matchup and advanced stats
        print("Retrieving historical matchup data and advanced metrics...")
        matchup_history = self.get_matchup_history(home_team, away_team)
        advanced_box = self.get_advanced_box_score(game_id)
        
        return {
            "game_info": {
                "id": game_id,
                "start_date": game["start_date"],
                "venue": game["venue"],
                "home_team": home_team,
                "away_team": away_team,
                "home_conference": game["home_conference"],
                "away_conference": game["away_conference"],
                "weather": weather,
                "pregame_win_probability": pregame_wp
            },
            "betting": betting,
            "matchup_history": matchup_history,
            "advanced_box_score": advanced_box,
            "home_team_data": {
                "season_stats": home_stats,
                "sp_ratings": home_sp,
                "fpi_ratings": home_fpi,
                "elo_ratings": home_elo,
                "srs_ratings": home_srs,
                "record": home_record,
                "returning_production": home_returning
            },
            "away_team_data": {
                "season_stats": away_stats,
                "sp_ratings": away_sp,
                "fpi_ratings": away_fpi,
                "elo_ratings": away_elo,
                "srs_ratings": away_srs,
                "record": away_record,
                "returning_production": away_returning
            },
            "talent_rankings": talent_rankings
        }

def display_games(games: List[Dict[str, Any]]) -> None:
    """Display available games"""
    print("\nAvailable Games:")
    print("-" * 60)
    for i, game in enumerate(games, 1):
        print(f"{i}. {game['away_team']} @ {game['home_team']}")
    print("-" * 60)

def save_matchup_data(data: Dict[str, Any], filename: str) -> None:
    """Save matchup data to file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def setup_api_key() -> CFBDataAPI:
    """Setup API key if not already configured"""
    api = CFBDataAPI()
    
    # Check if API key exists and is valid
    current_key = api.get_api_key()
    if current_key and api.test_api_key(current_key):
        return api
    
    # If no valid key, prompt for one
    while True:
        print("\nCFBD API key not found or invalid.")
        print("You can get an API key from https://collegefootballdata.com/")
        api_key = input("Please enter your CFBD API key: ").strip()
        
        if api.test_api_key(api_key):
            api.set_api_key(api_key)
            return api
        else:
            print("Invalid API key. Please try again.")

def main():
    # Setup API key if needed
    api = setup_api_key()
    
    # Get current week
    current = api.get_current_week()
    print(f"\nGetting games for Week {current['week']}, {current['year']}")
    
    # Get games for current week
    games = api.get_games(current['year'], current['week'], current['seasonType'])
    
    if not games:
        print("No games found for the current week.")
        return
    
    # Display games
    display_games(games)
    
    # Get user selection
    while True:
        try:
            selection = int(input("\nSelect a game number (or 0 to exit): "))
            if selection == 0:
                return
            if 1 <= selection <= len(games):
                break
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Get selected game
    selected_game = games[selection - 1]
    
    # Get comprehensive matchup data
    matchup_data = api.get_matchup_data(selected_game)
    
    # Save to file
    filename = f"matchup_data_{selected_game['away_team'].replace(' ', '_')}_{selected_game['home_team'].replace(' ', '_')}.json"
    save_matchup_data(matchup_data, filename)
    print(f"\nComprehensive matchup data saved to {filename}")

if __name__ == "__main__":
    main()
