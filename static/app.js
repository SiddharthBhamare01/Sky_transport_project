const FORM_FIELDS = [
  { key: "document_type", label: "Doc type", type: "select", options: ["BOL", "POD", "unknown"] },
  { key: "shipper_name", label: "Shipper" },
  { key: "shipper_address", label: "Shipper addr" },
  { key: "consignee_name", label: "Consignee" },
  { key: "consignee_address", label: "Consignee addr" },
  { key: "carrier_name", label: "Carrier" },
  { key: "load_number", label: "Load #" },
  { key: "pro_number", label: "PRO #" },
  { key: "pickup_date", label: "Pickup date" },
  { key: "delivery_date", label: "Delivery date" },
  { key: "weight", label: "Weight", type: "number" },
  { key: "weight_unit", label: "Weight unit", type: "select", options: ["lb", "kg"] },
  { key: "piece_count", label: "Pieces", type: "number" },
  { key: "commodity_description", label: "Commodity" },
  { key: "freight_charge_terms", label: "Terms", type: "select", options: ["prepaid", "collect", "third_party"] },
  { key: "signature_present", label: "Signed?", type: "select", options: ["true", "false"] },
];

const TABLE_FIELDS = [...FORM_FIELDS.map((f) => f.key), "review_recommended", "extraction_notes"];

const STORAGE_KEY = "shipment_rows_v1";

let currentFields = null;
let currentPreviewUrl = null;
let currentPreviewIsPdf = false;

const $ = (id) => document.getElementById(id);

function loadRows() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveRows(rows) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(rows));
}

let rows = loadRows();

async function init() {
  const cfg = await fetch("/api/config").then((r) => r.json());
  if (!cfg.has_api_key) $("sampleBanner").classList.add("visible");

  const samples = await fetch("/api/samples").then((r) => r.json());
  const container = $("sampleButtons");
  samples.forEach((s) => {
    const btn = document.createElement("button");
    btn.className = "sample-btn";
    btn.textContent = s.display_name;
    btn.onclick = () => runSample(s.sample_id, s.filename);
    container.appendChild(btn);
  });

  $("uploadBtn").onclick = runUpload;
  $("addRowBtn").onclick = addCurrentToTable;
  $("exportBtn").onclick = exportCsv;
  $("clearBtn").onclick = () => {
    if (confirm("Clear all rows?")) {
      rows = [];
      saveRows(rows);
      renderTable();
    }
  };

  renderTable();
}

function showError(msg) {
  const box = $("errorBox");
  if (!msg) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.classList.remove("hidden");
  box.textContent = msg;
}

async function runUpload() {
  const input = $("fileInput");
  if (!input.files.length) {
    showError("Choose a file first.");
    return;
  }
  const file = input.files[0];
  showError(null);
  const fd = new FormData();
  fd.append("file", file);
  await runExtraction(() => fetch("/api/extract", { method: "POST", body: fd }), URL.createObjectURL(file), file.type === "application/pdf");
}

async function runSample(sampleId, filename) {
  showError(null);
  const isPdf = filename.toLowerCase().endsWith(".pdf");
  await runExtraction(
    () => fetch(`/api/extract?sample_id=${encodeURIComponent(sampleId)}`, { method: "POST" }),
    `/samples/${filename}`,
    isPdf
  );
}

async function runExtraction(doFetch, previewUrl, isPdf) {
  $("uploadBtn").disabled = true;
  try {
    const resp = await doFetch();
    const data = await resp.json();
    if (data.error) {
      showError(`${data.error}: ${data.message}`);
      return;
    }
    currentFields = data.fields;
    currentPreviewUrl = previewUrl;
    currentPreviewIsPdf = isPdf;
    renderPreview();
    renderForm();
    $("resultPanel").classList.remove("hidden");
  } catch (e) {
    showError("Request failed: " + e);
  } finally {
    $("uploadBtn").disabled = false;
  }
}

function renderPreview() {
  const pane = $("previewPane");
  pane.innerHTML = "";
  if (!currentPreviewUrl) {
    pane.innerHTML = '<div class="empty">No document loaded</div>';
    return;
  }
  if (currentPreviewIsPdf) {
    const iframe = document.createElement("iframe");
    iframe.src = currentPreviewUrl;
    iframe.style.width = "100%";
    iframe.style.height = "460px";
    iframe.style.border = "none";
    pane.appendChild(iframe);
    const link = document.createElement("div");
    link.style.textAlign = "center";
    link.style.padding = "6px";
    link.innerHTML = `<a href="${currentPreviewUrl}" target="_blank" rel="noopener">Open PDF in new tab</a>`;
    pane.appendChild(link);
  } else {
    const img = document.createElement("img");
    img.src = currentPreviewUrl;
    pane.appendChild(img);
  }
}

function renderForm() {
  const form = $("fieldForm");
  form.innerHTML = "";
  const flag = $("reviewFlag");
  if (currentFields.review_recommended) {
    flag.classList.remove("hidden");
    flag.textContent = "⚠ Review recommended: " + (currentFields.extraction_notes || "low confidence on one or more fields.");
  } else {
    flag.classList.add("hidden");
  }

  FORM_FIELDS.forEach((f) => {
    const row = document.createElement("div");
    row.className = "field-row";
    const label = document.createElement("label");
    label.textContent = f.label;
    row.appendChild(label);

    let value = currentFields[f.key];
    let input;
    if (f.type === "select") {
      input = document.createElement("select");
      const blankOpt = document.createElement("option");
      blankOpt.value = "";
      blankOpt.textContent = "—";
      input.appendChild(blankOpt);
      f.options.forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        input.appendChild(o);
      });
      input.value = value === null || value === undefined ? "" : String(value);
    } else {
      input = document.createElement("input");
      input.type = f.type === "number" ? "number" : "text";
      input.value = value === null || value === undefined ? "" : value;
    }
    input.dataset.key = f.key;
    row.appendChild(input);
    form.appendChild(row);
  });
}

function readFormIntoFields() {
  const form = $("fieldForm");
  const out = { ...currentFields };
  FORM_FIELDS.forEach((f) => {
    const input = form.querySelector(`[data-key="${f.key}"]`);
    let v = input.value;
    if (v === "") {
      out[f.key] = null;
    } else if (f.type === "number") {
      out[f.key] = Number(v);
    } else if (f.key === "signature_present") {
      out[f.key] = v === "true";
    } else {
      out[f.key] = v;
    }
  });
  return out;
}

function addCurrentToTable() {
  if (!currentFields) return;
  const edited = readFormIntoFields();
  edited.review_recommended = currentFields.review_recommended;
  edited.extraction_notes = currentFields.extraction_notes;
  rows.push(edited);
  saveRows(rows);
  renderTable();
}

function renderTable() {
  const head = $("tableHead");
  head.innerHTML = "";
  TABLE_FIELDS.forEach((key) => {
    const th = document.createElement("th");
    th.textContent = key;
    head.appendChild(th);
  });
  const thAction = document.createElement("th");
  thAction.textContent = "";
  head.appendChild(thAction);

  const body = $("tableBody");
  body.innerHTML = "";
  rows.forEach((row, idx) => {
    const tr = document.createElement("tr");
    TABLE_FIELDS.forEach((key) => {
      const td = document.createElement("td");
      td.contentEditable = "true";
      td.textContent = row[key] === null || row[key] === undefined ? "" : row[key];
      td.oninput = () => {
        rows[idx][key] = td.textContent;
        saveRows(rows);
      };
      tr.appendChild(td);
    });
    const tdAction = document.createElement("td");
    const delBtn = document.createElement("button");
    delBtn.textContent = "Delete";
    delBtn.onclick = () => {
      rows.splice(idx, 1);
      saveRows(rows);
      renderTable();
    };
    tdAction.appendChild(delBtn);
    tr.appendChild(tdAction);
    body.appendChild(tr);
  });

  $("rowCount").textContent = rows.length;
}

function csvEscape(value) {
  const s = value === null || value === undefined ? "" : String(value);
  if (/[",\n]/.test(s)) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

function exportCsv() {
  if (!rows.length) {
    showError("No rows to export yet.");
    return;
  }
  const lines = [TABLE_FIELDS.map(csvEscape).join(",")];
  rows.forEach((row) => {
    lines.push(TABLE_FIELDS.map((key) => csvEscape(row[key])).join(","));
  });
  const csv = lines.join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "shipments.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

init();
