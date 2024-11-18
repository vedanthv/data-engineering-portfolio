import streamlit as st
import pandas as pd
import requests

# FastAPI URLs (Update with your FastAPI backend URLs)
BASE_URL = "http://ec2-3-109-101-141.ap-south-1.compute.amazonaws.com:8000/team-results"
LOG_URL = "http://ec2-3-109-101-141.ap-south-1.compute.amazonaws.com:8000/log-click"
PLAYERS_URL = "http://ec2-3-109-101-141.ap-south-1.compute.amazonaws.com:8000/players"  # Endpoint for player details

# Predefined list of teams (both abbreviations and full names for easy lookup)
team_abbr_dict = {
    "RCB": "Royal Challengers Bangalore",
    "MI": "Mumbai Indians",
    "DC": "Delhi Capitals",
    "CSK": "Chennai Super Kings",
    "KKR": "Kolkata Knight Riders",
    "PBKS": "Punjab Kings",
    "RR": "Rajasthan Royals",
    "SRH": "Sunrisers Hyderabad",
    "GT": "Gujarat Titans",
    "LSG": "Lucknow Super Giants"
}

# Function to fetch data from FastAPI (team results)
def fetch_data(team_name: str):
    try:
        response = requests.get(f"{BASE_URL}?team1={team_name}")
        if response.status_code == 200:
            return response.json()  # Return the data as JSON
        else:
            return []  # Return empty list if data fetch fails
    except Exception as e:
        return []  # Return empty list in case of an error

# Function to fetch player details from FastAPI
def fetch_players():
    try:
        response = requests.get(PLAYERS_URL)
        if response.status_code == 200:
            return response.json()  # Return the data as JSON
        else:
            return []  # Return empty list if data fetch fails
    except Exception as e:
        return []  # Return empty list in case of an error

# Function to log button click to FastAPI
def log_click(team_name: str, action: str):
    # Get user IP address
    ip_response = requests.get("https://api64.ipify.org?format=json")
    ip_address = ip_response.json().get("ip")

    # Send log to FastAPI backend
    log_payload = {
        "ip_address": ip_address,
        "team_name": team_name,
        "action": action
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(LOG_URL, json=log_payload, headers=headers)
    # Handle response
    if response.status_code == 200:
        st.success(f"Logged {action} for team {team_name}")

# Streamlit UI setup
st.set_page_config(page_title="Realtime Cricket Analytics", layout="wide")

# Set option to suppress warnings
st.set_option('client.showErrorDetails', False)  # Disable error details in the app

# Add custom dark mode style with media queries for responsiveness
st.markdown(
    """
    <style>
    body {
        background-color: #121212;
        color: #E0E0E0;
    }
    .sidebar .sidebar-content {
        background-color: #181818;
    }
    .stButton>button {
        background-color: #6200ee;
        color: white;
        border-radius: 8px;
        padding: 12px 30px;
        font-size: 16px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        border: none;
    }
    .stButton>button:hover {
        background-color: #3700b3;
    }
    .table-container {
        padding: 20px;
        background-color: #1f1f1f;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-top: 20px;
    }
    .table th {
        background-color: #333333;
        color: #ffffff;
    }
    .table td {
        color: #E0E0E0;
    }
    .header {
        color: #ffffff;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 20px;
    }
    .subheader {
        color: #888888;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 20px;
    }
    .section-header {
        color: #ffffff;
        font-size: 2em;
        margin-top: 40px;
        text-align: center;
    }
    
    /* Responsive Table */
    .streamlit-expanderHeader {
        background-color: #333333 !important;
    }

    /* Adjust layout for mobile screens */
    @media only screen and (max-width: 768px) {
        .header {
            font-size: 2em;
        }
        .subheader {
            font-size: 1em;
        }
        .stButton>button {
            font-size: 14px;
            padding: 10px 20px;
        }
        .stDataFrame {
            overflow-x: auto;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and header with banner image
st.image("https://preview.redd.it/poster-for-ipl-2024-auction-v0-sfl76d4g077c1.png?width=640&crop=smart&auto=webp&s=66700b2badaeac704850afef4a6bfc49526fb11c", use_container_width=True)  # Banner image URL
st.markdown('<p class="header">Realtime Cricket Analytics</p>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Cricket Stats and Numbers in split seconds at your fingertips :)</p>', unsafe_allow_html=True)

# Create navigation tabs
tab = st.radio("Select an option", ("Live Match Statistics", "Player Information"))

# Display content based on selected tab
if tab == "Live Match Statistics":
    st.markdown("### Live Match Details By Team",unsafe_allow_html=True)
    # Input box for team name with suggestions
    team_name_input = st.text_input("Enter Team Name (e.g., RCB or Royal Challengers Bangalore)", "")

    # Display suggestions based on user input (case-insensitive)
    if team_name_input:
        team_name_input_upper = team_name_input.strip().upper()
        team_name_full = team_abbr_dict.get(team_name_input_upper, None)
        
        if team_name_full:
            team_name = team_name_full
        else:
            suggestions = [team for abbr, team in team_abbr_dict.items() if team_name_input_upper in team.upper()]
            if suggestions:
                team_name = st.selectbox("Choose a team from the suggestions", suggestions)
            else:
                st.warning("No team matches the input. Please type again.")
    else:
        team_name = ""


    # Button to fetch team data
    with st.spinner('Preparing the data...'):
        if st.button("Fetch IPL Live Scores", key="fetch_data", help="Click to load live scores") and team_name:
            log_click(team_name, "Fetch IPL Live Scores")  # Log the click event
            data = fetch_data(team_name)

            if data:
                df = pd.DataFrame(data)
                if 'team1' in df.columns:
                    cols = ['team1'] + [col for col in df.columns if col != 'team1']
                    df = df[cols]
                st.markdown(f"### Total Records: {len(df)}")
                st.markdown("### Showing IPL Data for Team: " + team_name)
                st.markdown('<div class="table-container">', unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("No data found for the given team. Please check the team name or try again.")

elif tab == "Player Information":
    st.markdown("### Player Information", unsafe_allow_html=True)

    # New section for Player Details with a separate header
    with st.spinner('Preparing player data...'):
        if st.button("Fetch Player Details", key="fetch_players", help="Click to load player details"):
            team_name = "Click Log for Player Details"
            log_click(team_name, "Fetch Player Details")  # Log the click event for players
            player_data = fetch_players()

            if player_data:
                df_players = pd.DataFrame(player_data)
                st.markdown('<p class="section-header">Player Details</p>', unsafe_allow_html=True)  # New header for players
                st.markdown(f"### Total Players: {len(df_players)}")
                st.markdown("### Showing Player Details")
                st.markdown('<div class="table-container">', unsafe_allow_html=True)
                st.dataframe(df_players, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("No player data found. Please try again later.")
