
// Global State
let currentLang = 'ko'; // 'ko' or 'en'
let currentModel = 'gemini'; // 'gemini' or 'gpt'
let usStockChart = null;
let usCandleSeries = null;
let usVolumeSeries = null;
let currentChartTicker = null;
let currentChartPeriod = '1y';
let activeTab = '🇺🇸 US Market';
let chartResizeObserver = null;

// Indicator State
let indicatorState = { bb: false, sr: false, rsi: false, macd: false };
let indicatorData = null; // Cache for current ticker's indicators

// Indicator Series References
let bbUpperSeries, bbMiddleSeries, bbLowerSeries;
let srLines = [];
let rsiChart, rsiSeries;
let macdChart, macdLineSeries, macdSignalSeries, macdHistSeries;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Date Picker for Smart Money History
    // We can fetch available dates first
    loadUSHistoryDates();

    // Initial Load
    updateUSMarketDashboard();

    // Start Real-time Price Updates (every 10s for faster feel)
    setInterval(updateRealtimePrices, 10000);

    // Start Macro Analysis Refresh (every 5 min)
    setInterval(reloadMacroAnalysis, 300000);

    // Tab Switching Logic
    window.switchMarketTab = function (tabEl, tabName) {
        // Update visual state
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        tabEl.classList.add('active');
        activeTab = tabName;

        // Hide/Show Content Areas
        const usContent = document.getElementById('content-us-market');
        const calendarContent = document.getElementById('content-economic-calendar');

        if (tabName === '🇺🇸 US Market') {
            usContent.classList.remove('hidden');
            calendarContent.classList.add('hidden');
            updateUSMarketDashboard(); // Refresh data when switching back
        } else if (tabName === 'Economic Calendar') {
            usContent.classList.add('hidden');
            calendarContent.classList.remove('hidden');
            renderUSCalendar(); // Load calendar data
        }
    };

    // Language Toggle
    const langBtns = document.querySelectorAll('#lang-toggle button');
    langBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const lang = e.target.dataset.lang;
            if (lang && lang !== currentLang) {
                currentLang = lang;
                // Update UI Buttons
                langBtns.forEach(b => {
                    if (b.dataset.lang === lang) {
                        b.classList.remove('text-gray-400', 'hover:text-white');
                        b.classList.add('bg-blue-600', 'text-white');
                    } else {
                        b.classList.add('text-gray-400', 'hover:text-white');
                        b.classList.remove('bg-blue-600', 'text-white');
                    }
                });
                translateUI();
                updateUSMarketDashboard(); // Reload content with new lang
            }
        });
    });

    // AI Model Toggle
    const modelBtns = document.querySelectorAll('#model-toggle button');
    modelBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const model = e.target.dataset.model;
            if (model && model !== currentModel) {
                currentModel = model;
                // Update UI Buttons
                modelBtns.forEach(b => {
                    if (b.dataset.model === model) {
                        b.classList.remove('text-gray-400', 'hover:text-white');
                        b.classList.add(model === 'gemini' ? 'bg-purple-600' : 'bg-green-600', 'text-white');
                    } else {
                        b.classList.add('text-gray-400', 'hover:text-white');
                        b.classList.remove('bg-purple-600', 'bg-green-600', 'text-white');
                    }
                });
                // Update Label
                const label = document.getElementById('macro-model-label');
                if (label) label.innerText = model === 'gemini' ? 'Gemini 3.0 매크로 분석' : 'GPT-5.2 매크로 분석';

                reloadMacroAnalysis();
            }
        });
    });

    // Chart Period Buttons
    const periodBtns = document.querySelectorAll('#us-chart-period-btns button');
    periodBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const period = e.target.dataset.period;
            if (period) {
                currentChartPeriod = period;
                // Update styling
                periodBtns.forEach(b => {
                    if (b.dataset.period === period) {
                        b.classList.remove('bg-gray-700', 'text-gray-300', 'hover:bg-blue-600');
                        b.classList.add('bg-blue-600', 'text-white');
                    } else {
                        b.classList.add('bg-gray-700', 'text-gray-300', 'hover:bg-blue-600');
                        b.classList.remove('bg-blue-600', 'text-white');
                    }
                });
                if (currentChartTicker) loadUSStockChart(currentChartTicker, null, period);
            }
        });
    });
});

// --- Core Logic ---

async function updateUSMarketDashboard() {
    console.log("Updating US Dashboard...");
    // Run in parallel for speed
    Promise.all([
        fetch('/api/us/portfolio').then(r => r.json()).then(renderUSMarketIndices).catch(e => console.error(e)),
        fetch('/api/us/smart-money').then(r => r.json()).then(renderUSSmartMoneyPicks).catch(e => console.error(e)),
        fetch('/api/us/etf-flows').then(r => r.json()).then(renderUSETFFlows).catch(e => console.error(e)),
        fetch('/api/us/options-flow').then(r => r.json()).then(renderUSOptionsFlow).catch(e => console.error(e)),
        fetch(`/api/us/macro-analysis?lang=${currentLang}&model=${currentModel}`).then(r => r.json()).then(renderUSMacroAnalysis).catch(e => console.error(e)),
        fetch('/api/us/sector-heatmap').then(r => r.json()).then(renderUSSectorHeatmap).catch(e => console.error(e))
    ]);
}

async function reloadMacroAnalysis() {
    try {
        const res = await fetch(`/api/us/macro-analysis?lang=${currentLang}&model=${currentModel}`);
        const data = await res.json();
        renderUSMacroAnalysis(data);
    } catch (e) {
        console.error("Error reloading macro analysis:", e);
    }
}

async function loadUSHistoryDates() {
    try {
        const res = await fetch('/api/us/history-dates');
        const data = await res.json();
        const select = document.getElementById('us-history-date-select');
        if (data.dates && select) {
            select.innerHTML = '<option value="">📅 날짜 선택</option>';
            data.dates.forEach(date => {
                const opt = document.createElement('option');
                opt.value = date;
                opt.innerText = date;
                select.appendChild(opt);
            });
        }
    } catch (e) { console.error(e); }
}

async function loadUSHistoryByDate(date) {
    if (!date) {
        // If empty, reload current smart money
        fetch('/api/us/smart-money').then(r => r.json()).then(renderUSSmartMoneyPicks);
        return;
    }
    try {
        const res = await fetch(`/api/us/history/${date}`);
        const data = await res.json();
        renderUSSmartMoneyPicks(data);
    } catch (e) {
        console.error("Error loading history:", e);
        alert("해당 날짜의 데이터를 불러올 수 없습니다.");
    }
}

// --- Rendering Functions ---

function renderUSMarketIndices(data) {
    const container = document.getElementById('us-market-indices-container');
    if (!container || !data.market_indices) return;

    container.innerHTML = '';
    data.market_indices.forEach(idx => {
        const div = document.createElement('div');
        div.className = 'bg-[#1a1a1a] border border-[#2a2a2a] rounded p-3 flex flex-col items-center justify-center hover:bg-[#252525] transition-colors';

        // Color Logic
        const colorClass = idx.color === 'green' ? 'text-green-400' : (idx.color === 'red' ? 'text-red-400' : 'text-gray-400');
        const sign = idx.change_pct > 0 ? '+' : '';

        div.innerHTML = `
                      <span class="text-xs text-gray-400 mb-1">${idx.name}</span>
                      <span class="text-lg font-bold text-white mb-1">${idx.price}</span>
                      <span class="text-xs font-medium ${colorClass}">${idx.change} (${sign}${idx.change_pct}%)</span>
                  `;
        container.appendChild(div);
    });
}

async function renderUSSmartMoneyPicks(data) {
    const tbody = document.getElementById('us-smart-money-table');
    const summaryEl = document.getElementById('us-smart-money-summary');

    if (!tbody) return;
    tbody.innerHTML = '';

    const picks = data.top_picks || [];
    if (summaryEl && data.summary) {
        const perfText = data.summary.avg_performance ? `Avg Return: ${data.summary.avg_performance}%` : `Avg Score: ${data.summary.avg_score}`;
        summaryEl.innerText = `${data.summary.total_analyzed ? data.summary.total_analyzed + ' stocks analyzed' : ''} | ${perfText}`;
    }

    if (picks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="p-4 text-center text-gray-500">No picks available.</td></tr>';
        return;
    }

    // Load chart for top pick automatically if waiting
    if (!currentChartTicker && picks.length > 0) {
        loadUSStockChart(picks[0], 0, currentChartPeriod);
    }

    picks.forEach((pick, index) => {
        const tr = document.createElement('tr');
        tr.className = 'border-b border-[#2a2a2a] hover:bg-[#252525] transition-colors cursor-pointer group';
        // Highlight active row could be added here
        tr.onclick = () => loadUSStockChart(pick, index, currentChartPeriod);

        // Data processing
        const score = pick.final_score !== undefined ? pick.final_score : (pick.composite_score || 0);
        const upside = pick.target_upside || 0;
        const change = pick.change_since_rec || 0;

        // Colors
        const changeClass = change > 0 ? 'text-green-400' : (change < 0 ? 'text-red-400' : 'text-gray-400');
        const upsideClass = upside > 20 ? 'text-purple-400 font-bold' : 'text-blue-400';

        tr.innerHTML = `
                      <td class="p-2 text-gray-500 text-xs">${index + 1}</td>
                      <td class="p-2">
                          <div class="flex flex-col">
                              <span class="font-bold text-blue-400 group-hover:text-blue-300">${pick.ticker}</span>
                              <span class="text-[10px] text-gray-500">${pick.name || ''}</span>
                          </div>
                      </td>
                      <td class="p-2 text-center text-xs text-gray-300">${pick.sector || '-'}</td>
                      <td class="p-2 text-center text-yellow-400 font-bold text-xs">${score.toFixed(1)}</td>
                      <td class="p-2 text-center text-xs">
                          <span class="px-2 py-0.5 rounded-full bg-indigo-900 text-indigo-200 border border-indigo-700/50">${pick.category || 'Buy'}</span>
                      </td>
                      <td class="p-2 text-center text-xs text-gray-400">$${pick.price_at_rec || '-'}</td>
                      <td class="p-2 text-center text-xs font-mono text-white">$${pick.current_price || '-'}</td>
                      <td class="p-2 text-center text-xs font-mono ${changeClass}">${change > 0 ? '+' : ''}${change}%</td>
                      <td class="p-2 text-center text-xs font-mono ${upsideClass}">${upside > 0 ? '+' : ''}${upside}%</td>
                 `;
        tbody.appendChild(tr);
    });
}

// --- Charting Logic ---

async function loadUSStockChart(pick, idx, period = '1y') {
    // pick can be object or just ticker string
    const ticker = typeof pick === 'string' ? pick : pick.ticker;
    currentChartTicker = ticker;

    const container = document.getElementById('us-stock-chart');
    const tickerLabel = document.getElementById('us-chart-ticker');
    const infoLabel = document.getElementById('us-chart-info');

    if (tickerLabel) tickerLabel.innerText = ticker;
    if (infoLabel) infoLabel.innerText = pick.name ? `${pick.name} (${pick.sector})` : 'Loading...';

    // Reset indicators
    indicatorData = null;

    // --- Load Main Chart Data ---
    try {
        const res = await fetch(`/api/us/stock-chart/${ticker}?period=${period}`);
        const data = await res.json();

        if (data.error) {
            console.error("Chart data error:", data.error);
            return;
        }

        // Create Chart if not exists
        if (!usStockChart) {
            container.innerHTML = ''; // Clear icon
            usStockChart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 300,
                layout: { backgroundColor: '#1a1a1a', textColor: '#d1d5db' },
                grid: { vertLines: { color: '#2a2a2a' }, horzLines: { color: '#2a2a2a' } },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
                rightPriceScale: { borderColor: '#2a2a2a' },
                timeScale: { borderColor: '#2a2a2a', timeVisible: true }
            });

            usCandleSeries = usStockChart.addCandlestickSeries({
                upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350'
            });

            // Resize Observer
            new ResizeObserver(entries => {
                if (entries.length === 0 || !entries[0].contentRect) return;
                const rect = entries[0].contentRect;
                usStockChart.applyOptions({ width: rect.width, height: rect.height });
            }).observe(container);
        }

        usCandleSeries.setData(data.candles);
        usStockChart.timeScale().fitContent();

        // Load AI Summary for this stock
        loadUSAISummary(ticker);

        // Load Technical Indicators (Background)
        loadTechnicalIndicators(ticker, period);

    } catch (e) {
        console.error("Error loading chart:", e);
    }
}

async function loadTechnicalIndicators(ticker, period) {
    try {
        const res = await fetch(`/api/us/technical-indicators/${ticker}?period=${period}`);
        indicatorData = await res.json();

        // Re-render active indicators
        if (indicatorState.bb) renderBollingerBands();
        if (indicatorState.sr) renderSupportResistance();
        if (indicatorState.rsi) renderRSI();
        if (indicatorState.macd) renderMACD();

    } catch (e) {
        console.error("Technical indicators error:", e);
    }
}

function toggleIndicator(type) {
    indicatorState[type] = !indicatorState[type];
    const btn = document.getElementById(`toggle-${type}`);

    // Toggle Button Visual
    if (indicatorState[type]) {
        btn.classList.add('ring-2', 'ring-white');
    } else {
        btn.classList.remove('ring-2', 'ring-white');
    }

    // Logic
    if (!indicatorData && currentChartTicker) return; // Will load eventually

    if (type === 'bb') renderBollingerBands();
    else if (type === 'sr') renderSupportResistance();
    else if (type === 'rsi') renderRSI();
    else if (type === 'macd') renderMACD();
}

function renderBollingerBands() {
    if (!usStockChart) return;
    // Remove existing
    if (bbUpperSeries) { usStockChart.removeSeries(bbUpperSeries); bbUpperSeries = null; }
    if (bbMiddleSeries) { usStockChart.removeSeries(bbMiddleSeries); bbMiddleSeries = null; }
    if (bbLowerSeries) { usStockChart.removeSeries(bbLowerSeries); bbLowerSeries = null; }

    if (indicatorState.bb && indicatorData?.bollinger) {
        bbUpperSeries = usStockChart.addLineSeries({ color: 'rgba(147, 51, 234, 0.5)', lineWidth: 1, lastValueVisible: false });
        bbMiddleSeries = usStockChart.addLineSeries({ color: 'rgba(147, 51, 234, 0.8)', lineWidth: 1, lineStyle: 2, lastValueVisible: false });
        bbLowerSeries = usStockChart.addLineSeries({ color: 'rgba(147, 51, 234, 0.5)', lineWidth: 1, lastValueVisible: false });

        bbUpperSeries.setData(indicatorData.bollinger.upper);
        bbMiddleSeries.setData(indicatorData.bollinger.middle);
        bbLowerSeries.setData(indicatorData.bollinger.lower);
    }
}

function renderSupportResistance() {
    if (!usStockChart) return;
    // Remove existing
    srLines.forEach(l => usStockChart.removeSeries(l));
    srLines = [];

    if (indicatorState.sr && indicatorData?.support_resistance) {
        // Determine start/end time for horizontal lines
        // We'll just define lines across the visible chart area basically? 
        // Lightweight charts PriceLines are infinite horizontal lines attached to axis, but we want segments?
        // Actually easier to just use PriceLines on the CandleSeries if we want infinite, 
        // OR use LineSeries with 2 points for segments. Let's use LineSeries for visual control.

        // Need time range
        if (indicatorData.rsi && indicatorData.rsi.length > 0) {
            const t1 = indicatorData.rsi[0].time;
            const t2 = indicatorData.rsi[indicatorData.rsi.length - 1].time;

            indicatorData.support_resistance.support.forEach(val => {
                const l = usStockChart.addLineSeries({ color: '#22c55e', lineWidth: 1, lineStyle: 2, lastValueVisible: true, priceLineVisible: false });
                l.setData([{ time: t1, value: val }, { time: t2, value: val }]);
                srLines.push(l);
            });

            indicatorData.support_resistance.resistance.forEach(val => {
                const l = usStockChart.addLineSeries({ color: '#ef4444', lineWidth: 1, lineStyle: 2, lastValueVisible: true, priceLineVisible: false });
                l.setData([{ time: t1, value: val }, { time: t2, value: val }]);
                srLines.push(l);
            });
        }
    }
}

function renderRSI() {
    const container = document.getElementById('us-rsi-chart');
    if (indicatorState.rsi && indicatorData?.rsi) {
        container.classList.remove('hidden');
        if (!rsiChart) {
            container.innerHTML = '';
            rsiChart = LightweightCharts.createChart(container, {
                width: container.clientWidth, height: 80,
                layout: { backgroundColor: '#1a1a1a', textColor: '#666' },
                grid: { vertLines: { visible: false }, horzLines: { color: '#2a2a2a' } },
                timeScale: { visible: false },
                rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }
            });
            rsiSeries = rsiChart.addLineSeries({ color: '#a855f7', lineWidth: 1 });

            // Levels 70/30
            const top = rsiChart.addLineSeries({ color: '#ef4444', lineWidth: 1, lineStyle: 2 });
            const bot = rsiChart.addLineSeries({ color: '#22c55e', lineWidth: 1, lineStyle: 2 });

            // We need data points to draw lines
            const d = indicatorData.rsi;
            if (d.length > 0) {
                top.setData([{ time: d[0].time, value: 70 }, { time: d[d.length - 1].time, value: 70 }]);
                bot.setData([{ time: d[0].time, value: 30 }, { time: d[d.length - 1].time, value: 30 }]);
            }
        }
        rsiSeries.setData(indicatorData.rsi);
        rsiChart.timeScale().fitContent();
    } else {
        container.classList.add('hidden');
        // Could remove chart to save memory chart.remove()
    }
}

function renderMACD() {
    const container = document.getElementById('us-macd-chart');
    if (indicatorState.macd && indicatorData?.macd) {
        container.classList.remove('hidden');
        if (!macdChart) {
            container.innerHTML = '';
            macdChart = LightweightCharts.createChart(container, {
                width: container.clientWidth, height: 80,
                layout: { backgroundColor: '#1a1a1a', textColor: '#666' },
                grid: { vertLines: { visible: false }, horzLines: { color: '#2a2a2a' } },
                timeScale: { visible: false }
            });
            macdHistSeries = macdChart.addHistogramSeries({ color: '#26a69a', priceScaleId: 'right' });
            macdLineSeries = macdChart.addLineSeries({ color: '#3b82f6', lineWidth: 1 });
            macdSignalSeries = macdChart.addLineSeries({ color: '#f59e0b', lineWidth: 1 });
        }

        macdLineSeries.setData(indicatorData.macd.macd_line);
        macdSignalSeries.setData(indicatorData.macd.signal_line);

        const histData = indicatorData.macd.histogram.map(item => ({
            time: item.time, value: item.value,
            color: item.value >= 0 ? '#26a69a' : '#ef5350'
        }));
        macdHistSeries.setData(histData);
        macdChart.timeScale().fitContent();
    } else {
        container.classList.add('hidden');
    }
}

async function loadUSAISummary(ticker) {
    const el = document.getElementById('us-ai-summary');
    const updatedEl = document.getElementById('us-ai-updated');
    if (!el) return;

    el.innerHTML = '<span class="text-gray-500 animate-pulse">🤖 AI가 분석 중입니다...</span>';

    try {
        const res = await fetch(`/api/us/ai-summary/${ticker}?lang=${currentLang}`);
        const data = await res.json();

        if (data.error) {
            el.innerText = "분석 데이터가 없습니다.";
            return;
        }

        // Render Markdown
        el.innerHTML = marked.parse(data.summary);
        if (updatedEl && data.updated) updatedEl.innerText = `Updated: ${data.updated}`;

    } catch (e) {
        el.innerText = "분석 로드 실패";
    }
}

// --- Other Sections Rendering ---

function renderUSETFFlows(data) {
    const inflowEl = document.getElementById('us-etf-inflows');
    const outflowEl = document.getElementById('us-etf-outflows');
    const sentimentEl = document.getElementById('us-etf-sentiment');
    const aiBtn = document.getElementById('us-etf-ai-btn');
    const aiContent = document.getElementById('us-etf-ai-content');
    const aiContainer = document.getElementById('us-etf-ai-container');

    if (sentimentEl) sentimentEl.innerText = `Sentiment Score: ${data.market_sentiment_score}`;

    const renderFlow = (container, list, color) => {
        if (!container) return;
        container.innerHTML = '';
        list.forEach(item => {
            const div = document.createElement('div');
            div.className = 'flex justify-between items-center text-xs p-1 hover:bg-[#252525] border-b border-[#2a2a2a]';
            div.innerHTML = `
                          <span class="font-bold text-gray-300 w-12">${item.ticker}</span>
                          <span class="text-gray-500 truncate flex-1">${item.name}</span>
                          <span class="${color} font-mono w-16 text-right">${item.flow_score}</span>
                      `;
            container.appendChild(div);
        });
    };

    renderFlow(inflowEl, data.top_inflows || [], 'text-green-400');
    renderFlow(outflowEl, data.top_outflows || [], 'text-red-400');

    // AI Logic
    if (data.ai_analysis) {
        if (aiBtn) {
            aiBtn.classList.remove('hidden');
            aiBtn.onclick = () => {
                aiContainer.classList.toggle('hidden');
                aiContent.innerText = data.ai_analysis;
            };
        }
    }
}

function renderUSOptionsFlow(data) {
    const container = document.getElementById('us-options-flow');
    if (!container) return;
    container.innerHTML = '';

    // Limit to top 10 for grid
    // Limit to top 10 for grid
    const flows = (data.options_flow || []).slice(0, 10);

    flows.forEach(flow => {
        const ticker = flow.ticker;
        const metrics = flow.metrics || {};
        const pcRatio = metrics.pc_ratio || 0;

        // Derive sentiment from P/C Ratio if not provided
        let sentiment = flow.sentiment;
        if (!sentiment) {
            if (pcRatio < 0.6) sentiment = 'Bullish';
            else if (pcRatio > 1.0) sentiment = 'Bearish';
            else sentiment = 'Neutral';
        }

        const color = sentiment === 'Bullish' ? 'bg-green-900/30 border-green-800' : (sentiment === 'Bearish' ? 'bg-red-900/30 border-red-800' : 'bg-gray-800 border-gray-700');

        const div = document.createElement('div');
        div.className = `border rounded p-2 flex flex-col items-center justify-center ${color}`;
        div.innerHTML = `
                    <span class="font-bold text-gray-200 text-xs">${ticker}</span>
                    <span class="text-[10px] text-gray-400 mt-1">P/C: ${pcRatio}</span>
                    <span class="text-[10px] ${sentiment === 'Bullish' ? 'text-green-400' : (sentiment === 'Bearish' ? 'text-red-400' : 'text-gray-500')}">${sentiment}</span>
                `;
        container.appendChild(div);
    });
}

function renderUSMacroAnalysis(data) {
    const grid = document.getElementById('us-macro-indicators');
    const aiText = document.getElementById('us-macro-ai-analysis');
    const ts = document.getElementById('us-macro-timestamp');

    if (ts) ts.innerText = new Date().toLocaleTimeString();
    if (aiText) aiText.innerText = data.ai_analysis || "AI 분석 데이터 없음";

    // Indicators
    if (grid && data.macro_indicators) {
        grid.innerHTML = '';
        Object.entries(data.macro_indicators).forEach(([key, val]) => {
            const change = val.change_1d || 0;
            const color = change > 0 ? 'text-green-400' : (change < 0 ? 'text-red-400' : 'text-gray-400');

            const div = document.createElement('div');
            div.className = 'bg-[#1a1a1a] border border-[#2a2a2a] rounded p-2 flex flex-col items-center justify-center';
            div.innerHTML = `
                          <span class="text-[10px] text-gray-500">${key}</span>
                          <span class="text-xs font-bold text-white">${val.current}</span>
                          <span class="text-[10px] ${color}">${change}%</span>
                      `;
            grid.appendChild(div);
        });
    }
}

function renderUSSectorHeatmap(data) {
    // Rendering ApexCharts Treemap
    const container = document.getElementById('us-sector-heatmap');
    if (!container) return;
    container.innerHTML = '';

    if (!data.series || data.series.length === 0) {
        container.innerHTML = '<div class="absolute inset-0 flex items-center justify-center text-gray-500">No Vector Data</div>';
        return;
    }

    const options = {
        series: data.series,
        legend: { show: false },
        chart: {
            height: 300,
            type: 'treemap',
            toolbar: { show: false },
            background: 'transparent'
        },
        colors: [
            '#22c55e', '#ef4444', '#3b82f6', '#f59e0b', '#a855f7'
        ],
        plotOptions: {
            treemap: {
                distributed: true,
                enableShades: true
            }
        },
        dataLabels: {
            enabled: true,
            style: { fontSize: '10px' },
            formatter: function (text, op) {
                let item = op.w.config.series[op.seriesIndex].data[op.dataPointIndex];
                let val = item && item.change !== undefined ? item.change : 0;
                return [text, val.toFixed(2) + '%'];
            }
        },
        tooltip: {
            theme: 'dark'
        }
    };

    const chart = new ApexCharts(container, options);
    chart.render();
}

async function renderUSCalendar() {
    const container = document.getElementById('us-calendar-events');
    if (!container) return;

    container.innerHTML = '<div class="text-center text-gray-500">Loading...</div>';

    try {
        const res = await fetch('/api/us/calendar');
        const data = await res.json();

        if (!data.events || data.events.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500">No events this week.</div>';
            return;
        }

        container.innerHTML = '';

        // Group by date
        // Assuming events are sorted
        let currentDay = '';

        data.events.forEach(event => {
            const div = document.createElement('div');
            div.className = 'bg-[#1a1a1a] border border-[#2a2a2a] rounded p-3 mb-2 flex items-start gap-3';

            // Impact Color
            const impactColor = event.impact === 'High' ? 'bg-red-500' : (event.impact === 'Medium' ? 'bg-yellow-500' : 'bg-blue-500');

            div.innerHTML = `
                          <div class="w-1 h-full rounded-full ${impactColor} shrink-0 mt-1"></div>
                          <div class="flex-1">
                              <div class="flex justify-between items-center mb-1">
                                  <span class="text-xs font-bold text-gray-300">${event.time} ${event.currency}</span>
                                  <span class="text-[10px] text-gray-500">${event.date}</span>
                              </div>
                              <h4 class="text-sm font-medium text-white mb-2">${event.title}</h4>
                              <div class="grid grid-cols-3 gap-2 text-center text-xs bg-[#222] rounded p-2 mb-2">
                                   <div><div class="text-gray-500">Actual</div><span class="text-yellow-400 font-mono">${event.actual || '-'}</span></div>
                                   <div><div class="text-gray-500">Forecast</div><span class="text-gray-300 font-mono">${event.forecast || '-'}</span></div>
                                   <div><div class="text-gray-500">Previous</div><span class="text-gray-400 font-mono">${event.previous || '-'}</span></div>
                              </div>
                              ${event.ai_analysis ? `<div class="text-xs text-indigo-300 mt-1 bg-indigo-900/20 p-2 rounded">🤖 ${event.ai_analysis}</div>` : ''}
                          </div>
                      `;
            container.appendChild(div);
        });
    } catch (e) {
        container.innerHTML = 'Error loading calendar.';
    }
}

function translateUI() {
    // Simple mapping
    const dict = {
        'ai-analysis': { ko: '🤖 AI 투자 분석', en: '🤖 AI Investment Analysis' },
        'final-top10': { ko: '📊 Final Top 10 - Smart Money Picks', en: '📊 Final Top 10 - Smart Money Picks' },
        'etf-flows': { ko: '💰 ETF Fund Flows - 자금 흐름', en: '💰 ETF Fund Flows' },
        'options-flow': { ko: 'Options Flow - 기관 포지션', en: 'Options Flow' },
        'macro-analysis': { ko: '🌍 Macro Analysis - AI 예측', en: '🌍 Macro Analysis - AI Prediction' },
        // Add more as needed
    };

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (dict[key] && dict[key][currentLang]) {
            el.innerText = dict[key][currentLang];
        }
    });
}

async function updateRealtimePrices() {
    // Collect tickers on screen
    // Currently mostly just the table
    // However, Smart Money Table is main place for live prices
    const visibleTickers = [];
    document.querySelectorAll('#us-smart-money-table tr').forEach(tr => {
        const tickerEl = tr.querySelector('td:nth-child(2) span'); // Ticker is inside span
        if (tickerEl) visibleTickers.push(tickerEl.innerText);
    });

    if (visibleTickers.length === 0) return;

    try {
        const res = await fetch('/api/realtime-prices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers: visibleTickers })
        });
        const prices = await res.json();

        // Update DOM
        document.querySelectorAll('#us-smart-money-table tr').forEach(tr => {
            const tickerEl = tr.querySelector('td:nth-child(2) span');
            if (tickerEl) {
                const t = tickerEl.innerText;
                if (prices[t]) {
                    const priceCell = tr.querySelector('td:nth-child(7)'); // 7th column is Current Price
                    if (priceCell) {
                        const oldP = parseFloat(priceCell.innerText.replace('$', ''));
                        const newP = prices[t].current;

                        priceCell.innerText = `$${newP.toFixed(2)}`;

                        // Flash
                        if (newP > oldP) {
                            priceCell.classList.add('text-green-400');
                            setTimeout(() => priceCell.classList.remove('text-green-400'), 1000);
                        } else if (newP < oldP) {
                            priceCell.classList.add('text-red-400');
                            setTimeout(() => priceCell.classList.remove('text-red-400'), 1000);
                        }
                    }
                }
            }
        });
    } catch (e) { console.error(e); }
}
