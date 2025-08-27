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

st.title("💡Dashboard Analisis Kondisi PJU Kabupaten Tasikmalaya")
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
gdf_joined, gdf_kecamatan = load_data("data_bersih.csv", "maps_kabtasik.geojson")

# ----------------------------------------------------
# 2. Ringkasan Data
# ----------------------------------------------------
st.header("Ringkasan Data PJU")
col1, col2 = st.columns(2)

target_mentah = 5589
target_bersih = len(gdf_joined)

placeholder_mentah = col1.empty()
placeholder_bersih = col2.empty()

# Animasi
for i in range(0, 101):
    current_mentah = int(target_mentah * (i / 100))
    current_bersih = int(target_bersih * (i / 100))
    placeholder_mentah.metric("Jumlah Data Mentah", f"{current_mentah} data")
    placeholder_bersih.metric("Jumlah Data Bersih", f"{current_bersih} data")
    time.sleep(0.01)

placeholder_mentah.metric("Jumlah Data Mentah", f"{target_mentah} data")
placeholder_bersih.metric("Jumlah Data Bersih", f"{target_bersih} data")

st.markdown("---")
time.sleep(0.5)

# ----------------------------------------------------
# 3. Distribusi Kondisi
# ----------------------------------------------------
st.header("Distribusi Kondisi PJU")
#st.markdown("Melihat perbandingan jumlah PJU dalam kondisi Baik dan Rusak.")

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
# 4. Hubungan Atribut & Kondisi
# ----------------------------------------------------
st.header("Visualisasi Atribut & Kondisi")

# Jenis Lampu
st.subheader("Hubungan antara Jenis Lampu dan Kondisi")
fig, ax = plt.subplots(figsize=(12, 6))
sns.countplot(x="Jenis Lampu", hue="Kondisi_Biner", data=gdf_joined, palette="crest", ax=ax)
plt.title("Hubungan Jenis Lampu dan Kondisi")
plt.xlabel("Jenis Lampu")
plt.ylabel("Jumlah")
plt.xticks(rotation=45, ha="right")
plt.legend(title="Kondisi", labels=["Baik", "Rusak"])
for container in ax.containers:
    ax.bar_label(container, fmt='%d', padding=2)
st.pyplot(fig)

st.markdown("---")
time.sleep(0.5)

# Jenis Tiang
st.subheader("Hubungan antara Jenis Tiang dan Kondisi")
fig, ax = plt.subplots(figsize=(12, 6))
sns.countplot(x="Jenis Tiang", hue="Kondisi_Biner", data=gdf_joined, palette="crest", ax=ax)
plt.title("Hubungan Jenis Tiang dan Kondisi")
plt.xlabel("Jenis Tiang")
plt.ylabel("Jumlah")
plt.xticks(rotation=45, ha="right")
plt.legend(title="Kondisi", labels=["Baik", "Rusak"])
for container in ax.containers:
    ax.bar_label(container, fmt='%d', padding=2)
st.pyplot(fig)

st.markdown("---")
time.sleep(0.5)

# ----------------------------------------------------
# 5. Analisis Rusak per Atribut
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
# 8. Persentase Rusak per Atribut
# ----------------------------------------------------
st.header("Persentase PJU Rusak per Atribut")

col1, col2 = st.columns(2)

# === 1. Persentase rusak per jenis lampu ===
with col1:
    st.subheader("Persentase Rusak per Jenis Lampu")

    lampu_total = gdf_joined.groupby("Jenis Lampu")["Kondisi_Biner"].count()
    lampu_rusak = gdf_joined.groupby("Jenis Lampu")["Kondisi_Biner"].sum()
    lampu_persen = (lampu_rusak / lampu_total * 100).sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    lampu_persen.plot(kind="bar", color="blue", alpha=0.7, ax=ax)
    ax.set_ylabel("Persentase Rusak (%)")
    ax.set_title("Persentase PJU Rusak berdasarkan Jenis Lampu")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

    for i, v in enumerate(lampu_persen):
        ax.text(i, v + 1, f"{v:.1f}%", ha='center', va='bottom', fontsize=9)

    ax.set_ylim(0, lampu_persen.max() * 1.2)
    st.pyplot(fig)

# === 2. Persentase rusak per jenis tiang ===
with col2:
    st.subheader("Persentase Rusak per Jenis Tiang")

    tiang_total = gdf_joined.groupby("Jenis Tiang")["Kondisi_Biner"].count()
    tiang_rusak = gdf_joined.groupby("Jenis Tiang")["Kondisi_Biner"].sum()
    tiang_persen = (tiang_rusak / tiang_total * 100).sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    tiang_persen.plot(kind="bar", color="blue", alpha=0.7, ax=ax)
    ax.set_ylabel("Persentase Rusak (%)")
    ax.set_title("Persentase PJU Rusak berdasarkan Jenis Tiang")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

    for i, v in enumerate(tiang_persen):
        ax.text(i, v + 1, f"{v:.1f}%", ha='center', va='bottom', fontsize=9)

    ax.set_ylim(0, tiang_persen.max() * 1.2)
    st.pyplot(fig)
st.markdown("---")

# ----------------------------------------------------
# 9. Stacked Bar Baik vs Rusak
# ----------------------------------------------------
st.header("Distribusi Kondisi PJU (Stacked Bar)")

col1, col2 = st.columns(2)

# === Stacked bar: Baik vs Rusak per Jenis Tiang ===
with col1:
    st.subheader("Baik vs Rusak per Jenis Tiang")

    tiang_counts = gdf_joined.groupby(["Jenis Tiang", "Kondisi_Biner"]).size().unstack(fill_value=0)
    tiang_counts = tiang_counts.rename(columns={0: "Baik", 1: "Rusak"})

    fig, ax = plt.subplots(figsize=(8, 5))
    tiang_counts.plot(
        kind="bar",
        stacked=True,
        color=["blue", "grey"],
        ax=ax
    )

    ax.set_ylabel("Jumlah PJU")
    ax.set_title("Distribusi Kondisi PJU berdasarkan Jenis Tiang")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

    # Tambahkan persentase rusak di atas bar
    for i, total in enumerate(tiang_counts.sum(axis=1)):
        rusak = tiang_counts.iloc[i]["Rusak"]
        persen_rusak = (rusak / total) * 100 if total > 0 else 0
        ax.text(i, total + 5, f"{persen_rusak:.1f}%", ha="center", va="bottom", fontsize=9, color="red")

    plt.tight_layout()
    st.pyplot(fig)

# === Stacked bar: Baik vs Rusak per Jenis Lampu ===
with col2:
    st.subheader("Baik vs Rusak per Jenis Lampu")

    lampu_counts = gdf_joined.groupby(["Jenis Lampu", "Kondisi_Biner"]).size().unstack(fill_value=0)
    lampu_counts = lampu_counts.rename(columns={0: "Baik", 1: "Rusak"})

    fig, ax = plt.subplots(figsize=(8, 5))
    lampu_counts.plot(
        kind="bar",
        stacked=True,
        color=["blue", "grey"],
        ax=ax
    )

    ax.set_ylabel("Jumlah PJU")
    ax.set_title("Distribusi Kondisi PJU berdasarkan Jenis Lampu")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

    # Tambahkan persentase rusak di atas bar
    for i, total in enumerate(lampu_counts.sum(axis=1)):
        rusak = lampu_counts.iloc[i]["Rusak"]
        persen_rusak = (rusak / total) * 100 if total > 0 else 0
        ax.text(i, total + 3, f"{persen_rusak:.1f}%", ha="center", va="bottom", fontsize=9, color="red")

    plt.tight_layout()
    st.pyplot(fig)
st.markdown("---")

# ----------------------------------------------------
# 6. Top 10 Kecamatan
# ----------------------------------------------------
st.header("Visualisasi Top 10 Kecamatan")

pju_summary = gdf_joined.groupby("Kecamatan_Final").agg(
    total_pju=("Kondisi_Biner", "count"),
    rusak=("Kondisi_Biner", "sum")
).reset_index()
pju_summary["persen_rusak"] = (pju_summary["rusak"] / pju_summary["total_pju"]) * 100

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Kecamatan dengan Jumlah PJU Rusak Terbanyak")
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
    st.subheader("Top 10 Kecamatan dengan Persentase PJU Rusak Tertinggi")
    top10_persen = pju_summary.sort_values("persen_rusak", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6)) # Ukuran disesuaikan
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
# 7. Peta Interaktif
# ----------------------------------------------------
st.header("Peta Sebaran PJU di Kabupaten Tasikmalaya")
try:
    with open("PJU_Interaktif_FIX.html", "r", encoding="utf-8") as f:
        html_map = f.read()
    st.components.v1.html(html_map, height=600)
except FileNotFoundError:
    st.error("File PJU_Interaktif_FIX.html tidak ditemukan. Pastikan file berada di direktori yang sama.")

