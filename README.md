# 🏏 Cricket Auction Dashboard

A Streamlit-based application to manage and simulate a live team auction. This dashboard supports real-time bidding, team budget tracking, and a dedicated viewer mode for big-screen displays.

## Features

### 1. Roles
- **Admin**: Full control to manage teams, players, and conduct the auction. Requires login.
- **Viewer**: Read-only view for the audience. Shows live bids, team standings, and recent sales.

### 2. Auction Room (Admin)
- **Head-to-Head Bidding**: Select two competing teams and manage bids with live buttons (+100, +200, +500).
- **Random Selection**: "Pick Random Player" button to speed up the process.
- **Sold Screen**: Celebratory screen when a player is sold, synchronized across all viewers.
- **Budget Tracking**: Prevents overspending by validating bids against remaining purses.

### 3. Viewer Experience
- **Live Updates**: Real-time view of the current bid and holding team.
- **Player Pool**: Searchable list of all players and their status.
- **Team Standings**: Live leaderboard showing spent and remaining budgets.

## Setup & Installation

1.  **Install Dependencies**:
    ```bash
    pip install streamlit pandas
    ```

2.  **Initialize Database & Admin User**:
    Run this script once to set up the database and create the default admin account.
    ```bash
    python create_admin.py
    ```
    *Default Credentials:* `admin` / `admin123`

3.  **Run the Application**:
    ```bash
    streamlit run auction_app.py
    ```

4.  **Access the App**:
    - **Admin**: Log in via the sidebar using the credentials above.
    - **Viewer**: Open the app in a separate tab/window (no login required).

## Project Structure
- `auction_app.py`: Main Streamlit application.
- `db.py`: Database management module.
- `create_admin.py`: Setup script for DB and Admin user.
- `auction.db`: SQLite database (created after setup).
