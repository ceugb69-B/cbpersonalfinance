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

# --- AI SCANNER LOGIC ---
st.title("Bond Finances")

suggested_item = ""
suggested_amount = 0
suggested_cat = "Food 🍱"

# This expander keeps the camera hidden until you need it
with st.expander("📸 Scan Receipt with AI"):
    uploaded_file = st.camera_input("Take a photo of receipt")
    if uploaded_file:
        # Configure Gemini with your secret key
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(uploaded_file)
        
        with st.spinner("AI is reading the receipt..."):
            prompt = """
            Analyze this Japanese receipt. Return ONLY a JSON object:
            {"item": "store or item name", "amount": total_as_int, "category": "match one below"}
            Categories: Food 🍱, Transport 🚆, Shopping 🛍️, Sightseeing 🏯, Mortgage 🏠, Car 🚗, Water 💧, Electricity ⚡, Car Insurance 🛡️, Motorcycle Insurance 🏍️, Pet stuff 🐾, Gifts 🎁
            Look for '合計' or '税込' for the total.
            """
            response = model.generate_content([prompt, img])
            try:
                # Cleaning the text to find the JSON block
                raw_text = response.text.strip().replace('```json', '').replace('```', '')
                ai_data = json.loads(raw_text)
                
                suggested_item = ai_data.get('item', "")
                suggested_amount = ai_data.get('amount', 0)
                suggested_cat = ai_data.get('category', "Food 🍱")
                st.success(f"AI Detected: {suggested_item} (¥{suggested_amount})")
            except:
                st.error("AI couldn't parse the receipt. Please try again or enter manually.")

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





















