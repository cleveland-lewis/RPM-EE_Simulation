


/*--------HAMBURGER DROPDOWN SLECTION-----------*/
/*----------------------------------------------*/
function toggleMenu() {
  const menu = document.getElementById('menuDropdown');
  menu.classList.toggle('show');
  if (menu.classList.contains('show')) {
    setTimeout(() => {
      document.addEventListener('mousedown', closeMenuListener);
    }, 0);
  } else {
    document.removeEventListener('mousedown', closeMenuListener);
  }
}
function closeMenuListener(e) {
  const menu = document.getElementById('menuDropdown');
  const burger = document.querySelector('.hamburger');
  if (!menu.contains(e.target) && !burger.contains(e.target)) {
    menu.classList.remove('show');
    document.removeEventListener('mousedown', closeMenuListener);
  }
}
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.menu-dropdown a').forEach(link => {
    link.addEventListener('click', () => {
      document.getElementById('menuDropdown').classList.remove('show');
      document.removeEventListener('mousedown', closeMenuListener);
    });
  });
  // Auto-detect current page for label
  const PAGE_TITLES = {
    'dashboard.html': 'Dashboard',
    'contact.html': 'Contact',
    'about.html': 'About',
    'trials.html': 'Trials',
    'batch.html': 'Batch',
    'previous_trials.html': 'Previous Trials',
    'reports.html': 'Reports'
  };
  const path = window.location.pathname;
  const page = path.substring(path.lastIndexOf('/') + 1);
  const title = PAGE_TITLES[page] || document.title || page;
  const label = document.getElementById('current-page-name');
  if (label) label.textContent = title;
});
/*----------------------------------------------*/
/*----------------------------------------------*/


// --- Datashader Integration ---
// Call generateDatashaderPlots(logs) with the simulation log array after each simulation run.
async function generateDatashaderPlots(logs) {
  try {
    const resp = await fetch("http://127.0.0.1:8000/datashader-plots", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ logs: logs })
    });
    if (!resp.ok) throw new Error("Failed to generate plots");
    const result = await resp.json();
    if (result.status !== "success" || !result.plots || !Array.isArray(result.plots)) throw new Error("Invalid response from plot API");
    // Render PNGs as images
    const plotsContainer = document.getElementById("plots-container");
    let html = "";
    for (const url of result.plots) {
      html += `<div style="margin-bottom:1.2rem;"><img src="http://127.0.0.1:8000/${url}" alt="Plot" style="max-width: 90vw; border:2.5px solid #111; border-radius:8px; display:block; margin:0 auto;"/></div>`;
    }
    if (plotsContainer) plotsContainer.innerHTML = html;
  } catch (err) {
    const plotsContainer = document.getElementById("plots-container");
    if (plotsContainer) plotsContainer.innerHTML = `<div style="color:#c00; font-weight:700;">Plot generation failed.</div>`;
  }
}
// Example usage: call generateDatashaderPlots(latestLogs) after simulation run, where latestLogs is your logs array.