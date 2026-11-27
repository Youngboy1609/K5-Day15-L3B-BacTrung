(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const form = $("analyze-form");
  const urlInput = $("product-url");
  const modelInput = $("phone-model");
  const variantInput = $("case-variant");
  const submitButton = $("analyze-button");
  const demoButton = $("demo-button");
  const statusLine = $("form-status");
  const result = $("result");
  const feedback = $("feedback");
  const retryButton = $("retry-button");
  const state = { catalog: [], version: 0, busy: false };

  function setStatus(message) {
    statusLine.textContent = message;
  }

  function clearFieldErrors() {
    for (const input of [urlInput, modelInput, variantInput]) {
      input.removeAttribute("aria-invalid");
    }
    for (const id of ["url-error", "model-error", "variant-error"]) {
      $(id).hidden = true;
      $(id).textContent = "";
    }
  }

  function fieldError(input, message) {
    input.setAttribute("aria-invalid", "true");
    const errorId = input === urlInput ? "url-error" : input === modelInput ? "model-error" : "variant-error";
    $(errorId).textContent = message;
    $(errorId).hidden = false;
    setStatus(message);
    input.focus();
  }

  function clearResult(message) {
    state.version += 1;
    result.hidden = true;
    feedback.hidden = true;
    feedback.classList.remove("is-error");
    retryButton.hidden = true;
    setStatus(message || "");
  }

  function option(value, label) {
    const item = document.createElement("option");
    item.value = value;
    item.textContent = label;
    return item;
  }

  function findListing(url) {
    return state.catalog.find((item) => item.product_url === url) || null;
  }

  function setModels(listing) {
    modelInput.replaceChildren(option("", "Chọn dòng máy"));
    variantInput.replaceChildren(option("", "Chọn biến thể"));
    if (!listing) {
      modelInput.disabled = true;
      variantInput.disabled = true;
      return;
    }
    modelInput.disabled = false;
    for (const model of listing.phone_models) {
      modelInput.add(option(model.phone_model, model.phone_model));
    }
    if (listing.phone_models.length) {
      modelInput.value = listing.phone_models[0].phone_model;
      setVariants(listing.phone_models[0]);
    } else {
      variantInput.disabled = true;
    }
  }

  function setVariants(model) {
    variantInput.replaceChildren(option("", "Chọn biến thể"));
    if (!model) {
      variantInput.disabled = true;
      return;
    }
    variantInput.disabled = false;
    for (const variant of model.case_variants) {
      variantInput.add(option(variant, variant));
    }
    if (model.case_variants.length) {
      variantInput.value = model.case_variants[0];
    }
  }

  function setBusy(busy) {
    state.busy = busy;
    submitButton.disabled = busy;
    submitButton.textContent = busy ? "Đang phân tích…" : "Phân tích review";
    form.setAttribute("aria-busy", busy ? "true" : "false");
  }

  function showFeedback(title, message, code, isError) {
    result.hidden = true;
    feedback.hidden = false;
    feedback.classList.toggle("is-error", Boolean(isError));
    $("feedback-title").textContent = title;
    $("feedback-message").textContent = message;
    $("feedback-code").textContent = code || "";
    retryButton.hidden = !isError;
    setStatus(message);
  }

  function modeLabel(mode) {
    if (mode === "mock_not_real_ai") return "Mock · chưa phải AI thật";
    if (mode === "model") return "Model thật";
    return mode || "Không rõ";
  }

  function evidenceLabel(item, seen) {
    const labels = {
      negative: "Đáng lưu ý",
      positive: "Tích cực",
      mixed: "Hỗn hợp",
      unknown: "Chưa rõ",
    };
    if (!seen[item.sentiment]) {
      seen[item.sentiment] = true;
      return labels[item.sentiment] || "Dẫn chứng";
    }
    return "Dẫn chứng thêm";
  }

  function detailRow(list, label, value) {
    const row = document.createElement("div");
    row.className = "detail-row";
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    row.append(term, description);
    list.append(row);
  }

  function renderDetails(output) {
    const container = $("details-content");
    container.replaceChildren();
    const list = document.createElement("dl");
    list.className = "detail-list";
    detailRow(list, "Sản phẩm", output.product?.product_title || "—");
    detailRow(list, "Chế độ", modeLabel(output.analysis_mode));
    detailRow(list, "Chính sách", output.policy_status || "—");
    detailRow(list, "Seed", String(output.coverage?.sample_seed ?? "—"));
    detailRow(list, "Đã lấy mẫu", String(output.coverage?.review_count ?? "—"));
    detailRow(list, "Tổng đúng biến thể", String(output.coverage?.eligible_count ?? "—"));
    detailRow(list, "Media", output.media_note || "Chưa có thông tin media");
    container.append(list);

    const assessments = Array.isArray(output.review_assessments) ? output.review_assessments : [];
    if (assessments.length) {
      const heading = document.createElement("h3");
      heading.textContent = "Nhãn từng review";
      const items = document.createElement("ul");
      items.className = "assessment-list";
      for (const item of assessments) {
        const row = document.createElement("li");
        row.textContent = `${item.review_id} · ${item.stars}/5 · ${item.sentiment} · ${item.evidence_strength} — ${item.reason}`;
        items.append(row);
      }
      container.append(heading, items);
    }
  }

  function renderResult(output) {
    const coverage = output.coverage || {};
    const evidence = Array.isArray(output.evidence) ? output.evidence : [];
    $("result-context").textContent = `${output.product?.phone_model || "—"} · ${output.product?.case_variant || "—"}`;
    $("recommendation").textContent = output.recommendation;
    $("coverage-number").textContent = `${coverage.review_count ?? "—"} / ${coverage.eligible_count ?? "—"}`;
    $("coverage-label").textContent = "review đã phân tích / tổng review đúng biến thể";
    const eligible = Number(coverage.eligible_count || 0);
    $("coverage-note").textContent = eligible < 3
      ? `Chỉ có ${eligible} review đúng mẫu; nên đọc thêm trước khi quyết định.`
      : `Đã đọc ${coverage.review_count} review đúng biến thể trong bộ demo. ${modeLabel(output.analysis_mode)}.`;

    const list = $("evidence-list");
    list.replaceChildren();
    const seen = {};
    for (const item of evidence) {
      const article = document.createElement("article");
      article.className = "evidence-item";
      const label = document.createElement("p");
      label.className = "evidence-label";
      label.textContent = evidenceLabel(item, seen);
      const meta = document.createElement("p");
      meta.className = "evidence-meta";
      meta.textContent = `${item.stars}/5 · ${item.review_id}`;
      const quote = document.createElement("blockquote");
      quote.textContent = item.review_text;
      const reason = document.createElement("p");
      reason.className = "evidence-reason";
      reason.textContent = `${item.reason} ${item.media_assessment === "not_assessed" ? "Chưa phân tích media." : ""}`;
      article.append(label, meta, quote, reason);
      list.append(article);
    }
    if (!evidence.length) {
      const empty = document.createElement("p");
      empty.textContent = "Chưa có dẫn chứng đủ mạnh.";
      list.append(empty);
    }

    $("advice").textContent = output.advice || "Đối chiếu lại biến thể và chính sách đổi trả trước khi đặt.";
    renderDetails(output);
    feedback.hidden = true;
    result.hidden = false;
    result.focus({ preventScroll: true });
    setStatus(`Đã phân tích ${coverage.review_count ?? 0}/${coverage.eligible_count ?? 0} review đúng biến thể.`);
  }

  async function readResponse(response) {
    let data;
    try {
      data = await response.json();
    } catch (error) {
      throw new Error("Phản hồi phân tích không hợp lệ.");
    }
    if (!response.ok) {
      throw new Error(data.message || "Không đọc được phản hồi phân tích.");
    }
    if (typeof data.output === "string") {
      const output = JSON.parse(data.output);
      return { ...output, output: data.output, result: output };
    }
    return { ...data, result: data };
  }

  async function analyze(event) {
    event.preventDefault();
    if (state.busy) return;
    clearFieldErrors();
    const request = {
      product_url: urlInput.value.trim(),
      phone_model: modelInput.value,
      case_variant: variantInput.value,
    };
    if (!request.product_url || urlInput.validity.typeMismatch) {
      fieldError(urlInput, "Nhập link HTTPS của shopee.vn hoặc dùng mẫu demo.");
      return;
    }
    if (!request.phone_model) {
      fieldError(modelInput, "Chọn dòng máy trước khi phân tích.");
      return;
    }
    if (!request.case_variant) {
      fieldError(variantInput, "Chọn biến thể ốp trước khi phân tích.");
      return;
    }

    clearResult("Đang phân tích review đúng mẫu…");
    const version = state.version;
    setBusy(true);
    try {
      const response = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      const data = await readResponse(response);
      if (version !== state.version) return;
      if (data.status === "ok") {
        renderResult(data.result);
      } else if (data.status === "needs_input") {
        showFeedback("Cần chọn lại mẫu", data.message || "Biến thể chưa khớp.", data.code, true);
        variantInput.focus();
      } else {
        showFeedback("Chưa phân tích được", data.message || "Thử lại sau.", data.code, true);
      }
    } catch (error) {
      if (version === state.version) {
        showFeedback("Chưa phân tích được", error.message || "Kiểm tra kết nối local rồi thử lại.", "ANALYSIS_UNAVAILABLE", true);
      }
    } finally {
      setBusy(false);
    }
  }

  urlInput.addEventListener("input", () => {
    clearFieldErrors();
    const listing = findListing(urlInput.value.trim());
    setModels(listing);
    clearResult("Đã thay đổi link. Chọn mẫu rồi phân tích lại.");
  });
  urlInput.addEventListener("blur", () => {
    if (urlInput.value.trim() && !findListing(urlInput.value.trim())) {
      clearResult("Đã thay đổi link. Chọn mẫu rồi phân tích lại.");
      showFeedback("Chưa có dữ liệu cho link này", "Link chưa có trong bộ demo. Dùng link fixture hoặc mẫu demo; không truy cập Shopee.", "NO_LOCAL_DEMO_DATA", true);
    }
  });
  modelInput.addEventListener("change", () => {
    const listing = findListing(urlInput.value.trim());
    const model = listing?.phone_models.find((item) => item.phone_model === modelInput.value);
    setVariants(model);
    clearResult("Đã thay đổi mẫu. Phân tích lại để xem review đúng mẫu.");
  });
  variantInput.addEventListener("change", () => clearResult("Đã thay đổi biến thể. Phân tích lại."));
  form.addEventListener("submit", analyze);
  retryButton.addEventListener("click", () => form.requestSubmit());
  demoButton.addEventListener("click", () => {
    const listing = state.catalog[0];
    if (!listing) {
      setStatus("Danh mục demo chưa đọc được. Tải lại trang rồi thử lại.");
      return;
    }
    clearFieldErrors();
    urlInput.value = listing.product_url;
    setModels(listing);
    const proModel = listing.phone_models.find((item) => item.phone_model === "iPhone 15 Pro");
    if (proModel) {
      modelInput.value = proModel.phone_model;
      setVariants(proModel);
      if (proModel.case_variants.includes("Ốp trong suốt viền đen")) {
        variantInput.value = "Ốp trong suốt viền đen";
      }
    }
    clearResult("Đã điền mẫu demo. Bấm Phân tích review để xem kết quả.");
  });

  async function loadCatalog() {
    try {
      const response = await fetch("/catalog", { cache: "no-store" });
      const data = await readResponse(response);
      state.catalog = data.listings || [];
      const datalist = $("listing-options");
      datalist.replaceChildren();
      for (const listing of state.catalog) {
        const option = document.createElement("option");
        option.value = listing.product_url;
        option.label = listing.product_title;
        datalist.append(option);
      }
      setStatus("Chọn link demo hoặc dán link fixture để bắt đầu.");
    } catch (error) {
      setStatus("Chưa đọc được danh mục demo. Tải lại trang rồi thử lại.");
    }
  }

  loadCatalog();
})();