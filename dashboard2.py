import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium import LayerControl
from streamlit_folium import folium_static
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import time

# ----------------------------------------------------
# 0. Konfigurasi Halaman
# ----------------------------------------------------
st.set_page_config(
    page_title="Dashboard Analisis PJU Kabupaten Tasikmalaya",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Dashboard Analisis Kondisi PJU Kabupaten Tasikmalaya")
st.markdown("---")

# ----------------------------------------------------
# 1. Fungsi untuk Memuat Data
# ----------------------------------------------------
@st.cache_data
def load_data(data_filepath, geojson_filepath):
    try:
        gdf_joined = pd.read_csv(data_filepath)

        # GeoJSON
        gdf_kecamatan = gpd.read_file(geojson_filepath)
        if gdf_kecamatan.crs is None or gdf_kecamatan.crs.to_epsg() != 4326:
            gdf_kecamatan = gdf_kecamatan.to_crs("EPSG:4326")

        # Definisi kolom Kondisi_Biner (0=Baik, 1=Rusak)
        if 'Kondisi' in gdf_joined.columns:
            gdf_joined['Kondisi_Biner'] = gdf_joined['Kondisi'].astype(str).str.lower().apply(
                lambda x: 1 if "rusak" in x else 0
            )
        return gdf_joined, gdf_kecamatan

    except Exception as e:
        st.error(f"Terjadi kesalahan saat load data: {e}")
        st.stop()

# Load data
gdf_joined, gdf_kecamatan = load_data("dataset_clean.csv", "maps_kabtasik.geojson")

# ----------------------------------------------------
# 2. Ringkasan Data
# ----------------------------------------------------
# st.header("Ringkasan Data PJU")
# col1, col2 = st.columns(2)

# target_mentah = 5589
#target_bersih = len(gdf_joined)

#placeholder_mentah = col1.empty()
#placeholder_bersih = col2.empty()

# Animasi
# for i in range(0, 101):
#    current_mentah = int(target_mentah * (i / 100))
#    current_bersih = int(target_bersih * (i / 100))
#    placeholder_mentah.metric("Jumlah Data Mentah", f"{current_mentah} data")
#    placeholder_bersih.metric("Jumlah Data Bersih", f"{current_bersih} data")
#    time.sleep(0.01)

#placeholder_mentah.metric("Jumlah Data Mentah", f"{target_mentah} data")
#placeholder_bersih.metric("Jumlah Data Bersih", f"{target_bersih} data")

#st.markdown("---")
#time.sleep(0.5)

# ----------------------------------------------------
# 3. Distribusi Kondisi
# ----------------------------------------------------
st.header("Distribusi Kondisi PJU")

fig, ax = plt.subplots(figsize=(8, 6))
ax = sns.countplot(x="Kondisi_Biner", data=gdf_joined, palette="crest")
plt.title("Distribusi Kondisi PJU (Baik vs Rusak)")
plt.xlabel("Kondisi")
plt.ylabel("Jumlah")
plt.xticks([0, 1], ["Baik", "Rusak"])
for container in ax.containers:
    ax.bar_label(container, fmt='%d', label_type='edge', padding=3)
st.pyplot(fig)

st.markdown("---")
time.sleep(0.5)

# ----------------------------------------------------
# 4. Analisis Rusak per Atribut
# ----------------------------------------------------
st.header("Analisis PJU Rusak Berdasarkan Atribut")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Jumlah PJU Rusak Berdasarkan Jenis Lampu")
    rusak_per_lampu = (
        gdf_joined[gdf_joined["Kondisi_Biner"] == 1]["Jenis Lampu"]
        .value_counts()
        .reset_index()
    )
    rusak_per_lampu.columns = ["Jenis Lampu", "Jumlah Rusak"]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=rusak_per_lampu, x="Jenis Lampu", y="Jumlah Rusak", palette="crest", ax=ax)
    plt.xticks(rotation=45, ha="right")
    for i, v in enumerate(rusak_per_lampu["Jumlah Rusak"]):
        ax.text(i, v + 0.2, str(v), ha="center", fontsize=9)
    st.pyplot(fig)

with col2:
    st.subheader("Jumlah PJU Rusak Berdasarkan Jenis Tiang")
    rusak_per_tiang = (
        gdf_joined[gdf_joined["Kondisi_Biner"] == 1]["Jenis Tiang"]
        .value_counts()
        .reindex(gdf_joined["Jenis Tiang"].unique(), fill_value=0)
        .reset_index()
    )
    rusak_per_tiang.columns = ["Jenis Tiang", "Jumlah Rusak"]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=rusak_per_tiang, x="Jenis Tiang", y="Jumlah Rusak", palette="crest", ax=ax)
    plt.xticks(rotation=45, ha="right")
    for i, v in enumerate(rusak_per_tiang["Jumlah Rusak"]):
        ax.text(i, v + 0.2, str(v), ha="center", fontsize=9)
    st.pyplot(fig)

st.markdown("---")

# ----------------------------------------------------
# 5. Top 10 Kecamatan
# ----------------------------------------------------
st.header("Visualisasi Top 10 Kecamatan")

pju_summary = gdf_joined.groupby("Kecamatan_Final").agg(
    total_pju=("Kondisi_Biner", "count"),
    rusak=("Kondisi_Biner", "sum")
).reset_index()
pju_summary["persen_rusak"] = (pju_summary["rusak"] / pju_summary["total_pju"]) * 100

col1, col2 = st.columns(2)

with col1:
    st.subheader("10 Teratas Kecamatan dengan Jumlah PJU Rusak Terbanyak")
    top10 = pju_summary.sort_values("rusak", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(
        x="rusak", 
        y="Kecamatan_Final", 
        data=top10,
        order=top10.sort_values("rusak", ascending=False)["Kecamatan_Final"],
        palette="crest",
        ax=ax
    )
    for container in ax.containers:
        ax.bar_label(container, fmt='%d', padding=2)
    plt.xlabel("Jumlah PJU Rusak")
    plt.ylabel("Kecamatan")
    st.pyplot(fig)

with col2:
    st.subheader("10 Teratas Kecamatan dengan Persentase PJU Rusak Tertinggi")
    top10_persen = pju_summary.sort_values("persen_rusak", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(
        x="persen_rusak", 
        y="Kecamatan_Final", 
        data=top10_persen,
        order=top10_persen.sort_values("persen_rusak", ascending=False)["Kecamatan_Final"],
        palette="crest",
        ax=ax
    )
    for i, v in enumerate(top10_persen["persen_rusak"]):
        ax.text(v + 1, i, f"{v:.1f}%", va="center")
    plt.xlabel("Persentase PJU Rusak (%)")
    plt.ylabel("Kecamatan")
    st.pyplot(fig)

st.markdown("---")

# ----------------------------------------------------
# 6. Peta Interaktif
# ----------------------------------------------------
st.header("Peta Sebaran PJU di Kabupaten Tasikmalaya")
try:
    with open("peta_pju_tasik.html", "r", encoding="utf-8") as f:
        html_map = f.read()
    st.components.v1.html(html_map, height=600)
except FileNotFoundError:
    st.error("File tidak ditemukan. Pastikan file berada di direktori yang sama.")

# ----------------------------------------------------
# 6. Tabel Rekap
# ----------------------------------------------------

tabel = (
    gdf_joined.groupby("Kecamatan_Final")
    .agg(
        Total_PJU=("Kondisi_Biner", "count"),
        PJU_Rusak=("Kondisi_Biner", "sum"),
        PJU_Baik=("Kondisi_Biner", lambda x: (x == 0).sum())
    )
    .reset_index()
)

# ubah kolom
tabel = tabel.rename(columns={"Kecamatan_Final": "Kecamatan"})
tabel = tabel.rename(columns=lambda c: c.replace("_", " "))

# tambahkan nomor urut
tabel.insert(0, "No", range(1, len(tabel) + 1))

st.header("Tabel Rekapitulasi PJU per Kecamatan")

# =========================================
# ✅ Input search
# =========================================
search = st.text_input(
    "",
    placeholder="🔍 Cari nama kecamatan...",
    label_visibility="collapsed"
)

# =========================================
# ✅ Filter search
# =========================================
if search:
    mask = tabel["Kecamatan"].str.contains(search, case=False, na=False)
    rekap_view = tabel[mask].copy()
else:
    mask = pd.Series([False] * len(tabel), index=tabel.index)
    rekap_view = tabel.copy()

# =========================================
# ✅ Hilangkan index kiri
# =========================================
rekap_view = rekap_view.reset_index(drop=True)

# =========================================
# ✅ Highlight baris hasil pencarian
# =========================================
def highlight_row(row):
    return ['background-color: #d6eaff'] * len(row) if mask.loc[row.name] else [''] * len(row)

# =========================================
# ✅ Styling tabel
# =========================================
styler = (
    rekap_view.style
    .hide(axis="index")
    .set_table_styles([
        {'selector': 'table', 'props': [
            ('border-collapse', 'collapse'),
            ('width', '100%'),
        ]},
        {'selector': 'th, td', 'props': [
            ('border', '1px solid black'),
            ('padding', '6px')
        ]},
        {'selector': 'th', 'props': [
            ('text-align', 'center'),
            ('font-weight', 'bold'),
            ('background-color', '#f8f8f8')
        ]},
    ])
    .set_properties(**{
        'text-align': 'center',
        'white-space': 'normal',
        'overflow': 'visible',
        'text-overflow': 'clip',
    })
    .set_properties(
        subset=pd.IndexSlice[:, ["Kecamatan"]],
        **{'text-align': 'left'}
    )
    .apply(highlight_row, axis=1)
)

# =========================================
# ✅ CSS baru
# =========================================
st.markdown("""
    <style>
    div[data-testid="stElementToolbar"] {display: none;}

    .scroll-box {
        padding: 0px;
        max-height: 600px;
        overflow-y: auto;
        background-color: #ffffff;
        border: none !important;
        box-shadow: none !important;
    }

    .scroll-box table {
        width: 100% !important;
        border-collapse: collapse !important;
    }

    .scroll-box thead th {
        position: sticky;
        top: 0;
        background: silver !important;
        z-index: 10;
        border-top: 1px solid black !important;
        border-bottom: 1px solid black !important;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================
# ✅ Render tabel scroll
# =========================================
html_table = styler.to_html(index=False)
st.markdown(f"<div class='scroll-box'>{html_table}</div>", unsafe_allow_html=True)
