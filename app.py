import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import hashlib
import math

st.set_page_config(layout="wide")

st.title("📡 MDT LTE Dashboard (Telco Style)")

# =========================
# UPLOAD FILE
# =========================
uploaded_file = st.file_uploader("Upload CSV / CSV.GZ MDT", type=["csv", "gz"])

if uploaded_file is not None:

    # =========================
    # READ FILE
    # =========================
    if uploaded_file.name.endswith(".gz"):
        df = pd.read_csv(uploaded_file, compression="gzip")
    else:
        df = pd.read_csv(uploaded_file)

    df = df[["date", "site", "enodebid", "ci", "long_grid", "lat_grid"]]

    # =========================
    # FILTER SITE
    # =========================
    selected_site = st.selectbox("Select Site", df["site"].unique())
    df = df[df["site"] == selected_site]

    # =========================
    # COLOR PER CI
    # =========================
    def generate_color(ci):
        hash_val = hashlib.md5(str(ci).encode()).hexdigest()
        return f"#{hash_val[:6]}"

    unique_ci = df["ci"].unique()
    ci_color_map = {ci: generate_color(ci) for ci in unique_ci}

    # =========================
    # BAND CLASSIFICATION
    # =========================
    def classify_band(ci):
        ci = int(ci)
        if ci < 100000:
            return "LTE 900"
        elif ci < 200000:
            return "LTE 1800"
        elif ci < 300000:
            return "LTE 2100"
        else:
            return "LTE 2300"

    df["band"] = df["ci"].apply(classify_band)

    # =========================
    # FUNCTION: CREATE SECTOR FAN
    # =========================
    def create_sector(lat, lon, azimuth, distance=0.002):

        angle_left = math.radians(azimuth - 20)
        angle_right = math.radians(azimuth + 20)

        lat1 = lat + distance * math.cos(angle_left)
        lon1 = lon + distance * math.sin(angle_left)

        lat2 = lat + distance * math.cos(angle_right)
        lon2 = lon + distance * math.sin(angle_right)

        return [(lat, lon), (lat1, lon1), (lat2, lon2)]

    # =========================
    # MAP FUNCTION
    # =========================
    def create_map(data):

        if data.empty:
            return None

        center_lat = data["lat_grid"].mean()
        center_lon = data["long_grid"].mean()

        # 🗺️ Satellite Map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="ESRI Satellite"
        )

        for _, row in data.iterrows():

            color = ci_color_map[row["ci"]]

            # plot titik
            folium.CircleMarker(
                location=[row["lat_grid"], row["long_grid"]],
                radius=3,
                color=color,
                fill=True,
                fill_opacity=0.8
            ).add_to(m)

            # 🎯 DUMMY AZIMUTH (sementara)
            azimuth = int(row["ci"]) % 360

            sector = create_sector(
                row["lat_grid"],
                row["long_grid"],
                azimuth
            )

            folium.Polygon(
                locations=sector,
                color=color,
                fill=True,
                fill_opacity=0.3
            ).add_to(m)

        return m

    # =========================
    # SPLIT BAND
    # =========================
    df_900 = df[df["band"] == "LTE 900"]
    df_1800 = df[df["band"] == "LTE 1800"]
    df_2100 = df[df["band"] == "LTE 2100"]
    df_2300 = df[df["band"] == "LTE 2300"]

    # =========================
    # LAYOUT
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("LTE 900")
        m1 = create_map(df_900)
        if m1:
            st_folium(m1, height=400)

    with col2:
        st.subheader("LTE 1800")
        m2 = create_map(df_1800)
        if m2:
            st_folium(m2, height=400)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("LTE 2100")
        m3 = create_map(df_2100)
        if m3:
            st_folium(m3, height=400)

    with col4:
        st.subheader("LTE 2300")
        m4 = create_map(df_2300)
        if m4:
            st_folium(m4, height=400)

    # =========================
    # LEGEND
    # =========================
    st.subheader("📌 Legend")

    legend_html = ""
    for ci, color in ci_color_map.items():
        legend_html += f"""
        <div style="display:flex; align-items:center;">
            <div style="width:15px; height:15px; background:{color}; margin-right:5px;"></div>
            CI {ci}
        </div>
        """

    st.markdown(legend_html, unsafe_allow_html=True)
