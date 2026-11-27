(() => {
  "use strict";

  const LOCAL_LEADS_KEY = "qingyou_sku01_static_leads_v1";
  const PHONE_PATTERN = /^1\d{10}$/;

  function formatLocalIsoDate(offsetDays = 0) {
    const dt = new Date();
    dt.setHours(0, 0, 0, 0);
    dt.setDate(dt.getDate() + offsetDays);
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, "0");
    const d = String(dt.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function applyEmbeddedAssetsFallback() {
    const assetsMap = window.__SKU1_ASSETS__;
    if (!assetsMap || typeof assetsMap !== "object") {
      return;
    }

    const images = document.querySelectorAll("img[data-asset-key]");
    images.forEach((img) => {
      const key = img.getAttribute("data-asset-key");
      const dataUrl = key ? assetsMap[key] : "";
      if (!dataUrl) {
        return;
      }

      const swapToEmbedded = () => {
        if (img.getAttribute("src") !== dataUrl) {
          img.setAttribute("src", dataUrl);
        }
      };

      img.addEventListener("error", swapToEmbedded, { once: true });

      if (img.complete && img.naturalWidth === 0) {
        swapToEmbedded();
      } else if (window.location.protocol === "file:") {
        swapToEmbedded();
      }
    });
  }

  function initDateConstraints() {
    const dateInput = document.getElementById("bookingDate");
    if (!dateInput) {
      return;
    }
    const todayStr = formatLocalIsoDate(0);
    const tomorrowStr = formatLocalIsoDate(1);
    dateInput.setAttribute("min", todayStr);
    if (!dateInput.value) {
      dateInput.value = tomorrowStr;
    }
  }

  function initMiniprogramRulerToggle() {
    const toggleBtn = document.getElementById("miniprogramToggle");
    if (!toggleBtn) {
      return;
    }

    toggleBtn.addEventListener("click", () => {
      const active = document.body.classList.toggle("miniprogram-preview");
      toggleBtn.setAttribute("aria-pressed", active ? "true" : "false");
      toggleBtn.textContent = active ? "退出胶囊安全区标尺" : "微信小程序胶囊标尺";
    });
  }

  function initSmoothScrollLinks() {
    const triggers = document.querySelectorAll("[data-scroll-target]");
    triggers.forEach((el) => {
      el.addEventListener("click", (event) => {
        const selector = el.getAttribute("data-scroll-target");
        if (!selector) {
          return;
        }
        const target = document.querySelector(selector);
        if (!target) {
          return;
        }
        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function initSessionSelection() {
    const sessionSelect = document.getElementById("bookingSession");
    const cards = Array.from(document.querySelectorAll("[data-session-card]"));
    if (!sessionSelect || cards.length === 0) {
      return;
    }

    const syncCards = (selectedName) => {
      cards.forEach((card) => {
        const cardName = card.getAttribute("data-session-card");
        const isSelected = cardName === selectedName;
        card.classList.toggle("is-selected", isSelected);
        card.setAttribute("aria-pressed", isSelected ? "true" : "false");
        const badge = card.querySelector("[data-card-badge]");
        if (badge) {
          badge.textContent = isSelected ? "已选定" : "选择场次";
        }
      });
    };

    cards.forEach((card) => {
      card.addEventListener("click", () => {
        const sessionName = card.getAttribute("data-session-card");
        if (!sessionName) {
          return;
        }
        sessionSelect.value = sessionName;
        syncCards(sessionName);
      });
    });

    sessionSelect.addEventListener("change", () => {
      syncCards(sessionSelect.value);
    });

    syncCards(sessionSelect.value);
  }

  function showStatus(mode, text = "") {
    const panels = {
      empty: document.getElementById("statusEmpty"),
      loading: document.getElementById("statusLoading"),
      success: document.getElementById("statusSuccess"),
      duplicate: document.getElementById("statusDuplicate"),
      error: document.getElementById("statusError"),
    };

    Object.entries(panels).forEach(([key, panel]) => {
      if (!panel) {
        return;
      }
      panel.hidden = key !== mode;
    });

    if (mode === "success") {
      const target = document.getElementById("statusSuccessText");
      if (target) target.textContent = text;
    } else if (mode === "duplicate") {
      const target = document.getElementById("statusDuplicateText");
      if (target) target.textContent = text;
    } else if (mode === "error") {
      const target = document.getElementById("statusErrorText");
      if (target) target.textContent = text;
    }
  }

  function readUtmSource() {
    try {
      const params = new URLSearchParams(window.location.search);
      const raw = (params.get("utm_source") || "").trim();
      return raw || "direct";
    } catch {
      return "direct";
    }
  }

  function runStaticStorageFallback(payload) {
    let records = [];
    try {
      const saved = window.localStorage.getItem(LOCAL_LEADS_KEY);
      const parsed = saved ? JSON.parse(saved) : [];
      if (Array.isArray(parsed)) {
        records = parsed;
      }
    } catch {
      records = [];
    }

    const duplicated = records.some(
      (item) =>
        item &&
        item.phone === payload.phone &&
        item.date === payload.date
    );

    if (duplicated) {
      return {
        status: 409,
        data: {
          ok: false,
          error: "duplicate_booking",
          message: `手机号 ${payload.phone} 在 ${payload.date} 已有预约记录，同一手机号同一天禁止重复预约。`,
        },
      };
    }

    const refId = `QY-${Date.now().toString(36).toUpperCase()}`;
    const newLead = {
      id: refId,
      ...payload,
      created_at: new Date().toISOString(),
    };
    records.push(newLead);
    try {
      window.localStorage.setItem(LOCAL_LEADS_KEY, JSON.stringify(records));
    } catch {
      // Ignore storage quota issues in restricted browsers
    }

    return {
      status: 201,
      data: {
        ok: true,
        id: refId,
        lead: newLead,
        message: "预约已记录（静态预览本地队列）。",
      },
    };
  }

  async function submitLeadPayload(payload) {
    try {
      const response = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const contentType = (response.headers.get("content-type") || "").toLowerCase();
      const isJson = contentType.includes("application/json");

      if ((response.status === 404 || response.status === 405) && !isJson) {
        return runStaticStorageFallback(payload);
      }

      let data = {};
      if (isJson) {
        data = await response.json();
      } else {
        const rawText = await response.text();
        try {
          data = JSON.parse(rawText);
        } catch {
          if (response.status >= 400) {
            return runStaticStorageFallback(payload);
          }
        }
      }

      return { status: response.status, data };
    } catch {
      return runStaticStorageFallback(payload);
    }
  }

  function validatePayload(payload, minDate) {
    if (!payload.name) {
      return "请填写访客姓名。";
    }
    if (!PHONE_PATTERN.test(payload.phone)) {
      return "请输入 11 位有效手机号（以 1 开头）。";
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(payload.date)) {
      return "请选择有效的探店预约日期。";
    }
    if (minDate && payload.date < minDate) {
      return `预约日期不能早于今日（${minDate}）。`;
    }
    if (!payload.session) {
      return "请选择预约场次。";
    }
    return "";
  }

  function initLeadForm() {
    const form = document.getElementById("leadForm");
    const submitBtn = document.getElementById("submitLeadBtn");
    const dateInput = document.getElementById("bookingDate");
    if (!form || !submitBtn) {
      return;
    }

    showStatus("empty");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const payload = {
        name: (document.getElementById("bookingName")?.value || "").trim(),
        phone: (document.getElementById("bookingPhone")?.value || "").trim(),
        date: (dateInput?.value || "").trim(),
        session: (document.getElementById("bookingSession")?.value || "").trim(),
        guests: Number(document.getElementById("bookingGuests")?.value || 1),
        notes: (document.getElementById("bookingNotes")?.value || "").trim(),
        utm_source: readUtmSource(),
      };

      const validationMsg = validatePayload(
        payload,
        dateInput?.getAttribute("min") || ""
      );
      if (validationMsg) {
        showStatus("error", validationMsg);
        return;
      }

      submitBtn.disabled = true;
      showStatus("loading");

      try {
        const { status, data } = await submitLeadPayload(payload);

        if (status === 201) {
          const refId = data.id || data.lead?.id || "QY-CONFIRMED";
          showStatus(
            "success",
            `预约编号 ${refId}：${payload.name}（${payload.phone}）已成功预约 ${payload.date}「${payload.session}」（同行 ${payload.guests} 位）。`
          );
        } else if (status === 409) {
          showStatus(
            "duplicate",
            data.message ||
              `手机号 ${payload.phone} 在 ${payload.date} 已存在预约记录，同一手机号同一天禁止重复预约。`
          );
        } else {
          showStatus(
            "error",
            data.message || data.error || `提交失败（HTTP ${status}），请检查表单字段后重试。`
          );
        }
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    applyEmbeddedAssetsFallback();
    initDateConstraints();
    initMiniprogramRulerToggle();
    initSmoothScrollLinks();
    initSessionSelection();
    initLeadForm();
  });
})();
