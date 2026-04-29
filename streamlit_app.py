import streamlit as st
import pandas as pd

st.set_page_config(page_title="NIRVC Inventory Command Center", layout="wide")

st.title("NIRVC Inventory Command Center")
st.caption("Real-time inventory control, risk, pipeline, and weekly inventory movement tracking")

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

    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
    df["Total Current Cost Of Veh"] = pd.to_numeric(
        df["Total Current Cost Of Veh"], errors="coerce"
    )
    df["Purchase Price of Veh"] = pd.to_numeric(
        df["Purchase Price of Veh"], errors="coerce"
    )

    df["Stock Number"] = df["Stock Number"].astype(str).str.strip()
    df["NUD"] = df["NUD"].astype(str).str.upper().str.strip()
    df["On Order"] = df["On Order"].astype(str).str.upper().str.strip()
    df["On Hold"] = df["On Hold"].astype(str).str.upper().str.strip()

    return df


st.markdown("### Expo / Special Inventory Flags")
st.markdown("### Capital Deployed")
if current_file is not None:
    df = load_file(current_file)
    st.success("Current week spreadsheet uploaded successfully.")

    floorplan_rate = 0.0571

    # Core splits
    on_ground_df = df[df["On Order"] == "N"]
    on_order_df = df[df["On Order"] == "Y"]

    new_on_ground_df = df[
        (df["NUD"].str.startswith("N")) &
        (df["On Order"] == "N")
    ]

    new_on_order_df = df[
        (df["NUD"].str.startswith("N")) &
        (df["On Order"] == "Y")
    ]

    used_owned_on_ground_df = df[
        (df["NUD"].str.startswith("U")) &
        (df["On Order"] == "N") &
        (df["Purchase Price of Veh"] > 0)
    ]

    consigned_on_ground_df = df[
        (df["NUD"].str.startswith("U")) &
        (df["On Order"] == "N") &
        (df["Purchase Price of Veh"] == 0)
    ]

    demo_on_ground_df = df[
        (df["NUD"].str.startswith("D")) &
        (df["On Order"] == "N")
    ]

    # Expo / special stock number flags
    stock_numbers = df["Stock Number"].astype(str).str.upper().str.strip()

    mcme_expo_df = df[
        stock_numbers.str.endswith("X") &
        ~stock_numbers.str.endswith("VX")
    ]

    vegas_expo_df = df[
        stock_numbers.str.endswith("VX")
    ]

    expo_retail_order_df = df[
        stock_numbers.str.endswith("XO")
    ]

    cc_consignment_df = df[
        stock_numbers.str.contains("CC", na=False)
    ]

    # Optional crosscheck: used units with zero purchase price should generally match CC consignments
    used_zero_cost_df = df[
        (df["NUD"].str.startswith("U")) &
        (df["Purchase Price of Veh"] == 0)
    ]

    available_new_on_ground_df = df[
        (df["NUD"].str.startswith("N")) &
        (df["On Order"] == "N") &
        (df["On Hold"] == "N")
    ]

    # Unit counts
    total_pipeline_units = len(df)
    on_ground_units = len(on_ground_df)
    on_order_units = len(on_order_df)

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
    consigned_on_ground_cost = consigned_on_ground_df["Total Current Cost Of Veh"].sum()
    demo_on_ground_cost = demo_on_ground_df["Total Current Cost Of Veh"].sum()

    new_on_ground_avg_cost = new_on_ground_df["Total Current Cost Of Veh"].mean()

    units_120 = on_ground_df[on_ground_df["Age"] >= 120].shape[0]
    daily_carrying_cost = new_on_ground_cost * floorplan_rate / 365
    monthly_carrying_cost = new_on_ground_cost * floorplan_rate / 12

    # Executive Scoreboard
    st.markdown("## 📊 Executive Scoreboard")

    st.markdown("### Inventory Position")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pipeline", total_pipeline_units)
    col2.metric("On-Ground Units", on_ground_units)
    col3.metric("On-Order Units", on_order_units)

    col4, col5, col6, col7 = st.columns(4)
    col4.metric("New On-Ground Units", new_on_ground_units)
    col5.metric("Used Owned On-Ground Units", used_owned_on_ground_units)
    col6.metric("Consigned On-Ground Units", consigned_on_ground_units)
    col7.metric("Demo On-Ground Units", demo_on_ground_units)

    st.markdown("### Expo / Special Inventory Flags")

    col8, col9, col10, col11 = st.columns(4)
    col8.metric("MCME / Nashville Expo Units", len(mcme_expo_df))
    col9.metric("Las Vegas Expo Units", len(vegas_expo_df))
    col10.metric("Expo Retail Orders", len(expo_retail_order_df))
    col11.metric("CC Consignment Stock Numbers", len(cc_consignment_df))

    st.markdown("### Capital Deployed")
    col8, col9, col10 = st.columns(3)
    col8.metric("Capital Deployed - On Ground", f"${on_ground_cost:,.0f}")
    col9.metric("New On-Ground $", f"${new_on_ground_cost:,.0f}")
    col10.metric("Used Owned On-Ground $", f"${used_owned_on_ground_cost:,.0f}")

    st.markdown("### Incoming Pipeline Commitments")
    col11, col12, col13 = st.columns(3)
    col11.metric("On-Order Units", on_order_units)
    col12.metric("On-Order Pipeline $", f"${on_order_cost:,.0f}")
    col13.metric("Total Pipeline $", f"${total_pipeline_cost:,.0f}")

    st.markdown("### ⚠️ Aging Risk - On-Ground Inventory")

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

    col14, col15, col16, col17, col18 = st.columns(5)
    col14.metric("< 90 Days", f"${aging_buckets['< 90 Days']:,.0f}")
    col15.metric("91-180 Days", f"${aging_buckets['91-180 Days']:,.0f}")
    col16.metric("181-270 Days", f"${aging_buckets['181-270 Days']:,.0f}")
    col17.metric("271-365 Days", f"${aging_buckets['271-365 Days']:,.0f}")
    col18.metric("365+ Days", f"${aging_buckets['365+ Days']:,.0f}")

    st.markdown("### 💸 Floorplan Carrying Cost")
    col19, col20 = st.columns(2)
    col19.metric("Daily Carrying Cost - New On Ground", f"${daily_carrying_cost:,.0f}")
    col20.metric("Monthly Carrying Cost - New On Ground", f"${monthly_carrying_cost:,.0f}")

    st.markdown("### New / Used Owned / Consigned / Demo Split")
    col21, col22, col23, col24 = st.columns(4)
    col21.metric("New On-Ground Inventory $", f"${new_on_ground_cost:,.0f}")
    col22.metric("New On-Order Pipeline $", f"${new_on_order_cost:,.0f}")
    col23.metric("Used Owned On-Ground $", f"${used_owned_on_ground_cost:,.0f}")
    col24.metric("Consigned On-Ground Units", consigned_on_ground_units)

    col25, col26, col27 = st.columns(3)
    col25.metric("New On-Ground Avg Cost", f"${new_on_ground_avg_cost:,.0f}")
    col26.metric("Consigned On-Ground $", f"${consigned_on_ground_cost:,.0f}")
    col27.metric("Demo On-Ground $", f"${demo_on_ground_cost:,.0f}")

    if units_120 > 150:
        st.error("⚠️ High aged inventory risk — immediate action required")
    elif units_120 > 100:
        st.warning("⚠️ Elevated aged inventory — monitor closely")
    else:
        st.success("✅ Inventory aging within acceptable range")

    st.divider()

    st.subheader("Consignment Crosscheck")

    col1, col2, col3 = st.columns(3)
    col1.metric("Used Zero Purchase Price Units", len(used_zero_cost_df))
    col2.metric("CC Stock Number Units", len(cc_consignment_df))
    col3.metric(
        "Difference",
        len(used_zero_cost_df) - len(cc_consignment_df)
    )

    if len(used_zero_cost_df) != len(cc_consignment_df):
        st.warning("Consignment crosscheck does not match. Review Used $0 units vs stock numbers containing CC.")
    else:
        st.success("Consignment crosscheck matches: Used $0 units align with CC stock numbers.")

    with st.expander("Review Used $0 Consignment Candidates"):
        st.dataframe(used_zero_cost_df, use_container_width=True)

    with st.expander("Review CC Stock Number Units"):
        st.dataframe(cc_consignment_df, use_container_width=True)

    # Store Command Board
    st.subheader("Store Command Board")

    store_scoreboard = (
        on_ground_df.groupby("ProfitCenter")
        .agg(
            On_Ground_Units=("Stock Number", "count"),
            On_Ground_Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
            Units_120_Plus=("Age", lambda x: (x >= 120).sum()),
            Inventory_120_Plus_Dollars=(
                "Total Current Cost Of Veh",
                lambda x: x[on_ground_df.loc[x.index, "Age"] >= 120].sum(),
            ),
        )
        .reset_index()
        .sort_values("On_Ground_Inventory_Dollars", ascending=False)
    )

    store_display = store_scoreboard.copy()
    store_display["On_Ground_Inventory_Dollars"] = store_display[
        "On_Ground_Inventory_Dollars"
    ].map("${:,.0f}".format)
    store_display["Inventory_120_Plus_Dollars"] = store_display[
        "Inventory_120_Plus_Dollars"
    ].map("${:,.0f}".format)
    store_display["Average_Age"] = store_display["Average_Age"].round(0)

    st.dataframe(store_display, use_container_width=True)

    st.divider()

    # Week-over-week movement
    if prior_file is not None:
        prior_df = load_file(prior_file)
        prior_on_ground_df = prior_df[prior_df["On Order"] == "N"]

        current_stocks = set(on_ground_df["Stock Number"])
        prior_stocks = set(prior_on_ground_df["Stock Number"])

        new_stocks = current_stocks - prior_stocks
        sold_or_removed_stocks = prior_stocks - current_stocks

        new_units = on_ground_df[on_ground_df["Stock Number"].isin(new_stocks)]
        removed_units = prior_on_ground_df[
            prior_on_ground_df["Stock Number"].isin(sold_or_removed_stocks)
        ]

        new_units_cost = new_units["Total Current Cost Of Veh"].sum()
        removed_units_cost = removed_units["Total Current Cost Of Veh"].sum()

        st.subheader("Week-over-Week On-Ground Inventory Movement")

        col28, col29, col30 = st.columns(3)
        col28.metric("New On-Ground Units Added", len(new_units))
        col29.metric("Units Sold / Removed", len(removed_units))
        col30.metric("Net On-Ground Unit Change", len(new_units) - len(removed_units))

        col31, col32, col33 = st.columns(3)
        col31.metric("New On-Ground Inventory $ Added", f"${new_units_cost:,.0f}")
        col32.metric("Inventory $ Sold / Removed", f"${removed_units_cost:,.0f}")
        col33.metric("Net Inventory $ Change", f"${new_units_cost - removed_units_cost:,.0f}")

        new_units_new = new_units[new_units["NUD"].str.startswith("N")]
        new_units_used_owned = new_units[
            (new_units["NUD"].str.startswith("U")) &
            (new_units["Purchase Price of Veh"] > 0)
        ]
        new_units_consigned = new_units[
            (new_units["NUD"].str.startswith("U")) &
            (new_units["Purchase Price of Veh"] == 0)
        ]

        st.subheader("New On-Ground Units Added This Week")
        st.dataframe(new_units_new, use_container_width=True)

        st.subheader("Used Owned On-Ground Units Added This Week")
        st.dataframe(new_units_used_owned, use_container_width=True)

        st.subheader("Consigned On-Ground Units Added This Week")
        st.dataframe(new_units_consigned, use_container_width=True)

    else:
        st.info("Upload the prior week file to unlock week-over-week movement.")

    st.divider()

    # Top makes
    st.subheader("Top 10 Makes - New Available On-Ground Inventory")

    top_10_makes = (
        available_new_on_ground_df.groupby("Make")
        .agg(
            Units=("Stock Number", "count"),
            Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
        )
        .reset_index()
        .sort_values("Inventory_Dollars", ascending=False)
        .head(10)
    )

    top_10_makes_display = top_10_makes.copy()
    top_10_makes_display["Inventory_Dollars"] = top_10_makes_display[
        "Inventory_Dollars"
    ].map("${:,.0f}".format)
    top_10_makes_display["Average_Age"] = top_10_makes_display["Average_Age"].round(0)

    st.dataframe(top_10_makes_display, use_container_width=True)

    # Manufacturer summary
    st.subheader("Inventory by Manufacturer - On Ground")

    manufacturer_on_ground_summary = (
        on_ground_df.groupby("Manufacturer")
        .agg(
            On_Ground_Units=("Stock Number", "count"),
            On_Ground_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
        )
        .reset_index()
        .sort_values("On_Ground_Dollars", ascending=False)
    )

    manufacturer_on_ground_display = manufacturer_on_ground_summary.copy()
    manufacturer_on_ground_display["On_Ground_Dollars"] = manufacturer_on_ground_display[
        "On_Ground_Dollars"
    ].map("${:,.0f}".format)
    manufacturer_on_ground_display["Average_Age"] = manufacturer_on_ground_display[
        "Average_Age"
    ].round(0)

    st.dataframe(manufacturer_on_ground_display, use_container_width=True)

    # Manufacturer negotiation weapon
    st.subheader("Manufacturer Negotiation")

    manufacturer_scoreboard = (
        on_ground_df.groupby("Manufacturer")
        .agg(
            On_Ground_Units=("Stock Number", "count"),
            On_Ground_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
            Units_120_Plus=("Age", lambda x: (x >= 120).sum()),
            Inventory_120_Plus_Dollars=(
                "Total Current Cost Of Veh",
                lambda x: x[on_ground_df.loc[x.index, "Age"] >= 120].sum(),
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

    manufacturer_scoreboard = manufacturer_scoreboard.merge(
        on_order_by_manufacturer,
        on="Manufacturer",
        how="left"
    )

    manufacturer_scoreboard["On_Order_Units"] = manufacturer_scoreboard[
        "On_Order_Units"
    ].fillna(0)

    manufacturer_scoreboard["On_Order_Dollars"] = manufacturer_scoreboard[
        "On_Order_Dollars"
    ].fillna(0)

    total_on_ground_inventory_value = manufacturer_scoreboard[
        "On_Ground_Dollars"
    ].sum()

    manufacturer_scoreboard["Percent_of_On_Ground_Inventory"] = (
        manufacturer_scoreboard["On_Ground_Dollars"]
        / total_on_ground_inventory_value
        * 100
    )

    manufacturer_scoreboard["Total_Exposure_Dollars"] = (
        manufacturer_scoreboard["On_Ground_Dollars"]
        + manufacturer_scoreboard["On_Order_Dollars"]
    )

    manufacturer_scoreboard = manufacturer_scoreboard.sort_values(
        "Total_Exposure_Dollars",
        ascending=False
    )

    manufacturer_display = manufacturer_scoreboard.copy()
    manufacturer_display["Percent_of_On_Ground_Inventory"] = manufacturer_display[
        "Percent_of_On_Ground_Inventory"
    ].map("{:.1f}%".format)
    manufacturer_display["On_Ground_Dollars"] = manufacturer_display[
        "On_Ground_Dollars"
    ].map("${:,.0f}".format)
    manufacturer_display["On_Order_Dollars"] = manufacturer_display[
        "On_Order_Dollars"
    ].map("${:,.0f}".format)
    manufacturer_display["Total_Exposure_Dollars"] = manufacturer_display[
        "Total_Exposure_Dollars"
    ].map("${:,.0f}".format)
    manufacturer_display["Inventory_120_Plus_Dollars"] = manufacturer_display[
        "Inventory_120_Plus_Dollars"
    ].map("${:,.0f}".format)
    manufacturer_display["Average_Age"] = manufacturer_display["Average_Age"].round(0)
    manufacturer_display["On_Order_Units"] = manufacturer_display[
        "On_Order_Units"
    ].astype(int)

    manufacturer_display = manufacturer_display[
        [
            "Manufacturer",
            "Total_Exposure_Dollars",
            "On_Ground_Dollars",
            "On_Order_Dollars",
            "On_Ground_Units",
            "On_Order_Units",
            "Percent_of_On_Ground_Inventory",
            "Average_Age",
            "Units_120_Plus",
            "Inventory_120_Plus_Dollars",
        ]
    ]

    st.dataframe(manufacturer_display, use_container_width=True)

    st.subheader("🚨 Top 10 Oldest New On-Ground Units")

    top_aged_new = new_on_ground_df.sort_values("Age", ascending=False).head(10)
    st.dataframe(top_aged_new, use_container_width=True)

    st.divider()

    st.subheader("On-Order Units")
    st.dataframe(on_order_df, use_container_width=True)

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
    pipeline_display["On_Order_Inventory_Dollars"] = pipeline_display[
        "On_Order_Inventory_Dollars"
    ].map("${:,.0f}".format)

    st.dataframe(pipeline_display, use_container_width=True)

else:
    st.info("Upload the current week inventory spreadsheet to begin.")
