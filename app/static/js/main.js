/**
 * main.js
 *
 * Lightweight UI enhancements for the portfolio.
 *
 * Key responsibilities:
 * - Improve mobile navbar behavior on small screens.
 * - Provide a thin interaction layer on top of the server-rendered UI.
 * - Add scroll-to-top functionality.
 * - Add click-to-enlarge behavior for project detail screenshots.
 *
 * Phase 6 Section 3 updates:
 * - Improves scroll listener efficiency using passive events.
 * - Uses class-based visibility toggling instead of repeated inline style updates.
 */

document.addEventListener("DOMContentLoaded", function () {
  handleMobileNavbar();
  initScrollToTop();
  initDetailImageModal();
  initScreenshotThumbnails();
  initScreenshotViewToggle();
  initNavLoadBar();
});

/**
 * Close the mobile navbar after a navigation link is clicked.
 */
function handleMobileNavbar() {
  const navbarCollapse = document.getElementById("mainNavbar");

  if (!navbarCollapse) {
    return;
  }

  const navLinks = navbarCollapse.querySelectorAll(".nav-link");

  navLinks.forEach((link) => {
    link.addEventListener("click", function () {
      if (navbarCollapse.classList.contains("show")) {
        const collapseInstance = bootstrap.Collapse.getInstance(navbarCollapse);

        if (collapseInstance) {
          collapseInstance.hide();
        }
      }
    });
  });
}

/**
 * Initialize scroll-to-top button behavior.
 */
function initScrollToTop() {
  const btn = document.getElementById("scrollToTopBtn");

  if (!btn) {
    return;
  }

  function toggleButtonVisibility() {
    btn.classList.toggle("is-visible", window.scrollY > 300);
  }

  window.addEventListener("scroll", toggleButtonVisibility, { passive: true });
  toggleButtonVisibility();

  btn.addEventListener("click", function () {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });
}

/**
 * Initialize the screenshots gallery modal with prev/next navigation,
 * counter, and arrow key support.
 */
function initDetailImageModal() {
  const modal = document.getElementById("imagePreviewModal");
  const carouselEl = document.getElementById("modalCarousel");
  const counterEl = document.getElementById("galleryCounter");

  if (!modal || !carouselEl) return;

  const total = carouselEl.querySelectorAll(".carousel-item").length;
  const thumbs = document.querySelectorAll(".screenshot-thumb");

  function updateCounter(index) {
    if (counterEl) {
      counterEl.textContent = total > 1 ? (index + 1) + " / " + total : "";
    }
  }

  function syncThumbs(index) {
    thumbs.forEach(function (t, i) {
      t.classList.toggle("screenshot-thumb--active", i === index);
    });
  }

  // Jump to correct slide when modal opens, then init counter
  modal.addEventListener("show.bs.modal", function (event) {
    const trigger = event.relatedTarget;
    const idx = parseInt((trigger && trigger.getAttribute("data-gallery-index")) || "0", 10);
    const carousel = bootstrap.Carousel.getOrCreateInstance(carouselEl, { ride: false });
    carousel.to(isNaN(idx) ? 0 : idx);
    updateCounter(isNaN(idx) ? 0 : idx);
    syncThumbs(isNaN(idx) ? 0 : idx);
  });

  // Keep counter + thumbnails in sync as user navigates
  carouselEl.addEventListener("slid.bs.carousel", function (e) {
    updateCounter(e.to);
    syncThumbs(e.to);
  });

  // Arrow key navigation — modal captures focus so we handle it here
  modal.addEventListener("keydown", function (e) {
    if (!modal.classList.contains("show")) return;
    const carousel = bootstrap.Carousel.getInstance(carouselEl);
    if (!carousel) return;
    if (e.key === "ArrowLeft") { e.preventDefault(); carousel.prev(); }
    if (e.key === "ArrowRight") { e.preventDefault(); carousel.next(); }
  });
}

/**
 * Keep the 1/x counter in sync with the Bootstrap carousel.
 */
/**
 * Screenshot hero + thumbnail switcher.
 * Clicking a thumbnail swaps the hero image and updates the modal trigger's
 * data attributes so the lightbox opens at the correct image.
 */
function initScreenshotThumbnails() {
  const hero = document.getElementById("screenshotHero");
  const heroImg = document.getElementById("screenshotHeroImg");
  const thumbs = document.querySelectorAll(".screenshot-thumb");

  if (!hero || !heroImg || !thumbs.length) return;

  thumbs.forEach(function (thumb) {
    thumb.addEventListener("click", function () {
      const src = this.dataset.src;
      const alt = this.dataset.alt;
      const index = this.dataset.index;

      heroImg.src = src;
      heroImg.alt = alt;

      hero.setAttribute("data-image-src", src);
      hero.setAttribute("data-image-alt", alt);
      hero.setAttribute("data-gallery-index", index);

      thumbs.forEach(function (t) { t.classList.remove("screenshot-thumb--active"); });
      this.classList.add("screenshot-thumb--active");
    });
  });
}

/**
 * Toggle between grid and hero+thumbnail screenshot layouts.
 * Preference is persisted to localStorage so it survives page reloads.
 */
function initScreenshotViewToggle() {
  const toggle = document.getElementById("screenshotViewToggle");
  const gridView = document.getElementById("screenshotsGridView");
  const heroView = document.getElementById("screenshotsHeroView");

  if (!toggle || !gridView || !heroView) return;

  const STORAGE_KEY = "screenshotView";
  const buttons = toggle.querySelectorAll("[data-view]");

  function applyView(view) {
    const isGrid = view === "grid";
    gridView.classList.toggle("d-none", !isGrid);
    heroView.classList.toggle("d-none", isGrid);
    buttons.forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.view === view);
    });
    try { localStorage.setItem(STORAGE_KEY, view); } catch (e) {}
  }

  buttons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      applyView(this.dataset.view);
    });
  });

  var saved = "hero";
  try { saved = localStorage.getItem(STORAGE_KEY) || "hero"; } catch (e) {}
  applyView(saved);
}

/**
 * Show a progress bar at the top of the page on every internal link navigation.
 */
function initNavLoadBar() {
  const bar = document.getElementById("nav-load-bar");

  if (!bar) return;

  document.addEventListener("click", function (e) {
    const link = e.target.closest("a[href]");
    if (!link) return;

    const href = link.getAttribute("href");

    // Skip external links, anchors, and javascript: links
    if (
      !href ||
      href.startsWith("#") ||
      href.startsWith("http") ||
      href.startsWith("mailto") ||
      href.startsWith("javascript") ||
      link.target === "_blank"
    ) return;

    // Skip links that JS handles without a page load (filter/sort buttons)
    if (
      link.hasAttribute("data-category-btn") ||
      link.hasAttribute("data-tag-btn") ||
      link.hasAttribute("data-sort-btn")
    ) return;

    // Prevent navigation — let the bar complete first, then navigate
    e.preventDefault();

    const fill = bar.querySelector(".load-bar-fill");
    fill.style.width = "0%";
    bar.classList.remove("d-none");
    setTimeout(function () {
      fill.style.width = "100%";
      setTimeout(function () {
        window.location.href = href;
      }, 600);
    }, 16);
  });
}
