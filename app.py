import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Statistik Deskriptif",
    page_icon="📊",
    layout="wide",
)

NUMERIC = ['Age', 'Study_Hours', 'Sleep_Hours', 'Attendance',
           'Exam_Score', 'Monthly_Spending', 'Screen_Hours', 'Satisfaction']

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv('latihan1.csv')

df = load_data()

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📊 Dashboard Statistik Deskriptif")
st.caption("Data: latihan1.csv")
st.markdown("---")

# ------------------------------------------------------------
# SUMMARY CARDS
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Baris", len(df))
with col2:
    st.metric("Total Kolom", df.shape[1])
with col3:
    f_count = df['Gender'].value_counts().get('F', 0)
    m_count = df['Gender'].value_counts().get('M', 0)
    st.metric("Gender", f"{f_count}F / {m_count}M")
with col4:
    avg_score = df['Exam_Score'].mean().round(1)
    st.metric("Rata-rata Nilai", avg_score)

st.markdown("---")

# ------------------------------------------------------------
# STATS TABLE
# ------------------------------------------------------------
st.header("📈 Ringkasan Statistik per Kolom")

stats_rows = []
for col in NUMERIC:
    s = df[col].dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    stats_rows.append({
        'Kolom': col,
        'N': int(s.count()),
        'Mean': round(float(s.mean()), 2),
        'Median': round(float(s.median()), 2),
        'Modus': float(s.mode().iloc[0]),
        'Min': float(s.min()),
        'Max': float(s.max()),
        'Range': round(float(s.max() - s.min()), 2),
        'Std Dev': round(float(s.std()), 2),
        'Variance': round(float(s.var()), 2),
        'Q1': round(float(q1), 2),
        'Q3': round(float(q3), 2),
        'IQR': round(float(iqr), 2),
        'Skew': round(float(s.skew()), 2),
        'CV (%)': round(float(s.std() / s.mean() * 100), 2),
        'Outliers': int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()),
    })

stats_df = pd.DataFrame(stats_rows).set_index('Kolom')
st.dataframe(stats_df, use_container_width=True)

# ------------------------------------------------------------
# HISTOGRAMS
# ------------------------------------------------------------
st.header("📊 Distribusi Data")

cols_per_row = 2
for i in range(0, len(NUMERIC), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(NUMERIC[i:i + cols_per_row]):
        with cols[j]:
            fig = px.histogram(
                df, x=col, nbins=10,
                title=col,
                color_discrete_sequence=['#ff6b00']
            )
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=False,
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# CORRELATION HEATMAP
# ------------------------------------------------------------
st.header("🔥 Correlation Heatmap")

corr = df[NUMERIC].corr().round(2)

fig = px.imshow(
    corr,
    text_auto=True,
    aspect='auto',
    color_continuous_scale='RdBu_r',
    zmin=-1, zmax=1,
)
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# GENDER COMPARISON
# ------------------------------------------------------------
st.header("⚖️ Perbandingan Gender")

gender_exam = df.groupby('Gender')['Exam_Score'].mean().round(2).reset_index()
fig = px.bar(
    gender_exam, x='Gender', y='Exam_Score',
    color='Gender',
    text_auto=True,
    color_discrete_map={'F': '#e91e63', 'M': '#2196f3'},
)
fig.update_layout(showlegend=False, height=350)
st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# RAW DATA (expandable)
# ------------------------------------------------------------
with st.expander("🔍 Lihat Data Mentah"):
    st.dataframe(df, use_container_width=True)