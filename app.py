import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from PIL import Image
import json

# 1. Page Config
st.set_page_config(page_title="Yen Tracker Pro", page_icon="¥", layout="centered")

# 2. Connections
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["connections"]["gsheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 3. Open Sheets
SHEET_ID = "1L_0iJOrN-nMxjX5zjNm2yUnUyck9RlUqeg2rnXvpAlU" # <--- RE-PASTE YOUR SHEET ID HERE
sh = client.open_by_key(SHEET_ID)
expense_ws = sh.get_worksheet(0)
settings_ws = sh.worksheet("Settings")

# 4. Get Budget
try:
    budget_val = settings_ws.acell('B1').value
    monthly_budget = int(budget_val.replace(',', '')) if budget_val else 300000
except:
    monthly_budget = 300000

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Budget Settings")
    new_budget = st.number_input("Monthly Limit (¥)", value=monthly_budget, step=10000)
    if st.button("Save New Budget"):
        settings_ws.update_acell('B1', new_budget)
        st.success("Budget Saved!")
        st.rerun()

st.title("Bond Finances")

# --- ADD EXPENSE FORM ---
with st.form("expense_form", clear_on_submit=True):
    st.subheader("Add New Expense")
    
    # These fields are pre-filled if the AI worked!
    item = st.text_input("Item Name", value=suggested_item)
    amount = st.number_input("Amount (¥)", min_value=0, value=int(suggested_amount), step=1)
    
    categories = ["Food 🍱", "Transport 🚆", "Shopping 🛍️", "Sightseeing 🏯",
                  "Mortgage 🏠", "Car 🚗", "Water 💧", "Electricity ⚡", 
                  "Car Insurance 🛡️", "Motorcycle Insurance 🏍️", "Pet stuff 🐾", "Gifts 🎁"]
    
    # Match the category from the AI
    try:
        default_index = categories.index(suggested_cat)
    except:
        default_index = 0
        
    category = st.selectbox("Category", categories, index=default_index)
    date = st.date_input("Date")
    
    submit = st.form_submit_button("Save to Google Sheets")
    
    if submit:
        if item and amount > 0:
            expense_ws.append_row([str(date), item, category, amount])
            st.success(f"Saved: {item}")
            st.rerun()

# --- DATA PROCESSING & DASHBOARD ---
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

        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Spent This Month", f"¥{int(monthly_total):,}")
        m2.metric("Remaining", f"¥{int(remaining):,}", 
                  delta=f"{(remaining/monthly_budget)*100:.1f}% left",
                  delta_color="normal" if remaining > 0 else "inverse")
        
        st.progress(min(max(monthly_total / monthly_budget, 0.0), 1.0))
        st.dataframe(df[['Date', 'Item', 'Category', 'Amount']].iloc[::-1].head(10), hide_index=True)

# --- SIDEBAR FOR SETTINGS ---
with st.sidebar:
    st.header("Settings")
    new_budget = st.number_input("Edit Monthly Budget", value=monthly_budget, step=10000)
    if st.button("Update Budget"):
        settings_ws.update_acell('B1', new_budget)
        st.success("Budget updated in Sheet!")
        st.rerun()

























