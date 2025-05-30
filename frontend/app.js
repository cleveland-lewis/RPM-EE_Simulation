// --- Sound Setup ---
const sounds = {
  click: new Audio("mp3_files/mouse-click-117076.mp3"),
  complete: new Audio("mp3_files/system-notification-199277.mp3"),
  error: new Audio("mp3_files/short-beep-tone-47916.mp3"),
  processing: new Audio("mp3_files/computer-processing-sound-effect-01-122131.mp3"),
  boot: new Audio("mp3_files/8bit-computer-startup-66972.mp3")
};

document.addEventListener("DOMContentLoaded", () => {
  // --- Logging ---
  function logDebug(msg) {
    const now = new Date();
    const timestamp = now.toISOString().slice(11, 19);
    const panel = document.getElementById('debug-panel');
    if (panel) {
      panel.textContent += `[${timestamp}] ${msg}\n`;
      panel.scrollTop = panel.scrollHeight;
    }
    console.log(`[${timestamp}] ${msg}`);
  }

  // --- CSV Flattening ---
  function flattenForCSV(obj) {
    const flat = {};
    for (const k in obj) {
      const v = obj[k];
      if (k === "memory_config" && v && typeof v === "object") {
        flat["memory_config_low_salience_threshold"] = typeof v.low_salience_threshold === "number" ? v.low_salience_threshold : "";
        flat["memory_config_prune_min_salience"] = typeof v.prune_min_salience === "number" ? v.prune_min_salience : "";
        if (v.half_life_ranges && typeof v.half_life_ranges === "object") {
          flat["memory_config_half_life_low_start"] = Array.isArray(v.half_life_ranges.low) ? v.half_life_ranges.low[0] || "" : "";
          flat["memory_config_half_life_low_end"] = Array.isArray(v.half_life_ranges.low) ? v.half_life_ranges.low[1] || "" : "";
          flat["memory_config_half_life_high_start"] = Array.isArray(v.half_life_ranges.high) ? v.half_life_ranges.high[0] || "" : "";
          flat["memory_config_half_life_high_end"] = Array.isArray(v.half_life_ranges.high) ? v.half_life_ranges.high[1] || "" : "";
        } else {
          flat["memory_config_half_life_low_start"] = "";
          flat["memory_config_half_life_low_end"] = "";
          flat["memory_config_half_life_high_start"] = "";
          flat["memory_config_half_life_high_end"] = "";
        }
      } else if (k === "memory_stats" && v && typeof v === "object") {
        flat["memory_stats_short_term_count"] = typeof v.short_term_count === "number" ? v.short_term_count : "";
        flat["memory_stats_long_term_count"] = typeof v.long_term_count === "number" ? v.long_term_count : "";
      } else if (typeof v === "number") {
        flat[k] = v;
      } else if (typeof v === "string" && v.trim() !== "" && !isNaN(v)) {
        flat[k] = Number(v);
      } else {
        flat[k] = "";
      }
    }
    return flat;
  }

  function gatherAllKeys(arr) {
    const keys = new Set();
    arr.forEach(row => Object.keys(row).forEach(k => keys.add(k)));
    return Array.from(keys);
  }

  function arrayToCSV(arr) {
    if (!arr.length) return "";
    const allKeys = gatherAllKeys(arr);
    const rows = [allKeys.join(",")];
    arr.forEach(row => {
      const flat = flattenForCSV(row);
      rows.push(allKeys.map(k => (flat[k] === undefined ? "" : flat[k])).join(","));
    });
    return rows.join("\r\n");
  }

  // --- Render spreadsheet ---
  function renderSpreadsheet(arr) {
    const container = document.getElementById("spreadsheet");
    if (!arr.length) {
      container.innerHTML = "<div style='color:#888;'>[no data]</div>";
      return;
    }
    const header = Object.keys(arr[0]);
    let html = "<table id='spreadsheet-table'><thead><tr>";
    for (const h of header) html += `<th>${h}</th>`;
    html += "</tr></thead><tbody>";
    for (let i = 0; i < arr.length; ++i) {
      html += "<tr>";
      for (const h of header) {
        let val = arr[i][h];
        if (typeof val === "number") {
          val = Number.isFinite(val) ? val.toFixed(4) : "";
        }
        html += `<td>${val === undefined ? "" : val}</td>`;
      }
      html += "</tr>";
    }
    html += "</tbody></table>";
    container.innerHTML = html;
  }

  // --- Stats helpers ---
  function mean(arr) {
    return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
  }
  function median(arr) {
    if (!arr.length) return 0;
    const sorted = arr.slice().sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }
  function stdDev(arr) {
    if (!arr.length) return 0;
    const m = mean(arr);
    return Math.sqrt(arr.reduce((acc, val) => acc + (val - m) ** 2, 0) / arr.length);
  }

  function formatStats(arr) {
    return `
      Count: ${arr.length}<br>
      Mean: ${mean(arr).toFixed(4)}<br>
      Median: ${median(arr).toFixed(4)}<br>
      Std Dev: ${stdDev(arr).toFixed(4)}
    `;
  }

  function renderAnalysis(rawLogs) {
    const attunement = rawLogs.map(d => +d.attunement_score || 0);
    const stress = rawLogs.map(d => +d.schema_stress || 0);
    const affect = rawLogs.map(d => +d.avg_affect_feedback || 0);

    document.getElementById("analysisContent").innerHTML = `
      <b>Attunement Score</b><br>${formatStats(attunement)}<br><br>
      <b>Schema Stress</b><br>${formatStats(stress)}<br><br>
      <b>Affect Feedback</b><br>${formatStats(affect)}<br>
    `;

    Plotly.newPlot('attunementHist', [{
      x: attunement,
      type: 'histogram',
      marker: { color: 'blue' }
    }], { title: 'Attunement Score Distribution' });

    Plotly.newPlot('stressHist', [{
      x: stress,
      type: 'histogram',
      marker: { color: 'red' }
    }], { title: 'Schema Stress Distribution' });

    Plotly.newPlot('affectHist', [{
      x: affect,
      type: 'histogram',
      marker: { color: 'green' }
    }], { title: 'Affect Feedback Distribution' });
  }

  // --- Animate line graph ---
  function animateGraph(id, data, label) {
    if (!Array.isArray(data) || data.length === 0) {
      Plotly.purge(id);
      logDebug(`[WARN] No data for ${label}`);
      Plotly.newPlot(id, [{ x: [0], y: [0], mode: "lines", name: "No data" }], { title: `${label}: No Data` });
      return;
    }
    Plotly.purge(id);
    Plotly.newPlot(id, [{
      x: [...Array(data.length).keys()],
      y: data,
      mode: "lines",
      name: label
    }], { yaxis: { title: label } });
  }

  // --- Setup ---
  const runBtn = document.getElementById("runBtn");
  const downloadBtn = document.getElementById("downloadCSV");
  const statusBox = document.getElementById("status");
  const outputBox = document.getElementById("output");
  const windowEl = document.querySelector(".window");
  const graphIslands = document.querySelectorAll(".graph-island");
  const episodesInput = document.getElementById("episodes");
  const repetitionsInput = document.getElementById("repetitions");
  let lastFlatLogs = [];

  // Enable graph expansion on click
  graphIslands.forEach(island => {
    island.addEventListener("click", () => {
      island.classList.toggle("focused");
    });
  });

  runBtn.addEventListener("click", async () => {
    if (windowEl) {
      windowEl.classList.remove("idle-breathing", "collapsed");
      setTimeout(() => { windowEl.classList.add("expanded"); }, 10);
    }

    sounds.click.currentTime = 0; sounds.click.play();
    sounds.processing.currentTime = 0;
    sounds.processing.loop = true;
    sounds.processing.volume = 0.3;
    sounds.processing.play();

    const episodes = parseInt(episodesInput.value, 10) || 500;
    const repetitions = parseInt(repetitionsInput.value, 10) || 1;

    statusBox.textContent = "[ running simulation... ]";
    outputBox.textContent = "";
    logDebug(`Simulation started: episodes=${episodes}, repetitions=${repetitions}`);

    try {
      const response = await fetch("http://127.0.0.1:8000/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ episodes, repetitions })
      });

      if (!response.ok) throw new Error("Network response not OK");

      const result = await response.json();
      sounds.processing.pause();
      sounds.complete.play();

      statusBox.textContent = "[ simulation complete ]";
      outputBox.textContent = JSON.stringify(result, null, 2);

      // Flatten for CSV/export
      let allLogs = [];
      if (Array.isArray(result.data)) {
        for (const rep of result.data) {
          if (Array.isArray(rep)) allLogs.push(...rep);
        }
      }
      lastFlatLogs = allLogs.map(flattenForCSV);

      downloadBtn.disabled = !lastFlatLogs.length;

      // Graph aggregates
      const attunement = allLogs.map(d => +d.attunement_score || 0);
      const stress = allLogs.map(d => +d.schema_stress || 0);
      const affect = allLogs.map(d => +d.avg_affect_feedback || 0);

      animateGraph("attunementGraph", attunement, "Attunement Score");
      animateGraph("stressGraph", stress, "Schema Stress");
      animateGraph("affectGraph", affect, "Affect Feedback");
      logDebug("Graphs rendered.");

      // Detailed analysis + histograms
      renderAnalysis(allLogs);

      // Spreadsheet & averages
      renderSpreadsheet(allLogs);
      showAverages(allLogs);

    } catch (err) {
      sounds.processing.pause();
      sounds.error.play();
      statusBox.textContent = "[ error occurred ]";
      outputBox.textContent = err.toString();
      logDebug("[JS ERROR] " + err.toString());

      renderSpreadsheet([]);
      showAverages([]);
    }

    setTimeout(() => {
      if (windowEl) {
        windowEl.classList.remove("expanded");
        windowEl.classList.add("collapsed");
      }
    }, 800);
    setTimeout(() => {
      if (windowEl) windowEl.classList.add("idle-breathing");
    }, 2200);
  });

  downloadBtn.addEventListener("click", () => {
    if (!lastFlatLogs.length) return;
    const csv = arrayToCSV(lastFlatLogs);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const now = new Date();
    const dateStr = now.toISOString().slice(0, 10);
    link.download = `data_trial_${dateStr}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    logDebug("CSV exported.");
  });

  // If you need this, uncomment
  // sounds.boot.play();

  logDebug("Page loaded.");
  logDebug("Current URL: " + window.location.href);
});