"use strict";

const cdnBase = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
const form = document.getElementById("simulation-form");
const runButton = document.getElementById("run");
const saveButton = document.getElementById("save");
const statusEl = document.getElementById("runtime-status");
const outcome = document.getElementById("outcome");
const details = document.getElementById("details");
const output = document.getElementById("results");
let pyodidePromise = null;
let lastResult = null;

function setStatus(message) {
  statusEl.textContent = message;
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = resolve;
    script.onerror = () => reject(new Error("Unable to download the Python browser runtime"));
    document.head.appendChild(script);
  });
}

async function initializeRuntime() {
  await loadScript(cdnBase + "pyodide.js");
  if (typeof window.loadPyodide !== "function") {
    throw new Error("Pyodide loader is not available");
  }
  const py = await window.loadPyodide({ indexURL: cdnBase });
  const sourceUrl = new URL("qkd_bb84_engine/engine.py", document.baseURI);
  const response = await fetch(sourceUrl);
  if (!response.ok) {
    throw new Error("Unable to load the repository's BB84 engine (" + response.status + ")");
  }
  py.globals.set("_bb84_source", await response.text());
  await py.runPythonAsync(
    "import sys, types\n" +
    "_bb84_module = types.ModuleType('bb84_browser_engine')\n" +
    "exec(_bb84_source, _bb84_module.__dict__)\n" +
    "sys.modules['bb84_browser_engine'] = _bb84_module\n"
  );
  return py;
}

function getParams() {
  const n_qubits = Number(document.getElementById("qubits").value);
  const noise_prob = Number(document.getElementById("noise").value);
  const seed = Number(document.getElementById("seed").value);
  if (!Number.isSafeInteger(n_qubits) || n_qubits < 20 || n_qubits > 20000) {
    throw new Error("Qubit count must be an integer from 20 to 20,000");
  }
  if (!Number.isFinite(noise_prob) || noise_prob < 0 || noise_prob > 1) {
    throw new Error("Noise probability must be between 0 and 1");
  }
  if (!Number.isSafeInteger(seed)) {
    throw new Error("Seed must be a safe integer");
  }
  return {
    n_qubits,
    noise_prob,
    seed,
    eavesdrop: document.getElementById("eavesdrop").checked
  };
}

function render(result) {
  lastResult = result;
  const pct = (result.qber * 100).toFixed(2);
  document.getElementById("qber").textContent =
    result.parameter_estimation_possible ? pct + "%" : "Not estimated";
  document.getElementById("matching").textContent = String(result.matching_bases);
  document.getElementById("sample").textContent = String(result.sample_size);
  document.getElementById("key-length").textContent = String(result.final_key_length);
  const estimate = result.parameter_estimation_possible
    ? result.errors_found + " errors in " + result.sample_size + " disclosed sample bits"
    : "Too few sifted bits for error estimation";
  outcome.textContent = result.aborted
    ? "No key produced: " + result.abort_reason
    : "Demonstration output produced (not a cryptographically secure key)";
  outcome.className = result.aborted ? "warning" : "success";
  details.textContent =
    "Bases matched: " + result.matching_bases + " / " + result.n_qubits + " transmitted. " +
    "QBER: " + estimate + ". " +
    (result.eavesdrop_detected
      ? "Estimated QBER exceeds the illustrative 11% cutoff. "
      : "No QBER threshold exceedance was detected. This does not prove channel security. ") +
    "The model omits authentication, reconciliation, and finite-key security analysis.";
  const showKey = document.getElementById("show-key").checked;
  const summary = {
    transmitted_qubits: result.n_qubits,
    sifted_bits: result.sifted_key_length,
    disclosed_sample_bits: result.sample_size,
    observed_qber: result.parameter_estimation_possible ? result.qber : null,
    eavesdrop_detected: result.eavesdrop_detected,
    aborted: result.aborted,
    abort_reason: result.abort_reason,
    output_length: result.final_key_length,
    keys_match: result.keys_match
  };
  if (showKey && !result.aborted) {
    summary.demonstration_key_alice = result.final_key_alice.join("");
    summary.demonstration_key_bob = result.final_key_bob.join("");
  }
  output.textContent = JSON.stringify(summary, null, 2);
  saveButton.disabled = false;
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  runButton.disabled = true;
  saveButton.disabled = true;
  lastResult = null;
  try {
    const params = getParams();
    setStatus("Loading Python runtime and BB84 engine…");
    if (!pyodidePromise) {
      pyodidePromise = initializeRuntime().catch(error => {
        pyodidePromise = null;
        throw error;
      });
    }
    const py = await pyodidePromise;
    setStatus("Simulating BB84 states and measurements…");
    py.globals.set("_bb84_params", JSON.stringify(params));
    const serialized = await py.runPythonAsync(
      "import json\n" +
      "json.dumps(__import__('bb84_browser_engine').bb84_protocol(**json.loads(_bb84_params)))"
    );
    render(JSON.parse(serialized));
    setStatus("Simulation complete — all calculations ran in this browser");
  } catch (error) {
    outcome.className = "warning";
    outcome.textContent = "Simulation unavailable";
    details.textContent = error instanceof Error ? error.message : String(error);
    output.textContent = "No result was produced.";
    setStatus("Runtime error — retry or use the Python CLI");
  } finally {
    runButton.disabled = false;
  }
});

document.getElementById("show-key").addEventListener("change", () => {
  if (lastResult) render(lastResult);
});

saveButton.addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "bb84-simulation.json";
  anchor.click();
  URL.revokeObjectURL(url);
});