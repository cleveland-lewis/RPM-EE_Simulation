// --- Sound Setup ---
const sounds = {
  click: new Audio("mp3_files/mouse-click-117076.mp3"),
  complete: new Audio("mp3_files/system-notification-199277.mp3"),
  error: new Audio("mp3_files/short-beep-tone-47916.mp3"),
  processing: new Audio("mp3_files/computer-processing-sound-effect-01-122131.mp3"),
  boot: new Audio("mp3_files/8bit-computer-startup-66972.mp3")
};

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

// --- CSV Helpers ---
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


// --- Stats helpers ---
function mean(arr) { return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0; }
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

// --- Graph and analysis ---
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

function renderAnalysis(rawLogs) {
  const attunement = rawLogs.map(d => +d.attunement_score || 0);
  const stress = rawLogs.map(d => +d.schema_stress || 0);
  const affect = rawLogs.map(d => +d.avg_affect_feedback || 0);

  document.getElementById("analysisContent").innerHTML = `
    <b>Attunement Score</b><br>${formatStats(attunement)}<br><br>
    <b>Schema Stress</b><br>${formatStats(stress)}<br><br>
    <b>Affect Feedback</b><br>${formatStats(affect)}<br>
  `;
}

// --- Main App ---
document.addEventListener("DOMContentLoaded", () => {
  const runBtn = document.getElementById("runBtn");
  const saveBtn = document.getElementById("saveBtn");
  const downloadBtn = document.getElementById("downloadCSV");
  const statusBox = document.getElementById("status");
  const outputBox = document.getElementById("output");
  const episodesInput = document.getElementById("episodes");
  const repetitionsInput = document.getElementById("repetitions");
  const graphIslands = document.querySelectorAll(".graph-island");
  let lastRawLogs = [];
  let lastFlatLogs = [];

  // --- Initialize button states on load ---
  saveBtn.disabled = true;
  downloadBtn.disabled = true;

  // Graph expansion click
  graphIslands.forEach(island => {
    island.addEventListener("click", () => {
      island.classList.toggle("focused");
    });
  });

  runBtn.addEventListener("click", async () => {
    sounds.click.currentTime = 0; sounds.click.play();
    sounds.processing.currentTime = 0; sounds.processing.loop = true; sounds.processing.volume = 0.3; sounds.processing.play();

    const episodes = parseInt(episodesInput.value, 10) || 500;
    const repetitions = parseInt(repetitionsInput.value, 10) || 1;

    statusBox.textContent = "[ running simulation... ]";
    outputBox.textContent = "";
    logDebug(`Simulation started: episodes=${episodes}, repetitions=${repetitions}`);

    // Disable Save and Download until the run completes
    saveBtn.disabled = true;
    downloadBtn.disabled = true;

    try {
      const response = await fetch("http://127.0.0.1:8000/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ episodes, repetitions })
      });

      if (!response.ok) throw new Error("Network response not OK");

      const result = await response.json();
      sounds.processing.pause(); sounds.complete.play();
      statusBox.textContent = "[ simulation complete ]";
      outputBox.textContent = JSON.stringify(result, null, 2);

      let allLogs = [];
      if (Array.isArray(result.data)) {
        for (const rep of result.data) if (Array.isArray(rep)) allLogs.push(...rep);
      }
      lastRawLogs = allLogs;
      lastFlatLogs = allLogs.map(flattenForCSV);

      // Enable Save and Download if there is data
      saveBtn.disabled = !lastRawLogs.length;
      downloadBtn.disabled = !lastFlatLogs.length;

      const attunement = allLogs.map(d => +d.attunement_score || 0);
      const stress = allLogs.map(d => +d.schema_stress || 0);
      const affect = allLogs.map(d => +d.avg_affect_feedback || 0);

      animateGraph("attunementGraph", attunement, "Attunement Score");
      animateGraph("stressGraph", stress, "Schema Stress");
      animateGraph("affectGraph", affect, "Affect Feedback");
      logDebug("Graphs rendered.");

      renderAnalysis(allLogs);
      renderSpreadsheet(allLogs);

      // Update summary box
      if (allLogs.length) {
        const avgAtt = mean(attunement).toFixed(4);
        const avgStr = mean(stress).toFixed(4);
        document.getElementById("summaryBox").innerHTML =
          `<b>Avg Attunement:</b> <span style="color:#4682b4">${avgAtt}</span>
          &nbsp; &nbsp;
          <b>Avg Stress:</b> <span style="color:#a94442">${avgStr}</span>
          <span style="font-size:0.9em;color:#666;margin-left:2em;">(N=${allLogs.length})</span>`;
      } else {
        document.getElementById("summaryBox").textContent = "Averages will appear here after simulation.";
      }
    } catch (err) {
      sounds.processing.pause(); sounds.error.play();
      statusBox.textContent = "[ error occurred ]";
      outputBox.textContent = err.toString();
      logDebug("[JS ERROR] " + err.toString());
      renderSpreadsheet([]);
      document.getElementById("summaryBox").textContent = "Averages will appear here after simulation.";

      // Always disable Save and Download on error
      saveBtn.disabled = true;
      downloadBtn.disabled = true;
    }
  });

  document.getElementById('saveBtn').onclick = async function() {
  if (!lastRawLogs.length) return;
  try {
    const response = await fetch("http://127.0.0.1:8000/save-logs", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({logs: lastRawLogs})
    });
    const result = await response.json();
    document.getElementById('status').textContent =
      result.status === "success"
        ? "[ logs saved server-side ]"
        : `[ error: ${result.msg} ]`;
  } catch (e) {
    document.getElementById('status').textContent = "[ error saving results ]";
  }
};

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

  logDebug("Page loaded.");
  logDebug("Current URL: " + window.location.href);
  // sounds.boot.play(); // Uncomment if you want a startup sound
});