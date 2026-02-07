import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from PIL import Image
import json
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="Yen Tracker Pro", page_icon="¥", layout="wide")

# 2. Connections
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["connections"]["gsheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 3. Open Sheets
SHEET_ID = "1L_0iJOrN-nMxjX5zjNm2yUnUyck9RlUqeg2rnXvpAlU" 
sh = client.open_by_key(SHEET_ID)
expense_ws = sh.get_worksheet(0)
settings_ws = sh.worksheet("Settings")

# 4. Initialize AI Variables
suggested_item = ""
suggested_amount = 0
suggested_cat = "Food 🍱"

# 5. Get Salary
try:
    budget_val = settings_ws.acell('B1').value
    monthly_budget = int(budget_val.replace(',', '')) if budget_val else 300000
except:
    monthly_budget = 300000

st.title("Bond Finances")

# --- AI SCANNER ---
with st.expander("📸 Scan Receipt with AI"):
    uploaded_file = st.camera_input("Take a photo")
    if uploaded_file:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name='gemini-1.5-flash')
            img = Image.open(uploaded_file)
            
            with st.spinner("AI reading receipt..."):
                prompt = """Analyze receipt. Return ONLY JSON: {"item": "store", "amount": int, "category": "match"}
                Categories: Food 🍱, Transport 🚆, Shopping 🛍️, Sightseeing 🏯, Mortgage 🏠, Car 🚗, Water 💧, Electricity ⚡, Car Insurance 🛡️, Motorcycle Insurance 🏍️, Pet stuff 🐾, Gifts 🎁"""
                response = model.generate_content([prompt, img])
                raw_text = response.text.strip().replace('```json', '').replace('```', '')
                ai_data = json.loads(raw_text)
                suggested_item = ai_data.get('item', "")
                suggested_amount = ai_data.get('amount', 0)
                suggested_cat = ai_data.get('category', "Food 🍱")
                st.success(f"AI Detected: {suggested_item}")
        except Exception as e:
            st.error(f"AI Key or Region Error: {e}")

# --- ADD EXPENSE FORM ---
with st.form("expense_form", clear_on_submit=True):
    st.subheader("Add New Expense")
    col_a, col_b = st.columns(2)
    with col_a:
        item = st.text_input("Item Name", value=suggested_item)
        amount = st.number_input("Amount (¥)", min_value=0, value=int(suggested_amount), step=1)
        description = st.text_input("Description (Optional)", placeholder="e.g. Weekly groceries")
    with col_b:
        categories = ["Food 🍱", "Transport 🚆", "Shopping 🛍️", "Sightseeing 🏯",
                      "Mortgage 🏠", "Car 🚗", "Water 💧", "Electricity ⚡", 
                      "Car Insurance 🛡️", "Motorcycle Insurance 🏍️", "Pet stuff 🐾", "Gifts 🎁"]
        idx = categories.index(suggested_cat) if suggested_cat in categories else 0
        category = st.selectbox("Category", categories, index=idx)
        date = st.date_input("Date")
    
    submit = st.form_submit_button("Save to Google Sheets")
    
    if submit:
        if item and amount > 0:
            # Match the 5-column order: Date, Item, Amount, Category, Description
            expense_ws.append_row([str(date), item, amount, category, description])
            st.success(f"Saved: {item}")
            st.rerun()

# --- DASHBOARD ---
data = expense_ws.get_all_records()
if data:
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    
    # Ensure columns exist and map correctly
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Date', 'Amount'])

    if not df.empty:
        current_month = pd.Timestamp.now().to_period('M')
        df['MonthYear'] = df['Date'].dt.to_period('M')
        curr_month_df = df[df['MonthYear'] == current_month]
        
        monthly_total = curr_month_df['Amount'].sum()
        remaining = monthly_budget - monthly_total
        percent_spent = min(max(monthly_total / monthly_budget, 0.0), 1.0)

        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Spent This Month", f"¥{int(monthly_total):,}")
        m2.metric("Remaining Salary", f"¥{int(remaining):,}", 
                  delta=f"{(remaining/monthly_budget)*100:.1f}% left")
        st.progress(percent_spent)

        st.write("### Financial Visuals")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            trend_df = df.groupby('MonthYear')['Amount'].sum().reset_index()
            trend_df['MonthYear'] = trend_df['MonthYear'].astype(str)
            fig_bar = px.bar(trend_df, x='MonthYear', y='Amount', title="Spending History", color_discrete_sequence=['#ff4b4b'])
            fig_bar.add_hline(y=monthly_budget, line_dash="dot", line_color="green", annotation_text="Salary")
            st.plotly_chart(fig_bar, use_container_width=True)

        with chart_col2:
            if not curr_month_df.empty:
                cat_df = curr_month_df.groupby('Category')['Amount'].sum().reset_index()
                fig_pie = px.pie(cat_df, values='Amount', names='Category', title=f"Category Breakdown ({current_month})", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

        with st.expander("View Recent History"):
            # Show all 5 columns in the history table
            st.dataframe(df[['Date', 'Item', 'Amount', 'Category', 'Description']].iloc[::-1].head(10), hide_index=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    new_budget = st.number_input("Update Monthly Salary", value=monthly_budget, step=10000)
    if st.button("Save Salary"):
        settings_ws.update_acell('B1', new_budget)
        st.success("Salary updated!")
        st.rerun()











































