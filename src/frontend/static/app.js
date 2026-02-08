/* ==========================================================================
   App.js — Main Application Logic
   Coordinates data fetching, state management, and chart rendering for the
   Swimming Biomechanics Dashboard.
   ========================================================================== */

(() => {
  'use strict';

  // ---- Configuration ----
  const API_BASE = '/api';

  // ---- State ----
  let currentSession = null;

  // ---- API helpers ----

  /**
   * Fetch JSON from a URL.  Throws on non-OK responses.
   */
  async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`API error ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  // ---- Session list ----

  /**
   * Fetch available sessions and populate the dropdown.
   */
  async function loadSessions() {
    const dropdown = document.getElementById('session-dropdown');
    if (!dropdown) return;

    try {
      const sessions = await fetchJSON(`${API_BASE}/sessions`);

      // Clear existing options beyond the placeholder
      while (dropdown.options.length > 1) {
        dropdown.remove(1);
      }

      if (Array.isArray(sessions)) {
        sessions.forEach((filename) => {
          const opt = document.createElement('option');
          opt.value = filename;
          opt.textContent = filename;
          dropdown.appendChild(opt);
        });
      }
    } catch (err) {
      console.error('[app] Failed to load sessions:', err);
      window.dashboard.showError('Could not load session list. Is the API server running?');
    }
  }

  // ---- Session loading ----

  /**
   * Load a session by filename: fetch all endpoints in parallel, then
   * update the dashboard summary and render all four charts.
   */
  async function loadSession(filename) {
    if (!filename) {
      window.dashboard.resetSummaryStats();
      clearCharts();
      currentSession = null;
      return;
    }

    window.dashboard.hideError();
    window.dashboard.showLoading();

    try {
      // Fire all four requests concurrently
      const [summary, strokes, forceVelocity, phases] = await Promise.all([
        fetchJSON(`${API_BASE}/sessions/${encodeURIComponent(filename)}`),
        fetchJSON(`${API_BASE}/sessions/${encodeURIComponent(filename)}/strokes`),
        fetchJSON(`${API_BASE}/sessions/${encodeURIComponent(filename)}/force-velocity`),
        fetchJSON(`${API_BASE}/sessions/${encodeURIComponent(filename)}/phase-breakdown`),
      ]);

      currentSession = filename;

      // Summary stats
      window.dashboard.updateSummaryStats(summary);

      // Charts
      window.charts.renderVelocityProfile('chart-velocity', strokes);
      window.charts.renderForceVelocity('chart-force-velocity', forceVelocity);
      window.charts.renderPowerChart('chart-power', strokes);
      window.charts.renderPhaseBreakdown('chart-phase', phases);

    } catch (err) {
      console.error('[app] Failed to load session data:', err);
      window.dashboard.showError(`Error loading session "${filename}": ${err.message}`);
      window.dashboard.resetSummaryStats();
      clearCharts();
    } finally {
      window.dashboard.hideLoading();
    }
  }

  /**
   * Purge all four chart containers.
   */
  function clearCharts() {
    const ids = ['chart-velocity', 'chart-force-velocity', 'chart-power', 'chart-phase'];
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el && typeof Plotly !== 'undefined') {
        Plotly.purge(el);
      }
    });
  }

  // ---- Event wiring ----

  /**
   * Initialise the application once the DOM is ready.
   */
  function init() {
    const dropdown = document.getElementById('session-dropdown');
    if (dropdown) {
      dropdown.addEventListener('change', (e) => {
        loadSession(e.target.value);
      });
    }

    loadSessions();
  }

  // Auto-init on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', init);

  // ---- Public API (for tests and external use) ----
  window.app = {
    loadSessions,
    loadSession,
    clearCharts,
    fetchJSON,
    init,
    getCurrentSession: () => currentSession,
  };
})();
