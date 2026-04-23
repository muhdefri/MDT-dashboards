import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("📡 MDT LTE Dashboard (4 Band View)")

# =========================
# UPLOAD FILE
# =========================
uploaded_file = st.file_uploader("Upload CSV / CSV.GZ MDT", type=["csv", "gz"])

if uploaded_file is not None:

    # =========================
    # AUTO READ FILE (CSV / GZ)
    # =========================
    try:
        if uploaded_file.name.endswith(".gz"):
            df = pd.read_csv(uploaded_file, compression="gzip")
        else:
            df = pd.read_csv(uploaded_file)

    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        st.stop()

    # =========================
    # PREVIEW
    # =========================
    st.subheader("📄 Data Preview")
    st.dataframe(df.head())

    # =========================
    # VALIDASI KOLOM
    # =========================
    required_cols = ["site", "ci", "lat_grid", "long_grid", "rsrp_mean"]

    if not all(col in df.columns for col in required_cols):
        st.error("Kolom tidak sesuai! Pastikan ada: site, ci, lat_grid, long_grid, rsrp_mean")
        st.stop()

    # =========================
    # FILTER SITE
    # =========================
    selected_site = st.selectbox("Select Site", df["site"].unique())
    df = df[df["site"] == selected_site]

    # =========================
    # BAND CLASSIFICATION
    # =========================
    def classify_band(ci):
        try:
            ci = int(ci)
        except:
            return "Unknown"

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
    # COLOR FUNCTION (RSRP)
    # =========================
    def get_color(rsrp):
        try:
            rsrp = float(rsrp)
        except:
            return "gray"

        if rsrp >= -90:
            return "green"
        elif rsrp >= -105:
            return "yellow"
        elif rsrp >= -115:
            return "orange"
        else:
            return "red"

    # =========================
    # FUNCTION CREATE MAP
    # =========================
    def create_map(data):

        if data.empty:
            return None

        center_lat = data["lat_grid"].mean()
        center_lon = data["long_grid"].mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

        for _, row in data.iterrows():
            folium.CircleMarker(
                location=[row["lat_grid"], row["long_grid"]],
                radius=4,
                color=get_color(row["rsrp_mean"]),
                fill=True,
                fill_opacity=0.7,
                popup=f"""
                CI: {row['ci']}<br>
                RSRP: {row['rsrp_mean']}
                """
            ).add_to(m)

        return m

    # =========================
    # SPLIT DATA PER BAND
    # =========================
    df_900 = df[df["band"] == "LTE 900"]
    df_1800 = df[df["band"] == "LTE 1800"]
    df_2100 = df[df["band"] == "LTE 2100"]
    df_2300 = df[df["band"] == "LTE 2300"]

    # =========================
    # LAYOUT 4 MAP
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("LTE 900")
        m1 = create_map(df_900)
        if m1:
            st_folium(m1, height=400)
        else:
            st.info("No data")

    with col2:
        st.subheader("LTE 1800")
        m2 = create_map(df_1800)
        if m2:
            st_folium(m2, height=400)
        else:
            st.info("No data")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("LTE 2100")
        m3 = create_map(df_2100)
        if m3:
            st_folium(m3, height=400)
        else:
            st.info("No data")

    with col4:
        st.subheader("LTE 2300")
        m4 = create_map(df_2300)
        if m4:
            st_folium(m4, height=400)
        else:
            st.info("No data")
