/**
 * Vehicle picker: local CHARM exports (charm-manual-index.json) +
 * Operation CHARM coverage (charm-coverage.json) +
 * optional charm-vehicle-cache.json (scraped charm.li year pages → model/engine → vehicle URLs).
 *
 * Remote CHARM “search” cannot call charm.li from the browser (CORS). TOC titles for suggestions:
 * optional charm-section-toc-cache.json or .json.gz (scripts/build_charm_section_toc_cache.py), and/or bookmarklet /
 * fetch_charm_section_toc.py → paste → sessionStorage.
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

/** Populated in main() from charm-section-toc-cache.json (if present). */
let charmSectionTocFileCache = { byPath: {} };

async function loadCharmSectionTocFileCache() {
  const apply = (d) => {
    const bp = d && d.byPath;
    charmSectionTocFileCache = {
      byPath: bp && typeof bp === "object" ? bp : {},
    };
  };
  const base = import.meta.url;
  try {
    apply(await loadJson(new URL("charm-section-toc-cache.json", base).href));
    return;
  } catch {
    /* optional uncompressed local build */
  }
  try {
    const href = new URL("charm-section-toc-cache.json.gz", base).href;
    const res = await fetch(href, { cache: "no-store" });
    if (!res.ok) throw new Error(String(res.status));
    const buf = await res.arrayBuffer();
    const ds = new DecompressionStream("gzip");
    const text = await new Response(
      new Blob([buf]).stream().pipeThrough(ds)
    ).text();
    apply(JSON.parse(text));
  } catch {
    charmSectionTocFileCache = { byPath: {} };
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
 * Manual topic chips (single scroll row).
 * charmSection: which charm.li submenu fits that topic (see CHARM_SECTION_SUFFIX).
 */
const TOPIC_CATEGORIES = [
  {
    id: "labor",
    label: "Labor Times",
    keywords: ["Labor", "Labor time"],
    charmSection: "parts",
  },
  {
    id: "torque",
    label: "Torque Specs",
    keywords: ["Torque"],
    charmSection: "repair",
  },
  {
    id: "specifications",
    label: "Specifications",
    keywords: ["Specifications"],
    charmSection: "repair",
  },
  {
    id: "fluid",
    label: "Fluid Specs",
    keywords: ["Fluid", "Fluids", "Fluid Type Specifications"],
    charmSection: "repair",
  },
  {
    id: "dtc",
    label: "DTC Codes",
    keywords: ["DTC", "ALL Diagnostic Trouble Codes (DTC)"],
    charmSection: "repair",
  },
];

/**
 * Appended after the vehicle directory URL (same as Operation CHARM directory names).
 * e.g. …/Chevrolet/2009/Silverado%201500%204WD%20V8-6.0L/Repair%20and%20Diagnosis/
 * @see https://charm.li/…/Repair%20and%20Diagnosis/ and …/Parts%20and%20Labor/
 */
const CHARM_SECTION_SUFFIX = {
  "": "",
  repair: "Repair%20and%20Diagnosis/",
  parts: "Parts%20and%20Labor/",
};

/**
 * vehicleRootUrl: absolute URL to vehicle root (trailing slash optional).
 * sectionKey: "" | "repair" | "parts"
 */
function buildCharmSectionOpenUrl(vehicleRootUrl, sectionKey) {
  const base = String(vehicleRootUrl).replace(/\/?$/, "/");
  const suf = CHARM_SECTION_SUFFIX[sectionKey] ?? "";
  return base + suf;
}

/** Encode one path segment the way charm.li URLs use (%20 for spaces, etc.). */
function encodeCharmPathSegment(seg) {
  if (!seg) return "";
  try {
    return encodeURIComponent(decodeURIComponent(seg));
  } catch {
    return encodeURIComponent(seg);
  }
}

/**
 * Path for site: queries — segment-encoded to match indexed charm.li URLs
 * (e.g. /Chevrolet/2009/Silverado%201500%204WD%20V8-6.0L/Repair%20and%20Diagnosis).
 */
function charmPathForSiteOperator(charmAbsoluteUrl) {
  let u;
  try {
    u = new URL(charmAbsoluteUrl);
  } catch {
    return null;
  }
  const host = u.hostname.toLowerCase();
  if (host !== "charm.li" && host !== "www.charm.li") return null;
  const segments = u.pathname.split("/").filter(Boolean);
  if (!segments.length) return "/";
  return `/${segments.map(encodeCharmPathSegment).join("/")}`;
}

/**
 * Google search limited to the exact charm.li path (vehicle or Repair / Parts folder).
 * Use when "Search on that CHARM page" has text.
 */
function buildGoogleCharmScopedSearchUrl(charmAbsoluteUrl, userQuery) {
  const trimmed = String(userQuery || "").trim();
  if (!trimmed) return null;
  const path = charmPathForSiteOperator(charmAbsoluteUrl);
  if (path == null) return null;
  const siteScope = `site:charm.li${path}`;
  const q = `${siteScope} ${trimmed}`;
  return `https://www.google.com/search?q=${encodeURIComponent(q)}`;
}

/** sessionStorage key: vehicle root path + CHARM section (repair | parts | ""). */
function charmVehicleRootPathForStorage(vehicleRootUrl) {
  let u;
  try {
    u = new URL(vehicleRootUrl);
  } catch {
    return "";
  }
  const p = u.pathname.replace(/\/+$/, "");
  return p || "/";
}

function charmTocStorageKey(vehicleRootUrl, sectionKey) {
  const p = charmVehicleRootPathForStorage(vehicleRootUrl);
  return `ovd-charm-toc:${p}:${sectionKey ?? ""}`;
}

function loadCharmTocFromSession(vehicleRootUrl, sectionKey) {
  try {
    const raw = sessionStorage.getItem(
      charmTocStorageKey(vehicleRootUrl, sectionKey)
    );
    if (!raw) return [];
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function saveCharmTocToSession(vehicleRootUrl, sectionKey, titles) {
  const list = titles.filter((t) => typeof t === "string" && t.trim());
  sessionStorage.setItem(
    charmTocStorageKey(vehicleRootUrl, sectionKey),
    JSON.stringify(list)
  );
}

function getRemoteCharmBasesFromList(listEl) {
  const bases = [];
  if (!listEl) return bases;
  listEl.querySelectorAll("li.manual-list-item-remote a.manual-list-main").forEach((a) => {
    const b = a.dataset.charmBase;
    if (b && !bases.includes(b)) bases.push(b);
  });
  return bases;
}

function fileCharmTocTitlesForVehicle(vehicleRootUrl, sectionKey) {
  const key = charmVehicleRootPathForStorage(vehicleRootUrl);
  if (!key) return [];
  const row = charmSectionTocFileCache.byPath[key];
  if (!row || typeof row !== "object") return [];
  if (sectionKey === "repair") {
    return Array.isArray(row.repair) ? row.repair : [];
  }
  if (sectionKey === "parts") {
    return Array.isArray(row.parts) ? row.parts : [];
  }
  return [];
}

function loadMergedCharmTocTitles(listEl, sectionKey) {
  const bases = getRemoteCharmBasesFromList(listEl);
  const set = new Set();
  for (const base of bases) {
    for (const t of loadCharmTocFromSession(base, sectionKey)) {
      const s = String(t).trim();
      if (s) set.add(s);
    }
    for (const t of fileCharmTocTitlesForVehicle(base, sectionKey)) {
      const s = String(t).trim();
      if (s) set.add(s);
    }
  }
  return [...set].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
}

const CHARM_TOC_DATALIST_MAX = 3500;

function refreshCharmSearchDatalist(listEl, sectionKey, datalistEl) {
  if (!datalistEl) return;
  datalistEl.innerHTML = "";
  const titles = loadMergedCharmTocTitles(listEl, sectionKey);
  const slice = titles.slice(0, CHARM_TOC_DATALIST_MAX);
  for (const t of slice) {
    const opt = document.createElement("option");
    opt.value = t;
    datalistEl.appendChild(opt);
  }
}

function parseCharmTocPaste(text) {
  const raw = String(text || "").trim();
  if (!raw) return [];
  if (raw.startsWith("{") || raw.startsWith("[")) {
    try {
      const o = JSON.parse(raw);
      if (Array.isArray(o)) {
        return o
          .filter((x) => typeof x === "string")
          .map((s) => s.trim())
          .filter(Boolean);
      }
      const titles = o && o.titles;
      if (Array.isArray(titles)) {
        return titles
          .filter((x) => typeof x === "string")
          .map((s) => s.trim())
          .filter(Boolean);
      }
    } catch {
      return [];
    }
    return [];
  }
  return raw
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean);
}

/**
 * Bookmarklet: run on charm.li after Expand All on Repair or Parts — copies JSON { sourceUrl, titles }.
 * User saves this string as a bookmark URL, then activates it on the CHARM tab.
 */
function getCharmTocBookmarkletHref() {
  const code =
    '(function(){var base=location.pathname.replace(/\\/+$/,"")+"/";' +
    'var seen=new Set();var titles=[];' +
    'document.querySelectorAll("a[href]").forEach(function(a){try{' +
    'var u=new URL(a.getAttribute("href"),location.href);' +
    "if(u.origin!==location.origin)return;" +
    'var p=u.pathname;if(p.slice(-1)!=="/")p+="/";' +
    "if(!p.startsWith(base))return;" +
    'var txt=(a.textContent||"").trim().replace(/\\s+/g," ");' +
    "if(txt.length<2)return;var k=txt.toLowerCase();" +
    "if(seen.has(k))return;seen.add(k);titles.push(txt);" +
    "}catch(e){}});" +
    "titles.sort(function(a,b){return a.localeCompare(b)});" +
    "var o={sourceUrl:location.href,titles:titles};var s=JSON.stringify(o);" +
    "if(navigator.clipboard&&navigator.clipboard.writeText){" +
    "navigator.clipboard.writeText(s).then(function(){" +
    'alert("CHARM: copied "+titles.length+" titles. Paste into the catalog TOC box.");' +
    "},function(){window.prompt(\"Copy:\",s);});" +
    '}else{window.prompt("Copy:",s);}})();';
  return `javascript:${encodeURIComponent(code)}`;
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
  /* charm.li serves the manual UI from the directory URL; /index.html deep links error in-browser */
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
  const topicStripEl = document.getElementById("topic-categories-strip");
  const topicKeywordsLine = document.getElementById("topic-keywords-line");
  const charmSectionSel = document.getElementById("charm-section");
  const manualSearchInput = document.getElementById("manual-search-text");
  const charmTocDatalist = document.getElementById("charm-search-datalist");
  const charmTocPaste = document.getElementById("charm-toc-paste");
  const charmTocApply = document.getElementById("charm-toc-apply");
  const charmTocCopyBm = document.getElementById("charm-toc-copy-bookmarklet");
  const charmTocCopyStatus = document.getElementById("charm-toc-copy-status");
  const charmTocApplyStatus = document.getElementById("charm-toc-apply-status");
  const charmTocStorageHint = document.getElementById("charm-toc-storage-hint");

  let lastTopicSearchSuggestion = "";

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
  await loadCharmSectionTocFileCache();

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

  function refreshCharmTocUi() {
    const sectionKey =
      charmSectionSel && !charmSectionSel.disabled ? charmSectionSel.value : "";
    const bases = getRemoteCharmBasesFromList(listEl);
    const deep = isCharmDeepLinkingAvailable();
    if (charmTocApply) {
      charmTocApply.disabled = !(deep && bases.length > 0);
    }
    refreshCharmSearchDatalist(listEl, sectionKey, charmTocDatalist);
    if (charmTocStorageHint) {
      const n = loadMergedCharmTocTitles(listEl, sectionKey).length;
      if (!deep) {
        charmTocStorageHint.textContent = "";
      } else if (!bases.length) {
        charmTocStorageHint.textContent =
          "Pick a remote manual below, then paste or save titles for this CHARM section.";
      } else if (n > 0) {
        const extra =
          n >= CHARM_TOC_DATALIST_MAX
            ? ` (datalist shows up to ${CHARM_TOC_DATALIST_MAX})`
            : "";
        charmTocStorageHint.textContent = `${n} title(s) in session for the manuals shown and the current CHARM section${extra}.`;
      } else {
        charmTocStorageHint.textContent =
          "No titles saved yet. On charm.li use Expand All, run the bookmarklet, paste JSON here, then Save.";
      }
    }
  }

  function updateCharmDeepControlsState() {
    const on = isCharmDeepLinkingAvailable();
    if (charmSectionSel) {
      charmSectionSel.disabled = !on;
    }
    if (manualSearchInput) {
      manualSearchInput.disabled = !on;
    }
    const hint = document.getElementById("charm-deep-hint");
    if (hint) {
      hint.classList.toggle("hidden", !isLocalVehicleContext());
    }
    syncRemoteGoogleSideLinksAndFallback();
    refreshCharmTocUi();
  }

  function syncRemoteGoogleSideLinksAndFallback() {
    const items = listEl.querySelectorAll("li.manual-list-item-remote");
    const q =
      manualSearchInput && !manualSearchInput.disabled
        ? manualSearchInput.value.trim()
        : "";
    const sectionKey =
      charmSectionSel && !charmSectionSel.disabled
        ? charmSectionSel.value
        : "";
    items.forEach((li) => {
      const main = li.querySelector("a.manual-list-main");
      const gA = li.querySelector("a.manual-list-google");
      if (!main || !gA) return;
      const base = main.dataset.charmBase;
      if (!base) return;
      const charmUrl = buildCharmSectionOpenUrl(base, sectionKey);
      main.href = charmUrl;
      if (q && isCharmDeepLinkingAvailable()) {
        const gu = buildGoogleCharmScopedSearchUrl(charmUrl, q);
        if (gu) {
          gA.href = gu;
          gA.classList.remove("hidden");
        } else {
          gA.classList.add("hidden");
        }
      } else {
        gA.classList.add("hidden");
      }
    });

    const fb = document.getElementById("charm-google-fallback");
    const fbA = document.getElementById("charm-google-fallback-link");
    if (fb && fbA) {
      if (items.length > 1 && q && isCharmDeepLinkingAvailable()) {
        const firstMain = items[0]?.querySelector("a.manual-list-main");
        const base = firstMain?.dataset.charmBase;
        if (base) {
          const charmUrl = buildCharmSectionOpenUrl(base, sectionKey);
          const gu = buildGoogleCharmScopedSearchUrl(charmUrl, q);
          if (gu) {
            fbA.href = gu;
            fb.classList.remove("hidden");
          } else {
            fb.classList.add("hidden");
          }
        } else {
          fb.classList.add("hidden");
        }
      } else {
        fb.classList.add("hidden");
      }
    }
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
      syncRemoteGoogleSideLinksAndFallback();
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
      const rowWrap = document.createElement("div");
      rowWrap.className = "manual-list-row";
      const a = document.createElement("a");
      const href = remoteManualHref(vehicleCache, row);
      a.className = "manual-list-main";
      a.href = href;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      bindCharmRemoteManualOpensNewTab(a, href);
      a.textContent = row.label || row.pickerModel || "Manual";
      const gA = document.createElement("a");
      gA.className = "manual-list-google hidden";
      gA.target = "_blank";
      gA.rel = "noopener noreferrer";
      gA.textContent = "Google · this folder";
      rowWrap.appendChild(a);
      rowWrap.appendChild(gA);
      li.appendChild(rowWrap);
      listEl.appendChild(li);
    }
    syncRemoteGoogleSideLinksAndFallback();
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

  function syncManualTopicsUi() {
    if (!topicStripEl) return;
    const boxes = topicStripEl.querySelectorAll('input[type="checkbox"]:checked');
    const selected = [...boxes]
      .map((input) => TOPIC_CATEGORIES.find((c) => c.id === input.value))
      .filter(Boolean);

    if (!selected.length) {
      if (topicKeywordsLine) {
        topicKeywordsLine.classList.add("hidden");
        topicKeywordsLine.textContent = "";
      }
      lastTopicSearchSuggestion = "";
      return;
    }

    const partsKw = selected
      .filter((c) => c.charmSection === "parts")
      .flatMap((c) => c.keywords);
    const repairKw = selected
      .filter((c) => c.charmSection === "repair")
      .flatMap((c) => c.keywords);
    const uniq = (arr) => [...new Set(arr.map((s) => s.trim()).filter(Boolean))];

    if (topicKeywordsLine) {
      const bits = [];
      if (partsKw.length) {
        bits.push(
          `Parts and Labor — try: ${uniq(partsKw).join(", ")}.`
        );
      }
      if (repairKw.length) {
        bits.push(
          `Repair and Diagnosis — try: ${uniq(repairKw).join(", ")}.`
        );
      }
      topicKeywordsLine.textContent = bits.join(" ");
      topicKeywordsLine.classList.remove("hidden");
    }

    const allKeywords = uniq([...partsKw, ...repairKw]);
    const suggested = allKeywords.join(", ");
    if (manualSearchInput && suggested) {
      const cur = manualSearchInput.value.trim();
      if (cur === "" || cur === lastTopicSearchSuggestion) {
        manualSearchInput.value = suggested;
        lastTopicSearchSuggestion = suggested;
      }
    }
  }

  if (topicStripEl) {
    for (const cat of TOPIC_CATEGORIES) {
      const id = `topic-cat-${cat.id}`;
      const label = document.createElement("label");
      label.className = "topic-chip";
      label.title = cat.keywords.join(", ");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.id = id;
      input.value = cat.id;
      input.addEventListener("change", syncManualTopicsUi);
      const span = document.createElement("span");
      span.textContent = cat.label;
      label.appendChild(input);
      label.appendChild(span);
      topicStripEl.appendChild(label);
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
            "Choose CHARM section & search text above, then open the manual (new tab)."
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
  if (manualSearchInput) {
    manualSearchInput.addEventListener("input", syncRemoteGoogleSideLinksAndFallback);
  }
  if (charmSectionSel) {
    charmSectionSel.addEventListener("change", () => {
      syncRemoteGoogleSideLinksAndFallback();
      refreshCharmTocUi();
    });
  }

  if (charmTocCopyBm) {
    charmTocCopyBm.addEventListener("click", async () => {
      if (charmTocCopyStatus) charmTocCopyStatus.textContent = "";
      const href = getCharmTocBookmarkletHref();
      try {
        await navigator.clipboard.writeText(href);
        if (charmTocCopyStatus) {
          charmTocCopyStatus.textContent =
            "Copied bookmarklet URL. New bookmark → paste as the link address.";
        }
      } catch {
        window.prompt("Copy this entire line as the bookmark URL:", href);
      }
    });
  }

  if (charmTocApply) {
    charmTocApply.addEventListener("click", () => {
      if (charmTocApplyStatus) charmTocApplyStatus.textContent = "";
      const titles = parseCharmTocPaste(charmTocPaste?.value || "");
      if (!titles.length) {
        if (charmTocApplyStatus) {
          charmTocApplyStatus.textContent =
            "No titles parsed (JSON with titles[] or one title per line).";
        }
        return;
      }
      const bases = getRemoteCharmBasesFromList(listEl);
      if (!bases.length) {
        if (charmTocApplyStatus) {
          charmTocApplyStatus.textContent = "No remote manual in the list yet.";
        }
        return;
      }
      const sk =
        charmSectionSel && !charmSectionSel.disabled ? charmSectionSel.value : "";
      for (const b of bases) {
        saveCharmTocToSession(b, sk, titles);
      }
      const secLabel =
        sk === "repair"
          ? "Repair and Diagnosis"
          : sk === "parts"
            ? "Parts and Labor"
            : "vehicle root";
      if (charmTocApplyStatus) {
        charmTocApplyStatus.textContent = `Saved ${titles.length} title(s) for ${bases.length} URL(s) · ${secLabel}.`;
      }
      refreshCharmTocUi();
    });
  }

  if (charmTocPaste) {
    charmTocPaste.addEventListener("input", () => {
      if (charmTocApplyStatus) charmTocApplyStatus.textContent = "";
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
