const fs = require("fs");
const { JSDOM } = require("jsdom");

const html = fs.readFileSync("dashboard/bluestock_dashboard.html", "utf8");

const dom = new JSDOM(html, { runScripts: "outside-only" });
const { window } = dom;

// Stub Chart.js - we only want to test the surrounding data-wrangling JS,
// not actual canvas rendering (jsdom has no canvas backend).
let chartInstancesCreated = 0;
window.Chart = class {
  constructor(ctx, config) {
    chartInstancesCreated++;
    this.config = config;
    if (!ctx) throw new Error("Chart constructed with null ctx (missing canvas element)");
  }
  destroy() {}
};
window.Chart.defaults = { font: {}, plugins: { legend: { labels: {} } } };

const scriptText = dom.window.document.querySelector("script:not([src])").textContent;

try {
  window.eval(scriptText);
  console.log(`OK: script executed without throwing. Chart instances created: ${chartInstancesCreated}`);
} catch (err) {
  console.error("RUNTIME ERROR:", err.message);
  console.error(err.stack);
  process.exit(1);
}

// Simulate user interactions: switch tabs, change filters, change state
function click(id) { window.document.getElementById(id).dispatchEvent(new window.Event("click", { bubbles: true })); }
function change(id, value) {
  const el = window.document.getElementById(id);
  el.value = value;
  el.dispatchEvent(new window.Event("change", { bubbles: true }));
}

try {
  // Page 2 filters
  const catSelect = window.document.getElementById("filter-category");
  change("filter-category", catSelect.options[1].value);
  change("filter-category", "");

  // Fund selector
  const fundSel = window.document.getElementById("fund-selector");
  change("fund-selector", fundSel.options[1].value);

  // Page 3 state filter - the one I just wired up
  change("filter-state", "Punjab");
  change("filter-state", "ALL");

  // Table sort
  window.document.querySelector('#scorecard-table th[data-key="sharpe_ratio"]').dispatchEvent(
    new window.Event("click", { bubbles: true })
  );

  console.log("OK: all simulated interactions (filters, fund selector, state filter, table sort) ran without throwing.");
} catch (err) {
  console.error("INTERACTION ERROR:", err.message);
  console.error(err.stack);
  process.exit(1);
}
