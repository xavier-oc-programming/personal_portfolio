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
