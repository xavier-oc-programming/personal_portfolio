/* projects-filter.js
 *
 * Live project filtering — no page reloads.
 *
 * Strategy: fetch ALL projects once at page load, cache them in memory,
 * then filter and sort entirely client-side. Every filter click is instant —
 * no network round-trip after the initial prefetch.
 */

(function () {
  'use strict';

  const grid       = document.getElementById('projects-grid');
  const emptyState = document.getElementById('projects-empty');
  const stateEl    = document.getElementById('projects-filter-state');

  if (!grid || !stateEl) return;

  // Initialise filter state from the server-rendered page
  const state = {
    category: stateEl.dataset.activeCategory || '',
    tag:      stateEl.dataset.activeTag      || '',
    sort:     stateEl.dataset.activeSort     || 'az',
  };

  // ---- Row stagger helper -------------------------------------------------

  function colsPerRow() {
    if (window.innerWidth >= 992) return 3;  // col-lg-4
    if (window.innerWidth >= 768) return 2;  // col-md-6
    return 1;                                 // col-12
  }

  function staggerByRow(cols) {
    const arr = Array.from(cols);
    const n = colsPerRow();
    const oneRow = arr.length <= n;
    arr.forEach(function (col, i) {
      const index = oneRow ? i : Math.floor(i / n);
      const delay = oneRow ? index * 65 : index * 100;
      col.classList.add('card-entering');
      col.style.animationDelay = delay + 'ms';
      col.addEventListener('animationend', function () {
        col.classList.remove('card-entering');
        col.style.animationDelay = '';
      }, { once: true });
    });
  }

  // ---- Initial entrance animation -----------------------------------------

  setTimeout(function () { staggerByRow(grid.children); }, 100);

  // ---- Data cache ---------------------------------------------------------

  let cache = null;

  // Start the prefetch immediately — it runs in parallel with page render
  const prefetch = fetch('/api/v1/projects')
    .then(r => r.json())
    .then(json => { if (json.success) cache = json.data; })
    .catch(() => {});

  async function getAll() {
    if (cache) return cache;
    await prefetch;
    return cache || [];
  }

  // ---- Filtering & sorting ------------------------------------------------

  function applyFilters(projects) {
    let result = projects;
    if (state.category) result = result.filter(p => p.category === state.category);
    if (state.tag)      result = result.filter(p => p.tags && p.tags.includes(state.tag));
    return result;
  }

  function applySort(projects) {
    const copy = [...projects];
    if (state.sort === 'az') {
      copy.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
    } else if (state.sort === 'newest') {
      copy.sort((a, b) =>
        (b.date || '').localeCompare(a.date || '') || (a.title || '').localeCompare(b.title || '')
      );
    } else {
      copy.sort((a, b) =>
        (a.date || '').localeCompare(b.date || '') || (a.title || '').localeCompare(b.title || '')
      );
    }
    return copy;
  }

  // ---- HTML helpers -------------------------------------------------------

  function esc(str) {
    return String(str || '')
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;');
  }

  function buildCard(p) {
    const imgSrc = p.card_image
      ? (p.card_image.startsWith('http') ? p.card_image : '/static/' + p.card_image)
      : null;
    const img = imgSrc
      ? `<img src="${esc(imgSrc)}" class="card-img-top project-card-img" alt="${esc(p.title)} cover image" loading="lazy">`
      : '';

    const badge = p.category
      ? `<span class="badge text-bg-dark flex-shrink-0">${esc(p.category.charAt(0).toUpperCase() + p.category.slice(1))}</span>`
      : '';

    const tags = p.tags && p.tags.length
      ? `<div class="d-flex flex-wrap gap-2 mb-4">${p.tags.map(t =>
          `<a class="badge text-bg-secondary" href="/projects?tag=${encodeURIComponent(t)}" data-tag-btn="${esc(t)}">${esc(t)}</a>`
        ).join('')}</div>`
      : '';

    const warningBadge = p.loading_warning
      ? `<span class="badge text-bg-warning" title="This demo may take a minute or two to wake up">⏳ Loading Period</span>`
      : '';

    const githubBtn = p.github_url
      ? `<a class="btn btn-outline-dark btn-sm" href="${esc(p.github_url)}" target="_blank" rel="noopener">GitHub</a>`
      : `<button class="btn btn-outline-dark btn-sm" disabled>GitHub</button>`;

    const liveBtn = p.live_url
      ? `<a class="btn btn-outline-dark btn-sm" href="${esc(p.live_url)}" target="_blank" rel="noopener">Live</a>`
      : '';

    const detailsBtn = p.slug
      ? `<a class="btn btn-dark btn-sm" href="/projects/${esc(p.slug)}">Details</a>`
      : '';

    return `<div class="col-12 col-md-6 col-lg-4 d-flex">
  <div class="card h-100 project-card">
    ${img}
    <div class="card-body d-flex flex-column">
      <div class="d-flex justify-content-between align-items-start gap-2 mb-3">
        <h3 class="h5 mb-0">${esc(p.title) || 'Untitled Project'}</h3>
        ${badge}
      </div>
      <p class="text-secondary mb-3">${esc(p.summary) || ''}</p>
      ${tags}
      <div class="mt-auto d-flex flex-wrap gap-2">${githubBtn}${liveBtn}${detailsBtn}${warningBadge}</div>
    </div>
  </div>
</div>`;
  }

  // ---- Rendering ----------------------------------------------------------

  function renderGrid(projects, delay) {
    delay = delay || 70;
    // Fade out grid
    grid.style.transition = 'opacity 0.07s ease';
    grid.style.opacity    = '0';

    setTimeout(function () {
      // OPTION 2 — hide spinner
      if (loadSpinner) loadSpinner.classList.add('d-none');

      // OPTION 3 — hide skeleton
      if (loadSkeleton) loadSkeleton.classList.add('d-none');

      if (!projects.length) {
        grid.innerHTML = '';
        grid.classList.add('d-none');
        emptyState.classList.remove('d-none');
        grid.style.opacity = '1';
        return;
      }

      emptyState.classList.add('d-none');
      grid.classList.remove('d-none');
      grid.innerHTML = projects.map(buildCard).join('');

      staggerByRow(grid.children);

      grid.style.transition = 'opacity 0.1s ease';
      grid.style.opacity    = '1';
    }, delay);
  }

  // ---- Loading indicators (keep one, delete the other two) ---------------

  const loadBar      = document.getElementById('load-bar');
  const loadSpinner  = document.getElementById('load-spinner');
  const loadSkeleton = document.getElementById('load-skeleton');

  function showLoading() {
    if (loadBar) {
      const fill = loadBar.querySelector('.load-bar-fill');
      fill.style.width = '0%';
      loadBar.classList.remove('d-none');
      setTimeout(function () {
        fill.style.width = '100%';          // one frame later — transition fires cleanly
        setTimeout(function () {
          loadBar.classList.add('d-none');
          fill.style.width = '0%';          // reset for next use
        }, 600);                            // match transition duration
      }, 16);
    }
    // OPTION 2 — Spinner
    if (loadSpinner) loadSpinner.classList.remove('d-none');
    // OPTION 3 — Skeleton
    if (loadSkeleton) {
      grid.style.opacity = '0';
      loadSkeleton.classList.remove('d-none');
    }
  }

  async function update(delay) {
    const all      = await getAll();
    const filtered = applyFilters(all);
    const sorted   = applySort(filtered);
    renderGrid(sorted, delay);
  }

  // ---- URL helpers --------------------------------------------------------

  function buildPageUrl() {
    const params = new URLSearchParams();
    if (state.category)                    params.set('category', state.category);
    if (state.tag)                         params.set('tag',      state.tag);
    if (state.sort && state.sort !== 'az') params.set('sort',     state.sort);
    const qs = params.toString();
    return `/projects${qs ? '?' + qs : ''}`;
  }

  // ---- UI sync ------------------------------------------------------------

  function syncButtons() {
    document.querySelectorAll('[data-category-btn]').forEach(btn => {
      const active = btn.dataset.categoryBtn === state.category;
      btn.classList.toggle('btn-dark',         active);
      btn.classList.toggle('btn-outline-dark', !active);
    });

    document.querySelectorAll('[data-tag-btn]').forEach(btn => {
      const active = btn.dataset.tagBtn === state.tag;
      btn.classList.toggle('btn-dark',         active);
      btn.classList.toggle('btn-outline-dark', !active);
    });

    document.querySelectorAll('[data-sort-btn]').forEach(btn => {
      const active = btn.dataset.sortBtn === state.sort;
      btn.classList.toggle('btn-dark',         active);
      btn.classList.toggle('btn-outline-dark', !active);
    });

    // Sync mobile toggle label (left side)
    const toggleLabel = document.getElementById('filters-toggle-label');
    if (toggleLabel) {
      let label = state.category
        ? state.category.charAt(0).toUpperCase() + state.category.slice(1)
        : 'All';
      if (state.tag) label += ' \u00b7 ' + state.tag;
      toggleLabel.textContent = label;
    }

    // Sync mobile toggle sort label (right side)
    const sortLabel = document.getElementById('filters-sort-label');
    if (sortLabel) {
      const labels = { az: 'A\u2013Z', newest: 'Newest', oldest: 'Oldest' };
      sortLabel.textContent = labels[state.sort] || 'A\u2013Z';
    }

  }

  // ---- Events -------------------------------------------------------------

  document.addEventListener('click', function (e) {
    const catBtn = e.target.closest('[data-category-btn]');
    if (catBtn) {
      e.preventDefault();
      state.category = catBtn.dataset.categoryBtn;
      state.tag = '';
      history.pushState({ ...state }, '', buildPageUrl());
      syncButtons();
      update();
      return;
    }

    const tagBtn = e.target.closest('[data-tag-btn]');
    if (tagBtn) {
      e.preventDefault();
      const clicked = tagBtn.dataset.tagBtn;
      state.tag = (clicked === state.tag) ? '' : clicked;
      history.pushState({ ...state }, '', buildPageUrl());
      syncButtons();
      update();
      return;
    }

    const sortBtn = e.target.closest('[data-sort-btn]');
    if (sortBtn) {
      e.preventDefault();
      state.sort = sortBtn.dataset.sortBtn;
      history.pushState({ ...state }, '', buildPageUrl());
      syncButtons();
      showLoading();
      update(400);
      if (window.innerWidth < 768) {
        var panel = document.getElementById('filters-panel');
        if (panel) bootstrap.Collapse.getOrCreateInstance(panel).hide();
      }
    }
  });

  window.addEventListener('popstate', function (e) {
    if (e.state) {
      state.category = e.state.category || '';
      state.tag      = e.state.tag      || '';
      state.sort     = e.state.sort     || 'az';
      syncButtons();
      update();
    }
  });

  window.__syncFilterButtons = syncButtons;

}());
