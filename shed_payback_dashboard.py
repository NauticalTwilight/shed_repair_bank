import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE SETUP
# =============================

st.set_page_config(
    page_title="Shed Repair Bank",
    page_icon="🏦",
    layout="wide"
)

st_autorefresh(interval=15000, key="dashboard_refresh")

# =============================
# SETTINGS
# =============================

TOTAL_REPAIR_COST = 300
HOURLY_RATE = 5

# Original work/repair form response CSV
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ46p98flCzt2nVUELnpXG65xFFmi8Nd8ruu9NqTtenHaQFgUDzVktmXplAF9yPC7_SL37ZvV2_3XhL/pub?gid=430958332&single=true&output=csv"

# Spend Repair BANK form response CSV
SPEND_GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ46p98flCzt2nVUELnpXG65xFFmi8Nd8ruu9NqTtenHaQFgUDzVktmXplAF9yPC7_SL37ZvV2_3XhL/pub?gid=1126731422&single=true&output=csv"

NAME_COLUMN = "Name"
HOURS_COLUMN = "Hours worked per kid"
WORK_COLUMN = "Work Description:"
DATE_COLUMN = "Date Completed"
NOTES_COLUMN = "Parent Notes"

SPEND_AMOUNT_COLUMN = "Spend Amount"
SPEND_DATE_COLUMN = "Spend Date"
SPEND_DESCRIPTION_COLUMN = "Spend Description"
SPEND_NOTES_COLUMN = "Parent Notes"

MILESTONES = [
    (50, "First $50 earned"),
    (100, "First window paid down"),
    (150, "Halfway there"),
    (200, "Two-thirds paid"),
    (250, "Almost finished"),
    (300, "Paid in full")
]

# =============================
# CUSTOM STYLE
# =============================

st.markdown("""
<style>
.big-bank-title {
    background: linear-gradient(90deg, #0b3d2e, #167a4a);
    padding: 30px;
    border-radius: 18px;
    color: white;
    text-align: center;
    margin-bottom: 25px;
}
.bank-card {
    padding: 25px;
    border-radius: 18px;
    background-color: #f5f5f5;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.12);
    text-align: center;
}
.green-money {
    color: #0b8f3a;
    font-size: 42px;
    font-weight: 800;
}
.red-debt {
    color: #c0392b;
    font-size: 42px;
    font-weight: 800;
}
.big-number {
    font-size: 38px;
    font-weight: 800;
}
.countdown-box {
    background-color: #fff3f3;
    border: 3px solid #c0392b;
    border-radius: 18px;
    padding: 25px;
    text-align: center;
}
.success-box {
    background-color: #effaf1;
    border: 3px solid #0b8f3a;
    border-radius: 18px;
    padding: 25px;
    text-align: center;
}
.milestone-card {
    padding: 18px;
    border-radius: 14px;
    background-color: #f7f7f7;
    border-left: 6px solid #167a4a;
    margin-bottom: 10px;
}
.locked-card {
    padding: 18px;
    border-radius: 14px;
    background-color: #fff3f3;
    border-left: 6px solid #c0392b;
    margin-bottom: 10px;
}
.spend-card {
    padding: 18px;
    border-radius: 14px;
    background-color: #fff8e8;
    border-left: 6px solid #d68910;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =============================
# LOAD DATA
# =============================

@st.cache_data(ttl=10)
def load_data():
    try:
        return pd.read_csv(GOOGLE_SHEET_CSV_URL)
    except Exception:
        st.error("Could not load the original work/repair Google Sheet CSV link.")
        return pd.DataFrame()


@st.cache_data(ttl=10)
def load_spend_data():
    if not SPEND_GOOGLE_SHEET_CSV_URL:
        return pd.DataFrame()

    try:
        return pd.read_csv(SPEND_GOOGLE_SHEET_CSV_URL)
    except Exception:
        st.warning("Could not load Spend Repair BANK CSV link. Spend is currently being treated as $0.")
        return pd.DataFrame()


def clean_money_column(series):
    return (
        series
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )


def find_spend_amount_column(spend_df):
    if spend_df.empty:
        return None

    spend_df.columns = spend_df.columns.str.strip()

    # Safety rule:
    # Only subtract spend if the sheet has this exact column.
    # This prevents the spend sheet from accidentally wiping the dashboard.
    if SPEND_AMOUNT_COLUMN in spend_df.columns:
        return SPEND_AMOUNT_COLUMN

    return None


df = load_data()
spend_df = load_spend_data()

# =============================
# CLEAN + COLUMN DETECTION
# =============================

if not df.empty:
    df.columns = df.columns.str.strip()

    if NAME_COLUMN not in df.columns:
        possible_name_columns = [col for col in df.columns if "name" in col.lower()]
        if possible_name_columns:
            NAME_COLUMN = possible_name_columns[0]
        else:
            st.error("Could not find the Name column in the original work sheet.")
            st.write(list(df.columns))
            st.stop()

    if HOURS_COLUMN not in df.columns:
        possible_hours_columns = [col for col in df.columns if "hours" in col.lower()]
        if possible_hours_columns:
            HOURS_COLUMN = possible_hours_columns[0]
        else:
            st.error("Could not find the Hours column in the original work sheet.")
            st.write(list(df.columns))
            st.stop()

    if WORK_COLUMN not in df.columns:
        possible_work_columns = [col for col in df.columns if "work description" in col.lower()]
        if possible_work_columns:
            WORK_COLUMN = possible_work_columns[0]

    if DATE_COLUMN not in df.columns:
        possible_date_columns = [col for col in df.columns if "date" in col.lower()]
        if possible_date_columns:
            DATE_COLUMN = possible_date_columns[0]

    if NOTES_COLUMN not in df.columns:
        possible_notes_columns = [col for col in df.columns if "note" in col.lower()]
        if possible_notes_columns:
            NOTES_COLUMN = possible_notes_columns[0]

# =============================
# CALCULATE REPAIR EARNINGS
# =============================

if not df.empty:
    df[HOURS_COLUMN] = pd.to_numeric(df[HOURS_COLUMN], errors="coerce").fillna(0)

    df["Number of Kids"] = df[NAME_COLUMN].astype(str).apply(
        lambda x: len([name.strip() for name in x.split(",") if name.strip()])
    )

    df["Hours"] = df[HOURS_COLUMN] * df["Number of Kids"]
    df["Earned"] = df["Hours"] * HOURLY_RATE

    total_hours = df["Hours"].sum()
    raw_total_earned = df["Earned"].sum()

    individual_rows = []

    for _, row in df.iterrows():
        names = [name.strip() for name in str(row[NAME_COLUMN]).split(",") if name.strip()]

        for name in names:
            individual_rows.append({
                "Name": name,
                "Hours": row[HOURS_COLUMN],
                "Earned": row[HOURS_COLUMN] * HOURLY_RATE,
                "Work Description": row.get(WORK_COLUMN, ""),
                "Date Completed": row.get(DATE_COLUMN, ""),
                "Parent Notes": row.get(NOTES_COLUMN, "")
            })

    individual_df = pd.DataFrame(individual_rows)

else:
    total_hours = 0
    raw_total_earned = 0
    individual_df = pd.DataFrame()

# =============================
# CALCULATE GROUP SPEND
# =============================

total_spend = 0.0
spend_amount_column = None

if not spend_df.empty:
    spend_df.columns = spend_df.columns.str.strip()

    spend_amount_column = find_spend_amount_column(spend_df)

    if spend_amount_column:
        spend_df[spend_amount_column] = clean_money_column(spend_df[spend_amount_column])
        spend_df[spend_amount_column] = pd.to_numeric(
            spend_df[spend_amount_column],
            errors="coerce"
        ).fillna(0)

        # Only count actual positive spend entries.
        spend_df = spend_df[spend_df[spend_amount_column] > 0]

        total_spend = float(spend_df[spend_amount_column].sum())

    else:
        st.warning("Spend Repair BANK sheet loaded, but it does not have an exact 'Spend Amount' column. Spend is being treated as $0.")

# =============================
# APPLY SPEND RESET LOGIC
# =============================

# These are the dashboard-facing numbers.
# The boys' historical work log and per-child totals remain untouched below.
total_earned = max(raw_total_earned - total_spend, 0)
display_total_repair_cost = max(TOTAL_REPAIR_COST - total_spend, 0)

remaining_money = max(display_total_repair_cost - total_earned, 0)
remaining_hours = remaining_money / HOURLY_RATE if HOURLY_RATE else 0

if display_total_repair_cost > 0:
    progress = min(total_earned / display_total_repair_cost, 1)
else:
    progress = 1

# =============================
# HEADER
# =============================

st.markdown("""
<div class="big-bank-title">
    <h1>🏦 Shed Repair Bank</h1>
    <h3>Work Hard. Earn Money. Pay Back What Was Broken.</h3>
</div>
""", unsafe_allow_html=True)

# =============================
# BANK SUMMARY CARDS
# =============================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="bank-card">
        <h3>💰 Money Earned</h3>
        <div class="green-money">${total_earned:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="bank-card">
        <h3>🏚️ Total Repair Cost</h3>
        <div class="big-number">${display_total_repair_cost:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="bank-card">
        <h3>🚨 Debt Remaining</h3>
        <div class="red-debt">${remaining_money:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# DEBT COUNTDOWN METER
# =============================

st.divider()
st.header("📉 Debt Payoff Meter")

if remaining_money <= 0:
    st.markdown("""
    <div class="success-box">
        <h2>✅ PAID IN FULL</h2>
        <h3>The shed repair debt has been fully paid back.</h3>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="countdown-box">
        <h2>🚨 Debt Remaining: ${remaining_money:,.2f}</h2>
        <h3>{remaining_hours:.1f} hours left to work</h3>
    </div>
    """, unsafe_allow_html=True)

st.progress(progress)
st.markdown(f"### Payoff Progress: **{progress * 100:.1f}% complete**")


# =============================
# MILESTONES
# =============================

st.divider()
st.header("🎯 Payoff Milestones")

for amount, label in MILESTONES:
    if total_earned >= amount:
        st.markdown(f"""
        <div class="milestone-card">
            <h4>✅ ${amount} — {label}</h4>
            <p>Completed</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        amount_left = amount - total_earned
        hours_left = amount_left / HOURLY_RATE

        st.markdown(f"""
        <div class="locked-card">
            <h4>🔒 ${amount} — {label}</h4>
            <p>${amount_left:,.2f} left to reach this milestone — {hours_left:.1f} more hours</p>
        </div>
        """, unsafe_allow_html=True)
        break

# =============================
# HOURS SUMMARY
# =============================

st.divider()
st.header("⏱️ Work Hours Summary")

col4, col5, col6 = st.columns(3)

with col4:
    st.metric("Total Hours Worked", f"{total_hours:.1f}")

with col5:
    st.metric("Hourly Pay Rate", f"${HOURLY_RATE}/hour")

with col6:
    st.metric("Hours Remaining", f"{remaining_hours:.1f}")

# =============================
# MONEY EARNED PER CHILD
# =============================

st.divider()
st.header("👦 Money Earned Per Child")

if individual_df.empty:
    st.info("No work has been logged yet.")
else:
    child_summary = (
        individual_df.groupby("Name")
        .agg({
            "Hours": "sum",
            "Earned": "sum"
        })
        .reset_index()
        .sort_values("Name")
    )

    child_summary_display = child_summary.copy()
    child_summary_display["Earned"] = child_summary_display["Earned"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(child_summary_display, use_container_width=True)

    st.subheader("Money Earned by Child")
    chart_data = child_summary.set_index("Name")["Earned"]
    st.bar_chart(chart_data)

# =============================
# BANK TRANSACTION LOG
# =============================

st.divider()
st.header("📋 Bank Transaction Log")

if df.empty:
    st.info("No entries yet.")
else:
    display_cols = [
        "Timestamp",
        DATE_COLUMN,
        NAME_COLUMN,
        HOURS_COLUMN,
        "Number of Kids",
        "Hours",
        WORK_COLUMN,
        NOTES_COLUMN,
        "Earned"
    ]

    existing_cols = [col for col in display_cols if col in df.columns]

    transaction_display = df[existing_cols].sort_index(ascending=False).copy()

    if "Earned" in transaction_display.columns:
        transaction_display["Earned"] = transaction_display["Earned"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(transaction_display, use_container_width=True)


# =============================
# INDIVIDUAL WORK LOG
# =============================

st.divider()
st.header("🧾 Individual Work Log")

if individual_df.empty:
    st.info("No individual work entries yet.")
else:
    individual_display = individual_df.sort_index(ascending=False).copy()

    if "Earned" in individual_display.columns:
        individual_display["Earned"] = individual_display["Earned"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(individual_display, use_container_width=True)

# =============================
# SPEND SUMMARY
# =============================

st.divider()
st.header("💸 Spend Repair BANK Summary")

st.markdown(f"""
<div class="spend-card">
    <h4>Group Spend Subtracted</h4>
    <p style="font-size: 30px; font-weight: 800;">${total_spend:,.2f}</p>
    <p>This amount is subtracted from both Money Earned and Total Repair Cost.</p>
</div>
""", unsafe_allow_html=True)

# =============================
# SPEND REPAIR BANK LOG
# =============================

st.divider()
st.header("💸 Spend Repair BANK Log")

if spend_df.empty:
    st.info("No spend entries yet, or the Spend CSV URL has not been added.")
else:
    spend_display = spend_df.sort_index(ascending=False).copy()

    if spend_amount_column and spend_amount_column in spend_display.columns:
        spend_display[spend_amount_column] = spend_display[spend_amount_column].apply(lambda x: f"${x:,.2f}")

    st.dataframe(spend_display, use_container_width=True)


# =============================
# REFRESH
# =============================

st.divider()

col7, col8 = st.columns([1, 3])

with col7:
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

with col8:
    st.caption("Dashboard auto-refreshes every 15 seconds.")
