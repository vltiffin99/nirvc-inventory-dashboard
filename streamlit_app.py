import streamlit as st
import pandas as pd

st.set_page_config(page_title="NIRVC Inventory Dashboard", layout="wide")
st.title("NIRVC Inventory Dashboard")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #e6e8eb;
        padding: 18px;
        border-radius: 14px;
    }
    h2, h3 {
        margin-top: 1.5rem;
    }
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
    df["Stock Number"] = df["Stock Number"].astype(str).str.strip()
    df["NUD"] = df["NUD"].astype(str).str.upper().str.strip()
    df["On Order"] = df["On Order"].astype(str).str.upper().str.strip()

    return df


if current_file is not None:
    df = load_file(current_file)

    st.success("Current week spreadsheet uploaded successfully.")

    floorplan_rate = 0.0571

    on_ground_df = df[df["On Order"] == "N"]
    on_order_df = df[df["On Order"] == "Y"]

    new_df = df[df["NUD"].str.startswith("N")]
    used_df = df[df["NUD"].str.startswith("U")]
    demo_df = df[df["NUD"].str.startswith("D")]

    new_on_ground_df = on_ground_df[on_ground_df["NUD"].str.startswith("N")]
    used_on_ground_df = on_ground_df[on_ground_df["NUD"].str.startswith("U")]
    demo_on_ground_df = on_ground_df[on_ground_df["NUD"].str.startswith("D")]

    total_units = len(df)
    total_cost = df["Total Current Cost Of Veh"].sum()

    on_ground_units = len(on_ground_df)
    on_order_units = len(on_order_df)
    on_ground_cost = on_ground_df["Total Current Cost Of Veh"].sum()
    on_order_cost = on_order_df["Total Current Cost Of Veh"].sum()

    new_inventory_cost = new_df["Total Current Cost Of Veh"].sum()
    used_inventory_cost = used_df["Total Current Cost Of Veh"].sum()
    demo_inventory_cost = demo_df["Total Current Cost Of Veh"].sum()

    new_on_ground_cost = new_on_ground_df["Total Current Cost Of Veh"].sum()
    used_on_ground_cost = used_on_ground_df["Total Current Cost Of Veh"].sum()
    demo_on_ground_cost = demo_on_ground_df["Total Current Cost Of Veh"].sum()

    avg_age = on_ground_df["Age"].mean()
    units_90 = on_ground_df[on_ground_df["Age"] >= 90].shape[0]
    units_120 = on_ground_df[on_ground_df["Age"] >= 120].shape[0]
    cost_120 = on_ground_df[on_ground_df["Age"] >= 120][
        "Total Current Cost Of Veh"
    ].sum()

    daily_carrying_cost = new_on_ground_cost * floorplan_rate / 365
    monthly_carrying_cost = new_on_ground_cost * floorplan_rate / 12

    st.markdown("## 📊 Executive Scoreboard")

    st.markdown("### Inventory Position")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Units", total_units)
    col2.metric("On-Ground Units", on_ground_units)
    col3.metric("On-Order Units", on_order_units)

    st.markdown("### Capital Deployed")
    col4, col5, col6 = st.columns(3)
    col4.metric("Total Inventory $", f"${total_cost:,.0f}")
    col5.metric("On-Ground Inventory $", f"${on_ground_cost:,.0f}")
    col6.metric("On-Order Inventory $", f"${on_order_cost:,.0f}")

    st.markdown("### ⚠️ Aging Risk")
    col7, col8, col9 = st.columns(3)
    col7.metric("Average Age - On Ground", f"{avg_age:.0f} days")
    col8.metric("90+ Day Units - On Ground", units_90)
    col9.metric("120+ Day Units - On Ground", units_120)

    col10, col11 = st.columns(2)
    col10.metric("120+ Day Inventory $ - On Ground", f"${cost_120:,.0f}")
    col11.metric(
        "120+ % of On-Ground Inventory",
        f"{(cost_120 / on_ground_cost) * 100:.1f}%" if on_ground_cost else "0.0%"
    )

    st.markdown("### 💸 Floorplan Carrying Cost")
    col12, col13 = st.columns(2)
    col12.metric("Daily Carrying Cost - New On Ground", f"${daily_carrying_cost:,.0f}")
    col13.metric("Monthly Carrying Cost - New On Ground", f"${monthly_carrying_cost:,.0f}")

    st.markdown("### New / Used / Demo Split")
    col14, col15, col16 = st.columns(3)
    col14.metric("New Inventory $ - Total", f"${new_inventory_cost:,.0f}")
    col15.metric("Used Inventory $ - Total", f"${used_inventory_cost:,.0f}")
    col16.metric("Demo Inventory $ - Total", f"${demo_inventory_cost:,.0f}")

    col17, col18, col19 = st.columns(3)
    col17.metric("New On-Ground Inventory $", f"${new_on_ground_cost:,.0f}")
    col18.metric("Used On-Ground Inventory $", f"${used_on_ground_cost:,.0f}")
    col19.metric("Demo On-Ground Inventory $", f"${demo_on_ground_cost:,.0f}")

    st.divider()

    st.subheader("Store-Level Scoreboard")

    store_scoreboard = (
        on_ground_df.groupby("ProfitCenter")
        .agg(
            Total_On_Ground_Units=("Stock Number", "count"),
            On_Ground_Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
            Units_90_Plus=("Age", lambda x: (x >= 90).sum()),
            Units_120_Plus=("Age", lambda x: (x >= 120).sum()),
        )
        .reset_index()
    )

    risk_120 = (
        on_ground_df[on_ground_df["Age"] >= 120]
        .groupby("ProfitCenter")["Total Current Cost Of Veh"]
        .sum()
        .reset_index()
        .rename(columns={"Total Current Cost Of Veh": "Inventory_120_Plus_Dollars"})
    )

    store_scoreboard = store_scoreboard.merge(risk_120, on="ProfitCenter", how="left")
    store_scoreboard["Inventory_120_Plus_Dollars"] = store_scoreboard[
        "Inventory_120_Plus_Dollars"
    ].fillna(0)

    store_scoreboard_display = store_scoreboard.copy()
    store_scoreboard_display["On_Ground_Inventory_Dollars"] = store_scoreboard_display[
        "On_Ground_Inventory_Dollars"
    ].map("${:,.0f}".format)
    store_scoreboard_display["Inventory_120_Plus_Dollars"] = store_scoreboard_display[
        "Inventory_120_Plus_Dollars"
    ].map("${:,.0f}".format)
    store_scoreboard_display["Average_Age"] = store_scoreboard_display["Average_Age"].round(0)

    st.dataframe(store_scoreboard_display, use_container_width=True)

    st.divider()

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

        col20, col21, col22 = st.columns(3)
        col20.metric("New On-Ground Units Added", len(new_units))
        col21.metric("Units Sold / Removed", len(removed_units))
        col22.metric("Net On-Ground Unit Change", len(new_units) - len(removed_units))

        col23, col24, col25 = st.columns(3)
        col23.metric("New On-Ground Inventory $ Added", f"${new_units_cost:,.0f}")
        col24.metric("Inventory $ Sold / Removed", f"${removed_units_cost:,.0f}")
        col25.metric("Net Inventory $ Change", f"${new_units_cost - removed_units_cost:,.0f}")

        st.divider()

        st.subheader("Turn Velocity - Store Level")

        store_prior = prior_on_ground_df.groupby("ProfitCenter")["Stock Number"].count()
        store_current = on_ground_df.groupby("ProfitCenter")["Stock Number"].count()
        store_removed = removed_units.groupby("ProfitCenter")["Stock Number"].count()

        turn_store = pd.DataFrame({
            "Prior_On_Ground_Units": store_prior,
            "Current_On_Ground_Units": store_current,
            "Units_Sold_or_Removed": store_removed
        }).fillna(0)

        turn_store["Weekly_Turn_Rate"] = (
            turn_store["Units_Sold_or_Removed"] / turn_store["Prior_On_Ground_Units"]
        )

        turn_store["Estimated_Weeks_Supply"] = (
            turn_store["Current_On_Ground_Units"] / turn_store["Units_Sold_or_Removed"]
        )

        turn_store = turn_store.replace([float("inf"), -float("inf")], 0)

        turn_store_display = turn_store.reset_index()
        turn_store_display["Weekly_Turn_Rate"] = turn_store_display[
            "Weekly_Turn_Rate"
        ].map("{:.1%}".format)
        turn_store_display["Estimated_Weeks_Supply"] = turn_store_display[
            "Estimated_Weeks_Supply"
        ].round(1)

        st.dataframe(turn_store_display, use_container_width=True)

        st.subheader("Turn Velocity - Manufacturer Level")

        mfg_prior = prior_on_ground_df.groupby("Manufacturer")["Stock Number"].count()
        mfg_current = on_ground_df.groupby("Manufacturer")["Stock Number"].count()
        mfg_removed = removed_units.groupby("Manufacturer")["Stock Number"].count()

        turn_mfg = pd.DataFrame({
            "Prior_On_Ground_Units": mfg_prior,
            "Current_On_Ground_Units": mfg_current,
            "Units_Sold_or_Removed": mfg_removed
        }).fillna(0)

        turn_mfg["Weekly_Turn_Rate"] = (
            turn_mfg["Units_Sold_or_Removed"] / turn_mfg["Prior_On_Ground_Units"]
        )

        turn_mfg["Estimated_Weeks_Supply"] = (
            turn_mfg["Current_On_Ground_Units"] / turn_mfg["Units_Sold_or_Removed"]
        )

        turn_mfg = turn_mfg.replace([float("inf"), -float("inf")], 0)
        turn_mfg = turn_mfg.sort_values("Estimated_Weeks_Supply", ascending=False)

        turn_mfg_display = turn_mfg.reset_index()
        turn_mfg_display["Weekly_Turn_Rate"] = turn_mfg_display[
            "Weekly_Turn_Rate"
        ].map("{:.1%}".format)
        turn_mfg_display["Estimated_Weeks_Supply"] = turn_mfg_display[
            "Estimated_Weeks_Supply"
        ].round(1)

        st.dataframe(turn_mfg_display, use_container_width=True)

        st.subheader("Turn Velocity Visual - Manufacturer Weeks Supply")
        st.bar_chart(turn_mfg["Estimated_Weeks_Supply"].sort_values(ascending=True))

        st.divider()

        new_units_new = new_units[new_units["NUD"].str.startswith("N")]
        new_units_used = new_units[new_units["NUD"].str.startswith("U")]

        st.subheader("New On-Ground Units Added This Week")
        st.dataframe(new_units_new, use_container_width=True)

        st.subheader("Used On-Ground Units Added This Week")
        st.dataframe(new_units_used, use_container_width=True)

    else:
        st.info("Upload the prior week file to unlock week-over-week movement and turn velocity.")

    st.divider()

    st.subheader("Inventory by Location - On Ground")
    location_counts = on_ground_df["ProfitCenter"].value_counts().sort_values(ascending=True)
    st.bar_chart(location_counts)

    st.subheader("On-Order Units by Location")
    st.bar_chart(on_order_df["ProfitCenter"].value_counts().sort_values(ascending=True))

    st.subheader("120+ Day Risk by Location - On Ground")
    risk_by_store = (
        on_ground_df[on_ground_df["Age"] >= 120]
        .groupby("ProfitCenter")["Total Current Cost Of Veh"]
        .sum()
        .sort_values(ascending=True)
    )
    st.bar_chart(risk_by_store)

    st.subheader("Inventory by Manufacturer - On Ground")
    st.bar_chart(on_ground_df["Manufacturer"].value_counts().sort_values(ascending=True))

    st.subheader("On-Order Inventory by Manufacturer")
    st.bar_chart(on_order_df["Manufacturer"].value_counts().sort_values(ascending=True))

    st.divider()

    st.subheader("Manufacturer Negotiation Weapon - On Ground Inventory")

    manufacturer_scoreboard = (
        on_ground_df.groupby("Manufacturer")
        .agg(
            Total_Units=("Stock Number", "count"),
            Inventory_Dollars=("Total Current Cost Of Veh", "sum"),
            Average_Age=("Age", "mean"),
            Units_90_Plus=("Age", lambda x: (x >= 90).sum()),
            Units_120_Plus=("Age", lambda x: (x >= 120).sum()),
            Inventory_120_Plus_Dollars=(
                "Total Current Cost Of Veh",
                lambda x: x[on_ground_df.loc[x.index, "Age"] >= 120].sum(),
            ),
        )
        .reset_index()
    )

    total_on_ground_inventory_value = manufacturer_scoreboard["Inventory_Dollars"].sum()

    manufacturer_scoreboard["Percent_of_On_Ground_Inventory"] = (
        manufacturer_scoreboard["Inventory_Dollars"]
        / total_on_ground_inventory_value
        * 100
    )

    manufacturer_scoreboard = manufacturer_scoreboard.sort_values(
        "Inventory_Dollars",
        ascending=False,
    )

    st.subheader("OEM Exposure by Inventory Dollars")
    st.bar_chart(
        manufacturer_scoreboard.set_index("Manufacturer")["Inventory_Dollars"]
    )

    manufacturer_display = manufacturer_scoreboard.copy()

    manufacturer_display["Percent_of_On_Ground_Inventory"] = manufacturer_display[
        "Percent_of_On_Ground_Inventory"
    ].map("{:.1f}%".format)
    manufacturer_display["Inventory_Dollars"] = manufacturer_display[
        "Inventory_Dollars"
    ].map("${:,.0f}".format)
    manufacturer_display["Inventory_120_Plus_Dollars"] = manufacturer_display[
        "Inventory_120_Plus_Dollars"
    ].map("${:,.0f}".format)
    manufacturer_display["Average_Age"] = manufacturer_display["Average_Age"].round(0)

    manufacturer_display = manufacturer_display[
        [
            "Manufacturer",
            "Percent_of_On_Ground_Inventory",
            "Inventory_Dollars",
            "Total_Units",
            "Average_Age",
            "Units_90_Plus",
            "Units_120_Plus",
            "Inventory_120_Plus_Dollars",
        ]
    ]

    st.dataframe(manufacturer_display, use_container_width=True)

    st.subheader("120+ Day Risk by Manufacturer - On Ground")

    manufacturer_risk = (
        on_ground_df[on_ground_df["Age"] >= 120]
        .groupby("Manufacturer")["Total Current Cost Of Veh"]
        .sum()
        .sort_values(ascending=True)
    )
    st.bar_chart(manufacturer_risk)

    st.divider()

    st.subheader("🚨 Top 10 Oldest New On-Ground Units")

    top_aged_new = (
        on_ground_df[on_ground_df["NUD"].str.startswith("N")]
        .sort_values("Age", ascending=False)
        .head(10)
    )

    st.dataframe(top_aged_new, use_container_width=True)

    st.subheader("On-Order Units")
    st.dataframe(on_order_df, use_container_width=True)

else:
    st.info("Upload the current week inventory spreadsheet to begin.")
