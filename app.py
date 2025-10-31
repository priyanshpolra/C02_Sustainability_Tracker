import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import base64

st.set_page_config(
    page_title="Sustainability Tracker",
    page_icon="/logo.png",
    layout="wide"
)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

@st.cache_data
def load_data():
    routes = pd.read_csv("data/routes_distance.csv")
    vehicles = pd.read_csv("data/vehicle_fleet.csv")
    orders = pd.read_csv("data/orders.csv")
    return routes, vehicles, orders

routes, vehicles, orders = load_data()

df = orders.merge(routes, on="Order_ID", how="left")
vehicle_types = vehicles["Vehicle_Type"].unique()
df["Vehicle_Type"] = np.random.choice(vehicle_types, len(df))
vehicles_avg = vehicles.groupby("Vehicle_Type")["Fuel_Efficiency_KM_per_L"].mean().reset_index()
df = df.merge(vehicles_avg, on="Vehicle_Type", how="left")
df["CO2_Emissions_Kg_per_KM"] = 2.68 / df["Fuel_Efficiency_KM_per_L"]
df["total_emission_kg"] = df["Distance_KM"] * df["CO2_Emissions_Kg_per_KM"]
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.fillna(0, inplace=True)

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

image_base64 = get_base64_image("logo.png")

st.markdown(f"""
    <div class="navbar-custom">
        <img src="data:image/png;base64,{image_base64}" class="navbar-logo" alt="leaf-logo">
        <span class="navbar-title">Sustainability Tracker Dashboard</span>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("⦿ Filters")
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

st.markdown("<h3>⟾ Tracking CO₂ emissions across routes, vehicles, and warehouses</h3>", unsafe_allow_html=True)

total_emission = round(filtered_df["total_emission_kg"].sum(), 2)
avg_emission = round(filtered_df["total_emission_kg"].mean(), 2)
total_orders = filtered_df["Order_ID"].nunique()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""
        <div class='metric-box'>
            <h4>Total CO₂ Emissions (kg)</h4>
            <p>{total_emission:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
with col2:
    st.markdown(
        f"""
        <div class='metric-box'>
            <h4>Average Emission per Order (kg)</h4>
            <p>{avg_emission:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
with col3:
    st.markdown(
        f"""
        <div class='metric-box'>
            <h4>Total Orders Analyzed</h4>
            <p>{total_orders}</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

st.subheader("⟾ Emissions by Product Category")
fig1 = px.bar(
    filtered_df,
    x="Product_Category",
    y="total_emission_kg",
    color="Product_Category",
    title=None
)
fig1.update_traces(
    text=None,
    marker_line_width=0,
    hovertemplate="%{x}: %{y:.2f} kg<extra></extra>"
)
fig1.update_layout(
    width=650,
    height=387,
    showlegend=False,
    xaxis_title="Product Category",
    yaxis_title="Total Emission (kg)",
    template="simple_white",
    plot_bgcolor="rgba(255,255,255,0.9)",
    paper_bgcolor="rgba(255,255,255,0.9)",
    margin=dict(l=60, r=60, t=40, b=60),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
)
st.plotly_chart(fig1, config={"responsive": False})

st.markdown("<hr>", unsafe_allow_html=True)

st.subheader("⟾ Emissions by Warehouse (Origin)")
fig2 = px.bar(
    filtered_df,
    x="Origin",
    y="total_emission_kg",
    color="Origin",
    title=None
)
fig2.update_traces(
    text=None,
    marker_line_width=0,
    hovertemplate="%{x}: %{y:.2f} kg<extra></extra>"
)
fig2.update_layout(
    width=1050,
    height=387,
    showlegend=False,
    xaxis_title="Origin Warehouse",
    yaxis_title="Total Emission (kg)",
    template="simple_white",
    plot_bgcolor="rgba(255,255,255,0.9)",
    paper_bgcolor="rgba(255,255,255,0.9)",
    margin=dict(l=60, r=60, t=40, b=60),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
)
st.plotly_chart(fig2, config={"responsive": False})

st.markdown("<hr>", unsafe_allow_html=True)

st.subheader("⟾ Emission Contribution by Order Priority")
priority_emission = filtered_df.groupby("Priority")["total_emission_kg"].sum().reset_index()
fig3 = px.pie(priority_emission, names="Priority", values="total_emission_kg", title=None, hole=0.4)
fig3.update_layout(width=550, height=375)
fig3.update_traces(textfont=dict(color="black", size=13))
st.plotly_chart(fig3, config={"responsive": False})

st.divider()

st.subheader("♻️ Eco-Friendly Recommendations")

def recommend_action(row):
    if row["CO2_Emissions_Kg_per_KM"] > 0.5:
        return "🔋 Switch to Electric/Hybrid Vehicle"
    elif row["Distance_KM"] > 200:
        return "🏭 Use Regional Hub to Shorten Delivery Distance"
    elif "Traffic_Delay_Minutes" in row and row["Traffic_Delay_Minutes"] > 60:
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

csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download Sustainability Report",
    data=csv,
    file_name="sustainability_report.csv",
    mime="text/csv"
)

st.success("✅ Dashboard loaded successfully! Analyze emissions, filter insights, and download your sustainability report.")
