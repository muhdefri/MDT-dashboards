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
    # FILTER SITE
    # =========================
    selected_site = st.selectbox("Select Site", df_mdt["site"].unique())

    df_mdt = df_mdt[df_mdt["site"] == selected_site]
    df_mcom = df_mcom[df_mcom["Site_ID"] == selected_site]

    # =========================
    # COLOR PER CI
    # =========================
    def generate_color(ci):
        hash_val = hashlib.md5(str(ci).encode()).hexdigest()
        return f"#{hash_val[:6]}"

    unique_ci = df_mdt["ci"].unique()
    ci_color_map = {ci: generate_color(ci) for ci in unique_ci}

    # =========================
    # FUNCTION: CREATE SECTOR
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
    # MAP FUNCTION
    # =========================
    def create_map(mdt_data, mcom_data):

        if mdt_data.empty or mcom_data.empty:
            return None

        center_lat = mcom_data["Latitude"].mean()
        center_lon = mcom_data["Longitude"].mean()

        # 🗺️ Satellite Map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="ESRI Satellite"
        )

        # =========================
        # PLOT MDT GRID
        # =========================
        for _, row in mdt_data.iterrows():
            folium.CircleMarker(
                location=[row["lat_grid"], row["long_grid"]],
                radius=3,
                color=ci_color_map[row["ci"]],
                fill=True,
                fill_opacity=0.7
            ).add_to(m)

        # =========================
        # PLOT SECTOR (REAL FROM MCOM)
        # =========================
        for _, row in mcom_data.iterrows():

            site_lat = row["Latitude"]
            site_lon = row["Longitude"]
            azimuth = row["Dir Beam"]

            color = "#FFFFFF"  # sector warna putih transparan

            sector = create_sector(site_lat, site_lon, azimuth, beamwidth=60)

            folium.Polygon(
                locations=sector,
                color=color,
                fill=True,
                fill_opacity=0.2
            ).add_to(m)

        # =========================
        # PLOT SITE LABEL
        # =========================
        site_lat = mcom_data["Latitude"].mean()
        site_lon = mcom_data["Longitude"].mean()

        folium.Marker(
            location=[site_lat, site_lon],
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
    # SPLIT BAND (FROM MCOM)
    # =========================
    df_mcom["band"] = df_mcom["LTE"]

    bands = ["LTE900", "LTE1800", "LTE2100", "LTE2300"]

    maps = {}

    for band in bands:
        mcom_band = df_mcom[df_mcom["LTE"].astype(str).str.contains(band.replace("LTE", ""))]
        maps[band] = create_map(df_mdt, mcom_band)

    # =========================
    # DISPLAY MAPS
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("LTE 900")
        if maps["LTE900"]:
            st_folium(maps["LTE900"], height=400)

    with col2:
        st.subheader("LTE 1800")
        if maps["LTE1800"]:
            st_folium(maps["LTE1800"], height=400)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("LTE 2100")
        if maps["LTE2100"]:
            st_folium(maps["LTE2100"], height=400)

    with col4:
        st.subheader("LTE 2300")
        if maps["LTE2300"]:
            st_folium(maps["LTE2300"], height=400)

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
