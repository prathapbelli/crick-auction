import streamlit as st
import pandas as pd
import time
import db

# --- Page Configuration ---
st.set_page_config(page_title="Cricket Auction Dashboard", layout="wide")

# --- Database Initialization ---
if 'db_initialized' not in st.session_state:
    db.init_db()
    db_user = st.secrets["DB_USERNAME"]
    db_password = st.secrets["DB_PASSWORD"]
    db.create_user(db_user, db_password) 
    st.session_state['db_initialized'] = True

# --- Sidebar: Role Selection ---
st.sidebar.title("Auction Settings")
role = st.sidebar.radio("Select Role", ["Viewer", "Admin"])

# --- Admin Authentication ---
if role == "Admin":
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        if db.check_user(username, password):
            st.session_state['authenticated'] = True
            st.session_state['user'] = username
            st.sidebar.success(f"Welcome {username}")
        else:
            st.sidebar.error("Invalid Credentials")
    
    if not st.session_state.get('authenticated'):
        st.warning("Please login to access Admin features.")
        st.stop() # Stop execution here if not authenticated

# --- Helper Functions ---
def auto_refresh():
    time.sleep(2)
    st.rerun()

# --- VIEWER MODE ---
if role == "Viewer":
    st.title("👀 Live Auction View")
    
    # 1. Current Player on Auction
    current_player = db.get_current_player()
    
    if current_player:
        current_bid = current_player['current_bid'] if current_player['current_bid'] else 0
        holding_team = current_player['holding_team']
        
        if current_player['status'] == 'Sold':
            st.markdown(f"""
            <div style="background-color: #fff3e0; padding: 40px; border-radius: 15px; text-align: center; border: 3px solid #ff9800; margin-bottom: 20px;">
                <h1 style="color: #e65100; font-size: 4em;">🎉 SOLD!</h1>
                <h2 style="color: #333;">{current_player['name']}</h2>
                <hr>
                <h3 style="color: #555;">Sold to <span style="color: #d84315; font-weight: bold;">{current_player['sold_to']}</span></h3>
                <h1 style="color: #2e7d32; font-size: 3.5em;">₹ {int(current_player['price'])}</h1>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
        else:
            st.markdown(f"""
            <div style="background-color: #e8f5e9; padding: 40px; border-radius: 15px; text-align: center; border: 3px solid #4CAF50; margin-bottom: 20px;">
                <h1 style="color: #2e7d32; font-size: 3em;">{current_player['name']}</h1>
                <h3 style="color: #555;">{current_player['role']}</h3>
                <hr>
                <h2 style="color: #d32f2f; font-size: 2.5em;">Current Bid: ₹ {current_bid}</h2>
                <h3 style="color: #1976d2;">Holding: {holding_team if holding_team else 'Waiting for bids...'}</h3>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Waiting for the next player to be brought to the auction floor...")
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h2>⏳ Auction in Progress...</h2>
        </div>
        """, unsafe_allow_html=True)

    # 2. Recent Sales (Last 5)
    st.subheader("Recent Sales")
    players = db.get_players()
    sold_players = [p for p in players if p['status'] == 'Sold']
    if sold_players:
        df = pd.DataFrame(sold_players)
        df['price'] = df['price'].fillna(0).astype(int)
        st.table(df[['name', 'role', 'sold_to', 'price']].tail(5))
    else:
        st.write("No players sold yet.")

    # 3. Team Standings
    st.subheader("Team Standings")
    teams = db.get_teams()
    if teams:
        df_teams = pd.DataFrame(teams)
        df_teams['Remaining Purse'] = df_teams['budget'] - df_teams['spent']
        st.table(df_teams[['name', 'budget', 'spent', 'Remaining Purse']])
        
    # 4. Player Pool Status
    st.subheader("Player Pool Status")
    if players:
        # Show all players with relevant columns
        pool_df = pd.DataFrame(players)
        
        # Ensure price is integer (fill NaN with 0 first if needed, though Unsold has None)
        # For display, we can just format or fillna
        pool_df['price'] = pool_df['price'].fillna(0).astype(int)
        
        # Select user-friendly columns
        st.dataframe(pool_df[['name', 'role', 'status', 'sold_to', 'price']], use_container_width=True)
    else:
        st.info("No players in pool.")
    
    # Auto-refresh for live updates
    auto_refresh()

# --- ADMIN MODE ---
else:
    st.title("🏏 Auction Admin Console")
    
    tab1, tab2, tab3 = st.tabs(["1. Setup", "2. Auction Room", "3. Team Views"])
    
    # --- TAB 1: SETUP ---
    with tab1:
        st.header("Step 1: Configure Auction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add Teams")
            new_team = st.text_input("Team Name")
            team_budget = st.number_input("Team Budget", min_value=1000, value=10000, step=500)
            if st.button("Add Team"):
                if db.add_team(new_team, team_budget):
                    st.success(f"Added {new_team}")
                else:
                    st.error("Team already exists.")
            
            teams = db.get_teams()
            if teams:
                st.write("### Registered Teams")
                st.table(pd.DataFrame(teams))

        with col2:
            st.subheader("Add Player Pool")
            p_name = st.text_input("Player Name")
            p_role = st.selectbox("Role", ["Batsman", "Bowler", "All-Rounder", "Wicket Keeper"])
            if st.button("Add Player"):
                db.add_player(p_name, p_role)
                st.success(f"Added {p_name}")
            
            st.write("---")
            
            # Manage Pool
            st.subheader("Manage Pool")
            players = db.get_players()
            unsold_players = [p for p in players if p['status'] == 'Unsold']
            
            if unsold_players:
                p_options = [p['name'] for p in unsold_players]
                p_to_remove = st.selectbox("Select Player to Remove", p_options)
                if st.button("Remove Player"):
                    db.remove_player(p_to_remove)
                    st.success(f"Removed {p_to_remove}")
                    st.rerun()
            
            st.info(f"Total Players: {len(players)}")
            if players:
                st.dataframe(pd.DataFrame(players))

        if st.button("⚠️ Reset Entire Auction"):
            db.reset_auction()
            st.warning("Auction Reset!")
            st.rerun()

    # --- TAB 2: AUCTION ROOM ---
    with tab2:
        st.header("🔨 The Auction Floor")
        
        teams = db.get_teams()
        players = db.get_players()
        
        if not teams:
            st.warning("Add teams first.")
        elif not players:
            st.warning("Add players first.")
        else:
            # Check for current player
            current_player = db.get_current_player()
            
            # --- SCREEN 1: SELECTION ---
            if not current_player:
                unsold_players = [p for p in players if p['status'] == 'Unsold']
                if not unsold_players:
                    st.balloons()
                    st.success("Auction Complete!")
                else:
                    st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h2>🎯 Select Next Player</h2>
                        <p style="color: #666;">Choose how you want to bring the next player to the auction floor.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("")
                    st.write("")
                    
                    # Centered layout for selection
                    _, col_sel, _ = st.columns([1, 2, 1])
                    
                    with col_sel:
                        col_rand, col_spacer, col_manual = st.columns([2, 0.5, 2])
                        
                        with col_rand:
                            st.write("### 🎲 Random")
                            if st.button("Pick Random Player", type="primary", use_container_width=True):
                                import random
                                p_obj = random.choice(unsold_players)
                                db.set_current_player(p_obj['name'])
                                st.rerun()
                        
                        with col_manual:
                            st.write("### 👆 Manual")
                            p_options = [f"{p['name']} ({p['role']})" for p in unsold_players]
                            selected_option = st.selectbox("Select Player", p_options, label_visibility="collapsed")
                            
                            if st.button("Bring Selected to Auction", type="primary", use_container_width=True):
                                idx = p_options.index(selected_option)
                                p_obj = unsold_players[idx]
                                db.set_current_player(p_obj['name'])
                                st.rerun()
                    
                    st.divider()
                    st.info(f"Remaining Unsold Players: {len(unsold_players)}")

            # --- SCREEN 2: BIDDING ---
            else:
                # Full width bidding interface
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #4CAF50; margin-bottom: 20px;">
                        <h2 style="color: #333;">{current_player['name']}</h2>
                        <h4 style="color: #666;">{current_player['role']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                # --- Head-to-Head Bidding ---
                st.subheader("⚔️ Bidding War")
                
                # 1. Select Two Teams
                if 'bid_team_1' not in st.session_state: st.session_state['bid_team_1'] = None
                if 'bid_team_2' not in st.session_state: st.session_state['bid_team_2'] = None
                
                team_names = [t['name'] for t in teams]
                
                sel_col1, sel_col2 = st.columns(2)
                with sel_col1:
                    st.session_state['bid_team_1'] = st.selectbox("Team A", team_names, key="t1_sel")
                with sel_col2:
                    st.session_state['bid_team_2'] = st.selectbox("Team B", team_names, key="t2_sel", index=1 if len(team_names) > 1 else 0)
                
                st.divider()
                
                # 2. Live Bidding Controls
                t1 = st.session_state['bid_team_1']
                t2 = st.session_state['bid_team_2']
                
                # Get current bid state from DB
                current_bid = current_player['current_bid'] if current_player['current_bid'] else 0
                holding_team = current_player['holding_team']
                
                # Display Current Status
                st.markdown(f"""
                <div style="text-align: center; margin-bottom: 20px;">
                    <h1 style="font-size: 4em; color: #d32f2f;">₹ {current_bid}</h1>
                    <h3>Holding: <span style="color: #1976d2;">{holding_team if holding_team else 'None'}</span></h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Only show bidding controls if NOT sold
                if current_player['status'] == 'Unsold':
                    bid_col1, bid_col2 = st.columns(2)
                    
                    # Team A Controls
                    with bid_col1:
                        st.markdown(f"### {t1}")
                        t1_stats, _ = db.get_team_stats(t1)
                        t1_rem = t1_stats['budget'] - t1_stats['spent']
                        st.caption(f"Purse: {t1_rem}")
                        
                        c1, c2, c3 = st.columns(3)
                        if c1.button(f"+100", key="t1_100"):
                            db.update_bid(current_player['name'], t1, current_bid + 100)
                            st.rerun()
                        if c2.button(f"+200", key="t1_200"):
                            db.update_bid(current_player['name'], t1, current_bid + 200)
                            st.rerun()
                        if c3.button(f"+500", key="t1_500"):
                            db.update_bid(current_player['name'], t1, current_bid + 500)
                            st.rerun()

                    # Team B Controls
                    with bid_col2:
                        st.markdown(f"### {t2}")
                        t2_stats, _ = db.get_team_stats(t2)
                        t2_rem = t2_stats['budget'] - t2_stats['spent']
                        st.caption(f"Purse: {t2_rem}")
                        
                        c1, c2, c3 = st.columns(3)
                        if c1.button(f"+100", key="t2_100"):
                            db.update_bid(current_player['name'], t2, current_bid + 100)
                            st.rerun()
                        if c2.button(f"+200", key="t2_200"):
                            db.update_bid(current_player['name'], t2, current_bid + 200)
                            st.rerun()
                        if c3.button(f"+500", key="t2_500"):
                            db.update_bid(current_player['name'], t2, current_bid + 500)
                            st.rerun()

                st.divider()
                
                # 3. Finalize Sale
                if current_player['status'] == 'Sold':
                    st.success(f"✅ SOLD to {current_player['sold_to']} for {int(current_player['price'])}!")
                    if st.button("Next Auction ➡️", type="primary"):
                        db.dismiss_current_player()
                        st.rerun()
                else:
                    if st.button("🔨 SOLD at Current Price", type="primary", use_container_width=True):
                        if holding_team:
                            if db.sell_player(current_player['name'], holding_team, current_bid):
                                st.success(f"SOLD to {holding_team} for {current_bid}!")
                                st.rerun()
                            else:
                                st.error("Sale failed.")
                        else:
                            st.error("No bids placed yet.")
                    
                    if st.button("Pass (Unsold)"):
                        db.set_current_player(None)
                        st.info("Player passed.")
                        st.rerun()
            
            # Auto-refresh removed from here to allow Tab 3 to render

    # --- TAB 3: TEAM VIEWS ---
    with tab3:
        st.header("📊 Squad Summary")
        
        teams = db.get_teams()
        summary_data = []
        for t in teams:
            rem = t['budget'] - t['spent']
            # Get player count
            _, t_players = db.get_team_stats(t['name'])
            summary_data.append({
                "Team Name": t['name'],
                "Players Bought": len(t_players),
                "Total Spent": t['spent'],
                "Remaining Purse": rem
            })
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        
        st.write("---")
        
        selected_team = st.selectbox("View Squad Details:", [t['name'] for t in teams])
        if selected_team:
            _, t_players = db.get_team_stats(selected_team)
            st.subheader(f"{selected_team} Squad")
            if t_players:
                sq_df = pd.DataFrame(t_players)
                sq_df['price'] = sq_df['price'].fillna(0).astype(int)
                st.table(sq_df[['name', 'role', 'price']])
            else:
                st.info("No players purchased.")
        
        st.write("---")
        st.subheader("⚠️ Corrections")
        
        players = db.get_players()
        sold_list = [p['name'] for p in players if p['status'] == 'Sold']
        if sold_list:
            p_to_unsell = st.selectbox("Select Player to Unsell", sold_list)
            if st.button("Unsell Player"):
                if db.unsell_player(p_to_unsell):
                    st.success(f"Unsold {p_to_unsell}.")
                    st.rerun()
    
    # Auto-refresh for Admin to see updates (placed here to ensure all tabs render)
    auto_refresh()