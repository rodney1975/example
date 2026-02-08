/* ==========================================================================
   Dashboard Layout Management
   Handles summary stats, loading overlay, and error banner.
   ========================================================================== */

(() => {
  'use strict';

  // ---- DOM references ----
  const els = {
    loadingOverlay: () => document.getElementById('loading-overlay'),
    errorBanner:    () => document.getElementById('error-banner'),
    errorMessage:   () => document.getElementById('error-message'),
    errorClose:     () => document.getElementById('error-close'),

    statTotalReps:      () => document.getElementById('stat-value-total-reps'),
    statTotalDistance:   () => document.getElementById('stat-value-total-distance'),
    statAvgStrokeRate:  () => document.getElementById('stat-value-avg-stroke-rate'),
    statAvgStrokeLength:() => document.getElementById('stat-value-avg-stroke-length'),
  };

  // ---- Formatting helpers ----

  /**
   * Format a number for display.  Falls back to an em-dash when the value is
   * null / undefined / NaN.
   */
  const fmt = (value, decimals = 1) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return '\u2014';           // em-dash
    }
    return Number(value).toFixed(decimals);
  };

  // ---- Public API ----

  /**
   * Populate the four summary stat cards from a session summary object.
   *
   * Expected shape:
   *   { total_reps, total_distance, avg_stroke_rate, avg_stroke_length, ... }
   */
  function updateSummaryStats(sessionData) {
    if (!sessionData) return;

    const repEl = els.statTotalReps();
    const distEl = els.statTotalDistance();
    const rateEl = els.statAvgStrokeRate();
    const lenEl = els.statAvgStrokeLength();

    if (repEl) {
      repEl.textContent = sessionData.total_reps != null
        ? String(sessionData.total_reps)
        : '\u2014';
    }
    if (distEl) {
      distEl.textContent = fmt(sessionData.total_distance, 1);
    }
    if (rateEl) {
      rateEl.textContent = fmt(sessionData.avg_stroke_rate, 1);
    }
    if (lenEl) {
      lenEl.textContent = fmt(sessionData.avg_stroke_length, 2);
    }
  }

  /**
   * Reset all stat cards to placeholder dashes.
   */
  function resetSummaryStats() {
    const dash = '\u2014';
    const ids = [
      els.statTotalReps,
      els.statTotalDistance,
      els.statAvgStrokeRate,
      els.statAvgStrokeLength,
    ];
    ids.forEach((fn) => {
      const el = fn();
      if (el) el.textContent = dash;
    });
  }

  /**
   * Show the full-screen loading overlay.
   */
  function showLoading() {
    const overlay = els.loadingOverlay();
    if (overlay) overlay.classList.remove('hidden');
  }

  /**
   * Hide the loading overlay.
   */
  function hideLoading() {
    const overlay = els.loadingOverlay();
    if (overlay) overlay.classList.add('hidden');
  }

  /**
   * Display an error message in the top banner.
   */
  function showError(message) {
    const banner = els.errorBanner();
    const msgEl  = els.errorMessage();
    if (banner && msgEl) {
      msgEl.textContent = message;
      banner.classList.remove('hidden');
    }
  }

  /**
   * Hide the error banner.
   */
  function hideError() {
    const banner = els.errorBanner();
    if (banner) banner.classList.add('hidden');
  }

  // Wire up the close button on the error banner.
  document.addEventListener('DOMContentLoaded', () => {
    const closeBtn = els.errorClose();
    if (closeBtn) {
      closeBtn.addEventListener('click', hideError);
    }
  });

  // ---- Expose on window ----
  window.dashboard = {
    updateSummaryStats,
    resetSummaryStats,
    showLoading,
    hideLoading,
    showError,
    hideError,
  };
})();
