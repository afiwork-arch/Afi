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

  // お役立ち記事カルーセル（左右ボタンで1カード分ずつスクロール）
  var articleTrack = document.querySelector("[data-carousel-track]");
  var carouselPrev = document.querySelector("[data-carousel-prev]");
  var carouselNext = document.querySelector("[data-carousel-next]");

  if (articleTrack && carouselPrev && carouselNext) {
    var scrollByCard = function (direction) {
      var card = articleTrack.querySelector(".tile-article");
      var amount = card ? card.getBoundingClientRect().width + 5 : articleTrack.clientWidth;
      articleTrack.scrollBy({ left: amount * direction, behavior: "smooth" });
    };

    var updateCarouselNav = function () {
      var maxScroll = articleTrack.scrollWidth - articleTrack.clientWidth;
      carouselPrev.disabled = articleTrack.scrollLeft <= 2;
      carouselNext.disabled = maxScroll <= 2 || articleTrack.scrollLeft >= maxScroll - 2;
    };

    carouselPrev.addEventListener("click", function () { scrollByCard(-1); });
    carouselNext.addEventListener("click", function () { scrollByCard(1); });
    articleTrack.addEventListener("scroll", updateCarouselNav);
    window.addEventListener("resize", updateCarouselNav);
    updateCarouselNav();

    // 自動スライド（ホバー/フォーカス中は一時停止。読もうとしている最中に中身が
    // 変わる不快さを避けるため。prefers-reduced-motionのユーザーには実行しない）
    var AUTO_INTERVAL_MS = 5000;
    var autoTimer = null;
    var isPaused = false;
    var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var advanceAuto = function () {
      if (isPaused) return;
      var maxScroll = articleTrack.scrollWidth - articleTrack.clientWidth;
      if (articleTrack.scrollLeft >= maxScroll - 2) {
        articleTrack.scrollTo({ left: 0, behavior: "smooth" });
      } else {
        scrollByCard(1);
      }
    };

    if (!prefersReducedMotion) {
      autoTimer = window.setInterval(advanceAuto, AUTO_INTERVAL_MS);

      var carousel = articleTrack.closest(".article-carousel");
      if (carousel) {
        carousel.addEventListener("mouseenter", function () { isPaused = true; });
        carousel.addEventListener("mouseleave", function () { isPaused = false; });
        carousel.addEventListener("focusin", function () { isPaused = true; });
        carousel.addEventListener("focusout", function () { isPaused = false; });
      }
    }
  }
})();
