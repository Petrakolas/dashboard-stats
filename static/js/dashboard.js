const COLORS = ['#14213d', '#0f9d8a', '#e0a526', '#e4572e', '#5b6bd6', '#2a9fd6', '#8a5cc2', '#6b7a90'];
const $ = id => document.getElementById(id);
const charts = {};
const draw = (id, cfg) => { if (charts[id]) charts[id].destroy(); charts[id] = new Chart($(id), cfg); };
const skewInfo = s => Math.abs(s) < 0.5 ? ['Simetris', 'success'] : s > 0 ? ['Miring kanan', 'warning'] : ['Miring kiri', 'danger'];
const label = c => c.replace('_', ' ');

fetch('/api/stats').then(r => r.json()).then(data => {
    const cols = data.numeric_cols, S = data.stats, M = data.correlation;
    Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";

    // KPI
    const kpis = [
        [data.rows, 'Total mahasiswa', COLORS[0]],
        [data.columns, 'Kolom data', COLORS[1]],
        [S.Exam_Score.mean, 'Rata-rata nilai ujian', COLORS[2]],
        [S.Study_Hours.mean, 'Rata-rata jam belajar', COLORS[3]],
    ];
    $('kpis').innerHTML = kpis.map(k => `<div class="col-6 col-lg-3"><div class="kpi" style="--c:${k[2]}">
        <div class="v">${k[0]}</div><div class="l">${k[1]}</div></div></div>`).join('');

    // Selects
    const opts = cols.map(c => `<option value="${c}">${label(c)}</option>`).join('');
    ['colSelect', 'xSel', 'ySel'].forEach(id => $(id).innerHTML = opts);
    $('colSelect').value = 'Exam_Score';
    $('xSel').value = 'Study_Hours';
    $('ySel').value = 'Exam_Score';

    // Explorer: histogram + boxplot + chips
    function explorer(col) {
        const s = S[col], h = data.hist[col];
        draw('histChart', {
            type: 'bar',
            data: { labels: h.labels, datasets: [{ data: h.values, backgroundColor: 'rgba(15,157,138,.7)', borderRadius: 4 }] },
            options: { plugins: { legend: { display: false }, title: { display: true, text: 'Distribusi ' + label(col) } },
                       scales: { y: { title: { display: true, text: 'Frekuensi' } } } }
        });
        const pos = v => ((v - s.min) / ((s.max - s.min) || 1)) * 100;
        $('boxplot').innerHTML = `<div class="bp"><div class="bp-line"></div>
            <div class="bp-box" style="left:${pos(s.q1)}%;width:${pos(s.q3) - pos(s.q1)}%"></div>
            <div class="bp-med" style="left:${pos(s.median)}%" title="Median"></div></div>
            <div class="bp-labels"><span>Min ${s.min}</span><span>Q1 ${s.q1} | Median ${s.median} | Q3 ${s.q3}</span><span>Max ${s.max}</span></div>`;
        const sk = skewInfo(s.skew);
        const items = [['Mean (Rata-rata)', s.mean], ['Median (Nilai Tengah)', s.median], ['Modus (Nilai Paling Sering)', s.mode], ['Std Dev (Deviasi Standar)', s.std], ['Variansi (St Dev squared)', s.var],
            ['Range (Total distance between highest-lowest)', s.range], ['Q1 (Median of the 25%)', s.q1], ['Q3 (Median of the 75%)', s.q3], ['IQR (Spread of the middle 50%)', s.iqr], ['Skewness (Kemiringan)', s.skew], ['CV % (St Dev but %)', s.cv], ['Outlier', s.outliers]];
        $('chips').innerHTML = items.map(i => `<div class="chip"><b>${i[1]}</b><span>${i[0]}</span></div>`).join('')
            + `<div class="chip" style="grid-column:1/-1"><span class="badge text-bg-${sk[1]}">${sk[0]}</span></div>`;
    }
    $('colSelect').onchange = e => explorer(e.target.value);
    explorer('Exam_Score');

    // Gender
    const g = data.gender_counts;
    draw('genderChart', {
        type: 'doughnut',
        data: { labels: Object.keys(g), datasets: [{ data: Object.values(g), backgroundColor: [COLORS[3], COLORS[0]] }] },
        options: { cutout: '62%', plugins: { legend: { position: 'bottom' } } }
    });
    draw('genderExam', {
        type: 'bar',
        data: { labels: Object.keys(data.gender_exam), datasets: [{ data: Object.values(data.gender_exam), backgroundColor: [COLORS[3], COLORS[0]], borderRadius: 4 }] },
        options: { plugins: { legend: { display: false }, title: { display: true, text: 'Rata-rata Exam Score' } }, scales: { y: { min: 0 } } }
    });

    // Scatter + regression
    function scatter() {
        const x = $('xSel').value, y = $('ySel').value, X = data.raw[x], Y = data.raw[y], n = X.length;
        const mx = S[x].mean, my = S[y].mean;
        let sxy = 0, sxx = 0;
        for (let i = 0; i < n; i++) { sxy += (X[i] - mx) * (Y[i] - my); sxx += (X[i] - mx) ** 2; }
        const b = sxx ? sxy / sxx : 0, a = my - b * mx, r = M[cols.indexOf(x)][cols.indexOf(y)];
        draw('scatter', {
            type: 'scatter',
            data: { datasets: [
                { label: 'Data', data: X.map((v, i) => ({ x: v, y: Y[i] })), backgroundColor: 'rgba(15,157,138,.6)' },
                { label: 'Garis regresi', type: 'line', showLine: true, pointRadius: 0, borderColor: COLORS[3], borderWidth: 2,
                  data: [{ x: S[x].min, y: a + b * S[x].min }, { x: S[x].max, y: a + b * S[x].max }] }
            ] },
            options: { scales: { x: { title: { display: true, text: label(x) } }, y: { title: { display: true, text: label(y) } } },
                       plugins: { legend: { position: 'bottom' } } }
        });
        $('scatterNote').textContent = `r = ${r.toFixed(2)}, R\u00b2 = ${(r * r).toFixed(2)}, y = ${a.toFixed(2)} + ${b.toFixed(2)}x`;
    }
    $('xSel').onchange = $('ySel').onchange = scatter;
    scatter();

    // Skewness + CV
    const bar = (id, vals, colorFn) => draw(id, {
        type: 'bar',
        data: { labels: cols.map(label), datasets: [{ data: vals, backgroundColor: vals.map(colorFn), borderRadius: 4 }] },
        options: { indexAxis: 'y', plugins: { legend: { display: false } } }
    });
    bar('skewChart', cols.map(c => S[c].skew), v => v >= 0 ? COLORS[2] : COLORS[3]);
    bar('cvChart', cols.map(c => S[c].cv), () => COLORS[4]);

    // Stats table
    const heads = ['Kolom', 'N', 'Mean', 'Median', 'Modus', 'Min', 'Max', 'Range', 'Std', 'Var', 'Q1', 'Q3', 'IQR', 'Skew', 'Bentuk'];
    $('statsTable').innerHTML = `<div class="table-responsive"><table class="table table-striped table-sm mb-0">
        <thead class="table-dark"><tr>${heads.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>` +
        cols.map(c => { const s = S[c], k = skewInfo(s.skew);
            return `<tr><td><strong>${label(c)}</strong></td><td>${s.count}</td><td>${s.mean}</td><td>${s.median}</td><td>${s.mode}</td>
            <td>${s.min}</td><td>${s.max}</td><td>${s.range}</td><td>${s.std}</td><td>${s.var}</td><td>${s.q1}</td><td>${s.q3}</td>
            <td>${s.iqr}</td><td>${s.skew}</td><td><span class="badge text-bg-${k[1]}">${k[0]}</span></td></tr>`; }).join('') +
        '</tbody></table></div>';

    // Heatmap
    $('heatmap').innerHTML = `<div class="table-responsive"><table class="table table-bordered table-sm heatmap mb-0">
        <thead class="table-dark"><tr><th></th>${cols.map(c => `<th>${label(c)}</th>`).join('')}</tr></thead><tbody>` +
        cols.map((rn, i) => `<tr><th class="text-start">${label(rn)}</th>` + cols.map((cn, j) => {
            const r = M[i][j], rgb = r >= 0 ? '15,157,138' : '228,87,46';
            return `<td data-i="${i}" data-j="${j}" style="background:rgba(${rgb},${Math.abs(r)});color:${Math.abs(r) > .6 ? '#fff' : '#14213d'}"
                title="${label(rn)} vs ${label(cn)}">${r.toFixed(2)}</td>`;
        }).join('') + '</tr>').join('') + '</tbody></table></div>';
    $('heatmap').onclick = e => {
        const td = e.target.closest('td');
        if (!td) return;
        $('xSel').value = cols[td.dataset.i]; $('ySel').value = cols[td.dataset.j];
        scatter(); $('scatter').scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    // Auto insights
    const pairs = [];
    for (let i = 0; i < cols.length; i++) for (let j = i + 1; j < cols.length; j++) pairs.push([cols[i], cols[j], M[i][j]]);
    pairs.sort((p, q) => Math.abs(q[2]) - Math.abs(p[2]));
    const strength = r => { r = Math.abs(r); return r >= .7 ? 'kuat' : r >= .4 ? 'sedang' : r >= .2 ? 'lemah' : 'sangat lemah'; };
    const byCV = [...cols].sort((a, b) => S[b].cv - S[a].cv);
    const bySkew = [...cols].sort((a, b) => Math.abs(S[b].skew) - Math.abs(S[a].skew));
    const withOut = cols.filter(c => S[c].outliers > 0);
    const top = pairs[0];
    $('insights').innerHTML = [
        `Korelasi terkuat: <strong>${label(top[0])}</strong> dan <strong>${label(top[1])}</strong> (r = ${top[2].toFixed(2)}, ${top[2] > 0 ? 'positif' : 'negatif'}, ${strength(top[2])}).`,
        `Variabel paling bervariasi: <strong>${label(byCV[0])}</strong> (CV ${S[byCV[0]].cv}%). Paling stabil: <strong>${label(byCV[byCV.length - 1])}</strong> (CV ${S[byCV[byCV.length - 1]].cv}%).`,
        `Distribusi paling miring: <strong>${label(bySkew[0])}</strong> (skewness ${S[bySkew[0]].skew}, ${skewInfo(S[bySkew[0]].skew)[0].toLowerCase()}).`,
        withOut.length ? `Outlier (aturan 1.5 \u00d7 IQR) ada di: ${withOut.map(c => `${label(c)} (${S[c].outliers})`).join(', ')}.` : 'Tidak ada outlier berdasarkan aturan 1.5 \u00d7 IQR.',
        `Dari ${data.rows} mahasiswa, ${g.F || 0} perempuan dan ${g.M || 0} laki-laki. Korelasi tidak membuktikan sebab-akibat.`
    ].map(t => `<li>${t}</li>`).join('');
});
