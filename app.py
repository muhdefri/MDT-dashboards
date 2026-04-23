import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import hashlib
import math

st.set_page_config(layout="wide")

st.title("📡 MDT LTE Dashboard (MDT + MCOM Integrated)")

# =========================
# UPLOAD FILES
# =========================
mdt_file = st.file_uploader("Upload MDT CSV / CSV.GZ", type=["csv", "gz"])
mcom_file = st.file_uploader("Upload MCOM Excel", type=["xlsx"])

if mdt_file is not None and mcom_file is not None:

    # =========================
    # READ MDT
    # =========================
    if mdt_file.name.endswith(".gz"):
        df_mdt = pd.read_csv(mdt_file, compression="gzip")
    else:
        df_mdt = pd.read_csv(mdt_file)

    df_mdt = df_mdt[["date", "site", "enodebid", "ci", "long_grid", "lat_grid"]]

    # =========================
    # READ MCOM
    # =========================
    df_mcom = pd.read_excel(mcom_file)

    # =========================
    # SELECT SITE
    # =========================
    selected_site = st.selectbox("Select Site", df_mdt["site"].unique())

    df_mdt = df_mdt[df_mdt["site"] == selected_site]

    # =========================
    # 🔥 FIX SITE MATCHING
    # =========================
    # normalize text
    df_mdt["site_clean"] = df_mdt["site"].str.upper().str.replace("-", "").str.strip()
    df_mcom["site_clean"] = df_mcom["Site_ID"].astype(str).str.upper().str.replace("-", "").str.strip()

    selected_site_clean = selected_site.upper().replace("-", "")

    # match pakai sebagian string
    df_mcom = df_mcom[df_mcom["site_clean"].str.contains(selected_site_clean[:8], na=False)]

    # =========================
    # DEBUG INFO (PENTING)
    # =========================
    st.write("MDT rows:", len(df_mdt))
    st.write("MCOM rows:", len(df_mcom))

    if df_mcom.empty:
        st.error("❌ MCOM tidak match dengan MDT (cek nama site)")
        st.stop()

    # =========================
    # COLOR PER CI
    # =========================
    def generate_color(ci):
        hash_val = hashlib.md5(str(ci).encode()).hexdigest()
        return f"#{hash_val[:6]}"

    unique_ci = df_mdt["ci"].unique()
    ci_color_map = {ci: generate_color(ci) for ci in unique_ci}

    # =========================
    # CREATE SECTOR FUNCTION
    # =========================
    def create_sector(lat, lon, azimuth, beamwidth=60, distance=0.002):

        left = math.radians(azimuth - beamwidth / 2)
        right = math.radians(azimuth + beamwidth / 2)

        lat1 = lat + distance * math.cos(left)
        lon1 = lon + distance * math.sin(left)

        lat2 = lat + distance * math.cos(right)
        lon2 = lon + distance * math.sin(right)

        return [(lat, lon), (lat1, lon1), (lat2, lon2)]

    # =========================
    # CREATE MAP FUNCTION
    # =========================
    def create_map(mdt_data, mcom_data):

        center_lat = mcom_data["Latitude"].mean()
        center_lon = mcom_data["Longitude"].mean()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="ESRI Satellite"
        )

        # MDT GRID
        for _, row in mdt_data.iterrows():
            folium.CircleMarker(
                location=[row["lat_grid"], row["long_grid"]],
                radius=3,
                color=ci_color_map[row["ci"]],
                fill=True,
                fill_opacity=0.7
            ).add_to(m)

        # SECTOR FAN
        for _, row in mcom_data.iterrows():

            site_lat = row["Latitude"]
            site_lon = row["Longitude"]
            azimuth = row["Dir Beam"]

            sector = create_sector(site_lat, site_lon, azimuth)

            folium.Polygon(
                locations=sector,
                color="white",
                fill=True,
                fill_opacity=0.2
            ).add_to(m)

        # SITE LABEL
        folium.Marker(
            location=[center_lat, center_lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size:16px;
                    font-weight:bold;
                    color:white;
                    text-shadow:2px 2px 5px black;">
                    {selected_site}
                </div>
                """
            )
        ).add_to(m)

        return m

    # =========================
    # BAND SPLIT
    # =========================
    df_mcom["band"] = df_mcom["LTE"].astype(str)

    bands = {
        "LTE 900": "900",
        "LTE 1800": "1800",
        "LTE 2100": "2100",
        "LTE 2300": "2300"
    }

    maps = {}

    for band_name, band_val in bands.items():
        mcom_band = df_mcom[df_mcom["band"].str.contains(band_val, na=False)]
        maps[band_name] = create_map(df_mdt, mcom_band)

    # =========================
    # DISPLAY
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("LTE 900")
        if maps["LTE 900"]:
            st_folium(maps["LTE 900"], height=400)

    with col2:
        st.subheader("LTE 1800")
        if maps["LTE 1800"]:
            st_folium(maps["LTE 1800"], height=400)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("LTE 2100")
        if maps["LTE 2100"]:
            st_folium(maps["LTE 2100"], height=400)

    with col4:
        st.subheader("LTE 2300")
        if maps["LTE 2300"]:
            st_folium(maps["LTE 2300"], height=400)

    # =========================
    # LEGEND
    # =========================
    st.subheader("📌 Legend (CI)")

    legend_html = ""
    for ci, color in ci_color_map.items():
        legend_html += f"""
        <div style="display:flex; align-items:center;">
            <div style="width:12px; height:12px; background:{color}; margin-right:5px;"></div>
            CI {ci}
        </div>
        """

    st.markdown(legend_html, unsafe_allow_html=True)
