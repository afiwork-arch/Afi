(function () {
  "use strict";

  var toolbar = document.querySelector(".sort-toolbar");
  var table = document.getElementById("compare-table");

  if (toolbar && table) {
    var tbody = table.querySelector("tbody");
    var moreBtn = document.getElementById("table-more-btn");
    var tableExpanded = false;

    var applyRowLimit = function () {
      if (!moreBtn || tableExpanded) return;
      var limit = Number(moreBtn.dataset.limit);
      Array.prototype.slice.call(tbody.querySelectorAll("tr")).forEach(function (row, i) {
        row.hidden = i >= limit;
      });
    };

    var sortRows = function (mode) {
      var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));

      rows.sort(function (a, b) {
        if (mode === "default") {
          return Number(a.dataset.order) - Number(b.dataset.order);
        }
        if (mode === "price-asc") {
          return Number(a.dataset.price) - Number(b.dataset.price);
        }
        if (mode === "price-desc") {
          return Number(b.dataset.price) - Number(a.dataset.price);
        }
        if (mode === "disk-desc") {
          return Number(b.dataset.disk) - Number(a.dataset.disk);
        }
        return 0;
      });

      rows.forEach(function (row) {
        tbody.appendChild(row);
      });

      applyRowLimit();
    };

    toolbar.addEventListener("click", function (event) {
      var btn = event.target.closest(".sort-btn");
      if (!btn) return;

      toolbar.querySelectorAll(".sort-btn").forEach(function (b) {
        b.classList.remove("is-active");
      });
      btn.classList.add("is-active");

      sortRows(btn.dataset.sort);
    });

    if (moreBtn) {
      var moreLabel = moreBtn.textContent.trim();
      var lessLabel = "閉じる";

      moreBtn.hidden = false;
      applyRowLimit();

      moreBtn.addEventListener("click", function () {
        tableExpanded = !tableExpanded;

        if (tableExpanded) {
          Array.prototype.slice.call(tbody.querySelectorAll("tr")).forEach(function (row) {
            row.hidden = false;
          });
          moreBtn.textContent = lessLabel;
          moreBtn.classList.add("is-expanded");
        } else {
          applyRowLimit();
          moreBtn.textContent = moreLabel;
          moreBtn.classList.remove("is-expanded");
          table.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    }

    // LOW/MIDDLE/HIGH プラン切り替え
    var tierToolbar = document.getElementById("tier-toolbar");
    var tierPriceKey = { low: "priceLow", mid: "priceMid", high: "priceHigh" };
    var tierDiskKey = { low: "diskLow", mid: "diskMid", high: "diskHigh" };

    if (tierToolbar) {
      tierToolbar.addEventListener("click", function (event) {
        var btn = event.target.closest("[data-tier]");
        if (!btn) return;

        tierToolbar.querySelectorAll(".sort-btn").forEach(function (b) {
          b.classList.remove("is-active");
        });
        btn.classList.add("is-active");

        var tier = btn.dataset.tier;

        Array.prototype.slice.call(tbody.querySelectorAll("tr")).forEach(function (row) {
          row.querySelectorAll(".tier-variant").forEach(function (variant) {
            variant.hidden = variant.dataset.tier !== tier;
          });
          row.dataset.price = row.dataset[tierPriceKey[tier]];
          row.dataset.disk = row.dataset[tierDiskKey[tier]];
        });

        // 表示中のソート順を、切り替え後の価格・容量で再適用する
        var activeSortBtn = toolbar.querySelector(".sort-btn.is-active");
        sortRows(activeSortBtn ? activeSortBtn.dataset.sort : "default");
      });
    }
  }

  // 各社の特徴を詳しく（ドロップダウンで企業を切り替え）
  var reviewSelect = document.getElementById("review-select");
  var reviewPanels = document.querySelectorAll(".review-panel");
  if (reviewSelect && reviewPanels.length) {
    reviewSelect.addEventListener("change", function () {
      var slug = reviewSelect.value;
      reviewPanels.forEach(function (panel) {
        panel.hidden = panel.dataset.slug !== slug;
      });
    });
  }

  // かんたん診断（STEP1: 種類 → STEP2: 予算 → STEP3: ポイント → 結果）
  var diagnosis = document.querySelector(".diagnosis");
  var diagPanels = document.querySelectorAll(".diag-panel");
  var diagStep1 = document.querySelector(".diag-buttons-step1");
  var diagBudget = document.getElementById("diag-step-budget");
  var diagTrait = document.getElementById("diag-step-trait");
  var diagResult = document.getElementById("diag-result");
  var panel1 = diagPanels.length ? diagPanels[0] : null;

  if (diagnosis && diagStep1 && diagBudget && diagTrait && diagResult && panel1) {
    var state = { type: null };
    var history = [panel1];

    var TRANSITION_MS = 320;
    var transitioning = false;

    function clearInlineTransform(panel) {
      panel.style.transition = "";
      panel.style.transform = "";
      panel.style.opacity = "";
    }

    function showPanel(target, direction) {
      if (transitioning) return;
      var current = history[history.length - 1];
      if (current === target) return;

      var forward = direction !== "back";
      target.scrollIntoView({ behavior: "smooth", block: "nearest" });

      if (!current) {
        target.hidden = false;
        return;
      }

      // 新しいパネルを、進行方向の外側（右 or 左）に置いてから表示する
      target.hidden = false;
      target.style.transition = "none";
      target.style.transform = "translateX(" + (forward ? "100%" : "-100%") + ")";
      target.style.opacity = "0";
      void target.offsetWidth;
      target.style.transition = "";

      // 次のフレームで、現パネルは反対側へ、新パネルは中央へ同時にスライド
      transitioning = true;
      requestAnimationFrame(function () {
        target.style.transform = "translateX(0)";
        target.style.opacity = "1";
        current.style.transform = "translateX(" + (forward ? "-100%" : "100%") + ")";
        current.style.opacity = "0";
      });

      window.setTimeout(function () {
        current.hidden = true;
        clearInlineTransform(current);
        clearInlineTransform(target);
        transitioning = false;
      }, TRANSITION_MS);
    }

    function goForward(panel) {
      var current = history[history.length - 1];
      if (current === panel) return;
      showPanel(panel, "next");
      history.push(panel);
    }

    function goBack() {
      if (history.length <= 1) return;
      var target = history[history.length - 2];
      showPanel(target, "back");
      history.pop();
    }

    function resetAllActive() {
      diagPanels.forEach(function (panel) {
        panel.querySelectorAll(".diag-btn").forEach(function (b) {
          b.classList.remove("is-active");
        });
      });
    }

    function showResult(slug) {
      diagResult.querySelectorAll(".diag-result-card").forEach(function (card) {
        card.hidden = card.dataset.slug !== slug;
      });
      goForward(diagResult);
    }

    // STEP1: サーバー種類
    diagStep1.addEventListener("click", function (event) {
      var btn = event.target.closest(".diag-btn");
      if (!btn) return;

      diagStep1.querySelectorAll(".diag-btn").forEach(function (b) {
        b.classList.remove("is-active");
      });
      btn.classList.add("is-active");

      state.type = btn.dataset.step1Target;
      var group = diagTrait.querySelector('[data-step2-group="' + state.type + '"]');
      var options = group ? group.querySelectorAll(".diag-btn") : [];

      if (options.length <= 1) {
        if (options.length === 1) showResult(options[0].dataset.target);
        return;
      }

      diagBudget.querySelectorAll(".diag-btn").forEach(function (b) {
        b.classList.remove("is-active");
      });
      goForward(diagBudget);
    });

    // STEP2: 予算感
    diagBudget.addEventListener("click", function (event) {
      var btn = event.target.closest(".diag-btn");
      if (btn) {
        diagBudget.querySelectorAll(".diag-btn").forEach(function (b) {
          b.classList.remove("is-active");
        });
        btn.classList.add("is-active");

        var budget = btn.dataset.budgetTarget;
        var group = diagTrait.querySelector('[data-step2-group="' + state.type + '"]');
        var matched = [];

        diagTrait.querySelectorAll("[data-step2-group]").forEach(function (g) {
          g.hidden = g !== group;
        });

        if (group) {
          group.querySelectorAll(".diag-btn").forEach(function (b) {
            var isMatch = b.dataset.budget === budget;
            b.hidden = !isMatch;
            if (isMatch) matched.push(b);
          });
          // 該当0件のときは予算条件を無視して種類だけで絞り込む（保険）
          if (matched.length === 0) {
            group.querySelectorAll(".diag-btn").forEach(function (b) {
              b.hidden = false;
              matched.push(b);
            });
          }
        }

        if (matched.length <= 1) {
          if (matched.length === 1) showResult(matched[0].dataset.target);
          return;
        }

        diagTrait.querySelectorAll(".diag-btn").forEach(function (b) {
          b.classList.remove("is-active");
        });
        goForward(diagTrait);
        return;
      }
      if (event.target.closest(".diag-back")) goBack();
    });

    // STEP3: 重視するポイント
    diagTrait.addEventListener("click", function (event) {
      var btn = event.target.closest(".diag-btn");
      if (btn) {
        diagTrait.querySelectorAll(".diag-btn").forEach(function (b) {
          b.classList.remove("is-active");
        });
        btn.classList.add("is-active");
        showResult(btn.dataset.target);
        return;
      }
      if (event.target.closest(".diag-back")) goBack();
    });

    // 結果パネル（戻る・もう一度診断する）
    diagResult.addEventListener("click", function (event) {
      if (event.target.closest(".diag-reset")) {
        state.type = null;
        transitioning = false;
        history = [panel1];
        diagPanels.forEach(function (panel) {
          panel.hidden = panel !== panel1;
          clearInlineTransform(panel);
        });
        resetAllActive();
        diagnosis.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
      if (event.target.closest(".diag-back")) goBack();
    });
  }
})();
