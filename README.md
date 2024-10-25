# CFB Picker Data Gatherer

This application gathers comprehensive college football matchup data for AI model analysis. It features both a GUI and command-line interface for easy game selection and data collection.

## Features

- User-friendly GUI interface
- Fetches current week's college football matchups
- Gathers comprehensive data for selected matchups including:
  - Game information (teams, venue, date)
  - Weather conditions
  - Betting information:
    - Current game betting lines
    - Historical betting lines for both teams
    - Spread, over/under, moneyline odds
    - Line movement data
  - Pregame win probabilities
  - Advanced team statistics
  - Multiple rating systems:
    - SP+ ratings
    - FPI ratings
    - ELO ratings
    - SRS ratings
  - Team talent rankings
  - Historical matchup data
  - Team records and performance
  - Advanced box score metrics
  - Returning production metrics
- Progress tracking for data collection
- Secure API key management
- Data saved in structured JSON format

## Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Get an API key from [CollegeFootballData.com](https://collegefootballdata.com/)

## Usage

### GUI Version (Recommended)
Run the GUI version:
```bash
python cfb_picker_gui.py
```

The GUI provides:
- Easy game selection from a list
- Progress tracking
- Status updates
- Clean, modern interface

### Command Line Version
Run the command-line version:
```bash
python cfb_picker.py
```

## First Run

On first run, both versions will prompt you to enter your CFBD API key. The key will be saved locally in `config.json` for future use.

## Output

Both versions save data to a JSON file named `matchup_data_[away_team]_[home_team].json`. This comprehensive dataset contains:

### Game Information
- Basic game details (ID, date, venue, teams)
- Weather conditions
- Pregame win probabilities

### Betting Information
- Current game betting lines
- Historical betting lines for both teams
- Spread, over/under, moneyline odds
- Line movement data
- Opening and closing lines

### Team Data (for both home and away teams)
- Advanced season statistics
- Multiple rating systems (SP+, FPI, ELO, SRS)
- Team records
- Returning production metrics
- Historical betting performance

### Historical Data
- Head-to-head matchup history
- Advanced box score metrics
- Team talent rankings

This data can be used to train or feed into an AI model for making more informed game predictions.

## API Key Management

The application stores your API key securely in a local `config.json` file. The key is:
- Automatically loaded on startup
- Validated before use
- Persisted for future runs
- Never exposed in the code or output

If you need to update your API key, simply delete the `config.json` file and run the application again. You'll be prompted to enter a new key.
