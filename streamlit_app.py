import streamlit as st
import pandas as pd
import plotly.express as px
import os
CSV_PATH = os.path.join(os.path.dirname(__file__), 'latihan1.csv')
df = pd.read_csv(CSV_PATH)

st.set_page_config(page_title="Dashboard Statistik", layout="wide")

st.title("📊 Dashboard Statistik Deskriptif")
st.caption("Data: latihan1.csv")

# Summary cards
col1, col2, col3 = st.columns(3)
col1.metric("Total Baris", len(df))
col2.metric("Kolom Numerik", 8)
col3.metric("Gender", f"{df['Gender'].value_counts().get('F',0)}F / {df['Gender'].value_counts().get('M',0)}M")

# Numeric columns
numeric_cols = ['Age', 'Study_Hours', 'Sleep_Hours', 'Attendance',
                'Exam_Score', 'Monthly_Spending', 'Screen_Hours', 'Satisfaction']

# Stats table
st.header("📈 Ringkasan Statistik per Kolom")
stats_df = df[numeric_cols].describe().T
stats_df['range'] = stats_df['max'] - stats_df['min']
stats_df['skew'] = df[numeric_cols].skew()
stats_df = stats_df.round(2)
st.dataframe(stats_df, use_container_width=True)

# Histograms
st.header("📊 Distribusi Data")
for i in range(0, len(numeric_cols), 2):
    cols = st.columns(2)
    for j, col in enumerate(numeric_cols[i:i+2]):
        with cols[j]:
            fig = px.histogram(df, x=col, nbins=10, title=col)
            st.plotly_chart(fig, use_container_width=True)

# Correlation heatmap
st.header("🔥 Correlation Heatmap")
corr = df[numeric_cols].corr().round(2)
fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect='auto')
st.plotly_chart(fig, use_container_width=True)