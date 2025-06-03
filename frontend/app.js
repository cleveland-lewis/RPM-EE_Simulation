


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
