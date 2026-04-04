/**
 * Vehicle picker: local CHARM exports (charm-manual-index.json) +
 * Operation CHARM coverage (charm-coverage.json) +
 * charm-vehicle-cache.json (charm.li year pages → model/engine → vehicle URLs).
 */

async function loadJson(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`${url} → ${res.status}`);
  return res.json();
}

function loadCharmManifest() {
  return loadJson(new URL("charm-manual-index.json", import.meta.url).href);
}

function yearsFromManualRow(row) {
  if (typeof row.year === "number") return [row.year];
  const a = row.yearFrom;
  const b = row.yearTo;
  if (typeof a === "number" && typeof b === "number" && a <= b) {
    const out = [];
    for (let y = a; y <= b; y++) out.push(y);
    return out;
  }
  return [];
}

function manualYearMatches(row, yi) {
  if (typeof row.year === "number") return row.year === yi;
  if (typeof row.yearFrom === "number" && typeof row.yearTo === "number") {
    return yi >= row.yearFrom && yi <= row.yearTo;
  }
  return false;
}

function loadCharmCoverage() {
  return loadJson(new URL("charm-coverage.json", import.meta.url).href);
}

async function loadCharmVehicleCache() {
  try {
    return await loadJson(
      new URL("charm-vehicle-cache.json", import.meta.url).href
    );
  } catch {
    return {
      version: 1,
      charmBaseUrl: "https://charm.li",
      byMakeYear: {},
    };
  }
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

/**
 * Appended after the vehicle directory URL (same as Operation CHARM directory names).
 */
const CHARM_SECTION_SUFFIX = {
  "": "",
  repair: "Repair%20and%20Diagnosis/",
  parts: "Parts%20and%20Labor/",
};

function buildCharmSectionOpenUrl(vehicleRootUrl, sectionKey) {
  const base = String(vehicleRootUrl).replace(/\/?$/, "/");
  const suf = CHARM_SECTION_SUFFIX[sectionKey] ?? "";
  return base + suf;
}

function openUrlInNewTab(url) {
  const abs =
    typeof url === "string" && !/^[a-z][a-z0-9+.-]*:/i.test(url)
      ? new URL(url, window.location.href).href
      : url;
  window.open(abs, "_blank", "noopener,noreferrer");
}

/** Plain left-click → new tab via window.open; modifiers / middle-click keep default behavior. */
function bindManualOpensNewTab(anchor, href) {
  anchor.addEventListener("click", (e) => {
    if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) {
      return;
    }
    e.preventDefault();
    openUrlInNewTab(href);
  });
}

function engineKey(manual) {
  const e = (manual.pickerEngine || "").trim();
  return e || ENGINE_EMPTY;
}

function engineLabel(key) {
  return key === ENGINE_EMPTY ? "(as listed)" : key;
}

function engineKeyRemote(row) {
  const e = (row.pickerEngine || "").trim();
  return e || ENGINE_EMPTY;
}

function remoteRowsForMakeYear(vehicleCache, makeKey, yearStr) {
  const bag =
    vehicleCache &&
    vehicleCache.byMakeYear &&
    vehicleCache.byMakeYear[makeKey];
  if (!bag) return [];
  const y = String(yearStr);
  return bag[y] || [];
}

function remoteManualHref(vehicleCache, row) {
  const base = (vehicleCache.charmBaseUrl || "https://charm.li").replace(
    /\/$/,
    ""
  );
  let p = row.path || "";
  if (!p.startsWith("/")) p = "/" + p;
  if (!p.endsWith("/")) p += "/";
  return `${base}${p}`;
}

function charmYearUrl(coverage, coverageByKey, makeKey, yearStr) {
  const row = coverageByKey.get(makeKey);
  if (!row) return null;
  const base = (coverage.charmBaseUrl || "https://charm.li").replace(/\/$/, "");
  const y = parseInt(yearStr, 10);
  if (Number.isNaN(y)) return null;
  return `${base}/${encodeURIComponent(row.charmName)}/${y}/`;
}

async function main() {
  const makeSel = document.getElementById("make");
  const yearSel = document.getElementById("year");
  const modelSel = document.getElementById("model");
  const engineSel = document.getElementById("engine");
  const statusEl = document.getElementById("status");
  const listEl = document.getElementById("manual-list");
  const charmSectionSel = document.getElementById("charm-section");

  const status = (msg) => {
    statusEl.textContent = msg;
  };

  let manuals;
  let coverage = null;
  const coverageByKey = new Map();
  let vehicleCache = {
    version: 1,
    charmBaseUrl: "https://charm.li",
    byMakeYear: {},
  };

  let makeDisplayNames = {};
  try {
    const manifestData = await loadCharmManifest();
    manuals = manifestData.manuals || [];
    makeDisplayNames = manifestData.makeDisplayNames || {};
  } catch (e) {
    status(
      `Could not load charm-manual-index.json (${e.message}). Run scripts/build_charm_manifest.py and serve the repo root over HTTP.`
    );
    makeSel.innerHTML = "<option value=\"\">Error</option>";
    return;
  }

  try {
    coverage = await loadCharmCoverage();
    for (const x of coverage.makes || []) {
      coverageByKey.set(x.makeKey, x);
    }
  } catch {
    coverage = null;
  }

  vehicleCache = await loadCharmVehicleCache();

  function yearsFromCoverage(makeKey) {
    const row = coverageByKey.get(makeKey);
    return row ? row.years : [];
  }

  function mergeYearsForMake(makeKey) {
    const fromCov = yearsFromCoverage(makeKey);
    const fromMan = uniqSortedYears(
      manuals
        .filter((row) => row.make === makeKey)
        .flatMap((row) => yearsFromManualRow(row))
    );
    return uniqSortedYears([...fromCov, ...fromMan]);
  }

  function makeLabel(makeKey) {
    const row = coverageByKey.get(makeKey);
    if (row) return row.charmName;
    const custom = makeDisplayNames[makeKey];
    if (custom) return custom;
    return makeKey.charAt(0) + makeKey.slice(1).toLowerCase();
  }

  function filterByMake(m) {
    return manuals.filter((row) => row.make === m);
  }

  function filterByMakeYear(m, y) {
    const yi = parseInt(y, 10);
    return manuals.filter(
      (row) => row.make === m && manualYearMatches(row, yi)
    );
  }

  function filterByMakeYearModel(m, y, mod) {
    const yi = parseInt(y, 10);
    return manuals.filter(
      (row) =>
        row.make === m &&
        manualYearMatches(row, yi) &&
        (row.pickerModel || "") === mod
    );
  }

  function isCharmDeepLinkingAvailable() {
    const m = makeSel.value;
    const y = yearSel.value;
    if (!m || !y) return false;
    return filterByMakeYear(m, y).length === 0;
  }

  function isLocalVehicleContext() {
    const m = makeSel.value;
    const y = yearSel.value;
    if (!m || !y) return false;
    return filterByMakeYear(m, y).length > 0;
  }

  function syncRemoteManualHrefs() {
    const sectionKey =
      charmSectionSel && !charmSectionSel.disabled ? charmSectionSel.value : "";
    listEl.querySelectorAll("li.manual-list-item-remote a.manual-list-main").forEach((a) => {
      const base = a.dataset.charmBase;
      if (!base) return;
      a.href = buildCharmSectionOpenUrl(base, sectionKey);
    });
  }

  function updateCharmDeepControlsState() {
    const on = isCharmDeepLinkingAvailable();
    if (charmSectionSel) {
      charmSectionSel.disabled = !on;
    }
    const hint = document.getElementById("charm-deep-hint");
    if (hint) {
      hint.classList.toggle("hidden", !isLocalVehicleContext());
    }
    syncRemoteManualHrefs();
  }

  function bindCharmRemoteManualOpensNewTab(anchor, baseVehicleHref) {
    anchor.dataset.charmBase = baseVehicleHref;
    const syncHref = () => {
      if (charmSectionSel && !charmSectionSel.disabled) {
        anchor.href = buildCharmSectionOpenUrl(
          baseVehicleHref,
          charmSectionSel.value
        );
      } else {
        anchor.href = baseVehicleHref;
      }
      syncRemoteManualHrefs();
    };
    syncHref();
    anchor.addEventListener("mouseenter", syncHref);
    anchor.addEventListener("focus", syncHref);
    anchor.addEventListener("click", (e) => {
      if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) {
        return;
      }
      e.preventDefault();
      syncHref();
      openUrlInNewTab(anchor.href);
    });
  }

  function appendCharmYearBrowseLink(makeKey, y) {
    const url = charmYearUrl(coverage, coverageByKey, makeKey, y);
    if (!url) return;
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    bindManualOpensNewTab(a, url);
    const name = makeLabel(makeKey);
    a.textContent = `Browse ${name} ${y} on charm.li (manual UI)`;
    li.appendChild(a);
    listEl.appendChild(li);
  }

  function showRemoteIndexNotAdded(makeKey, y) {
    listEl.innerHTML = "";
    listEl.classList.remove("hidden");
    status(
      "Index not yet added — this make/year is not in charm-vehicle-cache.json. Run scripts/build_charm_vehicle_cache.py (see README), or open the year page on charm.li."
    );
    appendCharmYearBrowseLink(makeKey, y);
  }

  function showRemoteResults(rows) {
    listEl.innerHTML = "";
    listEl.classList.remove("hidden");
    for (const row of rows) {
      const li = document.createElement("li");
      li.className = "manual-list-item-remote";
      const a = document.createElement("a");
      const href = remoteManualHref(vehicleCache, row);
      a.className = "manual-list-main";
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      bindCharmRemoteManualOpensNewTab(a, href);
      a.textContent = row.label || row.pickerModel || "Manual";
      li.appendChild(a);
      listEl.appendChild(li);
    }
    syncRemoteManualHrefs();
  }

  function remoteModelKey(row) {
    return (row.pickerModel || "").trim() || row.label || "";
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
      const href = row.href;
      a.className = "manual-list-main";
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      bindManualOpensNewTab(a, href);
      a.textContent = row.title;
      li.appendChild(a);
      listEl.appendChild(li);
    }
  }

  const refreshYears = () => {
    try {
      const m = makeSel.value;
      if (!m) {
        populateSelect(yearSel, [], "Year");
        populateSelect(modelSel, [], "Model");
        populateSelect(engineSel, [], "Engine");
        yearSel.disabled = true;
        modelSel.disabled = true;
        engineSel.disabled = true;
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
        status("Select a make.");
        return;
      }
      const years = mergeYearsForMake(m);
      if (!years.length) {
        populateSelect(yearSel, [], "Year");
        yearSel.disabled = true;
        status("No years listed for this make (check charm-coverage.json and local exports).");
        return;
      }
      populateSelect(yearSel, years.map(String), "Year", (v) => v);
      yearSel.disabled = false;
      populateSelect(modelSel, [], "Model");
      modelSel.disabled = true;
      populateSelect(engineSel, [], "Engine");
      engineSel.disabled = true;
      listEl.classList.add("hidden");
      listEl.innerHTML = "";
      status("Select year, then model (or charm.li).");
    } finally {
      updateCharmDeepControlsState();
    }
  };

  const refreshModels = () => {
    try {
      const m = makeSel.value;
      const y = yearSel.value;
      if (!m || !y) {
        populateSelect(modelSel, [], "Model");
        populateSelect(engineSel, [], "Engine");
        modelSel.disabled = true;
        engineSel.disabled = true;
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
        return;
      }
      const local = filterByMakeYear(m, y);
      if (local.length) {
        const models = uniqSortedStrings(local.map((row) => row.pickerModel || ""));
        populateSelect(modelSel, models, "Model");
        modelSel.disabled = false;
        populateSelect(engineSel, [], "Engine");
        engineSel.disabled = true;
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
        status("Select model (and engine if more than one).");
      } else {
        const remote = remoteRowsForMakeYear(vehicleCache, m, y);
        if (!remote.length) {
          populateSelect(modelSel, [], "Model");
          modelSel.disabled = true;
          populateSelect(engineSel, [], "Engine");
          engineSel.disabled = true;
          showRemoteIndexNotAdded(m, y);
          return;
        }
        const models = uniqSortedStrings(remote.map((row) => remoteModelKey(row)));
        populateSelect(modelSel, models, "Model");
        modelSel.disabled = false;
        populateSelect(engineSel, [], "Engine");
        engineSel.disabled = true;
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
        status("Select model and engine, then open the manual on Operation CHARM.");
      }
    } finally {
      updateCharmDeepControlsState();
    }
  };

  const refreshEngines = () => {
    try {
      const m = makeSel.value;
      const y = yearSel.value;
      const mod = modelSel.value;
      if (!m || !y) {
        populateSelect(engineSel, [], "Engine");
        engineSel.disabled = true;
        return;
      }
      const localMy = filterByMakeYear(m, y);
      if (!localMy.length) {
        const remote = remoteRowsForMakeYear(vehicleCache, m, y);
        if (!mod) {
          populateSelect(engineSel, [], "Engine");
          engineSel.disabled = true;
          listEl.classList.add("hidden");
          listEl.innerHTML = "";
          return;
        }
        const subset = remote.filter((row) => remoteModelKey(row) === mod);
        const keys = uniqSortedStrings(subset.map((row) => engineKeyRemote(row)));
        populateSelect(engineSel, keys, "Engine", engineLabel);
        engineSel.disabled = keys.length <= 1;
        if (keys.length === 1) {
          engineSel.value = keys[0];
        } else {
          engineSel.value = "";
        }
        applyEngineFilter();
        return;
      }
      if (!mod) {
        populateSelect(engineSel, [], "Engine");
        engineSel.disabled = true;
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
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
    } finally {
      updateCharmDeepControlsState();
    }
  };

  function applyEngineFilter() {
    try {
      const m = makeSel.value;
      const y = yearSel.value;
      const mod = modelSel.value;
      const eng = engineSel.value;
      if (!m || !y) {
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
        return;
      }
      const localMy = filterByMakeYear(m, y);
      if (!localMy.length) {
        const remote = remoteRowsForMakeYear(vehicleCache, m, y);
        if (!mod) {
          status("Select make, year, and model.");
          listEl.classList.add("hidden");
          listEl.innerHTML = "";
          return;
        }
        let subset = remote.filter((row) => remoteModelKey(row) === mod);
        if (eng) {
          subset = subset.filter((row) => engineKeyRemote(row) === eng);
        }
        if (!subset.length) {
          listEl.classList.add("hidden");
          listEl.innerHTML = "";
          status(
            "Index not yet added — no matching vehicle line in charm-vehicle-cache.json for this model/engine."
          );
          appendCharmYearBrowseLink(m, y);
          return;
        }
        if (subset.length === 1) {
          status(
            "Optional: choose CHARM menu section, then open the manual (new tab)."
          );
        } else {
          status(`${subset.length} manuals match — pick one below (new tab).`);
        }
        showRemoteResults(subset);
        return;
      }

      if (!mod) {
        status("Select make, year, and model.");
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
        return;
      }
      let subset = filterByMakeYearModel(m, y, mod);
      if (eng) {
        subset = subset.filter((row) => engineKey(row) === eng);
      }
      if (!subset.length) {
        listEl.classList.add("hidden");
        listEl.innerHTML = "";
        status("No manual matched those choices.");
        return;
      }
      if (subset.length === 1) {
        status("Open the local manual below.");
      } else {
        status(`${subset.length} local manuals match — pick one.`);
      }
      showResults(subset);
    } finally {
      updateCharmDeepControlsState();
    }
  }

  const makeKeysFromCov = coverage
    ? coverage.makes.map((x) => x.makeKey)
    : [];
  const makeKeysFromMan = uniqSortedStrings(manuals.map((row) => row.make));
  const allMakeKeys = uniqSortedStrings([...makeKeysFromCov, ...makeKeysFromMan]);
  if (!allMakeKeys.length) {
    status("No makes in coverage or local index.");
    populateSelect(makeSel, [], "Make");
    return;
  }

  populateSelect(makeSel, allMakeKeys, "Make", makeLabel);
  if (allMakeKeys.length === 1) {
    makeSel.value = allMakeKeys[0];
  }

  makeSel.addEventListener("change", refreshYears);
  yearSel.addEventListener("change", refreshModels);
  modelSel.addEventListener("change", refreshEngines);
  engineSel.addEventListener("change", applyEngineFilter);
  if (charmSectionSel) {
    charmSectionSel.addEventListener("change", () => {
      syncRemoteManualHrefs();
    });
  }

  refreshYears();
  if (makeSel.value) {
    refreshModels();
    if (yearSel.value && modelSel.value) {
      refreshEngines();
    }
  }
}

main();
