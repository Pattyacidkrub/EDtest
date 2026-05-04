(function () {
  const root = document.documentElement;
  const storageKey = "chapter-baseline-theme";
  const sidebarStorageKey = "chapter-baseline-sidebar-collapsed";
  const themeButton = document.querySelector("[data-theme-toggle]");
  const sidebarButton = document.querySelector("[data-sidebar-toggle]");
  const app = document.querySelector(".app");
  const links = Array.from(document.querySelectorAll(".sidebar__link"));
  const sections = Array.from(document.querySelectorAll("[data-observe-section]"));
  const scoreFill = document.querySelector("[data-score-fill]");
  const scoreText = document.querySelector("[data-score-text]");
  const mobileSidebarQuery = window.matchMedia("(max-width: 960px)");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    if (themeButton) {
      themeButton.textContent = theme === "dark" ? "Light" : "Dark";
    }
  }

  function initTheme() {
    const saved = localStorage.getItem(storageKey);
    applyTheme(saved || "light");
  }

  function toggleTheme() {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    localStorage.setItem(storageKey, next);
    applyTheme(next);
  }

  function applySidebarState(collapsed) {
    if (!app || !sidebarButton) {
      return;
    }
    app.classList.toggle("is-sidebar-collapsed", collapsed);
    sidebarButton.textContent = collapsed ? "เปิดสารบัญ" : "ซ่อนสารบัญ";
    sidebarButton.setAttribute("aria-expanded", String(!collapsed));
  }

  function initSidebar() {
    const saved = localStorage.getItem(sidebarStorageKey);
    const collapsed = saved === null ? mobileSidebarQuery.matches : saved === "true";
    applySidebarState(collapsed);
  }

  function toggleSidebar() {
    if (!app) {
      return;
    }
    const collapsed = !app.classList.contains("is-sidebar-collapsed");
    localStorage.setItem(sidebarStorageKey, String(collapsed));
    applySidebarState(collapsed);
  }

  function updateScore() {
    const allQuestions = Array.from(document.querySelectorAll(".mcq"));
    const reviewOnlyTotal = allQuestions.filter((node) => node.dataset.reviewOnly === "true").length;
    const questions = allQuestions.filter((node) => node.dataset.reviewOnly !== "true");
    const answered = questions.filter((node) => node.dataset.answered === "true").length;
    const total = questions.length;
    const correct = questions.filter((node) => node.dataset.correct === "true").length;
    const width = total === 0 ? 0 : Math.round((answered / total) * 100);

    if (scoreFill) {
      scoreFill.style.width = width + "%";
    }
    if (scoreText) {
      scoreText.textContent = total === 0
        ? "ยังไม่มีข้อแบบฝึกหัดในบทนี้"
        : `ถูก ${correct} / ทำแล้ว ${answered} / นับคะแนน ${total} ข้อ${reviewOnlyTotal ? ` + ${reviewOnlyTotal} ต้องทบทวน source` : ""}`;
    }
  }

  function updateLessonToggle(mcq) {
    const explanation = mcq.querySelector(".mcq__explanation");
    const toggle = mcq.querySelector("[data-lesson-toggle]");
    if (!explanation || !toggle) {
      return;
    }
    const isOpen = !explanation.hidden;
    toggle.textContent = isOpen ? "ซ่อนบทเรียน/เฉลย" : "เปิดบทเรียน/เฉลย";
    toggle.setAttribute("aria-expanded", String(isOpen));
  }

  function preserveQuestionPosition(mcq, updateFn) {
    if (!mcq || typeof updateFn !== "function") {
      return;
    }
    updateFn();
    window.requestAnimationFrame(() => {
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
      }
      scrollToTarget(mcq, "auto");
      window.requestAnimationFrame(() => scrollToTarget(mcq, "auto"));
      window.setTimeout(() => scrollToTarget(mcq, "auto"), 80);
    });
  }

  function getScrollOffset() {
    const utilityBar = document.querySelector(".utility-bar");
    return utilityBar ? utilityBar.getBoundingClientRect().height + 16 : 18;
  }

  function scrollToTarget(target, behavior) {
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const top = window.scrollY + target.getBoundingClientRect().top - getScrollOffset();
    const previousScrollBehavior = root.style.scrollBehavior;
    if ((behavior || "auto") === "auto") {
      root.style.scrollBehavior = "auto";
    }
    window.scrollTo({ top: Math.max(top, 0), left: 0, behavior: behavior || "auto" });
    if ((behavior || "auto") === "auto") {
      window.requestAnimationFrame(() => {
        root.style.scrollBehavior = previousScrollBehavior;
      });
    }
  }

  function initSidebarLinks() {
    links.forEach((link) => {
      link.addEventListener("click", (event) => {
        const href = link.getAttribute("href");
        if (!href || !href.startsWith("#") || href.length < 2) {
          return;
        }
        const target = document.getElementById(decodeURIComponent(href.slice(1)));
        if (!target) {
          return;
        }
        event.preventDefault();
        history.pushState(null, "", href);
        scrollToTarget(target, "auto");
        window.requestAnimationFrame(() => scrollToTarget(target, "auto"));
        window.setTimeout(() => scrollToTarget(target, "auto"), 80);
      });
    });
  }

  function setLessonOpen(mcq, shouldOpen) {
    const explanation = mcq.querySelector(".mcq__explanation");
    const rationales = mcq.querySelector(".mcq__rationales");
    const reference = mcq.querySelector(".mcq__reference");
    const isAnswered = mcq.dataset.answered === "true";

    if (explanation) {
      explanation.hidden = !shouldOpen;
    }
    if (rationales && isAnswered) {
      rationales.hidden = !shouldOpen;
    }
    if (reference && isAnswered) {
      reference.hidden = !shouldOpen;
    }
    if (isAnswered) {
      setAnsweredDetailsVisibility(mcq, shouldOpen && getAnsweredDetailsVisibility(mcq));
    }
    updateLessonToggle(mcq);
  }

  function setAnsweredDetailsVisibility(mcq, shouldOpen) {
    if (!mcq || mcq.dataset.answered !== "true") {
      return;
    }

    const inlineRationales = Array.from(mcq.querySelectorAll(".mcq__option-rationale"));
    const reference = mcq.querySelector(".mcq__reference");

    inlineRationales.forEach((node) => {
      node.hidden = !shouldOpen;
    });
    if (reference) {
      reference.hidden = !shouldOpen;
    }
  }

  function getAnsweredDetailsVisibility(mcq) {
    if (!mcq || mcq.dataset.answered !== "true") {
      return false;
    }

    const teachingCard = mcq.querySelector(".question-teaching-card");
    if (teachingCard) {
      return teachingCard.open;
    }

    return true;
  }

  function answerQuestion(button) {
    const option = button;
    const mcq = option.closest(".mcq");
    if (!mcq || mcq.dataset.answered === "true") {
      return;
    }

    const selected = option.dataset.optionKey;
    const answer = mcq.dataset.answer;
    const answers = answer ? answer.split("|").filter(Boolean) : [];
    const reviewOnly = mcq.dataset.reviewOnly === "true" || answers.length === 0;
    const options = Array.from(mcq.querySelectorAll(".mcq__option"));

    options.forEach((node) => {
      node.disabled = true;
      if (!reviewOnly && answers.includes(node.dataset.optionKey)) {
        node.classList.add("is-correct");
      }
      if (!reviewOnly && node.dataset.optionKey === selected && !answers.includes(selected)) {
        node.classList.add("is-wrong");
      }
    });

    mcq.dataset.answered = "true";
    mcq.dataset.correct = reviewOnly ? "false" : String(answers.includes(selected));

    setLessonOpen(mcq, true);
    setAnsweredDetailsVisibility(mcq, getAnsweredDetailsVisibility(mcq));

    updateScore();
  }

  function initQuestions() {
    document.querySelectorAll(".mcq__option").forEach((button) => {
      button.addEventListener("click", function () {
        answerQuestion(button);
      });
    });
    document.querySelectorAll("[data-lesson-toggle]").forEach((button) => {
      const mcq = button.closest(".mcq");
      if (!mcq) {
        return;
      }
      updateLessonToggle(mcq);
      button.addEventListener("click", function () {
        const explanation = mcq.querySelector(".mcq__explanation");
        if (!explanation) {
          return;
        }
        const shouldOpen = explanation.hidden;
        preserveQuestionPosition(mcq, function () {
          setLessonOpen(mcq, shouldOpen);
        });
      });
    });
    document.querySelectorAll("[data-lesson-close]").forEach((button) => {
      const mcq = button.closest(".mcq");
      if (!mcq) {
        return;
      }
      button.addEventListener("click", function () {
        preserveQuestionPosition(mcq, function () {
          setLessonOpen(mcq, false);
        });
      });
    });
    document.querySelectorAll("[data-teaching-card-close]").forEach((button) => {
      const card = button.closest(".question-teaching-card");
      if (!card) {
        return;
      }
      button.addEventListener("click", function () {
        const mcq = card.closest(".mcq");
        const summary = card.querySelector(".question-teaching-card__summary");
        preserveQuestionPosition(mcq, function () {
          card.open = false;
          setAnsweredDetailsVisibility(mcq, false);
        });
        if (summary instanceof HTMLElement) {
          summary.focus({ preventScroll: true });
        }
      });
    });
    document.querySelectorAll(".question-teaching-card").forEach((card) => {
      const mcq = card.closest(".mcq");
      if (!mcq) {
        return;
      }
      const summary = card.querySelector(".question-teaching-card__summary");
      if (summary instanceof HTMLElement) {
        summary.addEventListener("click", function (event) {
          event.preventDefault();
          preserveQuestionPosition(mcq, function () {
            card.open = !card.open;
            setAnsweredDetailsVisibility(mcq, card.open);
          });
        });
      }
      card.addEventListener("toggle", function () {
        setAnsweredDetailsVisibility(mcq, card.open);
      });
    });
    updateScore();
  }

  function initObserver() {
    if (!("IntersectionObserver" in window) || sections.length === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }
          const id = entry.target.getAttribute("id");
          links.forEach((link) => {
            link.classList.toggle("is-active", link.getAttribute("href") === `#${id}`);
          });
        });
      },
      { rootMargin: "-25% 0px -60% 0px", threshold: 0.1 }
    );

    sections.forEach((section) => observer.observe(section));
  }

  initTheme();
  initSidebar();
  initSidebarLinks();
  initQuestions();
  initObserver();

  if (themeButton) {
    themeButton.addEventListener("click", toggleTheme);
  }

  if (sidebarButton) {
    sidebarButton.addEventListener("click", toggleSidebar);
  }

  links.forEach((link) => {
    link.addEventListener("click", () => {
      if (mobileSidebarQuery.matches) {
        localStorage.setItem(sidebarStorageKey, "true");
        applySidebarState(true);
      }
    });
  });
})();
