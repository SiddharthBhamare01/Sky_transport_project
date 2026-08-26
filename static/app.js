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

const NUMBER_FIELDS = new Set(["weight"]);
const INT_FIELDS = new Set(["piece_count"]);
const BOOL_FIELDS = new Set(["signature_present", "review_recommended"]);
const NIL_ID = "00000000-0000-0000-0000-000000000000";

let currentFields = null;
let currentPreviewUrl = null;
let currentPreviewIsPdf = false;

const $ = (id) => document.getElementById(id);

// Coerces the always-stringy values that come out of form inputs / inline
// table edits into the types Supabase's columns actually expect, so a
// cleared numeric/boolean cell doesn't get sent as "" and rejected.
function toRow(fields) {
  const out = { ...fields };
  Object.keys(out).forEach((k) => {
    const v = out[k];
    if (NUMBER_FIELDS.has(k)) {
      out[k] = v === "" || v === null || v === undefined ? null : Number(v);
    } else if (INT_FIELDS.has(k)) {
      out[k] = v === "" || v === null || v === undefined ? null : parseInt(v, 10);
    } else if (BOOL_FIELDS.has(k)) {
      out[k] = v === "" || v === null || v === undefined ? null : (v === true || v === "true");
    }
  });
  if ("low_confidence_fields" in out) out.low_confidence_fields = out.low_confidence_fields || [];
  return out;
}

let rows = [];

async function loadRowsFromSupabase() {
  const { data, error } = await db.from("shipment_rows").select("*").order("created_at", { ascending: true });
  if (error) {
    showError("Could not load saved rows: " + error.message);
    return [];
  }
  return data;
}

async function init() {
  const { data: sessionData } = await db.auth.getSession();
  if (!sessionData.session) {
    location.href = "./login.html";
    return;
  }
  $("userEmail").textContent = sessionData.session.user.email;
  $("logoutBtn").onclick = async () => {
    await signOut();
    location.href = "./login.html";
  };

  const cfg = await fetch(`${RENDER_ORIGIN}/api/config`).then((r) => r.json());
  if (!cfg.has_api_key) $("sampleBanner").classList.add("visible");

  const samples = await fetch(`${RENDER_ORIGIN}/api/samples`).then((r) => r.json());
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
  $("clearBtn").onclick = async () => {
    if (!confirm("Clear all rows for everyone? This deletes the shared queue and cannot be undone.")) return;
    const { error } = await db.from("shipment_rows").delete().neq("id", NIL_ID);
    if (error) {
      showError("Could not clear rows: " + error.message);
      return;
    }
    rows = [];
    renderTable();
  };

  const fileInput = $("fileInput");
  const dropzone = document.querySelector(".dropzone");
  fileInput.addEventListener("change", () => updateDropzoneLabel(fileInput.files[0]));
  if (dropzone) {
    ["dragenter", "dragover"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      })
    );
    dropzone.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files[0];
      if (!file) return;
      fileInput.files = e.dataTransfer.files;
      updateDropzoneLabel(file);
    });
  }

  rows = await loadRowsFromSupabase();
  renderTable();
}

function updateDropzoneLabel(file) {
  const label = document.querySelector(".dropzone-text");
  if (!label) return;
  label.textContent = file ? file.name : "Drop a file or browse";
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
  await runExtraction(
    () => fetch(`${RENDER_ORIGIN}/api/extract`, { method: "POST", body: fd }),
    URL.createObjectURL(file),
    file.type === "application/pdf"
  );
}

async function runSample(sampleId, filename) {
  showError(null);
  const isPdf = filename.toLowerCase().endsWith(".pdf");
  await runExtraction(
    () => fetch(`${RENDER_ORIGIN}/api/extract?sample_id=${encodeURIComponent(sampleId)}`, { method: "POST" }),
    `${RENDER_ORIGIN}/samples/${filename}`,
    isPdf
  );
}

async function runExtraction(doFetch, previewUrl, isPdf) {
  $("uploadBtn").disabled = true;
  try {
    const resp = await doFetch();
    let data = null;
    try {
      data = await resp.json();
    } catch {
      // non-JSON body (e.g. a raw 500) - fall through to the generic error below
    }
    if (!resp.ok || !data || data.error || !data.fields) {
      showError((data && (data.message || data.detail)) || `Request failed (HTTP ${resp.status}).`);
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
  const lowConfidence = new Set(currentFields.low_confidence_fields || []);
  const flag = $("reviewFlag");
  if (currentFields.review_recommended) {
    flag.classList.remove("hidden");
    flag.textContent = "⚠ Review recommended: " + (currentFields.extraction_notes || "low confidence on one or more fields.");
  } else {
    flag.classList.add("hidden");
  }

  FORM_FIELDS.forEach((f) => {
    const row = document.createElement("div");
    row.className = "field-row" + (lowConfidence.has(f.key) ? " low-confidence" : "");
    const label = document.createElement("label");
    label.textContent = f.label + (lowConfidence.has(f.key) ? " ⚠" : "");
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

async function addCurrentToTable() {
  if (!currentFields) return;
  const edited = readFormIntoFields();
  edited.review_recommended = currentFields.review_recommended;
  edited.extraction_notes = currentFields.extraction_notes;
  edited.low_confidence_fields = currentFields.low_confidence_fields || [];

  const btn = $("addRowBtn");
  btn.disabled = true;
  const { data, error } = await db.from("shipment_rows").insert(toRow(edited)).select().single();
  btn.disabled = false;
  if (error) {
    showError("Could not save row: " + error.message);
    return;
  }
  rows.push(data);
  renderTable();
  notifyBackend("/api/notify/row-added", {
    load_number: data.load_number,
    shipper_name: data.shipper_name,
    consignee_name: data.consignee_name,
    carrier_name: data.carrier_name,
    weight: data.weight,
    weight_unit: data.weight_unit,
    piece_count: data.piece_count,
  });
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
    const rowLowConfidence = new Set(row.low_confidence_fields || []);
    TABLE_FIELDS.forEach((key) => {
      const td = document.createElement("td");
      if (rowLowConfidence.has(key)) td.classList.add("low-confidence");
      if (BOOL_FIELDS.has(key)) {
        const val = row[key] === true || row[key] === "true" ? "true" : row[key] === false || row[key] === "false" ? "false" : "";
        const nullable = key !== "review_recommended"; // review_recommended is NOT NULL in Supabase
        const select = document.createElement("select");
        select.className = "pill-select pill-" + (val === "true" ? "yes" : val === "false" ? "no" : "unset");
        (nullable ? [["", "—"], ["true", "Yes"], ["false", "No"]] : [["true", "Yes"], ["false", "No"]]).forEach(([v, label]) => {
          const opt = document.createElement("option");
          opt.value = v;
          opt.textContent = label;
          if (v === val) opt.selected = true;
          select.appendChild(opt);
        });
        select.onchange = async () => {
          const newValue = select.value;
          select.className = "pill-select pill-" + (newValue === "true" ? "yes" : newValue === "false" ? "no" : "unset");
          rows[idx][key] = newValue;
          if (!rows[idx].id) return;
          const { error } = await db.from("shipment_rows").update(toRow({ [key]: newValue })).eq("id", rows[idx].id);
          if (error) showError("Could not save edit: " + error.message);
        };
        td.appendChild(select);
      } else {
        td.contentEditable = "true";
        td.textContent = row[key] === null || row[key] === undefined ? "" : row[key];
        td.onblur = async () => {
          const newValue = td.textContent;
          if (rows[idx][key] === newValue) return;
          rows[idx][key] = newValue;
          if (!rows[idx].id) return;
          const { error } = await db.from("shipment_rows").update(toRow({ [key]: newValue })).eq("id", rows[idx].id);
          if (error) showError("Could not save edit: " + error.message);
        };
      }
      tr.appendChild(td);
    });
    const tdAction = document.createElement("td");
    const delBtn = document.createElement("button");
    delBtn.textContent = "Delete";
    delBtn.onclick = async () => {
      const row = rows[idx];
      if (row.id) {
        const { error } = await db.from("shipment_rows").delete().eq("id", row.id);
        if (error) {
          showError("Could not delete row: " + error.message);
          return;
        }
      }
      rows.splice(idx, 1);
      renderTable();
    };
    tdAction.appendChild(delBtn);
    tr.appendChild(tdAction);
    body.appendChild(tr);
  });

  $("rowCount").textContent = rows.length;
}

function csvEscape(value) {
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  let s = value === null || value === undefined ? "" : String(value);
  // Guard against CSV/formula injection when this opens in Excel/Sheets -
  // field values originate from documents read by the model, so treat them
  // as untrusted input.
  if (/^[=+\-@\t\r]/.test(s)) {
    s = "'" + s;
  }
  if (/[",\n]/.test(s)) {
    s = '"' + s.replace(/"/g, '""') + '"';
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
