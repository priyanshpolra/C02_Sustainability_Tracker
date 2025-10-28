import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="Sustainability Tracker", layout="wide")

# ------------------ LOAD DATA ------------------
@st.cache_data
def load_data():
    routes = pd.read_csv("data/routes_distance.csv")
    vehicles = pd.read_csv("data/vehicle_fleet.csv")
    orders = pd.read_csv("data/orders.csv")
    return routes, vehicles, orders

routes, vehicles, orders = load_data()

# ------------------ MERGE & PREPARE DATA ------------------
# Merge orders + routes (common column = Order_ID)
df = orders.merge(routes, on="Order_ID", how="left")

# Assign random or proportional vehicle types to each order

vehicle_types = vehicles["Vehicle_Type"].unique()
df["Vehicle_Type"] = np.random.choice(vehicle_types, len(df))

# Add average fuel efficiency for each vehicle type
vehicles_avg = vehicles.groupby("Vehicle_Type")["Fuel_Efficiency_KM_per_L"].mean().reset_index()
df = df.merge(vehicles_avg, on="Vehicle_Type", how="left")

# Calculate CO2 emission per km using efficiency
df["CO2_Emissions_Kg_per_KM"] = 2.68 / df["Fuel_Efficiency_KM_per_L"]

# Calculate total emissions
df["total_emission_kg"] = df["Distance_KM"] * df["CO2_Emissions_Kg_per_KM"]

# Replace missing or infinite values
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.fillna(0, inplace=True)


# ------------------ SIDEBAR FILTERS ------------------
st.sidebar.header("Filters")
priority = st.sidebar.multiselect("Select Order Priority:", df["Priority"].dropna().unique())
product_category = st.sidebar.multiselect("Select Product Category:", df["Product_Category"].dropna().unique())
origin = st.sidebar.multiselect("Select Origin Warehouse:", df["Origin"].dropna().unique())

filtered_df = df.copy()
if priority:
    filtered_df = filtered_df[filtered_df["Priority"].isin(priority)]
if product_category:
    filtered_df = filtered_df[filtered_df["Product_Category"].isin(product_category)]
if origin:
    filtered_df = filtered_df[filtered_df["Origin"].isin(origin)]

# ------------------ KPI SECTION ------------------
st.title("🌍 Sustainability Tracker Dashboard")
st.markdown("### Tracking CO₂ emissions across routes, vehicles, and warehouses")

total_emission = round(filtered_df["total_emission_kg"].sum(), 2)
avg_emission = round(filtered_df["total_emission_kg"].mean(), 2)
total_orders = filtered_df["Order_ID"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total CO₂ Emissions (kg)", f"{total_emission:,}")
col2.metric("Average Emission per Order (kg)", f"{avg_emission:.2f}")
col3.metric("Total Orders Analyzed", total_orders)

st.divider()

# ------------------ VISUALIZATIONS ------------------
col1, col2 = st.columns(2)

# Emission by Product Category
with col1:
    fig1 = px.bar(filtered_df, x="Product_Category", y="total_emission_kg", color="Product_Category",
                  title="Emissions by Product Category", text_auto=True)
    st.plotly_chart(fig1, use_container_width=True)

# Emission by Origin Warehouse
with col2:
    fig2 = px.bar(filtered_df, x="Origin", y="total_emission_kg", color="Origin",
                  title="Emissions by Warehouse (Origin)", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

# ------------------ PIE CHART: PRIORITY CONTRIBUTION ------------------
st.subheader("📊 Emission Contribution by Order Priority")
priority_emission = filtered_df.groupby("Priority")["total_emission_kg"].sum().reset_index()
fig3 = px.pie(priority_emission, names="Priority", values="total_emission_kg",
              title="Share of Emissions by Priority Type", hole=0.4)
st.plotly_chart(fig3, use_container_width=True)

# ------------------ RECOMMENDATIONS ------------------
st.subheader("♻️ Eco-Friendly Recommendations")

def recommend_action(row):
    if row["CO2_Emissions_Kg_per_KM"] > 0.5:
        return "🔋 Switch to Electric/Hybrid Vehicle"
    elif row["Distance_KM"] > 200:
        return "🏭 Use Regional Hub to Shorten Delivery Distance"
    elif row["Traffic_Delay_Minutes"] > 60:
        return "🚦 Avoid Peak Hour Routes"
    elif "Food" in str(row["Product_Category"]):
        return "❄️ Use Refrigerated Efficient Vehicles"
    else:
        return "✅ Route is Eco-Efficient"

filtered_df["Recommendation"] = filtered_df.apply(recommend_action, axis=1)

st.dataframe(filtered_df[[
    "Order_ID", "Priority", "Product_Category", "Origin",
    "Distance_KM", "total_emission_kg", "Recommendation"
]])

# ------------------ DOWNLOAD BUTTON ------------------
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Sustainability Report", data=csv,
                   file_name="sustainability_report.csv", mime="text/csv")

st.success("✅ Dashboard loaded successfully! Analyze emissions, filter insights, and download your sustainability report.")
