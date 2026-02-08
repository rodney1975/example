/* ==========================================================================
   Chart Rendering — Plotly.js
   Each function takes a container element ID and the relevant dataset,
   then draws or updates the corresponding Plotly chart.
   ========================================================================== */

(() => {
  'use strict';

  // ---- Colour palette (matches dashboard theme) ----
  const COLORS = {
    rose:    '#e94560',
    navy:    '#0f3460',
    purple:  '#533483',
    teal:    '#48c9b0',
    amber:   '#f39c12',
  };

  // ---- Shared Plotly layout defaults ----
  const baseLayout = () => ({
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor:  'rgba(0,0,0,0)',
    font: {
      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      color:  '#e0e0e0',
      size:   12,
    },
    margin: { t: 30, r: 25, b: 50, l: 55 },
    xaxis: {
      gridcolor:  'rgba(255,255,255,0.08)',
      zerolinecolor: 'rgba(255,255,255,0.12)',
      color: '#e0e0e0',
    },
    yaxis: {
      gridcolor:  'rgba(255,255,255,0.08)',
      zerolinecolor: 'rgba(255,255,255,0.12)',
      color: '#e0e0e0',
    },
  });

  const plotConfig = { responsive: true, displayModeBar: false };

  // ---- Helpers ----

  /**
   * Safely get a DOM container element.  Returns null and logs a warning
   * if the element does not exist.
   */
  function getContainer(containerId) {
    const el = document.getElementById(containerId);
    if (!el) {
      console.warn(`[charts] Container #${containerId} not found.`);
    }
    return el;
  }

  // =====================================================================
  //  1. Velocity Profile — line chart over rep numbers
  // =====================================================================

  /**
   * @param {string}  containerId   DOM id of the target div
   * @param {Array}   strokesData   Array of stroke metric objects.  Each must
   *                                include rep_number, avg_velocity, peak_velocity.
   */
  function renderVelocityProfile(containerId, strokesData) {
    const el = getContainer(containerId);
    if (!el || !Array.isArray(strokesData) || strokesData.length === 0) return;

    const reps  = strokesData.map((s) => s.rep_number);
    const avgV  = strokesData.map((s) => s.avg_velocity);
    const peakV = strokesData.map((s) => s.peak_velocity);

    const traces = [
      {
        x: reps,
        y: avgV,
        name: 'Avg Velocity',
        mode: 'lines+markers',
        line:   { color: COLORS.teal, width: 2.5 },
        marker: { color: COLORS.teal, size: 5 },
      },
      {
        x: reps,
        y: peakV,
        name: 'Peak Velocity',
        mode: 'lines+markers',
        line:   { color: COLORS.rose, width: 2.5, dash: 'dot' },
        marker: { color: COLORS.rose, size: 5 },
      },
    ];

    const layout = {
      ...baseLayout(),
      xaxis: { ...baseLayout().xaxis, title: 'Rep Number' },
      yaxis: { ...baseLayout().yaxis, title: 'Velocity (m/s)' },
      legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
    };

    Plotly.newPlot(el, traces, layout, plotConfig);
  }

  // =====================================================================
  //  2. Force-Velocity Scatter with trend line
  // =====================================================================

  /**
   * @param {string}  containerId
   * @param {Array}   fvData   Array of { velocity, force } objects.
   */
  function renderForceVelocity(containerId, fvData) {
    const el = getContainer(containerId);
    if (!el || !Array.isArray(fvData) || fvData.length === 0) return;

    const velocities = fvData.map((d) => d.velocity);
    const forces     = fvData.map((d) => d.force);

    // Simple linear regression for trend line
    const n     = velocities.length;
    const sumX  = velocities.reduce((a, b) => a + b, 0);
    const sumY  = forces.reduce((a, b) => a + b, 0);
    const sumXY = velocities.reduce((acc, v, i) => acc + v * forces[i], 0);
    const sumX2 = velocities.reduce((acc, v) => acc + v * v, 0);

    const denom = n * sumX2 - sumX * sumX;
    let slope = 0;
    let intercept = sumY / n;
    if (denom !== 0) {
      slope     = (n * sumXY - sumX * sumY) / denom;
      intercept = (sumY - slope * sumX) / n;
    }

    const minV = Math.min(...velocities);
    const maxV = Math.max(...velocities);
    const trendX = [minV, maxV];
    const trendY = trendX.map((x) => slope * x + intercept);

    const traces = [
      {
        x: velocities,
        y: forces,
        mode: 'markers',
        name: 'Data',
        marker: { color: COLORS.purple, size: 9, opacity: 0.85 },
      },
      {
        x: trendX,
        y: trendY,
        mode: 'lines',
        name: 'Trend',
        line: { color: COLORS.amber, width: 2, dash: 'dash' },
      },
    ];

    const layout = {
      ...baseLayout(),
      xaxis: { ...baseLayout().xaxis, title: 'Velocity (m/s)' },
      yaxis: { ...baseLayout().yaxis, title: 'Force (N)' },
      legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
    };

    Plotly.newPlot(el, traces, layout, plotConfig);
  }

  // =====================================================================
  //  3. Power Output per Stroke — grouped bar chart
  // =====================================================================

  /**
   * @param {string}  containerId
   * @param {Array}   strokesData   Array with rep_number, avg_power, peak_power.
   */
  function renderPowerChart(containerId, strokesData) {
    const el = getContainer(containerId);
    if (!el || !Array.isArray(strokesData) || strokesData.length === 0) return;

    const reps  = strokesData.map((s) => `Rep ${s.rep_number}`);
    const avgP  = strokesData.map((s) => s.avg_power);
    const peakP = strokesData.map((s) => s.peak_power);

    const traces = [
      {
        x: reps,
        y: avgP,
        name: 'Avg Power',
        type: 'bar',
        marker: { color: COLORS.navy },
      },
      {
        x: reps,
        y: peakP,
        name: 'Peak Power',
        type: 'bar',
        marker: { color: COLORS.rose },
      },
    ];

    const layout = {
      ...baseLayout(),
      barmode: 'group',
      xaxis: { ...baseLayout().xaxis, title: 'Stroke' },
      yaxis: { ...baseLayout().yaxis, title: 'Power (W)' },
      legend: { orientation: 'h', y: -0.25, x: 0.5, xanchor: 'center' },
    };

    Plotly.newPlot(el, traces, layout, plotConfig);
  }

  // =====================================================================
  //  4. Stroke Phase Breakdown — donut chart
  // =====================================================================

  /**
   * @param {string}  containerId
   * @param {Object}  phaseData   Dict of { phase_name: time_proportion }.
   *                              Expected keys: Catch, Pull, Push, Recovery, Glide
   */
  function renderPhaseBreakdown(containerId, phaseData) {
    const el = getContainer(containerId);
    if (!el || !phaseData || typeof phaseData !== 'object') return;

    const labels = Object.keys(phaseData);
    const values = Object.values(phaseData);

    const colorMap = [COLORS.rose, COLORS.navy, COLORS.purple, COLORS.teal, COLORS.amber];

    const traces = [
      {
        labels,
        values,
        type: 'pie',
        hole: 0.45,
        marker: {
          colors: colorMap.slice(0, labels.length),
          line: { color: '#16213e', width: 2 },
        },
        textinfo: 'label+percent',
        textfont: { color: '#e0e0e0', size: 12 },
        hoverinfo: 'label+value+percent',
        sort: false,
      },
    ];

    const layout = {
      ...baseLayout(),
      showlegend: true,
      legend: {
        orientation: 'h',
        y: -0.1,
        x: 0.5,
        xanchor: 'center',
        font: { color: '#e0e0e0' },
      },
      margin: { t: 20, r: 20, b: 40, l: 20 },
    };

    Plotly.newPlot(el, traces, layout, plotConfig);
  }

  // ---- Expose on window ----
  window.charts = {
    renderVelocityProfile,
    renderForceVelocity,
    renderPowerChart,
    renderPhaseBreakdown,
    COLORS,
  };
})();
