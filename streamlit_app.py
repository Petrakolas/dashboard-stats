from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Dashboard Statistik Deskriptif", page_icon="📊", layout="wide")

NUMERIC = ['Age', 'Study_Hours', 'Sleep_Hours', 'Attendance',
           'Exam_Score', 'Monthly_Spending', 'Screen_Hours', 'Satisfaction']
TEAL, NAVY, AMBER, CORAL = '#0f9d8a', '#14213d', '#e0a526', '#e4572e'


@st.cache_data
def load_data(path):
    return pd.read_csv(path)


def skew_label(s):
    if abs(s) < 0.5:
        return 'Simetris'
    return 'Miring kanan' if s > 0 else 'Miring kiri'


@st.cache_data
def describe(df):
    rows = []
    for c in NUMERIC:
        s = df[c].dropna()
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        rows.append({
            'Kolom': c, 'N': int(s.count()), 'Mean': s.mean(), 'Median': s.median(),
            'Modus': s.mode().iloc[0], 'Min': s.min(), 'Max': s.max(),
            'Range': s.max() - s.min(), 'Std': s.std(), 'Var': s.var(),
            'Q1': q1, 'Q3': q3, 'IQR': iqr, 'Skew': s.skew(),
            'CV %': s.std() / s.mean() * 100,
            'Outlier': int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()),
            'Bentuk': skew_label(s.skew()),
        })
    return pd.DataFrame(rows).set_index('Kolom')


# ---------- Data ----------
default_path = Path(__file__).parent / 'latihan1.csv'
uploaded = st.sidebar.file_uploader("Ganti dataset (CSV)", type='csv')
if uploaded is not None:
    df = pd.read_csv(uploaded)
elif default_path.exists():
    df = load_data(default_path)
else:
    st.error("File latihan1.csv tidak ditemukan. Letakkan di folder yang sama dengan streamlit_app.py atau unggah lewat sidebar.")
    st.stop()

missing = [c for c in NUMERIC + ['Gender'] if c not in df.columns]
if missing:
    st.error(f"Kolom berikut tidak ada di CSV: {', '.join(missing)}")
    st.stop()

stats = describe(df)
corr = df[NUMERIC].corr().round(2)

# ---------- Header ----------
st.title("📊 Statistik Deskriptif Mahasiswa")
st.caption("Sumber data: latihan1.csv. Kebiasaan belajar, tidur, layar, dan nilai ujian.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total mahasiswa", len(df))
k2.metric("Kolom data", df.shape[1])
k3.metric("Rata-rata nilai ujian", f"{stats.loc['Exam_Score', 'Mean']:.2f}")
k4.metric("Rata-rata jam belajar", f"{stats.loc['Study_Hours', 'Mean']:.2f}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Jelajahi variabel", "Hubungan variabel", "Perbandingan", "Tabel & korelasi", "Temuan"])

# ---------- Tab 1: explorer ----------
with tab1:
    col = st.selectbox("Pilih variabel", NUMERIC, index=NUMERIC.index('Exam_Score'))
    s = stats.loc[col]
    left, right = st.columns([3, 2])
    with left:
        fig = px.histogram(df, x=col, nbins=10, color_discrete_sequence=[TEAL])
        fig.add_vline(x=s['Mean'], line_dash='dash', line_color=CORAL, annotation_text='Mean')
        fig.add_vline(x=s['Median'], line_dash='dot', line_color=NAVY, annotation_text='Median',
                      annotation_position='bottom right')
        fig.update_layout(title=f"Distribusi {col}", yaxis_title="Frekuensi", bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)
        box = px.box(df, x=col, points='all', color_discrete_sequence=[TEAL])
        box.update_layout(height=200, margin=dict(t=10, b=10))
        st.plotly_chart(box, use_container_width=True)
    with right:
        items = ['Mean', 'Median', 'Modus', 'Std', 'Var', 'Range', 'Q1', 'Q3', 'IQR', 'Skew', 'CV %', 'Outlier']
        for i in range(0, len(items), 3):
            cols3 = st.columns(3)
            for c3, name in zip(cols3, items[i:i + 3]):
                v = s[name]
                c3.metric(name, f"{v:.2f}" if name != 'Outlier' else int(v))
        st.info(f"Bentuk distribusi: **{s['Bentuk']}** (skewness {s['Skew']:.2f})")

# ---------- Tab 2: scatter ----------
with tab2:
    c1, c2 = st.columns(2)
    x = c1.selectbox("Sumbu X", NUMERIC, index=NUMERIC.index('Study_Hours'))
    y = c2.selectbox("Sumbu Y", NUMERIC, index=NUMERIC.index('Exam_Score'))
    fig = px.scatter(df, x=x, y=y, color='Gender', opacity=0.8,
                     color_discrete_map={'F': CORAL, 'M': NAVY})
    b, a = np.polyfit(df[x], df[y], 1)
    xs = np.array([df[x].min(), df[x].max()])
    fig.add_trace(go.Scatter(x=xs, y=a + b * xs, mode='lines', name='Regresi',
                             line=dict(color=AMBER, width=3)))
    st.plotly_chart(fig, use_container_width=True)
    r = corr.loc[x, y]
    st.caption(f"r = {r:.2f}, R² = {r * r:.2f}, y = {a:.2f} + {b:.2f}x")

# ---------- Tab 3: comparisons ----------
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        counts = df['Gender'].value_counts()
        fig = px.pie(values=counts.values, names=counts.index, hole=0.55, title="Komposisi gender",
                     color=counts.index, color_discrete_map={'F': CORAL, 'M': NAVY})
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        ge = df.groupby('Gender')['Exam_Score'].mean().round(2).reset_index()
        fig = px.bar(ge, x='Gender', y='Exam_Score', text='Exam_Score', title="Rata-rata Exam Score per gender",
                     color='Gender', color_discrete_map={'F': CORAL, 'M': NAVY})
        st.plotly_chart(fig, use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        fig = px.bar(stats.reset_index(), x='Skew', y='Kolom', orientation='h', title="Skewness",
                     color='Skew', color_continuous_scale=[CORAL, '#eeeeee', AMBER], color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        fig = px.bar(stats.reset_index(), x='CV %', y='Kolom', orientation='h',
                     title="Variasi relatif (CV %)", color_discrete_sequence=['#5b6bd6'])
        st.plotly_chart(fig, use_container_width=True)

# ---------- Tab 4: table + heatmap ----------
with tab4:
    st.subheader("Ringkasan statistik")
    st.dataframe(stats.round(2), use_container_width=True)
    st.download_button("Unduh tabel (CSV)", stats.round(2).to_csv().encode('utf-8'),
                       "ringkasan_statistik.csv", "text/csv")
    st.subheader("Peta korelasi")
    fig = px.imshow(corr, text_auto=True, zmin=-1, zmax=1, aspect='auto',
                    color_continuous_scale=[CORAL, '#ffffff', TEAL])
    fig.update_layout(height=550)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Tab 5: insights ----------
with tab5:
    pairs = [(NUMERIC[i], NUMERIC[j], corr.iloc[i, j])
             for i in range(len(NUMERIC)) for j in range(i + 1, len(NUMERIC))]
    pairs.sort(key=lambda p: abs(p[2]), reverse=True)
    top = pairs[0]

    def strength(r):
        r = abs(r)
        return 'kuat' if r >= .7 else 'sedang' if r >= .4 else 'lemah' if r >= .2 else 'sangat lemah'

    by_cv = stats['CV %'].sort_values(ascending=False)
    by_skew = stats['Skew'].abs().sort_values(ascending=False)
    out = stats[stats['Outlier'] > 0]['Outlier']
    g = df['Gender'].value_counts()

    st.markdown(f"""
- Korelasi terkuat: **{top[0]}** dan **{top[1]}** (r = {top[2]:.2f}, {'positif' if top[2] > 0 else 'negatif'}, {strength(top[2])}).
- Variabel paling bervariasi: **{by_cv.index[0]}** (CV {by_cv.iloc[0]:.2f}%). Paling stabil: **{by_cv.index[-1]}** (CV {by_cv.iloc[-1]:.2f}%).
- Distribusi paling miring: **{by_skew.index[0]}** (skewness {stats.loc[by_skew.index[0], 'Skew']:.2f}, {skew_label(stats.loc[by_skew.index[0], 'Skew']).lower()}).
- {('Outlier (aturan 1.5 × IQR) ada di: ' + ', '.join(f'{k} ({v})' for k, v in out.items())) if len(out) else 'Tidak ada outlier berdasarkan aturan 1.5 × IQR.'}
- Dari {len(df)} mahasiswa, {g.get('F', 0)} perempuan dan {g.get('M', 0)} laki-laki. Korelasi tidak membuktikan sebab-akibat.
""")
