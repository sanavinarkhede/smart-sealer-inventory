
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Smart Sealer Inventory",
    page_icon="🏭",
    layout="wide"
)

# ---------------- CONFIGURATION ----------------
CAPACITY_DEFAULT = 200.0

# ---------------- INITIAL DATA ------------------
if "drums" not in st.session_state:
    st.session_state.drums = {
        "SD-001": {"type": "Hemming Sealer", "capacity": 200.0, "stock": 165.0},
        "SD-002": {"type": "Hemming Sealer", "capacity": 200.0, "stock": 120.0},
        "SD-003": {"type": "Body Sealer", "capacity": 200.0, "stock": 45.0},
        "SD-004": {"type": "Body Sealer", "capacity": 200.0, "stock": 15.0},
        "SD-005": {"type": "Hemming Sealer", "capacity": 200.0, "stock": 200.0},
    }

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "daily_consumption" not in st.session_state:
    st.session_state.daily_consumption = 0.0

if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False

if "sensor_offset" not in st.session_state:
    st.session_state.sensor_offset = 10.0

# ---------------- HELPER FUNCTIONS -------------
def log_transaction(drum_id, action, qty, balance):
    st.session_state.transactions.insert(0, {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Drum ID": drum_id,
        "Action": action,
        "Quantity (kg)": round(qty, 2),
        "Balance (kg)": round(balance, 2),
    })

def consume(drum_id, qty):
    drum = st.session_state.drums[drum_id]
    qty = min(float(qty), drum["stock"])

    if qty <= 0:
        return

    drum["stock"] = round(drum["stock"] - qty, 2)
    st.session_state.daily_consumption += qty
    log_transaction(drum_id, "Consumption", qty, drum["stock"])

def refill(drum_id, qty):
    drum = st.session_state.drums[drum_id]
    available = drum["capacity"] - drum["stock"]
    qty = min(float(qty), available)

    if qty <= 0:
        return

    drum["stock"] = round(drum["stock"] + qty, 2)
    log_transaction(drum_id, "Refill", qty, drum["stock"])

def status_of(stock, capacity):
    pct = stock / capacity * 100 if capacity > 0 else 0

    if stock <= 0:
        return "Empty"
    if pct <= 10:
        return "Critical"
    if pct <= 25:
        return "Low"
    return "Normal"

# ---------------- SIDEBAR -----------------------
st.sidebar.title("🏭 Smart Sealer")
st.sidebar.caption("Digital Inventory Monitoring")
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Drum Monitoring", "Sensor Simulation",
     "Inventory Transactions", "Settings"]
)

st.sidebar.divider()
st.sidebar.caption("DEMO MODE — Simulated Sensor Data")
st.sidebar.metric(
    "Total Inventory",
    f"{sum(d['stock'] for d in st.session_state.drums.values()):,.1f} kg"
)

# ---------------- COMMON CALCULATIONS -----------
drums = st.session_state.drums
total_stock = sum(d["stock"] for d in drums.values())
total_capacity = sum(d["capacity"] for d in drums.values())
total_consumed_today = st.session_state.daily_consumption
low_drums = sum(
    status_of(d["stock"], d["capacity"]) in ["Low", "Critical", "Empty"]
    for d in drums.values()
)

# ---------------- OVERVIEW ----------------------
if page == "Overview":
    st.title("Smart Sealer Inventory Dashboard")
    st.info("DEMO MODE — All sensor readings and initial inventory are simulated.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Inventory", f"{total_stock:.1f} kg")
    c2.metric("Total Capacity", f"{total_capacity:.0f} kg")
    c3.metric("Simulated Consumption", f"{total_consumed_today:.1f} kg")
    c4.metric("Low / Critical Drums", str(low_drums))

    st.subheader("Drum Inventory Status")

    rows = []
    for drum_id, d in drums.items():
        pct = d["stock"] / d["capacity"] * 100
        rows.append({
            "Drum ID": drum_id,
            "Sealer Type": d["type"],
            "Remaining (kg)": d["stock"],
            "Capacity (kg)": d["capacity"],
            "Remaining (%)": round(pct, 1),
            "Status": status_of(d["stock"], d["capacity"])
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    left, right = st.columns(2)

    with left:
        fig = px.bar(
            df,
            x="Drum ID",
            y="Remaining (kg)",
            color="Status",
            title="Remaining Sealer by Drum",
            hover_data=["Sealer Type", "Remaining (%)"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.pie(
            df,
            names="Drum ID",
            values="Remaining (kg)",
            hole=0.45,
            title="Inventory Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Inventory Alerts")
    alerts = df[df["Status"].isin(["Low", "Critical", "Empty"])]

    if alerts.empty:
        st.success("All drums are above the low-stock threshold.")
    else:
        for _, row in alerts.iterrows():
            if row["Status"] == "Critical" or row["Status"] == "Empty":
                st.error(
                    f'{row["Drum ID"]}: {row["Remaining (kg)"]:.1f} kg remaining — '
                    f'{row["Status"]} stock'
                )
            else:
                st.warning(
                    f'{row["Drum ID"]}: {row["Remaining (kg)"]:.1f} kg remaining — Low stock'
                )

# ---------------- DRUM MONITORING ----------------
elif page == "Drum Monitoring":
    st.title("Drum Monitoring")

    selected = st.selectbox("Select Drum", list(drums.keys()))
    d = drums[selected]
    pct = d["stock"] / d["capacity"] * 100
    remaining_height = pct  # Illustrative percentage, not a real distance

    a, b, c = st.columns(3)
    a.metric("Remaining Sealer", f'{d["stock"]:.1f} kg')
    b.metric("Capacity", f'{d["capacity"]:.1f} kg')
    c.metric("Remaining Level", f"{pct:.1f}%")

    st.progress(min(max(pct / 100, 0.0), 1.0))
    st.write("**Sealer Type:**", d["type"])
    st.write("**Inventory Status:**", status_of(d["stock"], d["capacity"]))

    st.caption(
        "Level bar is calculated from simulated stock. "
        "It is not a real sensor measurement."
    )

    st.subheader("Drum Actions")
    x, y = st.columns(2)

    with x:
        qty = st.number_input(
            "Consumption quantity (kg)",
            min_value=0.1,
            max_value=float(d["capacity"]),
            value=5.0,
            step=1.0,
            key="manual_consume"
        )
        if st.button("Record Consumption", use_container_width=True):
            if d["stock"] <= 0:
                st.error("Drum is empty.")
            else:
                consume(selected, qty)
                st.success("Consumption recorded.")
                st.rerun()

    with y:
        refill_qty = st.number_input(
            "Refill quantity (kg)",
            min_value=0.1,
            max_value=float(d["capacity"]),
            value=20.0,
            step=1.0,
            key="manual_refill"
        )
        if st.button("Receive / Refill Sealer", use_container_width=True):
            if d["stock"] >= d["capacity"]:
                st.warning("Drum is already full.")
            else:
                refill(selected, refill_qty)
                st.success("Receipt recorded.")
                st.rerun()

# ---------------- SENSOR SIMULATION ---------------
elif page == "Sensor Simulation":
    st.title("IoT Sensor Simulation")
    st.info(
        "This page simulates sensor behavior. No physical ESP32 or sensor is connected."
    )

    selected = st.selectbox("Select Drum for Simulation", list(drums.keys()))
    d = drums[selected]

    st.subheader("Simulated Sensor Settings")
    consumption_rate = st.slider(
        "Consumption per simulation step (kg)",
        min_value=1.0,
        max_value=20.0,
        value=5.0,
        step=1.0
    )

    st.caption(
        "Each click on the simulation button represents one consumption step."
    )

    p1, p2, p3 = st.columns(3)
    p1.metric("Simulated True Mass", f'{d["stock"]:.1f} kg')
    p2.metric(
        "Simulated Level",
        f'{d["stock"] / d["capacity"] * 100:.1f}%'
    )
    p3.metric("Sensor State", "ONLINE (SIMULATED)")

    # Illustrative distance only: 10 cm offset plus a scaled level.
    simulated_distance = (
        st.session_state.sensor_offset
        + (1 - d["stock"] / d["capacity"]) * 80
    )
    st.metric("Simulated Sensor Distance", f"{simulated_distance:.1f} cm")
    st.caption(
        "Distance uses an illustrative mathematical model. "
        "It must be calibrated for an actual follower plate."
    )

    a, b, c = st.columns(3)

    with a:
        if st.button("▶ Simulate Consumption", use_container_width=True):
            consume(selected, consumption_rate)
            st.rerun()

    with b:
        if st.button("＋ Simulate Refill 20 kg", use_container_width=True):
            refill(selected, 20)
            st.rerun()

    with c:
        if st.button("Reset Selected Drum", use_container_width=True):
            old = d["stock"]
            d["stock"] = d["capacity"]
            log_transaction(
                selected, "Demo Reset", d["capacity"] - old, d["stock"]
            )
            st.rerun()

    st.subheader("Simulated Level Indicator")
    st.progress(max(0.0, min(1.0, d["stock"] / d["capacity"])))
    st.write(f"**{status_of(d['stock'], d['capacity'])}**")

# ---------------- TRANSACTIONS ---------------------
elif page == "Inventory Transactions":
    st.title("Inventory Transactions")

    if st.session_state.transactions:
        tx = pd.DataFrame(st.session_state.transactions)
        st.dataframe(tx, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Transactions CSV",
            data=tx.to_csv(index=False).encode("utf-8"),
            file_name="sealer_inventory_transactions.csv",
            mime="text/csv"
        )
    else:
        st.info("No transactions yet. Record consumption or a refill to begin.")

    st.subheader("Record Material Consumption")
    with st.form("consumption_form"):
        drum_id = st.selectbox("Drum", list(drums.keys()), key="tx_drum")
        qty = st.number_input("Quantity consumed (kg)", min_value=0.1, value=5.0)
        submitted = st.form_submit_button("Save Consumption")

        if submitted:
            if qty > drums[drum_id]["stock"]:
                st.error("Consumption cannot exceed the available drum quantity.")
            else:
                consume(drum_id, qty)
                st.success("Transaction saved.")
                st.rerun()

    st.subheader("Record Material Receipt")
    with st.form("receipt_form"):
        drum_id = st.selectbox("Drum to refill", list(drums.keys()), key="rx_drum")
        qty = st.number_input("Quantity received (kg)", min_value=0.1, value=20.0)
        submitted = st.form_submit_button("Save Receipt")

        if submitted:
            available = drums[drum_id]["capacity"] - drums[drum_id]["stock"]
            if qty > available:
                st.error(f"Drum capacity exceeded. Available space: {available:.1f} kg.")
            else:
                refill(drum_id, qty)
                st.success("Receipt saved.")
                st.rerun()

# ---------------- SETTINGS -------------------------
elif page == "Settings":
    st.title("Inventory Settings")

    st.write("Configure demo drum capacity and inventory thresholds.")
    selected = st.selectbox("Select Drum", list(drums.keys()))
    d = drums[selected]

    new_capacity = st.number_input(
        "Nominal drum capacity (kg)",
        min_value=1.0,
        max_value=2000.0,
        value=float(d["capacity"])
    )

    if st.button("Save Capacity"):
        if new_capacity < d["stock"]:
            st.error("Capacity cannot be lower than the current stock.")
        else:
            d["capacity"] = float(new_capacity)
            st.success("Capacity updated.")
            st.rerun()

    st.divider()
    st.subheader("Reorder Planning")

    daily_use = st.number_input(
        "Average daily consumption (kg)",
        min_value=0.1,
        value=100.0
    )
    lead_time = st.number_input(
        "Supplier lead time (days)",
        min_value=0,
        value=5
    )
    safety_stock = st.number_input(
        "Safety stock (kg)",
        min_value=0.0,
        value=100.0
    )

    reorder_point = daily_use * lead_time + safety_stock
    coverage = total_stock / daily_use if daily_use > 0 else 0

    a, b = st.columns(2)
    a.metric("Reorder Point", f"{reorder_point:.1f} kg")
    b.metric("Estimated Stock Coverage", f"{coverage:.1f} days")

    if total_stock <= reorder_point:
        st.error("REORDER REQUIRED — Inventory has reached the reorder point.")
    else:
        st.success("Inventory is above the configured reorder point.")

    st.divider()
    if st.button("Reset All Demo Data"):
        for drum in drums.values():
            drum["stock"] = drum["capacity"]
        st.session_state.transactions = []
        st.session_state.daily_consumption = 0.0
        st.success("Demo drums reset to full. Settings and drum IDs are retained.")
        st.rerun()

# ---------------- FOOTER ---------------------------
st.sidebar.divider()
st.sidebar.caption("Smart Sealer Inventory | Prototype v1.0")
st.sidebar.caption("Demo data is stored in the current session.")
