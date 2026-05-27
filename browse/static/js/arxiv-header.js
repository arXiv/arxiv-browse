/* arxiv-header.js
 *
 * Two responsibilities:
 *  (a) Open/close the header search overlay.
 *  (b) Populate the inline member-institution acknowledgement from the
 *      IP-keyed /institutional_banner endpoint.
 *
 * Replaces the prior arxiv-base member_acknowledgement.js, which targeted
 * the legacy #support-ack-url element with text that no longer matches the
 * spinout-era footer copy.
 */

(function () {
  "use strict";

  /* ----- Search overlay ----- */
  const toggle = document.getElementById("arxiv-search-toggle");
  const overlay = document.getElementById("arxiv-search-overlay");
  const input = document.getElementById("arxiv-search-input");

  function openOverlay() {
    if (!overlay) return;
    overlay.removeAttribute("hidden");
    overlay.classList.add("is-open");
    if (toggle) toggle.setAttribute("aria-expanded", "true");
    if (input) setTimeout(function () { input.focus(); }, 50);
  }

  function closeOverlay() {
    if (!overlay) return;
    overlay.classList.remove("is-open");
    overlay.setAttribute("hidden", "");
    if (toggle) {
      toggle.setAttribute("aria-expanded", "false");
      toggle.focus();
    }
  }

  if (toggle && overlay) {
    toggle.addEventListener("click", openOverlay);
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeOverlay();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && overlay.classList.contains("is-open")) {
        closeOverlay();
      } else if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        openOverlay();
      }
    });
  }

  /* ----- Institutional ack ----- */
  const MEMBER_TTL_MS = 30 * 24 * 60 * 60 * 1000;
  const FAIL_TTL_MS = 60 * 60 * 1000;

  async function fetchInstitutionLabel() {
    let label = localStorage.getItem("member_label");
    const expiresStr = localStorage.getItem("member_expires");
    const now = new Date();
    let expired = true;
    if (expiresStr) {
      const expires = new Date(expiresStr);
      if (!isNaN(expires.getTime()) && now < expires) expired = false;
    }

    if (!expired) return label;

    localStorage.removeItem("member_label");
    localStorage.removeItem("member_expires");

    let ttl = MEMBER_TTL_MS;
    try {
      const result = await fetch("/institutional_banner");
      if (result && result.ok) {
        const j = await result.json();
        if (j && j.label) {
          label = j.label;
          localStorage.setItem("member_label", label);
        } else {
          label = null;
        }
      } else {
        ttl = FAIL_TTL_MS;
        label = null;
      }
    } catch (e) {
      ttl = FAIL_TTL_MS;
      label = null;
    }

    const newExpires = new Date(now.getTime() + ttl);
    localStorage.setItem("member_expires", newExpires.toISOString());
    return label;
  }

  function renderMemberLabel(label) {
    if (!label) return;
    const wrap = document.getElementById("arxiv-ack-member");
    if (!wrap) return;
    const strong = wrap.querySelector("strong");
    if (strong) strong.textContent = label;
    wrap.hidden = false;
  }

  fetchInstitutionLabel().then(renderMemberLabel);
})();
