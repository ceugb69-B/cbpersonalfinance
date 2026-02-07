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

# --- VIEW DATA ---
st.divider()
st.subheader("Recent Expenses")
data = worksheet.get_all_records()
df = pd.DataFrame(data)
st.dataframe(df)











