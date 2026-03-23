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
 * Initialize the Bootstrap modal used to enlarge project detail images.
 */
function initDetailImageModal() {
  const modal = document.getElementById("imagePreviewModal");
  const modalImg = document.getElementById("imagePreviewModalImg");

  if (!modal || !modalImg) {
    return;
  }

  modal.addEventListener("show.bs.modal", function (event) {
    const trigger = event.relatedTarget;

    if (!trigger) {
      return;
    }

    const imageSrc = trigger.getAttribute("data-image-src");
    const imageAlt =
      trigger.getAttribute("data-image-alt") || "Expanded image preview";

    modalImg.src = imageSrc || "";
    modalImg.alt = imageAlt;
  });

  modal.addEventListener("hidden.bs.modal", function () {
    modalImg.src = "";
    modalImg.alt = "";
  });
}

/**
 * Show a progress bar at the top of the page on every internal link navigation.
 */
function initNavLoadBar() {
  const bar = document.getElementById("nav-load-bar");

  if (!bar) return;

  const fill = bar.querySelector(".load-bar-fill");

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
    if (link.hasAttribute("data-category-btn") || link.hasAttribute("data-tag-btn")) return;

    bar.classList.remove("d-none");
    fill.style.animation = "none";
    void fill.offsetWidth;
    fill.style.animation = "";
  });
}
