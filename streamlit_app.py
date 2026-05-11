import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="NIRVC Inventory Command Center", layout="wide")

st.title("NIRVC Inventory Command Center")
st.caption("Inventory control, business mix, aging risk, profitability, and weekly movement")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #e6e8eb;
        padding: 18px;
        border-radius: 14px;
    }
    h2, h3 { margin-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True
)

prior_file = st.file_uploader("Upload PRIOR week inventory spreadsheet", type=["xlsx"])
current_file = st.file_uploader("Upload CURRENT week inventory spreadsheet", type=["xlsx"])


def load_file(file):
    df = pd.read_excel(file, header=0)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how="all")

    numeric_cols = [
        "Age",
        "Total Current Cost Of Veh",
        "Purchase Price of Veh",
        "Suggested Selling Price",
        "Yr",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = [
        "Stock Number",
        "NUD",
        "On Order",
        "On Hold",
        "Manufacturer",
        "Make",
        "Model",
        "ProfitCenter",
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    return df


def money_format(series):
    return series.apply(lambda x: "${:,.0f}".format(x) if pd.notna(x) else "$0")


def action_flag(age):
    if pd.isna(age):
        return "REVIEW"
    if age >= 365:
        return "LIQUIDATE / BOOK VALUE REVIEW"
    elif age >= 270:
        return "LIQUIDATE"
    elif age >= 180:
        return "AGGRESSIVE PRICE"
    elif age >= 120:
        return "PRICE ADJUST"
    else:
        return "HOLD"


def add_economic_fields(df, floorplan_rate):
    df = df.copy()

    df["Daily Flooring Cost"] = (
        df["Total Current Cost Of Veh"] * floorplan_rate / 365
    )

    df["Accumulated Flooring Cost"] = (
        df["Daily Flooring Cost"] * df["Age"]
    )

    df["Book Value Drop Rate"] = np.where(
        df["Age"] >= 365,
        0.10 + (np.floor((df["Age"] - 365) / 90).clip(lower=0) * 0.04),
        0
    )

    df["Book Value Drop"] = (
        df["Total Current Cost Of Veh"] * df["Book Value Drop Rate"]
    )

    df["Expected Gross Profit"] = (
        df["Suggested Selling Price"] - df["Total Current Cost Of Veh"]
    )

    df["Total Economic Drag"] = (
        df["Accumulated Flooring Cost"] +
        df["Book Value Drop"] -
        df["Expected Gross Profit"]
    )

    df["Action"] = df["Age"].apply(action_flag)

    return df


if current_file is not None:
    df = load_file(current_file)
    st.success("Current week spreadsheet uploaded successfully.")

    floorplan_rate = 0.058
    consignment_fee_rate = 0.075

    # Core splits
    on_ground_df = df[df["On Order"] == "N"].copy()
    on_order_df = df[df["On Order"] == "Y"].copy()

    new_on_ground_df = df[
        (df["NUD"].str.startswith("N")) &
        (df["On Order"] == "N")
    ].copy()

    new_on_order_df = df[
        (df["NUD"].str.startswith("N")) &
        (df["On Order"] == "Y")
    ].copy()

    used_owned_on_ground_df = df[
        (df["NUD"].str.startswith("U")) &
        (df["On Order"] == "N") &
        (df["Purchase Price of Veh"] > 0)
    ].copy()

    consigned_on_ground_df = df[
        (df["NUD"].str.startswith("U")) &
        (df["On Order"] == "N") &
        (df["Purchase Price of Veh"] == 0)
    ].copy()

    demo_on_ground_df = df[
        (df["NUD"].str.startswith("D")) &
        (df["On Order"] == "N")
    ].copy()

    # Add calculated fields early
    on_ground_df = add_economic_fields(on_ground_df, floorplan_rate)
    new_on_ground_df = add_economic_fields(new_on_ground_df, floorplan_rate)

    available_new_on_ground_df = new_on_ground_df[
        new_on_ground_df["On Hold"] == "N"
    ].copy()

    # Consignment economics
    consigned_on_ground_df["Potential Consignment Gross Profit"] = (
        consigned_on_ground_df["Suggested Selling Price"] * consignment_fee_rate
    )

    consigned_avg_asking_price = consigned_on_ground_df["Suggested Selling Price"].mean()
    total_consignment_asking_value = consigned_on_ground_df["Suggested Selling Price"].sum()
    total_consignment_gross_profit = consigned_on_ground_df[
        "Potential Consignment Gross Profit"
    ].sum()

    # Expo / stock number flags
    stock_numbers = df["Stock Number"]

    vegas_expo_order_df = df[stock_numbers.str.endswith("VXO")].copy()

    vegas_expo_df = df[
        stock_numbers.str.endswith("VX") &
        ~stock_numbers.str.endswith("VXO")
    ].copy()

    mcme_expo_order_df = df[
        stock_numbers.str.endswith("XO") &
        ~stock_numbers.str.endswith("VXO")
    ].copy()

    mcme_expo_df = df[
        stock_numbers.str.endswith("X") &
        ~stock_numbers.str.endswith("VX") &
        ~stock_numbers.str.endswith("XO") &
        ~stock_numbers.str.endswith("VXO")
    ].copy()

    # Counts
    total_pipeline_units = len(df)
    on_ground_units = len(on_ground_df)
    on_order_units = len(on_order_df)
    on_hold_units = len(on_ground_df[on_ground_df["On Hold"] == "Y"])

    new_on_ground_units = len(new_on_ground_df)
    used_owned_on_ground_units = len(used_owned_on_ground_df)
    consigned_on_ground_units = len(consigned_on_ground_df)
    demo_on_ground_units = len(demo_on_ground_df)

    # Dollars
    total_pipeline_cost = df["Total Current Cost Of Veh"].sum()
    on_ground_cost = on_ground_df["Total Current Cost Of Veh"].sum()
    on_order_cost = on_order_df["Total Current Cost Of Veh"].sum()

    new_on_ground_cost = new_on_ground_df["Total Current Cost Of Veh"].sum()
    new_on_order_cost = new_on_order_df["Total Current Cost Of Veh"].sum()
    used_owned_on_ground_cost = used_owned_on_ground_df["Total Current Cost Of Veh"].sum()
    demo_on_ground_cost = demo_on_ground_df["Total Current Cost Of Veh"].sum()

    new_on_ground_avg_cost = new_on_ground_df["Total Current Cost Of Veh"].mean()

    units_240 = on_ground_df[on_ground_df["Age"] >= 240].shape[0]
    daily_carrying_cost = new_on_ground_cost * floorplan_rate / 365
    monthly_carrying_cost = new_on_ground_cost * floorplan_rate / 12

    # ======================================================
    # 1. EXECUTIVE SCOREBOARD
    # ======================================================

    st.markdown("## 📊 Executive Scoreboard")

    st.markdown("### Inventory Position")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pipeline", total_pipeline_units)
    col2.metric("On-Ground Units", on_ground_units)
    col3.metric("On-Order Units", on_order_units)
    col4.metric("On-Hold Units", on_hold_units)

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("New On-Ground Units", new_on_ground_units)
    col6.metric("Used Owned On-Ground Units", used_owned_on_ground_units)
    col7.metric("Consigned On-Ground Units", consigned_on_ground_units)
    col8.metric("Demo On-Ground Units", demo_on_ground_units)

    st.markdown("### Capital Deployed")
    col9, col10, col11 = st.columns(3)
    col9.metric("Capital Deployed - On Ground", f"${on_ground_cost:,.0f}")
    col10.metric("New On-Ground $", f"${new_on_ground_cost:,.0f}")
    col11.metric("Used Owned On-Ground $", f"${used_owned_on_ground_cost:,.0f}")

    st.markdown("### Incoming Pipeline Commitments")
    col12, col13, col14 = st.columns(3)
    col12.metric("On-Order Units", on_order_units)
    col13.metric("On-Order Pipeline $", f"${on_order_cost:,.0f}")
    col14.metric("Total Pipeline $", f"${total_pipeline_cost:,.0f}")

    st.markdown("### Floorplan & Consignment Snapshot")
    col15, col16, col17, col18 = st.columns(4)
    col15.metric("Daily Carrying Cost - New", f"${daily_carrying_cost:,.0f}")
    col16.metric("Monthly Carrying Cost - New", f"${monthly_carrying_cost:,.0f}")
    col17.metric("Avg Consigned Asking Price", f"${consigned_avg_asking_price:,.0f}")
    col18.metric("Potential Consignment GP", f"${total_consignment_gross_profit:,.0f}")

    if units_240 > 150:
        st.error("⚠️ High 240+ inventory risk — immediate action required")
    elif units_240 > 100:
        st.warning("⚠️ Elevated 240+ inventory — monitor closely")
    else:
        st.success("✅ 240+ inventory aging within acceptable range")

    st.divider()

    # ======================================================
    # 2. MANUFACTURER BUSINESS MIX
    # ======================================================

    st.markdown("## 🏭 Manufacturer Business Mix")

    manufacturer_business = (
        df.groupby("Manufacturer")
        .agg(
            Total_Pipeline_Units=("Stock Number", "count"),
            Total_Pipeline_Dollars=("Total Current Cost Of Veh", "sum"),
        )
        .reset_index()
    )

    on_ground_by_manufacturer = (
        on_ground_df.groupby("Manufacturer")
        .agg(
            On_Ground_Units=("Stock Number", "count"),
            On_Ground_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
            Units_240_Plus=("Age", lambda x: (x >= 240).sum()),
            Inventory_240_Plus_Dollars=(
                "Total Current Cost Of Veh",
                lambda x: x[on_ground_df.loc[x.index, "Age"] >= 240].sum(),
            ),
        )
        .reset_index()
    )

    on_order_by_manufacturer = (
        on_order_df.groupby("Manufacturer")
        .agg(
            On_Order_Units=("Stock Number", "count"),
            On_Order_Dollars=("Total Current Cost Of Veh", "sum"),
        )
        .reset_index()
    )

    manufacturer_business = manufacturer_business.merge(
        on_ground_by_manufacturer,
        on="Manufacturer",
        how="left"
    )

    manufacturer_business = manufacturer_business.merge(
        on_order_by_manufacturer,
        on="Manufacturer",
        how="left"
    )

    manufacturer_business = manufacturer_business.fillna(0)

    total_pipeline_value = manufacturer_business["Total_Pipeline_Dollars"].sum()

    manufacturer_business["Percent_of_Total_Pipeline_Dollars"] = np.where(
        total_pipeline_value > 0,
        manufacturer_business["Total_Pipeline_Dollars"] /
        total_pipeline_value * 100,
        0
    )

    manufacturer_business = manufacturer_business.sort_values(
        "Total_Pipeline_Dollars",
        ascending=False
    )

    manufacturer_display = manufacturer_business.copy()

    for col in [
        "Total_Pipeline_Dollars",
        "On_Ground_Dollars",
        "On_Order_Dollars",
        "Inventory_240_Plus_Dollars",
    ]:
        manufacturer_display[col] = money_format(manufacturer_display[col])

    manufacturer_display["Percent_of_Total_Pipeline_Dollars"] = manufacturer_display[
        "Percent_of_Total_Pipeline_Dollars"
    ].map("{:.1f}%".format)

    manufacturer_display["Average_Age"] = manufacturer_display["Average_Age"].round(0)

    manufacturer_display = manufacturer_display[
        [
            "Manufacturer",
            "Total_Pipeline_Dollars",
            "Percent_of_Total_Pipeline_Dollars",
            "Total_Pipeline_Units",
            "On_Ground_Dollars",
            "On_Ground_Units",
            "On_Order_Dollars",
            "On_Order_Units",
            "Average_Age",
            "Units_240_Plus",
            "Inventory_240_Plus_Dollars",
        ]
    ]

    st.dataframe(manufacturer_display, use_container_width=True, hide_index=True)

    st.divider()

    # ======================================================
    # 3. AGING RISK & ECONOMIC DRAG
    # ======================================================

    st.markdown("## ⚠️ Aging Risk & Economic Drag")

    st.markdown("### Aging Buckets - On-Ground Inventory")

    aging_buckets = {
        "< 90 Days": on_ground_df[
            on_ground_df["Age"] < 90
        ]["Total Current Cost Of Veh"].sum(),
        "91-180 Days": on_ground_df[
            (on_ground_df["Age"] >= 90) &
            (on_ground_df["Age"] <= 180)
        ]["Total Current Cost Of Veh"].sum(),
        "181-270 Days": on_ground_df[
            (on_ground_df["Age"] > 180) &
            (on_ground_df["Age"] <= 270)
        ]["Total Current Cost Of Veh"].sum(),
        "271-365 Days": on_ground_df[
            (on_ground_df["Age"] > 270) &
            (on_ground_df["Age"] <= 365)
        ]["Total Current Cost Of Veh"].sum(),
        "365+ Days": on_ground_df[
            on_ground_df["Age"] > 365
        ]["Total Current Cost Of Veh"].sum(),
    }

    col19, col20, col21, col22, col23 = st.columns(5)
    col19.metric("< 90 Days", f"${aging_buckets['< 90 Days']:,.0f}")
    col20.metric("91-180 Days", f"${aging_buckets['91-180 Days']:,.0f}")
    col21.metric("181-270 Days", f"${aging_buckets['181-270 Days']:,.0f}")
    col22.metric("271-365 Days", f"${aging_buckets['271-365 Days']:,.0f}")
    col23.metric("365+ Days", f"${aging_buckets['365+ Days']:,.0f}")

    st.markdown("### Aging Cost Analysis - On-Ground Inventory")

    aging_cost_summary = (
        on_ground_df
        .assign(
            Age_Bucket=pd.cut(
                on_ground_df["Age"],
                bins=[-1, 90, 180, 270, 365, float("inf")],
                labels=[
                    "< 90 Days",
                    "91-180 Days",
                    "181-270 Days",
                    "271-365 Days",
                    "365+ Days",
                ],
            )
        )
        .groupby("Age_Bucket", observed=False)
        .agg(
            Units=("Stock Number", "count"),
            Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Daily_Flooring_Cost=("Daily Flooring Cost", "sum"),
            Accumulated_Flooring_Cost=("Accumulated Flooring Cost", "sum"),
            Book_Value_Drop=("Book Value Drop", "sum"),
            Expected_Gross_Profit=("Expected Gross Profit", "sum"),
            Total_Economic_Drag=("Total Economic Drag", "sum"),
            Average_Age=("Age", "mean"),
        )
        .reset_index()
    )

    aging_cost_display = aging_cost_summary.copy()

    for col in [
        "Inventory_Dollars",
        "Daily_Flooring_Cost",
        "Accumulated_Flooring_Cost",
        "Book_Value_Drop",
        "Expected_Gross_Profit",
        "Total_Economic_Drag",
    ]:
        aging_cost_display[col] = money_format(aging_cost_display[col])

    aging_cost_display["Average_Age"] = aging_cost_display["Average_Age"].round(0)

    st.dataframe(aging_cost_display, use_container_width=True, hide_index=True)

    st.subheader("🚨 Oldest 10% of New On-Ground Inventory")

    oldest_10_percent_count = max(1, round(len(new_on_ground_df) * 0.10))

    oldest_10_percent_new = (
        new_on_ground_df
        .sort_values("Age", ascending=False)
        .head(oldest_10_percent_count)
        .copy()
    )

    oldest_10_cost = oldest_10_percent_new["Total Current Cost Of Veh"].sum()
    oldest_10_avg_age = oldest_10_percent_new["Age"].mean()
    oldest_10_avg_cost = oldest_10_percent_new["Total Current Cost Of Veh"].mean()
    oldest_10_economic_drag = oldest_10_percent_new["Total Economic Drag"].sum()
    oldest_10_daily_flooring = oldest_10_percent_new["Daily Flooring Cost"].sum()
    oldest_10_accumulated_flooring = oldest_10_percent_new["Accumulated Flooring Cost"].sum()
    oldest_10_book_value_drop = oldest_10_percent_new["Book Value Drop"].sum()
    oldest_10_expected_gross = oldest_10_percent_new["Expected Gross Profit"].sum()

    oldest_10_percent_of_new_on_ground = (
        oldest_10_cost / new_on_ground_cost * 100
        if new_on_ground_cost > 0 else 0
    )

    st.caption(
        f"Showing {oldest_10_percent_count} units out of "
        f"{len(new_on_ground_df)} new on-ground units."
    )

    col24, col25, col26, col27 = st.columns(4)
    col24.metric("Oldest 10% Inventory $", f"${oldest_10_cost:,.0f}")
    col25.metric("% of New On-Ground $", f"{oldest_10_percent_of_new_on_ground:.1f}%")
    col26.metric("Average Age", f"{oldest_10_avg_age:.0f} days")
    col27.metric("Average Cost / Unit", f"${oldest_10_avg_cost:,.0f}")

    col28, col29, col30, col31 = st.columns(4)
    col28.metric("Daily Flooring Burn", f"${oldest_10_daily_flooring:,.0f}")
    col29.metric("Accumulated Flooring Cost", f"${oldest_10_accumulated_flooring:,.0f}")
    col30.metric("Book Value Drop", f"${oldest_10_book_value_drop:,.0f}")
    col31.metric("Expected Gross Profit", f"${oldest_10_expected_gross:,.0f}")

    col32, col33 = st.columns(2)
    col32.metric("Total Economic Drag", f"${oldest_10_economic_drag:,.0f}")
    col33.metric("Floorplan Rate", f"{floorplan_rate:.2%}")

    oldest_10_by_store = (
        oldest_10_percent_new
        .groupby("ProfitCenter")
        .agg(
            Units=("Stock Number", "count"),
            Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Daily_Flooring_Cost=("Daily Flooring Cost", "sum"),
            Accumulated_Flooring_Cost=("Accumulated Flooring Cost", "sum"),
            Book_Value_Drop=("Book Value Drop", "sum"),
            Expected_Gross_Profit=("Expected Gross Profit", "sum"),
            Total_Economic_Drag=("Total Economic Drag", "sum"),
            Average_Age=("Age", "mean"),
        )
        .reset_index()
        .sort_values("Total_Economic_Drag", ascending=False)
    )

    oldest_10_by_store_display = oldest_10_by_store.copy()

    for col in [
        "Inventory_Dollars",
        "Daily_Flooring_Cost",
        "Accumulated_Flooring_Cost",
        "Book_Value_Drop",
        "Expected_Gross_Profit",
        "Total_Economic_Drag",
    ]:
        oldest_10_by_store_display[col] = money_format(oldest_10_by_store_display[col])

    oldest_10_by_store_display["Average_Age"] = oldest_10_by_store_display[
        "Average_Age"
    ].round(0)

    st.markdown("#### Oldest 10% by Location")
    st.dataframe(oldest_10_by_store_display, use_container_width=True, hide_index=True)

    oldest_10_by_make = (
        oldest_10_percent_new
        .groupby("Make")
        .agg(
            Units=("Stock Number", "count"),
            Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Daily_Flooring_Cost=("Daily Flooring Cost", "sum"),
            Accumulated_Flooring_Cost=("Accumulated Flooring Cost", "sum"),
            Book_Value_Drop=("Book Value Drop", "sum"),
            Expected_Gross_Profit=("Expected Gross Profit", "sum"),
            Total_Economic_Drag=("Total Economic Drag", "sum"),
            Average_Age=("Age", "mean"),
        )
        .reset_index()
        .sort_values("Total_Economic_Drag", ascending=False)
    )

    oldest_10_by_make_display = oldest_10_by_make.copy()

    for col in [
        "Inventory_Dollars",
        "Daily_Flooring_Cost",
        "Accumulated_Flooring_Cost",
        "Book_Value_Drop",
        "Expected_Gross_Profit",
        "Total_Economic_Drag",
    ]:
        oldest_10_by_make_display[col] = money_format(oldest_10_by_make_display[col])

    oldest_10_by_make_display["Average_Age"] = oldest_10_by_make_display[
        "Average_Age"
    ].round(0)

    st.markdown("#### Oldest 10% by Make")
    st.dataframe(oldest_10_by_make_display, use_container_width=True, hide_index=True)

    st.markdown("#### Unit Detail - Oldest 10%")

    oldest_10_detail = oldest_10_percent_new.copy()

    detail_columns = [
        "Stock Number",
        "ProfitCenter",
        "Yr",
        "Manufacturer",
        "Make",
        "Model",
        "Age",
        "Total Current Cost Of Veh",
        "Suggested Selling Price",
        "Expected Gross Profit",
        "Daily Flooring Cost",
        "Accumulated Flooring Cost",
        "Book Value Drop Rate",
        "Book Value Drop",
        "Total Economic Drag",
        "Action",
    ]

    oldest_10_detail = oldest_10_detail[
        [col for col in detail_columns if col in oldest_10_detail.columns]
    ].copy()

    for col in [
        "Total Current Cost Of Veh",
        "Suggested Selling Price",
        "Expected Gross Profit",
        "Daily Flooring Cost",
        "Accumulated Flooring Cost",
        "Book Value Drop",
        "Total Economic Drag",
    ]:
        if col in oldest_10_detail.columns:
            oldest_10_detail[col] = money_format(oldest_10_detail[col])

    if "Book Value Drop Rate" in oldest_10_detail.columns:
        oldest_10_detail["Book Value Drop Rate"] = oldest_10_detail[
            "Book Value Drop Rate"
        ].map("{:.1%}".format)

    st.dataframe(oldest_10_detail, use_container_width=True, hide_index=True)

    st.subheader("💣 Top Economic Offenders")

    top_offenders = (
        new_on_ground_df
        .sort_values("Total Economic Drag", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    top_offenders_display = top_offenders[
        [
            "Stock Number",
            "ProfitCenter",
            "Yr",
            "Manufacturer",
            "Make",
            "Model",
            "Age",
            "Total Current Cost Of Veh",
            "Suggested Selling Price",
            "Expected Gross Profit",
            "Daily Flooring Cost",
            "Accumulated Flooring Cost",
            "Book Value Drop Rate",
            "Book Value Drop",
            "Total Economic Drag",
            "Action",
        ]
    ].copy()

    for col in [
        "Total Current Cost Of Veh",
        "Suggested Selling Price",
        "Expected Gross Profit",
        "Daily Flooring Cost",
        "Accumulated Flooring Cost",
        "Book Value Drop",
        "Total Economic Drag",
    ]:
        top_offenders_display[col] = money_format(top_offenders_display[col])

    top_offenders_display["Book Value Drop Rate"] = top_offenders_display[
        "Book Value Drop Rate"
    ].map("{:.1%}".format)

    st.caption(
        "Ranked by Total Economic Drag = Accumulated Flooring Cost + Book Value Drop - Expected Gross Profit."
    )

    st.dataframe(top_offenders_display, use_container_width=True, hide_index=True)

    st.divider()

    # ======================================================
    # 4. STORE COMMAND BOARD
    # ======================================================

    st.markdown("## 🏬 Store Command Board")

    new_store = (
        new_on_ground_df.groupby("ProfitCenter")
        .agg(
            New_Units=("Stock Number", "count"),
            New_Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            New_Avg_Age=("Age", "mean"),
            New_240_Plus_Units=("Age", lambda x: (x >= 240).sum()),
            New_240_Plus_Dollars=(
                "Total Current Cost Of Veh",
                lambda x: x[new_on_ground_df.loc[x.index, "Age"] >= 240].sum(),
            ),
            New_Daily_Flooring_Cost=("Daily Flooring Cost", "sum"),
            New_Total_Economic_Drag=("Total Economic Drag", "sum"),
        )
        .reset_index()
    )

    used_store = (
        used_owned_on_ground_df.groupby("ProfitCenter")
        .agg(
            Used_Owned_Units=("Stock Number", "count"),
            Used_Owned_Dollars=("Total Current Cost Of Veh", "sum"),
            Used_Avg_Age=("Age", "mean"),
        )
        .reset_index()
    )

    consignment_store = (
        consigned_on_ground_df.groupby("ProfitCenter")
        .agg(
            Consigned_Units=("Stock Number", "count"),
            Consignment_Asking_Dollars=("Suggested Selling Price", "sum"),
            Potential_Consignment_GP=("Potential Consignment Gross Profit", "sum"),
            Consignment_Avg_Age=("Age", "mean"),
        )
        .reset_index()
    )

    demo_store = (
        demo_on_ground_df.groupby("ProfitCenter")
        .agg(
            Demo_Units=("Stock Number", "count"),
            Demo_Dollars=("Total Current Cost Of Veh", "sum"),
        )
        .reset_index()
    )

    store_scoreboard = new_store.merge(used_store, on="ProfitCenter", how="outer")
    store_scoreboard = store_scoreboard.merge(consignment_store, on="ProfitCenter", how="outer")
    store_scoreboard = store_scoreboard.merge(demo_store, on="ProfitCenter", how="outer")
    store_scoreboard = store_scoreboard.fillna(0)

    store_scoreboard = store_scoreboard.sort_values(
        "New_Inventory_Dollars",
        ascending=False
    )

    store_display = store_scoreboard.copy()

    for col in [
        "New_Inventory_Dollars",
        "New_240_Plus_Dollars",
        "New_Daily_Flooring_Cost",
        "New_Total_Economic_Drag",
        "Used_Owned_Dollars",
        "Consignment_Asking_Dollars",
        "Potential_Consignment_GP",
        "Demo_Dollars",
    ]:
        store_display[col] = money_format(store_display[col])

    for col in [
        "New_Avg_Age",
        "Used_Avg_Age",
        "Consignment_Avg_Age",
    ]:
        store_display[col] = store_display[col].round(0)

    st.dataframe(store_display, use_container_width=True, hide_index=True)

    st.divider()

    # ======================================================
    # 5. CONSIGNMENT ECONOMICS
    # ======================================================

    st.markdown("## 🤝 Consignment Economics")

    col34, col35, col36 = st.columns(3)
    col34.metric("Consignment Asking Value", f"${total_consignment_asking_value:,.0f}")
    col35.metric("Consignment Fee Rate", f"{consignment_fee_rate:.1%}")
    col36.metric("Potential Consignment GP", f"${total_consignment_gross_profit:,.0f}")

    consigned_on_ground_df["Consignment Price Band"] = pd.cut(
        consigned_on_ground_df["Suggested Selling Price"],
        bins=[0, 100000, 160000, 200000, 250000, 300000, 400000, float("inf")],
        labels=[
            "<100K",
            "100K-160K",
            "160K-200K",
            "200K-250K",
            "250K-300K",
            "300K-400K",
            "400K+",
        ],
    )

    consignment_band_summary = (
        consigned_on_ground_df
        .groupby("Consignment Price Band", observed=False)
        .agg(
            Units=("Stock Number", "count"),
            Asking_Dollars=("Suggested Selling Price", "sum"),
            Average_Asking_Price=("Suggested Selling Price", "mean"),
            Potential_GP=("Potential Consignment Gross Profit", "sum"),
            Average_Age=("Age", "mean"),
        )
        .reset_index()
    )

    consignment_band_display = consignment_band_summary.copy()

    for col in [
        "Asking_Dollars",
        "Average_Asking_Price",
        "Potential_GP",
    ]:
        consignment_band_display[col] = money_format(consignment_band_display[col])

    consignment_band_display["Average_Age"] = consignment_band_display[
        "Average_Age"
    ].round(0)

    st.markdown("### Consignment Price Band Analysis")
    st.dataframe(consignment_band_display, use_container_width=True, hide_index=True)

    consignment_by_store = (
        consigned_on_ground_df
        .groupby("ProfitCenter")
        .agg(
            Consigned_Units=("Stock Number", "count"),
            Asking_Dollars=("Suggested Selling Price", "sum"),
            Average_Asking_Price=("Suggested Selling Price", "mean"),
            Potential_GP=("Potential Consignment Gross Profit", "sum"),
            Average_Age=("Age", "mean"),
        )
        .reset_index()
        .sort_values("Asking_Dollars", ascending=False)
    )

    consignment_by_store_display = consignment_by_store.copy()

    for col in [
        "Asking_Dollars",
        "Average_Asking_Price",
        "Potential_GP",
    ]:
        consignment_by_store_display[col] = money_format(consignment_by_store_display[col])

    consignment_by_store_display["Average_Age"] = consignment_by_store_display[
        "Average_Age"
    ].round(0)

    st.markdown("### Consignment Inventory by Store")
    st.dataframe(consignment_by_store_display, use_container_width=True, hide_index=True)

    st.divider()

    # ======================================================
    # 6. WEEKLY INVENTORY MOVEMENT
    # ======================================================

    st.markdown("## 🔁 Weekly Inventory Movement")

    if prior_file is not None:
        prior_df = load_file(prior_file)
        prior_on_ground_df = prior_df[prior_df["On Order"] == "N"].copy()

        current_stocks = set(on_ground_df["Stock Number"])
        prior_stocks = set(prior_on_ground_df["Stock Number"])

        new_stocks = current_stocks - prior_stocks
        sold_or_removed_stocks = prior_stocks - current_stocks

        new_units = on_ground_df[on_ground_df["Stock Number"].isin(new_stocks)].copy()
        removed_units = prior_on_ground_df[
            prior_on_ground_df["Stock Number"].isin(sold_or_removed_stocks)
        ].copy()

        new_units_cost = new_units["Total Current Cost Of Veh"].sum()
        removed_units_cost = removed_units["Total Current Cost Of Veh"].sum()

        col37, col38, col39 = st.columns(3)
        col37.metric("New On-Ground Units Added", len(new_units))
        col38.metric("Units Sold / Removed", len(removed_units))
        col39.metric("Net On-Ground Unit Change", len(new_units) - len(removed_units))

        col40, col41, col42 = st.columns(3)
        col40.metric("New On-Ground Inventory $ Added", f"${new_units_cost:,.0f}")
        col41.metric("Inventory $ Sold / Removed", f"${removed_units_cost:,.0f}")
        col42.metric("Net Inventory $ Change", f"${new_units_cost - removed_units_cost:,.0f}")

        def movement_summary(group_col):
            prior_group = (
                prior_on_ground_df
                .groupby(group_col)
                .agg(
                    Prior_On_Ground_Units=("Stock Number", "count"),
                    Prior_On_Ground_Dollars=("Total Current Cost Of Veh", "sum"),
                )
                .reset_index()
            )

            added_group = (
                new_units
                .groupby(group_col)
                .agg(
                    Units_Added=("Stock Number", "count"),
                    Dollars_Added=("Total Current Cost Of Veh", "sum"),
                )
                .reset_index()
            )

            removed_group = (
                removed_units
                .groupby(group_col)
                .agg(
                    Units_Sold_Removed=("Stock Number", "count"),
                    Dollars_Sold_Removed=("Total Current Cost Of Veh", "sum"),
                )
                .reset_index()
            )

            current_group = (
                on_ground_df
                .groupby(group_col)
                .agg(
                    Current_On_Ground_Units=("Stock Number", "count"),
                    Current_On_Ground_Dollars=("Total Current Cost Of Veh", "sum"),
                )
                .reset_index()
            )

            summary = prior_group.merge(added_group, on=group_col, how="outer")
            summary = summary.merge(removed_group, on=group_col, how="outer")
            summary = summary.merge(current_group, on=group_col, how="outer")
            summary = summary.fillna(0)

            summary["Net_Unit_Change"] = (
                summary["Units_Added"] - summary["Units_Sold_Removed"]
            )

            summary["Net_Dollar_Change"] = (
                summary["Dollars_Added"] - summary["Dollars_Sold_Removed"]
            )

            summary = summary.sort_values("Dollars_Sold_Removed", ascending=False)

            display = summary.copy()

            for col in [
                "Prior_On_Ground_Dollars",
                "Dollars_Added",
                "Dollars_Sold_Removed",
                "Current_On_Ground_Dollars",
                "Net_Dollar_Change",
            ]:
                display[col] = money_format(display[col])

            return display

        st.markdown("### Weekly Movement by Make")
        st.dataframe(movement_summary("Make"), use_container_width=True, hide_index=True)

        st.markdown("### Weekly Movement by Manufacturer")
        st.dataframe(movement_summary("Manufacturer"), use_container_width=True, hide_index=True)

        st.markdown("### Weekly Movement by Location")
        st.dataframe(movement_summary("ProfitCenter"), use_container_width=True, hide_index=True)

        st.markdown("### New On-Ground Units Added This Week")
        st.dataframe(new_units, use_container_width=True, hide_index=True)

        st.markdown("### Units Sold / Removed This Week")
        st.dataframe(removed_units, use_container_width=True, hide_index=True)

    else:
        st.info("Upload the prior week file to unlock weekly movement.")

    st.divider()

    # ======================================================
    # 7. EXPO & PIPELINE
    # ======================================================

    st.markdown("## 🚐 Expo & Pipeline")

    st.markdown("### Expo / Special Inventory Flags")
    col43, col44, col45, col46 = st.columns(4)
    col43.metric("MCME / Nashville Expo Units", len(mcme_expo_df))
    col44.metric("MCME Expo Retail Orders", len(mcme_expo_order_df))
    col45.metric("Las Vegas Expo Units", len(vegas_expo_df))
    col46.metric("Vegas Expo Retail Orders", len(vegas_expo_order_df))

    st.markdown("### Expo Units by Model Year")

    expo_units = pd.concat(
        [
            mcme_expo_df.assign(Expo_Type="MCME / Nashville Expo"),
            mcme_expo_order_df.assign(Expo_Type="MCME Retail Order"),
            vegas_expo_df.assign(Expo_Type="Vegas Expo"),
            vegas_expo_order_df.assign(Expo_Type="Vegas Retail Order"),
        ],
        ignore_index=True
    )

    if len(expo_units) > 0:
        expo_by_year = (
            expo_units
            .groupby(["Expo_Type", "Yr"])
            .agg(
                Units=("Stock Number", "count"),
                Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
                Average_Age=("Age", "mean"),
            )
            .reset_index()
            .sort_values(["Expo_Type", "Yr"])
        )

        expo_by_year_display = expo_by_year.copy()
        expo_by_year_display["Inventory_Dollars"] = money_format(
            expo_by_year_display["Inventory_Dollars"]
        )
        expo_by_year_display["Average_Age"] = expo_by_year_display[
            "Average_Age"
        ].round(0)

        st.dataframe(expo_by_year_display, use_container_width=True, hide_index=True)
    else:
        st.info("No Expo units found in the current file.")

    st.subheader("On-Order Units")
    st.dataframe(on_order_df, use_container_width=True, hide_index=True)

    st.subheader("On-Order Pipeline by Expected Delivery Month")

    on_order_pipeline = on_order_df.copy()
    on_order_pipeline["Expected Delivery Date"] = pd.to_datetime(
        on_order_pipeline["Expected Delivery Date"],
        errors="coerce"
    )

    on_order_pipeline["Expected Delivery Month"] = (
        on_order_pipeline["Expected Delivery Date"]
        .dt.to_period("M")
        .astype(str)
    )

    pipeline_by_month = (
        on_order_pipeline
        .groupby("Expected Delivery Month")
        .agg(
            On_Order_Units=("Stock Number", "count"),
            On_Order_Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
        )
        .reset_index()
        .sort_values("Expected Delivery Month")
    )

    pipeline_display = pipeline_by_month.copy()
    pipeline_display["On_Order_Inventory_Dollars"] = money_format(
        pipeline_display["On_Order_Inventory_Dollars"]
    )

    st.dataframe(pipeline_display, use_container_width=True, hide_index=True)

    st.divider()

    # ======================================================
    # 8. DETAIL TABLES
    # ======================================================

    st.markdown("## 🔎 Detail Tables")

    st.subheader("Top 10 Makes - New Available On-Ground Inventory")

    top_10_makes = (
        available_new_on_ground_df.groupby("Make")
        .agg(
            Units=("Stock Number", "count"),
            Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
            Daily_Flooring_Cost=("Daily Flooring Cost", "sum"),
            Accumulated_Flooring_Cost=("Accumulated Flooring Cost", "sum"),
            Book_Value_Drop=("Book Value Drop", "sum"),
            Expected_Gross_Profit=("Expected Gross Profit", "sum"),
            Total_Economic_Drag=("Total Economic Drag", "sum"),
        )
        .reset_index()
        .sort_values("Inventory_Dollars", ascending=False)
        .head(10)
    )

    top_10_makes_display = top_10_makes.copy()

    for col in [
        "Inventory_Dollars",
        "Daily_Flooring_Cost",
        "Accumulated_Flooring_Cost",
        "Book_Value_Drop",
        "Expected_Gross_Profit",
        "Total_Economic_Drag",
    ]:
        top_10_makes_display[col] = money_format(top_10_makes_display[col])

    top_10_makes_display["Average_Age"] = top_10_makes_display[
        "Average_Age"
    ].round(0)

    st.dataframe(top_10_makes_display, use_container_width=True, hide_index=True)

else:
    st.info("Upload the current week inventory spreadsheet to begin.")