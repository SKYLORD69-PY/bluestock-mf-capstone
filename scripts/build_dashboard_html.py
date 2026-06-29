"""
build_dashboard_html.py
========================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 5 bonus: builds a real, working interactive HTML dashboard
(dashboard/bluestock_dashboard.html) as a substitute for the .pbix file
that can't be produced programmatically. Uses Chart.js via CDN, with the
project's actual data embedded inline as JSON (built by dashboard_pages.py
data exports) so it works standalone, no server needed.

Run from the project root:
    python scripts/build_dashboard_html.py
"""
import json
from pathlib import Path

DATA_PATH = Path("dashboard/_data_for_html.json")
OUT_PATH = Path("dashboard/bluestock_dashboard.html")

data = json.loads(DATA_PATH.read_text())
DATA_JSON = json.dumps(data)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Bluestock MF Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root {
    --navy: #0B2545; --blue: #1B6CA8; --teal: #13A89E; --gold: #B8791C;
    --red: #C8553D; --gray: #6B7280; --bg: #F4F6F8; --border: #D0D5DD;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; background: var(--bg); color: var(--navy); }
  header { background: white; border-bottom: 1px solid var(--border); padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 10; }
  .brand { font-weight: 800; font-size: 18px; letter-spacing: 0.5px; }
  .brand span { display: block; font-weight: 400; font-size: 11px; color: var(--gray); letter-spacing: 0; }
  nav { display: flex; gap: 6px; }
  nav button { background: none; border: none; padding: 10px 16px; font-size: 14px; color: var(--gray); cursor: pointer; border-radius: 6px; font-weight: 600; }
  nav button.active { background: var(--navy); color: white; }
  nav button:hover:not(.active) { background: #EEF2F6; }
  main { padding: 22px 26px 60px; max-width: 1400px; margin: 0 auto; }
  .page { display: none; }
  .page.active { display: block; animation: fadein 0.25s ease; }
  @keyframes fadein { from { opacity: 0; transform: translateY(4px);} to { opacity:1; transform: translateY(0);} }
  .kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
  .kpi { border-radius: 10px; padding: 18px 20px; color: white; }
  .kpi .val { font-size: 26px; font-weight: 800; }
  .kpi .lbl { font-size: 13px; opacity: 0.9; margin-top: 4px; }
  .kpi .sub { font-size: 11px; opacity: 0.75; margin-top: 6px; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .grid2.wide-left { grid-template-columns: 1.3fr 1fr; }
  .card { background: white; border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; margin-bottom: 16px; }
  .card h3 { margin: 0 0 12px; font-size: 14px; color: var(--navy); font-weight: 700; }
  .full { grid-column: 1 / -1; }
  .controls { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
  select, .filter-chip { font-size: 13px; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; background: white; color: var(--navy); }
  .filter-chip { cursor: pointer; background: #EEF2F6; user-select: none; }
  .filter-chip.active { background: var(--blue); color: white; border-color: var(--blue); }
  table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  th, td { padding: 7px 8px; text-align: left; border-bottom: 1px solid #EEF2F6; }
  th { cursor: pointer; color: var(--navy); background: #F8FAFB; position: sticky; top: 0; user-select: none; }
  th:hover { background: #EEF2F6; }
  th.sorted::after { content: " \\25BC"; font-size: 9px; }
  tbody tr:hover { background: #F8FAFB; }
  .footnote { font-size: 11px; color: var(--gray); font-style: italic; margin-top: 6px; }
  canvas { max-height: 340px; }
  .heatmap-table td { text-align: center; font-size: 10px; color: #1f2937; }
  .heatmap-table th { font-size: 10px; }
</style>
</head>
<body>

<header>
  <div class="brand">BLUESTOCK<span>Mutual Fund Analytics — Interactive Dashboard</span></div>
  <nav id="tabs">
    <button data-page="p1" class="active">Industry Overview</button>
    <button data-page="p2">Fund Performance</button>
    <button data-page="p3">Investor Analytics</button>
    <button data-page="p4">SIP &amp; Market Trends</button>
  </nav>
</header>

<main>

<!-- PAGE 1 -->
<div class="page active" id="p1">
  <div class="kpis">
    <div class="kpi" style="background:var(--navy)"><div class="val">Rs 81L Cr</div><div class="lbl">Total Industry AUM</div><div class="sub">Dec 2025, AMFI (full industry)</div></div>
    <div class="kpi" style="background:var(--blue)"><div class="val" id="kpi-sip"></div><div class="lbl">Monthly SIP Inflow</div><div class="sub">All-time high, Dec 2025</div></div>
    <div class="kpi" style="background:var(--teal)"><div class="val" id="kpi-folios"></div><div class="lbl">Total Folios</div><div class="sub">Dec 2025</div></div>
    <div class="kpi" style="background:var(--gold)"><div class="val">1,908</div><div class="lbl">Total Schemes</div><div class="sub">Dec 2025, AMFI (full industry)</div></div>
  </div>
  <div class="grid2">
    <div class="card"><h3>AUM Trend — Sum of the 10 Fund Houses in This Dataset</h3><canvas id="chart-amc-trend"></canvas></div>
    <div class="card"><h3>AUM by Fund House — Latest Snapshot</h3><canvas id="chart-amc-bar"></canvas></div>
  </div>
  <div class="card"><h3>Monthly SIP Inflow Trend, Jan 2022 - Dec 2025</h3><canvas id="chart-sip-trend"></canvas></div>
</div>

<!-- PAGE 2 -->
<div class="page" id="p2">
  <div class="controls">
    <select id="filter-category"><option value="">All categories</option></select>
    <select id="filter-fundhouse"><option value="">All fund houses</option></select>
  </div>
  <div class="grid2 wide-left">
    <div class="card"><h3>Return vs Risk (bubble size = AUM)</h3><canvas id="chart-scatter"></canvas></div>
    <div class="card">
      <h3>Fund Scorecard (click a header to sort)</h3>
      <table id="scorecard-table">
        <thead><tr>
          <th data-key="scheme_name">Scheme</th>
          <th data-key="return_3yr_pct">3yr Ret %</th>
          <th data-key="sharpe_ratio">Sharpe</th>
          <th data-key="fund_score">Score</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
  <div class="card full">
    <h3>NAV vs Benchmark — Trailing 3 Years (indexed to 100)</h3>
    <div class="controls">
      <label style="font-size:13px;color:var(--gray)">Fund: </label>
      <select id="fund-selector"></select>
    </div>
    <canvas id="chart-nav-bench" style="max-height:380px"></canvas>
  </div>
</div>

<!-- PAGE 3 -->
<div class="page" id="p3">
  <div class="controls">
    <select id="filter-state"><option value="ALL">All states</option></select>
  </div>
  <div class="grid2">
    <div class="card"><h3>Transaction Amount by State</h3><canvas id="chart-state-bar"></canvas></div>
    <div class="card"><h3>Transaction Amount Split — SIP / Lumpsum / Redemption</h3><canvas id="chart-type-donut"></canvas></div>
    <div class="card"><h3>Average SIP Amount by Age Group</h3><canvas id="chart-age-bar"></canvas></div>
    <div class="card"><h3>Monthly Transaction Volume</h3><canvas id="chart-tx-volume"></canvas></div>
  </div>
</div>

<!-- PAGE 4 -->
<div class="page" id="p4">
  <div class="card"><h3>SIP Inflow (bar) vs NIFTY 50 (line), 2022-2025</h3><canvas id="chart-dual" style="max-height:380px"></canvas></div>
  <div class="grid2">
    <div class="card"><h3>Category Net Inflow Heatmap, FY 2024-25</h3><div id="heatmap-container" style="overflow-x:auto"></div></div>
    <div class="card"><h3>Top 5 Categories by Net Inflow, FY 2024-25</h3><canvas id="chart-top5cat"></canvas></div>
  </div>
</div>

</main>

<script>
const DATA = __DATA_JSON__;
const PALETTE = { navy:"#0B2545", blue:"#1B6CA8", teal:"#13A89E", gold:"#B8791C", red:"#C8553D", gray:"#6B7280" };
Chart.defaults.font.family = "-apple-system, 'Segoe UI', Roboto, Arial, sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.labels.boxWidth = 12;

// ---- Tab navigation ----
document.getElementById("tabs").addEventListener("click", (e) => {
  const btn = e.target.closest("button"); if (!btn) return;
  document.querySelectorAll("#tabs button").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById(btn.dataset.page).classList.add("active");
});

// ---- KPI text ----
document.getElementById("kpi-sip").textContent = DATA.kpi.sip_inflow;
document.getElementById("kpi-folios").textContent = DATA.kpi.folios;

// ============================ PAGE 1 ============================
new Chart(document.getElementById("chart-amc-trend"), {
  type: "line",
  data: { labels: DATA.amc_trend.labels, datasets: [{ label: "AUM (Rs lakh crore)", data: DATA.amc_trend.values,
    borderColor: PALETTE.blue, backgroundColor: PALETTE.blue, tension: 0.15, pointRadius: 3 }] },
  options: { plugins: { legend: { display: false } }, scales: { y: { title: { display:true, text:"Rs lakh crore" } } } }
});
new Chart(document.getElementById("chart-amc-bar"), {
  type: "bar",
  data: { labels: DATA.amc_bar.labels, datasets: [{ label: "AUM (Rs lakh crore)", data: DATA.amc_bar.values, backgroundColor: PALETTE.navy }] },
  options: { indexAxis: "y", plugins: { legend: { display: false } } }
});
new Chart(document.getElementById("chart-sip-trend"), {
  type: "bar",
  data: { labels: DATA.sip_trend.labels, datasets: [{ label: "SIP inflow (Rs crore)", data: DATA.sip_trend.values, backgroundColor: PALETTE.teal }] },
  options: { plugins: { legend: { display: false } } }
});

// ============================ PAGE 2 ============================
const catSelect = document.getElementById("filter-category");
const fhSelect = document.getElementById("filter-fundhouse");
DATA.categories.forEach(c => catSelect.insertAdjacentHTML("beforeend", `<option value="${c}">${c}</option>`));
DATA.fund_houses.forEach(f => fhSelect.insertAdjacentHTML("beforeend", `<option value="${f}">${f}</option>`));

let scatterChart, sortKey = "fund_score", sortDir = -1;

function filteredScorecard() {
  return DATA.scorecard.filter(r =>
    (!catSelect.value || r.category === catSelect.value) &&
    (!fhSelect.value || r.fund_house === fhSelect.value)
  );
}

function renderScatter() {
  const rows = filteredScorecard();
  const byCategory = { Equity: [], Debt: [] };
  rows.forEach(r => { (byCategory[r.category] || (byCategory[r.category] = [])).push(
    { x: r.return_3yr_pct, y: r.risk_std_pct, r: Math.sqrt(r.aum_crore) / 8, label: r.scheme_name }); });
  const datasets = Object.entries(byCategory).map(([cat, pts]) => ({
    label: cat, data: pts, backgroundColor: cat === "Equity" ? "rgba(27,108,168,0.6)" : "rgba(200,85,61,0.6)",
  }));
  if (scatterChart) scatterChart.destroy();
  scatterChart = new Chart(document.getElementById("chart-scatter"), {
    type: "bubble",
    data: { datasets },
    options: {
      scales: { x: { title: { display:true, text:"3yr return (%)" } }, y: { title: { display:true, text:"Risk — annualised std dev (%)" } } },
      plugins: { tooltip: { callbacks: { label: (ctx) => `${ctx.raw.label}: ${ctx.raw.x.toFixed(1)}% ret, ${ctx.raw.y.toFixed(1)}% risk` } } }
    }
  });
}

function renderTable() {
  let rows = filteredScorecard();
  rows = rows.slice().sort((a, b) => (a[sortKey] > b[sortKey] ? 1 : -1) * sortDir);
  const tbody = document.querySelector("#scorecard-table tbody");
  tbody.innerHTML = rows.map(r => `<tr>
    <td>${r.scheme_name}</td><td>${r.return_3yr_pct.toFixed(2)}</td>
    <td>${r.sharpe_ratio.toFixed(2)}</td><td>${r.fund_score.toFixed(1)}</td></tr>`).join("");
  document.querySelectorAll("#scorecard-table th").forEach(th => {
    th.classList.toggle("sorted", th.dataset.key === sortKey);
  });
}

document.querySelectorAll("#scorecard-table th").forEach(th => th.addEventListener("click", () => {
  if (sortKey === th.dataset.key) sortDir *= -1; else { sortKey = th.dataset.key; sortDir = -1; }
  renderTable();
}));
[catSelect, fhSelect].forEach(el => el.addEventListener("change", () => { renderScatter(); renderTable(); }));
renderScatter(); renderTable();

// NAV vs benchmark, with fund selector
const fundSelector = document.getElementById("fund-selector");
Object.entries(DATA.nav_vs_bench.fund_names).forEach(([code, name]) =>
  fundSelector.insertAdjacentHTML("beforeend", `<option value="${code}">${name}</option>`));
let navChart;
function renderNavChart() {
  const code = fundSelector.value || Object.keys(DATA.nav_vs_bench.fund_names)[0];
  if (navChart) navChart.destroy();
  navChart = new Chart(document.getElementById("chart-nav-bench"), {
    type: "line",
    data: { labels: DATA.nav_vs_bench.labels, datasets: [
      { label: DATA.nav_vs_bench.fund_names[code], data: DATA.nav_vs_bench.funds[code], borderColor: PALETTE.blue, pointRadius: 0, borderWidth: 2 },
      { label: "NIFTY 100", data: DATA.nav_vs_bench.nifty100, borderColor: PALETTE.gray, borderDash: [5, 4], pointRadius: 0, borderWidth: 2 },
    ] },
    options: { scales: { y: { title: { display:true, text:"Indexed (start = 100)" } } } }
  });
}
fundSelector.addEventListener("change", renderNavChart);
renderNavChart();

// ============================ PAGE 3 ============================
const stateSelect = document.getElementById("filter-state");
DATA.states_list.forEach(s => stateSelect.insertAdjacentHTML("beforeend", `<option value="${s}">${s}</option>`));

new Chart(document.getElementById("chart-state-bar"), {
  type: "bar",
  data: { labels: DATA.state_amounts.labels, datasets: [{ label: "Amount (Rs crore)", data: DATA.state_amounts.values, backgroundColor: PALETTE.navy }] },
  options: { indexAxis: "y", plugins: { legend: { display: false } } }
});

let typeChart, ageChart, txVolChart;
function renderStateFilteredCharts() {
  const key = stateSelect.value || "ALL";
  const d = DATA.by_state[key];

  if (typeChart) typeChart.destroy();
  typeChart = new Chart(document.getElementById("chart-type-donut"), {
    type: "doughnut",
    data: { labels: d.type_donut.labels, datasets: [{ data: d.type_donut.values, backgroundColor: [PALETTE.blue, PALETTE.teal, PALETTE.red] }] },
  });

  if (ageChart) ageChart.destroy();
  ageChart = new Chart(document.getElementById("chart-age-bar"), {
    type: "bar",
    data: { labels: d.age_bar.labels, datasets: [{ label: "Avg SIP (Rs)", data: d.age_bar.values,
      backgroundColor: [PALETTE.navy, PALETTE.blue, PALETTE.teal, PALETTE.gold, "#6FA84B"] }] },
    options: { plugins: { legend: { display: false } } }
  });

  if (txVolChart) txVolChart.destroy();
  txVolChart = new Chart(document.getElementById("chart-tx-volume"), {
    type: "line",
    data: { labels: d.tx_volume.labels, datasets: [{ label: "Transactions", data: d.tx_volume.values, borderColor: PALETTE.teal, tension: 0.2 }] },
    options: { plugins: { legend: { display: false } } }
  });
}
stateSelect.addEventListener("change", renderStateFilteredCharts);
renderStateFilteredCharts();

// ============================ PAGE 4 ============================
new Chart(document.getElementById("chart-dual"), {
  data: {
    labels: DATA.sip_trend.labels,
    datasets: [
      { type: "bar", label: "SIP inflow (Rs Cr)", data: DATA.sip_trend.values, backgroundColor: PALETTE.teal, yAxisID: "y" },
      { type: "line", label: "NIFTY 50", data: DATA.nifty50_monthly.values, borderColor: PALETTE.navy, yAxisID: "y1", pointRadius: 0, borderWidth: 2 },
    ]
  },
  options: { scales: {
    y: { type: "linear", position: "left", title: { display:true, text:"SIP inflow (Rs Cr)" } },
    y1: { type: "linear", position: "right", title: { display:true, text:"NIFTY 50" }, grid: { drawOnChartArea: false } },
  } }
});

// Heatmap (custom table, since Chart.js has no native heatmap)
(function renderHeatmap() {
  const { categories, months, values } = DATA.cat_heatmap;
  const flat = values.flat();
  const min = Math.min(...flat), max = Math.max(...flat);
  function color(v) {
    const t = (v - min) / (max - min || 1);
    const r = Math.round(255 - t * 215), g = Math.round(255 - t * 75), b = Math.round(200 - t * 150);
    return `rgb(${Math.max(r,40)},${Math.max(g,150)},${Math.max(b,60)})`;
  }
  let html = '<table class="heatmap-table"><thead><tr><th></th>' + months.map(m => `<th>${m}</th>`).join("") + "</tr></thead><tbody>";
  categories.forEach((cat, i) => {
    html += `<tr><th style="text-align:left">${cat}</th>` + values[i].map(v => `<td style="background:${color(v)}">${Math.round(v)}</td>`).join("") + "</tr>";
  });
  html += "</tbody></table>";
  document.getElementById("heatmap-container").innerHTML = html;
})();

new Chart(document.getElementById("chart-top5cat"), {
  type: "bar",
  data: { labels: DATA.top5_cat.labels, datasets: [{ label: "Net inflow (Rs '000 Cr)", data: DATA.top5_cat.values, backgroundColor: PALETTE.teal }] },
  options: { indexAxis: "y", plugins: { legend: { display: false } } }
});
</script>
</body>
</html>
"""

OUT_PATH.write_text(HTML.replace("__DATA_JSON__", DATA_JSON))
print(f"Written {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")
