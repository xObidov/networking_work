/* ===== Global UI behaviour: dark mode, sidebar, AJAX helpers, kanban ===== */

// ---- Dark mode (persisted in localStorage) ----
(function () {
  const stored = localStorage.getItem("crm-theme");
  if (stored) document.documentElement.setAttribute("data-bs-theme", stored);

  document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("themeToggle");
    if (!toggle) return;
    const setIcon = () => {
      const dark = document.documentElement.getAttribute("data-bs-theme") === "dark";
      toggle.innerHTML = dark ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
    };
    setIcon();
    toggle.addEventListener("click", function () {
      const dark = document.documentElement.getAttribute("data-bs-theme") === "dark";
      const next = dark ? "light" : "dark";
      document.documentElement.setAttribute("data-bs-theme", next);
      localStorage.setItem("crm-theme", next);
      setIcon();
    });
  });
})();

// ---- Mobile sidebar toggle ----
document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (btn && sidebar) {
    btn.addEventListener("click", () => sidebar.classList.toggle("show"));
  }
});

// ---- CSRF helper for AJAX (reads the csrftoken cookie) ----
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

// ---- Kanban drag & drop (deals board) ----
document.addEventListener("DOMContentLoaded", function () {
  const board = document.querySelector(".kanban-board");
  if (!board) return;

  let dragged = null;

  board.querySelectorAll(".kanban-card").forEach((card) => {
    card.addEventListener("dragstart", () => {
      dragged = card;
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      dragged = null;
    });
  });

  board.querySelectorAll(".kanban-column").forEach((column) => {
    column.addEventListener("dragover", (e) => {
      e.preventDefault();
      column.classList.add("drag-over");
    });
    column.addEventListener("dragleave", () => column.classList.remove("drag-over"));
    column.addEventListener("drop", (e) => {
      e.preventDefault();
      column.classList.remove("drag-over");
      if (!dragged) return;
      const stage = column.dataset.stage;
      const dealId = dragged.dataset.dealId;
      fetch(`/deals/${dealId}/stage/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ stage: stage }),
      })
        .then((r) => {
          if (!r.ok) throw new Error("Failed to move deal");
          column.querySelector(".kanban-cards").appendChild(dragged);
        })
        .catch(() => alert("Could not update deal stage."));
    });
  });
});

// ---- Mark notification read via AJAX ----
document.addEventListener("click", function (e) {
  const el = e.target.closest("[data-notification-read]");
  if (!el) return;
  fetch(el.dataset.notificationRead, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
  });
});
