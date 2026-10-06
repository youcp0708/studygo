/* insights/static/insights/insights.js
 * 依 <canvas data-chart=...> 的設定畫 Chart.js 圖表。
 *   data-source   對應 json_script 的 id
 *   data-label    標籤欄位
 *   data-value    數值欄位（可用 a.b 取巢狀值）；null（樣本不足）會留空
 *   data-value2   第二組數值（選填）
 *   data-horizontal="1" 橫向長條圖；data-unit 數值後綴
 */
(function () {
  'use strict';
  if (typeof Chart === 'undefined') return;

  var COLORS = ['#579884', '#db6b47', '#e7be67', '#9fd1e6', '#17534d', '#b7a3d6', '#8fb996', '#c9c9c9'];

  function pick(obj, path) {
    return path.split('.').reduce(function (o, k) { return o == null ? null : o[k]; }, obj);
  }

  document.querySelectorAll('canvas[data-chart]').forEach(function (canvas) {
    var source = document.getElementById(canvas.dataset.source);
    if (!source) return;
    var rows = JSON.parse(source.textContent);
    if (!rows.length) {
      canvas.replaceWith(Object.assign(document.createElement('p'), { className: 'ins-muted', textContent: '尚無資料' }));
      return;
    }

    var type = canvas.dataset.chart;
    var unit = canvas.dataset.unit || '';
    // 橫向長條圖一律依筆數決定高度（每列 32px），每個標籤才有足夠空間顯示；
    // 外層 ins-chart-scroll 限制最大高度，筆數多時在框內捲動
    var tall = !!canvas.dataset.horizontal;
    if (tall) {
      var scroller = document.createElement('div');
      scroller.className = 'ins-chart-scroll';
      var wrapper = document.createElement('div');
      wrapper.className = 'ins-chart-tall';
      wrapper.style.height = Math.max(rows.length * 32 + 50, 160) + 'px';
      canvas.parentNode.insertBefore(scroller, canvas);
      scroller.appendChild(wrapper);
      wrapper.appendChild(canvas);
    }
    var labels = rows.map(function (r) { return pick(r, canvas.dataset.label); });
    var datasets = [{
      label: canvas.dataset.valueName || '',
      data: rows.map(function (r) { return pick(r, canvas.dataset.value); }),
      backgroundColor: type === 'doughnut' ? COLORS : COLORS[0],
      borderColor: type === 'line' ? COLORS[0] : undefined,
      spanGaps: true,
    }];
    if (canvas.dataset.value2) {
      datasets.push({
        label: canvas.dataset.value2Name || '',
        data: rows.map(function (r) { return pick(r, canvas.dataset.value2); }),
        backgroundColor: COLORS[1],
        borderColor: type === 'line' ? COLORS[1] : undefined,
        spanGaps: true,
      });
    }

    new Chart(canvas, {
      type: type,
      data: { labels: labels, datasets: datasets },
      options: {
        indexAxis: canvas.dataset.horizontal ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: !tall,
        plugins: {
          legend: { display: type === 'doughnut' || datasets.length > 1 },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var v = ctx.raw;
                var name = ctx.dataset.label ? ctx.dataset.label + '：' : (type === 'doughnut' ? ctx.label + '：' : '');
                return name + (v == null ? '樣本不足' : v + unit);
              },
            },
          },
        },
        scales: type === 'doughnut' ? {} : {
          // autoSkip: false：標籤再多也全部顯示，不讓 Chart.js 自動略過
          x: { beginAtZero: true, ticks: { autoSkip: false } },
          y: { beginAtZero: true, ticks: { autoSkip: false, font: { size: 13 } } },
        },
      },
    });
  });
})();
