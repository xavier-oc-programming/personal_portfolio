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
 * Initialize the screenshots gallery modal with prev/next navigation,
 * counter, and arrow key support.
 */
function initDetailImageModal() {
  const modal = document.getElementById("imagePreviewModal");
  const modalImg = document.getElementById("imagePreviewModalImg");
  const counterEl = document.getElementById("galleryCounter");
  const navEl = document.getElementById("galleryNav");
  const prevBtn = document.getElementById("galleryPrev");
  const nextBtn = document.getElementById("galleryNext");

  if (!modal || !modalImg) {
    return;
  }

  const triggers = Array.from(
    document.querySelectorAll(".detail-media-trigger[data-gallery-index]")
  );
  let currentIndex = 0;

  function showImage(index) {
    if (!triggers.length) return;
    currentIndex = ((index % triggers.length) + triggers.length) % triggers.length;
    const trigger = triggers[currentIndex];
    modalImg.src = trigger.getAttribute("data-image-src") || "";
    modalImg.alt = trigger.getAttribute("data-image-alt") || "Screenshot";
    if (counterEl) {
      counterEl.textContent = triggers.length > 1
        ? (currentIndex + 1) + " / " + triggers.length
        : "";
    }
  }

  modal.addEventListener("show.bs.modal", function (event) {
    const trigger = event.relatedTarget;
    if (!trigger) return;
    const idx = parseInt(trigger.getAttribute("data-gallery-index") || "0", 10);
    showImage(isNaN(idx) ? 0 : idx);
    if (navEl) navEl.style.display = triggers.length <= 1 ? "none" : "";
  });

  if (prevBtn) {
    prevBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      showImage(currentIndex - 1);
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      showImage(currentIndex + 1);
    });
  }

  modal.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      showImage(currentIndex - 1);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      showImage(currentIndex + 1);
    }
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

    const fill = bar.querySelector(".load-bar-fill");
    fill.style.width = "0%";
    bar.classList.remove("d-none");
    setTimeout(function () {
      fill.style.width = "100%";
      setTimeout(function () {
        bar.classList.add("d-none");
        fill.style.width = "0%";
      }, 600);
    }, 16);
  });
}
