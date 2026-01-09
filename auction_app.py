import streamlit as st
import pandas as pd
import random

# --- Page Configuration ---
st.set_page_config(page_title="Cricket Auction Dashboard", layout="wide")

# --- Session State Initialization ---
# We use session_state to keep data alive as the user interacts with the app
if 'teams' not in st.session_state:
    st.session_state['teams'] = []  # List of team names
if 'team_stats' not in st.session_state:
    st.session_state['team_stats'] = {} # Dictionary to store players and spent money
if 'players' not in st.session_state:
    st.session_state['players'] = [] # The pool of players to be auctioned
if 'sold_players' not in st.session_state:
    st.session_state['sold_players'] = []
if 'current_player' not in st.session_state:
    st.session_state['current_player'] = None

# --- Helper Functions ---
def add_team(name, budget):
    if name and name not in st.session_state['teams']:
        st.session_state['teams'].append(name)
        st.session_state['team_stats'][name] = {'budget': budget, 'spent': 0, 'players': []}
        return True
    return False

def add_player(name, role):
    st.session_state['players'].append({'name': name, 'role': role, 'status': 'Unsold'})

def get_random_player():
    unsold = [p for p in st.session_state['players'] if p['status'] == 'Unsold']
    if unsold:
        return random.choice(unsold)
    return None

def sell_player(player, team_name, price):
    # Update player status
    player['status'] = 'Sold'
    player['sold_to'] = team_name
    player['price'] = price
    
    # Update team stats
    st.session_state['team_stats'][team_name]['spent'] += price
    st.session_state['team_stats'][team_name]['players'].append(player)
    st.session_state['sold_players'].append(player)
    
    # Clear current player to fetch a new one next time
    st.session_state['current_player'] = None

def remove_player(name):
    st.session_state['players'] = [p for p in st.session_state['players'] if p['name'] != name]

def unsell_player(player_name):
    # Find player
    player = next((p for p in st.session_state['players'] if p['name'] == player_name), None)
    if player and player['status'] == 'Sold':
        team_name = player['sold_to']
        price = player['price']
        
        # Refund team
        st.session_state['team_stats'][team_name]['spent'] -= price
        # Remove from team's player list
        st.session_state['team_stats'][team_name]['players'] = [
            p for p in st.session_state['team_stats'][team_name]['players'] 
            if p['name'] != player_name
        ]
        
        # Remove from sold_players list
        st.session_state['sold_players'] = [
            p for p in st.session_state['sold_players'] 
            if p['name'] != player_name
        ]
        
        # Reset player status
        player['status'] = 'Unsold'
        player['sold_to'] = None
        player['price'] = None
        return True
    return False

# --- UI Layout ---

st.title("🏏 Cricket Team Auction Board")

# Create Tabs for different stages of the auction
tab1, tab2, tab3 = st.tabs(["1. Setup", "2. Auction Room", "3. Team Views"])

# --- TAB 1: SETUP ---
with tab1:
    st.header("Step 1: Configure Auction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add Teams")
        new_team = st.text_input("Team Name")
        team_budget = st.number_input("Team Budget (Points/Currency)", min_value=1000, value=10000, step=500)
        if st.button("Add Team"):
            if add_team(new_team, team_budget):
                st.success(f"Added {new_team}")
            else:
                st.error("Team already exists or name is empty.")
        
        # Display current teams
        if st.session_state['teams']:
            st.write("### Registered Teams")
            st.table(pd.DataFrame([
                {'Team': k, 'Budget': v['budget']} 
                for k, v in st.session_state['team_stats'].items()
            ]))

    with col2:
        st.subheader("Add Player Pool")
        p_name = st.text_input("Player Name")
        p_role = st.selectbox("Role", ["Batsman", "Bowler", "All-Rounder", "Wicket Keeper"])
        if st.button("Add Player"):
            add_player(p_name, p_role)
            st.success(f"Added {p_name} ({p_role})")
        
        st.write("---")
        
        # Manage Pool Section
        st.subheader("Manage Pool")
        unsold_for_removal = [p['name'] for p in st.session_state['players'] if p['status'] == 'Unsold']
        if unsold_for_removal:
            p_to_remove = st.selectbox("Select Player to Remove", unsold_for_removal)
            if st.button("Remove Player"):
                remove_player(p_to_remove)
                st.success(f"Removed {p_to_remove}")
                st.rerun()
        else:
            st.info("No unsold players to remove.")

        # Display pool stats
        st.info(f"Total Players in Pool: {len(st.session_state['players'])}")
        
        if st.session_state['players']:
            st.write("### Player Pool")
            # Filter to show only unsold players or all players? 
            # The request asked for "existing players pool", usually implies available players.
            # But let's show all and their status for clarity, or just the list.
            # Let's show a dataframe of the players list.
            st.dataframe(pd.DataFrame(st.session_state['players']))

# --- TAB 2: AUCTION ROOM ---
with tab2:
    st.header("🔨 The Auction Floor")
    
    if not st.session_state['teams']:
        st.warning("Please add teams in the Setup tab first.")
    elif not st.session_state['players']:
        st.warning("Please add players in the Setup tab first.")
    else:
        # Start/Next Button
        col_act, col_info = st.columns([1, 2])
        
        with col_act:
            if st.session_state['current_player'] is None:
                # Get list of unsold players
                unsold_players = [p for p in st.session_state['players'] if p['status'] == 'Unsold']
                
                if not unsold_players:
                    st.balloons()
                    st.success("Auction Complete! No more unsold players.")
                else:
                    # Create a list of names for the dropdown
                    player_options = [f"{p['name']} ({p['role']})" for p in unsold_players]
                    selected_option = st.selectbox("Select Player to Auction", player_options)
                    
                    col_select, col_remove = st.columns([3, 1])
                    with col_select:
                        if st.button("Bring to Auction", type="primary", use_container_width=True):
                            # Find the selected player object
                            selected_index = player_options.index(selected_option)
                            st.session_state['current_player'] = unsold_players[selected_index]
                            st.rerun()
                    with col_remove:
                        if st.button("Delete from Pool", type="secondary", use_container_width=True):
                             # Find the selected player object to remove
                            selected_index = player_options.index(selected_option)
                            player_to_remove = unsold_players[selected_index]
                            remove_player(player_to_remove['name'])
                            st.success(f"Removed {player_to_remove['name']}")
                            st.rerun()
        
        # Display Current Player Card
        if st.session_state['current_player']:
            cp = st.session_state['current_player']
            
            # A nice card UI
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #4CAF50;">
                    <h2 style="color: #333;">{cp['name']}</h2>
                    <h4 style="color: #666;">{cp['role']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
            st.write("") # Spacer
            
            # Bidding Controls
            st.subheader("Place Winning Bid")
            
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                winner = st.selectbox("Winning Team", st.session_state['teams'])
            with b_col2:
                # Calculate max bid possible for this team
                current_budget = st.session_state['team_stats'][winner]['budget']
                spent = st.session_state['team_stats'][winner]['spent']
                remaining = current_budget - spent
                
                bid_price = st.number_input("Winning Price", min_value=0, max_value=remaining, step=100)
                st.caption(f"Remaining Purse: {remaining}")
            
            with b_col3:
                st.write("") # Alignment spacer
                st.write("")
                if st.button("🔨 SOLD", type="primary"):
                    sell_player(cp, winner, bid_price)
                    st.success(f"SOLD to {winner} for {bid_price}!")
                    st.rerun()

            if st.button("Pass (Unsold)"):
                st.session_state['current_player'] = None
                st.info("Player passed. Returned to pool.")
                st.rerun()

# --- TAB 3: TEAM VIEWS ---
with tab3:
    st.header("📊 Squad Summary")
    
    # Calculate leaderboard data
    summary_data = []
    for team in st.session_state['teams']:
        stats = st.session_state['team_stats'][team]
        rem = stats['budget'] - stats['spent']
        count = len(stats['players'])
        summary_data.append({
            "Team Name": team,
            "Players Bought": count,
            "Total Spent": stats['spent'],
            "Remaining Purse": rem
        })
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    st.write("---")
    
    # Detailed Team View
    selected_team_view = st.selectbox("View Squad Details:", st.session_state['teams'])
    if selected_team_view:
        t_data = st.session_state['team_stats'][selected_team_view]
        st.subheader(f"{selected_team_view} Squad")
        
        if t_data['players']:
            squad_df = pd.DataFrame(t_data['players'])
            st.table(squad_df[['name', 'role', 'price']])
        else:
            st.info("No players purchased yet.")

    st.write("---")
    st.subheader("⚠️ Corrections / Unsell")
    
    # List of sold players
    sold_list = [p['name'] for p in st.session_state['players'] if p['status'] == 'Sold']
    if sold_list:
        p_to_unsell = st.selectbox("Select Player to Unsell (Return to Pool)", sold_list)
        if st.button("Unsell Player"):
            if unsell_player(p_to_unsell):
                st.success(f"Unsold {p_to_unsell}. Money refunded to team.")
                st.rerun()
            else:
                st.error("Could not unsell player.")
    else:
        st.info("No players sold yet.")