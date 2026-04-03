/**
 * Vehicle picker built only from charm-manual-index.json (CHARM export paths).
 * Year / make / model / engine are parsed from folder titles in build_charm_manifest.py.
 */

async function loadJson(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`${url} → ${res.status}`);
  return res.json();
}

function loadCharmManifest() {
  return loadJson(new URL("charm-manual-index.json", import.meta.url).href);
}

function uniqSortedStrings(arr) {
  return [...new Set(arr.filter(Boolean))].sort((a, b) =>
    a.localeCompare(b, undefined, { sensitivity: "base", numeric: true })
  );
}

function uniqSortedYears(arr) {
  return [...new Set(arr.filter((y) => y != null))].sort((a, b) => a - b);
}

function populateSelect(el, values, placeholder, valueToLabel) {
  el.innerHTML = "";
  const ph = document.createElement("option");
  ph.value = "";
  ph.textContent = placeholder;
  el.appendChild(ph);
  const labelFn = valueToLabel || ((v) => String(v));
  for (const v of values) {
    const o = document.createElement("option");
    o.value = v;
    o.textContent = labelFn(v);
    el.appendChild(o);
  }
  el.disabled = false;
}

const ENGINE_EMPTY = "__none__";

function engineKey(manual) {
  const e = (manual.pickerEngine || "").trim();
  return e || ENGINE_EMPTY;
}

function engineLabel(key) {
  return key === ENGINE_EMPTY ? "(as listed)" : key;
}

async function main() {
  const makeSel = document.getElementById("make");
  const yearSel = document.getElementById("year");
  const modelSel = document.getElementById("model");
  const engineSel = document.getElementById("engine");
  const statusEl = document.getElementById("status");
  const listEl = document.getElementById("manual-list");

  const status = (msg) => {
    statusEl.textContent = msg;
  };

  let manuals;
  try {
    const data = await loadCharmManifest();
    manuals = data.manuals || [];
  } catch (e) {
    status(
      `Could not load charm-manual-index.json (${e.message}). Run scripts/build_charm_manifest.py and serve the repo root over HTTP.`
    );
    makeSel.innerHTML = "<option value=\"\">Error</option>";
    return;
  }

  if (!manuals.length) {
    status("No manuals indexed. Add CHARM exports and run scripts/build_charm_manifest.py.");
    populateSelect(makeSel, [], "Make");
    return;
  }

  function filterByMake(m) {
    return manuals.filter((row) => row.make === m);
  }

  function filterByMakeYear(m, y) {
    const yi = parseInt(y, 10);
    return manuals.filter((row) => row.make === m && row.year === yi);
  }

  function filterByMakeYearModel(m, y, mod) {
    const yi = parseInt(y, 10);
    return manuals.filter(
      (row) =>
        row.make === m &&
        row.year === yi &&
        (row.pickerModel || "") === mod
    );
  }

  function showResults(rows) {
    listEl.innerHTML = "";
    if (!rows.length) {
      listEl.classList.add("hidden");
      return;
    }
    listEl.classList.remove("hidden");
    for (const row of rows) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = row.href;
      a.textContent = row.title;
      li.appendChild(a);
      listEl.appendChild(li);
    }
  }

  const refreshYears = () => {
    const m = makeSel.value;
    if (!m) {
      populateSelect(yearSel, [], "Year");
      populateSelect(modelSel, [], "Model");
      populateSelect(engineSel, [], "Engine");
      yearSel.disabled = true;
      modelSel.disabled = true;
      engineSel.disabled = true;
      showResults([]);
      status("Select a make.");
      return;
    }
    const years = uniqSortedYears(filterByMake(m).map((row) => row.year));
    populateSelect(
      yearSel,
      years.map(String),
      "Year",
      (v) => v
    );
    yearSel.disabled = false;
    populateSelect(modelSel, [], "Model");
    modelSel.disabled = true;
    populateSelect(engineSel, [], "Engine");
    engineSel.disabled = true;
    showResults([]);
    status("Select year and model.");
  };

  const refreshModels = () => {
    const m = makeSel.value;
    const y = yearSel.value;
    if (!m || !y) {
      populateSelect(modelSel, [], "Model");
      populateSelect(engineSel, [], "Engine");
      modelSel.disabled = true;
      engineSel.disabled = true;
      showResults([]);
      return;
    }
    const models = uniqSortedStrings(
      filterByMakeYear(m, y).map((row) => row.pickerModel || "")
    );
    populateSelect(modelSel, models, "Model");
    modelSel.disabled = false;
    populateSelect(engineSel, [], "Engine");
    engineSel.disabled = true;
    showResults([]);
    status("Select model (and engine if more than one).");
  };

  const refreshEngines = () => {
    const m = makeSel.value;
    const y = yearSel.value;
    const mod = modelSel.value;
    if (!m || !y || !mod) {
      populateSelect(engineSel, [], "Engine");
      engineSel.disabled = true;
      showResults([]);
      return;
    }
    const subset = filterByMakeYearModel(m, y, mod);
    const keys = uniqSortedStrings(subset.map((row) => engineKey(row)));
    populateSelect(engineSel, keys, "Engine", engineLabel);
    engineSel.disabled = keys.length <= 1;
    if (keys.length === 1) {
      engineSel.value = keys[0];
    } else {
      engineSel.value = "";
    }
    applyEngineFilter();
  };

  function applyEngineFilter() {
    const m = makeSel.value;
    const y = yearSel.value;
    const mod = modelSel.value;
    const eng = engineSel.value;
    if (!m || !y || !mod) {
      showResults([]);
      status("Select make, year, and model.");
      return;
    }
    let subset = filterByMakeYearModel(m, y, mod);
    if (eng) {
      subset = subset.filter((row) => engineKey(row) === eng);
    }
    if (!subset.length) {
      showResults([]);
      status("No manual matched those choices.");
      return;
    }
    if (subset.length === 1) {
      status("Open the manual below.");
    } else {
      status(`${subset.length} manuals match — pick one.`);
    }
    showResults(subset);
  }

  const makes = uniqSortedStrings(manuals.map((row) => row.make));
  populateSelect(makeSel, makes, "Make", (name) =>
    name.charAt(0) + name.slice(1).toLowerCase()
  );
  if (makes.length === 1) {
    makeSel.value = makes[0];
  }

  makeSel.addEventListener("change", refreshYears);
  yearSel.addEventListener("change", refreshModels);
  modelSel.addEventListener("change", refreshEngines);
  engineSel.addEventListener("change", applyEngineFilter);

  refreshYears();
  if (makeSel.value) {
    refreshModels();
    if (yearSel.value) {
      refreshEngines();
    }
  }
}

main();
