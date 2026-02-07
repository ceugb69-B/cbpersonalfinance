import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
st.set_page_config(
    page_title="Yen Tracker",
    page_icon="¥",
    layout="centered", # Better for narrow phone screens
    initial_sidebar_state="collapsed"
)

# 1. Setup Connection
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["connections"]["gsheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 2. Open the Sheet (Use your Sheet ID here)
SHEET_ID = "1L_0iJOrN-nMxjX5zjNm2yUnUyck9RlUqeg2rnXvpAlU"
sh = client.open_by_key(SHEET_ID)
worksheet = sh.get_worksheet(0)

st.title("Bond Finance Tracker")
# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Budget Settings")
    # This creates a box where you can type your monthly limit
    monthly_budget = st.number_input(
        "Set Monthly Budget (¥)", 
        min_value=0, 
        value=300000, # Default starting value
        step=10000
    )
    st.info(f"Your current budget is ¥{monthly_budget:,}")

# --- ADD EXPENSE FORM ---
with st.form("expense_form"):
    st.subheader("Add New Expense")
    category = st.selectbox("Category", [
    "Food 🍱", 
    "Transport 🚆", 
    "Shopping 🛍️", 
    "Sightseeing 🏯",
    "Mortgage 🏠", 
    "Car 🚗", 
    "Water 💧", 
    "Electricity ⚡", 
    "Car Insurance 🛡️", 
    "Motorcycle Insurance 🏍️", 
    "Pet stuff 🐾", 
    "Gifts 🎁"
])
    amount = st.number_input("Amount (¥)", min_value=0, step=1, format="%d")
    date = st.date_input("Date")
    
    submit = st.form_submit_button("Save to Google Sheets")
    
# Updated append_row to include the category
if submit:
    if item:
        worksheet.append_row([str(date), item, category, amount])
        st.success(f"Added ¥{amount} for {item}!")
    else:
            st.error("Please enter an item name.")

# --- 1. ACCESS THE SETTINGS TAB ---
# Connect to the 'Settings' worksheet
settings_ws = sh.worksheet("Settings")

# Get the current budget from cell B1
current_budget_from_sheet = int(settings_ws.acell('B1').value or 300000)

with st.sidebar:
    st.header("Budget Settings")
    new_budget = st.number_input("Monthly Budget (¥)", value=current_budget_from_sheet, step=10000)
    
    if st.button("Update Budget in Sheet"):
        settings_ws.update_acell('B1', new_budget)
        st.success("Budget Updated!")
        st.rerun() # Refresh to use the new number

monthly_budget = new_budget

# --- 2. DATA PROCESSING (Expenses Tab) ---
# Ensure we are looking at the first tab for expenses
expense_ws = sh.get_worksheet(0) 
data = expense_ws.get_all_records()

if data:
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Date', 'Amount'])

    if not df.empty:
        current_month = pd.Timestamp.now().to_period('M')
        df['MonthYear'] = df['Date'].dt.to_period('M')
        
        monthly_total = df[df['MonthYear'] == current_month]['Amount'].sum()
        remaining = monthly_budget - monthly_total

        # --- DASHBOARD METRICS ---
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Spent (This Month)", f"¥{int(monthly_total):,}")
        m2.metric("Remaining", f"¥{int(remaining):,}", 
                  delta=f"{(remaining/monthly_budget)*100:.1f}% left",
                  delta_color="normal" if remaining > 0 else "inverse")
        
        # Progress Bar
        st.progress(min(max(monthly_total / monthly_budget, 0.0), 1.0))
















