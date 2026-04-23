import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Finance AI App", layout="wide")

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
.stApp { background-color: #0e1117; color: white; }

.metric-card {
    background: linear-gradient(135deg, #6a11cb, #2575fc);
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("finance.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    date TEXT,
    income REAL,
    food REAL,
    travel REAL,
    shopping REAL,
    others REAL,
    loan REAL,
    rate REAL,
    months INTEGER,
    emi REAL
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
def calculate_emi(loan, rate, months):
    if loan > 0 and rate > 0 and months > 0:
        r = rate / (12 * 100)
        return (loan * r * (1+r)**months)/((1+r)**months - 1)
    return 0

def get_risk(income, emi):
    if income == 0:
        return "Unknown"
    ratio = emi / income
    if ratio < 0.3:
        return "Safe ✅"
    elif ratio < 0.5:
        return "Risky ⚠️"
    return "Danger ❌"

def ai_insights(income, food, travel, shopping, others, emi):
    insights = []
    total = food + travel + shopping + others

    if total > income:
        insights.append("⚠️ Overspending detected")
    if shopping > income * 0.25:
        insights.append("🛍 High shopping expense")
    if emi > income * 0.5:
        insights.append("🚨 High EMI risk")
    if income - total - emi < income * 0.1:
        insights.append("💡 Low savings")

    if not insights:
        insights.append("✅ Healthy finances")

    return insights

def financial_precautions(income, total, emi):
    tips = []

    if total > income:
        tips.append("❌ Avoid spending more than income")
    else:
        tips.append("✅ Maintain a proper budget")

    if emi > income * 0.5:
        tips.append("🚨 Avoid high EMI loans")
    else:
        tips.append("✅ Keep EMI under control")

    if income - total - emi < income * 0.1:
        tips.append("💡 Save at least 10%")
    else:
        tips.append("✅ Good savings habit")

    tips.append("📌 Avoid unnecessary credit usage")
    tips.append("📌 Keep emergency fund (3–6 months)")

    return tips

# ---------------- LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🔐 Login / Register")

    option = st.radio("Select", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Register":
        if st.button("Register"):
            try:
                cursor.execute("INSERT INTO users VALUES (?,?)", (username, password))
                conn.commit()
                st.success("Registered! Now login.")
            except:
                st.error("Username already exists")

    else:
        if st.button("Login"):
            user = cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()

            if user:
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.success(f"👤 {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

page = st.sidebar.radio("Navigate", ["Input", "Dashboard"])

# ---------------- INPUT PAGE ----------------
if page == "Input":
    st.title("💰 Enter Details")

    col1, col2 = st.columns(2)

    with col1:
        income = st.number_input("Income", min_value=0.0, key="income")
        food = st.number_input("Food", min_value=0.0, key="food")
        travel = st.number_input("Travel", min_value=0.0, key="travel")
        shopping = st.number_input("Shopping", min_value=0.0, key="shopping")
        others = st.number_input("Others", min_value=0.0, key="others")

    with col2:
        loan = st.number_input("Loan", min_value=0.0, key="loan")
        rate = st.number_input("Rate %", min_value=0.0, key="rate")
        months = st.number_input("Months", min_value=0, key="months")

    if st.button("➡️ Go to Dashboard"):
        st.session_state.page = "Dashboard"
        st.rerun()

# ---------------- DASHBOARD ----------------
else:
    st.title("📊 Dashboard")

    income = st.session_state.get("income", 0)
    food = st.session_state.get("food", 0)
    travel = st.session_state.get("travel", 0)
    shopping = st.session_state.get("shopping", 0)
    others = st.session_state.get("others", 0)
    loan = st.session_state.get("loan", 0)
    rate = st.session_state.get("rate", 0)
    months = st.session_state.get("months", 0)

    total = food + travel + shopping + others
    emi = calculate_emi(loan, rate, months)
    balance = income - total - emi
    risk = get_risk(income, emi)

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card">Income<br>₹{income:.0f}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card">Expense<br>₹{total:.0f}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card">EMI<br>₹{emi:.0f}</div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card">Balance<br>₹{balance:.0f}</div>', unsafe_allow_html=True)

    st.subheader("🚦 Financial Status")
    st.write(risk)

    # Charts
    st.subheader("📊 Charts")

    col1, col2 = st.columns(2)

    with col1:
        if total > 0:
            pie = px.pie(
                names=["Food","Travel","Shopping","Others"],
                values=[food, travel, shopping, others]
            )
            st.plotly_chart(pie, use_container_width=True)

    with col2:
        bar = px.bar(
            x=["Income","Expense","EMI"],
            y=[income, total, emi]
        )
        st.plotly_chart(bar, use_container_width=True)

    # AI
    st.subheader("🤖 AI Insights")
    for tip in ai_insights(income, food, travel, shopping, others, emi):
        st.write(tip)

    # Tips
    st.subheader("🛡️ Precautions")
    for tip in financial_precautions(income, total, emi):
        st.write(tip)

    # ML Prediction
    df = pd.read_sql_query(
        "SELECT * FROM records WHERE username=?",
        conn,
        params=(st.session_state.user,)
    )

    if len(df) > 3:
        df['total'] = df[['food','travel','shopping','others']].sum(axis=1)
        df['index'] = range(len(df))

        x = df['index']
        y = df['total']

        m = ((x-x.mean())*(y-y.mean())).sum()/((x-x.mean())**2).sum()
        b = y.mean() - m*x.mean()
        pred = m*len(df)+b

        st.info(f"📈 Predicted Expense: ₹{pred:.2f}")

    # Save
    if st.button("💾 Save"):
        cursor.execute("""
        INSERT INTO records 
        VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            st.session_state.user,
            datetime.now(),
            income, food, travel, shopping, others,
            loan, rate, months, emi
        ))
        conn.commit()
        st.success("Saved!")