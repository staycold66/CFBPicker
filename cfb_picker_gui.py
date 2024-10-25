import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
import threading
import json
import os
from typing import Dict, List, Any, Optional
import requests

# Create outputs directory if it doesn't exist
OUTPUTS_DIR = "outputs"
os.makedirs(OUTPUTS_DIR, exist_ok=True)

class CFBPickerGUI:
    def __init__(self):
        # Create main window
        self.root = ttk.Window(themename="darkly")
        self.root.title("CFB Picker")
        self.root.geometry("800x600")
        
        # Initialize API
        self.api = CFBDataAPI()
        self.games = []
        
        # Create GUI elements
        self.create_widgets()
        
        # Start with API key check
        self.root.after(100, self.check_api_key)

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=YES)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="College Football Game Picker (FBS Only)",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=10)

        # Games list frame
        games_frame = ttk.LabelFrame(main_frame, text="Available FBS Games", padding="10")
        games_frame.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Games listbox with scrollbar
        self.games_listbox = ttk.Treeview(
            games_frame,
            columns=("away", "home"),
            show="headings",
            height=10
        )
        self.games_listbox.heading("away", text="Away Team")
        self.games_listbox.heading("home", text="Home Team")
        self.games_listbox.pack(fill=BOTH, expand=YES, side=LEFT)

        scrollbar = ttk.Scrollbar(games_frame, orient=VERTICAL, command=self.games_listbox.yview)
        scrollbar.pack(fill=Y, side=RIGHT)
        self.games_listbox.configure(yscrollcommand=scrollbar.set)

        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=X, padx=5, pady=5)

        self.status_label = ttk.Label(status_frame, text="Initializing...", wraplength=700)
        self.status_label.pack(fill=X)

        self.progress_bar = ttk.Progressbar(
            status_frame,
            mode='determinate',
            length=200
        )

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        self.refresh_button = ttk.Button(
            button_frame,
            text="Refresh Games",
            command=self.refresh_games,
            style="primary.TButton"
        )
        self.refresh_button.pack(side=LEFT, padx=5)

        self.analyze_button = ttk.Button(
            button_frame,
            text="Analyze Selected Game",
            command=self.analyze_game,
            style="success.TButton"
        )
        self.analyze_button.pack(side=LEFT, padx=5)
        self.analyze_button.configure(state="disabled")

        # Week info label
        self.week_label = ttk.Label(
            main_frame,
            text="",
            font=("Helvetica", 10)
        )
        self.week_label.pack(pady=5)

    def check_api_key(self):
        """Check if API key exists and is valid"""
        self.status_label.config(text="Checking API key...")
        
        current_key = self.api.get_api_key()
        if current_key and self.api.test_api_key(current_key):
            self.refresh_games()
        else:
            self.show_api_key_dialog()

    def show_api_key_dialog(self):
        """Show dialog for API key input"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("API Key Required")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text="Please enter your CFBD API key\nGet one from collegefootballdata.com",
            justify=CENTER
        ).pack(pady=20)

        api_key_var = tk.StringVar()
        api_key_entry = ttk.Entry(dialog, textvariable=api_key_var, width=40)
        api_key_entry.pack(pady=10)

        def submit_key():
            key = api_key_var.get().strip()
            if self.api.test_api_key(key):
                self.api.set_api_key(key)
                dialog.destroy()
                self.refresh_games()
            else:
                ttk.Label(
                    dialog,
                    text="Invalid API key. Please try again.",
                    foreground="red"
                ).pack(pady=5)

        ttk.Button(
            dialog,
            text="Submit",
            command=submit_key,
            style="primary.TButton"
        ).pack(pady=10)

    def refresh_games(self):
        """Refresh the games list"""
        self.status_label.config(text="Fetching current week's FBS games...")
        self.refresh_button.configure(state="disabled")
        self.analyze_button.configure(state="disabled")
        
        def fetch():
            try:
                # Get current week
                current = self.api.get_current_week()
                self.root.after(0, lambda: self.week_label.config(
                    text=f"Week {current['week']}, {current['year']} ({current['seasonType']})"
                ))
                
                # Get games
                self.games = self.api.get_games(
                    current['year'],
                    current['week'],
                    current['seasonType']
                )
                
                # Update UI in main thread
                self.root.after(0, self.update_games_list)
                self.root.after(0, lambda: self.status_label.config(text="Ready"))
                self.root.after(0, lambda: self.refresh_button.configure(state="normal"))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Error fetching games: {str(e)}"
                ))
                self.root.after(0, lambda: self.refresh_button.configure(state="normal"))

        threading.Thread(target=fetch, daemon=True).start()

    def update_games_list(self):
        """Update the games listbox"""
        # Clear current items
        for item in self.games_listbox.get_children():
            self.games_listbox.delete(item)
        
        # Add new items
        for game in self.games:
            self.games_listbox.insert(
                "",
                END,
                values=(game['away_team'], game['home_team'])
            )
        
        # Enable analyze button when item is selected
        def on_select(event):
            self.analyze_button.configure(
                state="normal" if self.games_listbox.selection() else "disabled"
            )
        
        self.games_listbox.bind('<<TreeviewSelect>>', on_select)

    def analyze_game(self):
        """Analyze the selected game"""
        selection = self.games_listbox.selection()
        if not selection:
            return
        
        # Get selected game
        item = self.games_listbox.item(selection[0])
        away_team, home_team = item['values']
        game = next(g for g in self.games 
                   if g['away_team'] == away_team and g['home_team'] == home_team)
        
        # Show progress bar
        self.progress_bar.pack(pady=10)
        self.progress_bar['value'] = 0
        self.analyze_button.configure(state="disabled")
        self.refresh_button.configure(state="disabled")
        
        def analyze():
            try:
                # Get matchup data
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Analyzing {away_team} @ {home_team}..."
                ))
                
                def update_progress(text, progress):
                    self.root.after(0, lambda: self.status_label.config(text=text))
                    self.root.after(0, lambda: self.progress_bar.configure(value=progress))
                
                # Get comprehensive matchup data with progress updates
                matchup_data = self.api.get_matchup_data(game, update_progress)
                
                # Save to file in outputs directory
                filename = os.path.join(
                    OUTPUTS_DIR,
                    f"matchup_data_{away_team.replace(' ', '_')}_{home_team.replace(' ', '_')}.json"
                )
                with open(filename, 'w') as f:
                    json.dump(matchup_data, f, indent=2)
                
                # Update UI
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Analysis complete! Data saved to {filename}"
                ))
                self.root.after(0, lambda: self.progress_bar.pack_forget())
                self.root.after(0, lambda: self.analyze_button.configure(state="normal"))
                self.root.after(0, lambda: self.refresh_button.configure(state="normal"))
            
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Error analyzing game: {str(e)}"
                ))
                self.root.after(0, lambda: self.progress_bar.pack_forget())
                self.root.after(0, lambda: self.analyze_button.configure(state="normal"))
                self.root.after(0, lambda: self.refresh_button.configure(state="normal"))

        threading.Thread(target=analyze, daemon=True).start()

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
            
            # Special handling for certain endpoints that should return full lists
            list_endpoints = {'lines', 'calendar', 'teams/matchup'}
            if endpoint in list_endpoints:
                return data
            
            # For other endpoints, return first item if it's a list
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except Exception as e:
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
                except (KeyError, ValueError):
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
        """Get FBS games for specified week"""
        try:
            response = requests.get(
                f"{self.base_url}/games",
                headers=self.headers,
                params={
                    "year": year,
                    "week": week,
                    "seasonType": season_type,
                    "division": "fbs"  # Filter for FBS games only
                }
            )
            return response.json()
        except Exception as e:
            print(f"Warning: Failed to get games: {str(e)}")
            return []

    def get_pregame_win_prob(self, game_id: int, year: int, season_type: str) -> Optional[Dict[str, Any]]:
        """Get pregame win probability for a specific game"""
        try:
            response = requests.get(
                f"{self.base_url}/metrics/wp/pregame",
                headers=self.headers,
                params={
                    "year": year,
                    "seasonType": season_type,
                    "gameId": game_id
                }
            )
            data = response.json()
            if isinstance(data, list):
                # Find the matching game in the response
                for game in data:
                    if game.get('gameId') == game_id:
                        return game
            return None
        except Exception as e:
            print(f"Warning: Failed to get pregame win probability: {str(e)}")
            return None

    def get_betting_lines_by_game(self, game_id: int, year: int) -> Optional[List[Dict[str, Any]]]:
        """Get betting lines for a specific game"""
        try:
            response = requests.get(
                f"{self.base_url}/lines",
                headers=self.headers,
                params={
                    "gameId": game_id,
                    "year": year
                }
            )
            data = response.json()
            # Filter to ensure we only get data for our specific game
            if isinstance(data, list):
                return [line for line in data if line.get('id') == game_id]
            return None
        except Exception as e:
            print(f"Warning: Failed to get betting lines: {str(e)}")
            return None

    def get_historical_betting_lines(self, team: str, year: int) -> Optional[List[Dict[str, Any]]]:
        """Get historical betting lines for a team's season"""
        try:
            response = requests.get(
                f"{self.base_url}/lines",
                headers=self.headers,
                params={
                    "year": year,
                    "team": team
                }
            )
            data = response.json()
            if isinstance(data, list):
                # Sort by week for better organization
                return sorted(data, key=lambda x: x.get('week', 0))
            return None
        except Exception as e:
            print(f"Warning: Failed to get historical betting lines: {str(e)}")
            return None

    def get_talent_rankings(self, year: int, teams: List[str]) -> Dict[str, Any]:
        """Get talent rankings for specific teams"""
        try:
            response = requests.get(
                f"{self.base_url}/talent",
                headers=self.headers,
                params={"year": year}
            )
            data = response.json()
            if isinstance(data, list):
                # Filter for our teams and create a dictionary
                team_talent = {}
                for team in teams:
                    team_data = next((item for item in data if item.get('school') == team), None)
                    if team_data:
                        team_talent[team] = {
                            "year": team_data.get('year'),
                            "talent": team_data.get('talent')
                        }
                return team_talent
            return None
        except Exception as e:
            print(f"Warning: Failed to get talent rankings: {str(e)}")
            return None

    def get_matchup_data(self, game: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Get comprehensive matchup data with progress updates"""
        year = game["season"]
        home_team = game["home_team"]
        away_team = game["away_team"]
        game_id = game["id"]
        season_type = game.get("season_type", "regular")
        
        if progress_callback:
            progress_callback("Getting betting lines data...", 10)
        
        # Get current game betting lines
        betting = self.get_betting_lines_by_game(game_id, year)
        
        # Get historical betting lines for both teams
        if progress_callback:
            progress_callback("Getting historical betting data...", 20)
        
        home_betting_history = self.get_historical_betting_lines(home_team, year)
        away_betting_history = self.get_historical_betting_lines(away_team, year)
        
        if progress_callback:
            progress_callback("Getting pregame win probability data...", 30)
        
        pregame_wp = self.get_pregame_win_prob(game_id, year, season_type)
        
        if progress_callback:
            progress_callback("Getting team performance metrics...", 45)
        
        home_stats = self.safe_api_call("stats/season/advanced", {
            "year": year,
            "team": home_team,
            "excludeGarbageTime": True
        })
        away_stats = self.safe_api_call("stats/season/advanced", {
            "year": year,
            "team": away_team,
            "excludeGarbageTime": True
        })
        
        if progress_callback:
            progress_callback("Getting advanced ratings...", 60)
        
        home_sp = self.safe_api_call("ratings/sp", {"year": year, "team": home_team})
        away_sp = self.safe_api_call("ratings/sp", {"year": year, "team": away_team})
        home_fpi = self.safe_api_call("ratings/fpi", {"year": year, "team": home_team})
        away_fpi = self.safe_api_call("ratings/fpi", {"year": year, "team": away_team})
        home_elo = self.safe_api_call("ratings/elo", {"year": year, "team": home_team})
        away_elo = self.safe_api_call("ratings/elo", {"year": year, "team": away_team})
        home_srs = self.safe_api_call("ratings/srs", {"year": year, "team": home_team})
        away_srs = self.safe_api_call("ratings/srs", {"year": year, "team": away_team})
        
        if progress_callback:
            progress_callback("Getting team records and talent data...", 75)
        
        home_record = self.safe_api_call("records", {"year": year, "team": home_team})
        away_record = self.safe_api_call("records", {"year": year, "team": away_team})
        talent_rankings = self.get_talent_rankings(year, [home_team, away_team])
        
        if progress_callback:
            progress_callback("Getting returning production metrics...", 85)
        
        home_returning = self.safe_api_call("player/returning", {"year": year, "team": home_team})
        away_returning = self.safe_api_call("player/returning", {"year": year, "team": away_team})
        
        if progress_callback:
            progress_callback("Getting historical matchup data...", 95)
        
        matchup_history = self.safe_api_call("teams/matchup", {"team1": home_team, "team2": away_team})
        
        if progress_callback:
            progress_callback("Compiling data...", 100)
        
        return {
            "game_info": {
                "id": game_id,
                "start_date": game["start_date"],
                "venue": game["venue"],
                "home_team": home_team,
                "away_team": away_team,
                "home_conference": game["home_conference"],
                "away_conference": game["away_conference"],
                "season_type": season_type,
                "pregame_win_probability": pregame_wp
            },
            "betting": {
                "current_lines": betting[0] if betting else None,
                "home_team_betting_history": home_betting_history,
                "away_team_betting_history": away_betting_history
            },
            "matchup_history": matchup_history,
            "home_team_data": {
                "season_stats": home_stats,
                "sp_ratings": home_sp,
                "fpi_ratings": home_fpi,
                "elo_ratings": home_elo,
                "srs_ratings": home_srs,
                "record": home_record,
                "returning_production": home_returning,
                "talent_ranking": talent_rankings.get(home_team) if talent_rankings else None
            },
            "away_team_data": {
                "season_stats": away_stats,
                "sp_ratings": away_sp,
                "fpi_ratings": away_fpi,
                "elo_ratings": away_elo,
                "srs_ratings": away_srs,
                "record": away_record,
                "returning_production": away_returning,
                "talent_ranking": talent_rankings.get(away_team) if talent_rankings else None
            }
        }

def main():
    app = CFBPickerGUI()
    app.root.mainloop()

if __name__ == "__main__":
    main()
