/**
 * Coffee Analytics Dashboard - JavaScript
 * Handles data fetching, chart rendering, and interactivity.
 */

// ============================================================
// Global State
// ============================================================

let charts = {};
let isScraping = false;

// Chart.js defaults
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#6B5B4E';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;

const COLORS = {
    primary: '#6F4E37',
    primaryLight: '#A67B5B',
    accent: '#D4A574',
    accentLight: '#F5E6D3',
    success: '#4CAF50',
    warning: '#FF9800',
    danger: '#F44336',
    info: '#2196F3',
    palette: [
        '#6F4E37', '#A67B5B', '#D4A574', '#8BC34A', '#FF9800',
        '#2196F3', '#9C27B0', '#F44336', '#00BCD4', '#795548'
    ]
};

// ============================================================
// Initialization
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

async function loadDashboard() {
    showLoading();
    try {
        const [summary, drinks, hours, days, sentiment, ages, keywords, engagement, heatmap, sources, posts, sentimentTime] = await Promise.all([
            fetchJSON('/api/summary'),
            fetchJSON('/api/popular-drinks'),
            fetchJSON('/api/peak-hours'),
            fetchJSON('/api/day-patterns'),
            fetchJSON('/api/sentiment'),
            fetchJSON('/api/age-distribution'),
            fetchJSON('/api/trending-keywords'),
            fetchJSON('/api/engagement-by-drink'),
            fetchJSON('/api/heatmap'),
            fetchJSON('/api/source-breakdown'),
            fetchJSON('/api/posts?limit=50'),
            fetchJSON('/api/sentiment-over-time?days=7')
        ]);

        renderSummary(summary);
        renderDrinkChart(drinks);
        renderHourChart(hours);
        renderDayChart(days);
        renderSentimentChart(sentiment);
        renderAgeChart(ages);
        renderKeywordCloud(keywords);
        renderEngagementChart(engagement);
        renderHeatmap(heatmap);
        renderSourceChart(sources);
        renderPostsTable(posts);
        renderSentimentTimeChart(sentimentTime);
        
        updateTimestamp();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError(error.message);
    }
}

// ============================================================
// Data Fetching
// ============================================================

async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }
    return response.json();
}

function showLoading() {
    // Don't replace innerHTML - it destroys canvas elements!
    // Instead, just add a loading overlay without removing canvases.
    document.querySelectorAll('.chart-container').forEach(el => {
        // Only show loading on containers that have a canvas
        const canvas = el.querySelector('canvas');
        if (canvas) {
            canvas.style.opacity = '0.3';
        }
    });
}

function showError(message) {
    // Only show error in containers that have a canvas (don't destroy them)
    document.querySelectorAll('.chart-container').forEach(el => {
        const canvas = el.querySelector('canvas');
        if (canvas) {
            canvas.style.opacity = '0.3';
        }
    });
}

function updateTimestamp() {
    const now = new Date().toLocaleString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
    document.getElementById('last-updated').textContent = now;
}

// ============================================================
// Summary Cards
// ============================================================

function renderSummary(data) {
    if (!data) return;
    
    document.getElementById('total-posts').textContent = formatNumber(data.total_posts);
    document.getElementById('unique-drinks').textContent = data.unique_drinks_mentioned;
    document.getElementById('avg-sentiment').textContent = data.average_sentiment_score.toFixed(2);
    document.getElementById('avg-engagement').textContent = formatNumber(data.average_engagement_score);
    document.getElementById('positive-pct').textContent = data.positive_sentiment_percentage + '%';
}

function formatNumber(num) {
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

// ============================================================
// Popular Drinks Chart
// ============================================================

function renderDrinkChart(data) {
    if (!data || !data.drinks) return;
    
    const ctx = document.getElementById('drinkChart').getContext('2d');
    const labels = Object.keys(data.drinks);
    const values = Object.values(data.drinks);

    destroyChart('drinkChart');
    charts.drinkChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Mentions',
                data: values,
                backgroundColor: COLORS.palette.slice(0, labels.length),
                borderRadius: 6,
                borderSkipped: false,
                barPercentage: 0.7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: function(ctx) {
                            if (data.percentages && labels[ctx.dataIndex]) {
                                return data.percentages[labels[ctx.dataIndex]] + '%';
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(111,78,55,0.06)' },
                    ticks: { font: { size: 11 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, maxRotation: 45 }
                }
            }
        }
    });
}

// ============================================================
// Sentiment Pie Chart
// ============================================================

function renderSentimentChart(data) {
    if (!data) return;
    
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    const positive = data.positive?.count || 0;
    const neutral = data.neutral?.count || 0;
    const negative = data.negative?.count || 0;
    const total = data.total_posts || 0;

    destroyChart('sentimentChart');
    charts.sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [positive, neutral, negative],
                backgroundColor: [COLORS.success, COLORS.warning, COLORS.danger],
                borderWidth: 3,
                borderColor: '#FFFFFF',
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                            return `${ctx.label}: ${ctx.parsed} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

// ============================================================
// Peak Hours Line Chart
// ============================================================

function renderHourChart(data) {
    if (!data || !data.hourly_data) return;
    
    const ctx = document.getElementById('hourChart').getContext('2d');
    const labels = data.hourly_data.map(h => h.hour_label);
    const counts = data.hourly_data.map(h => h.post_count);

    destroyChart('hourChart');
    charts.hourChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Posts',
                data: counts,
                borderColor: COLORS.primary,
                backgroundColor: 'rgba(111,78,55,0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(111,78,55,0.06)' },
                    ticks: { font: { size: 11 } }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 10 },
                        maxTicksLimit: 12
                    }
                }
            }
        }
    });
}

// ============================================================
// Day of Week Bar Chart
// ============================================================

function renderDayChart(data) {
    if (!data || !data.daily_data) return;
    
    const ctx = document.getElementById('dayChart').getContext('2d');
    const labels = data.daily_data.map(d => d.day);
    const counts = data.daily_data.map(d => d.post_count);

    destroyChart('dayChart');
    charts.dayChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Posts',
                data: counts,
                backgroundColor: COLORS.accent,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(111,78,55,0.06)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// ============================================================
// Age Distribution Chart
// ============================================================

function renderAgeChart(data) {
    if (!data || !data.distribution) return;
    
    const ctx = document.getElementById('ageChart').getContext('2d');
    const labels = Object.keys(data.distribution);
    const values = labels.map(l => data.distribution[l].count);

    destroyChart('ageChart');
    charts.ageChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#6F4E37', '#A67B5B', '#D4A574', '#8BC34A', '#FF9800'
                ],
                borderWidth: 2,
                borderColor: '#FFFFFF',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 12,
                        font: { size: 11 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            if (data.distribution[ctx.label]) {
                                return `${ctx.label}: ${ctx.parsed} (${data.distribution[ctx.label].percentage}%)`;
                            }
                            return ctx.label;
                        }
                    }
                }
            }
        }
    });
}

// ============================================================
// Keyword Cloud
// ============================================================

function renderKeywordCloud(data) {
    if (!data || !data.trending) return;
    
    const container = document.getElementById('keyword-cloud');
    const keywords = data.trending;
    const maxFreq = Math.max(...keywords.map(k => k.frequency));
    const minFreq = Math.min(...keywords.map(k => k.frequency));

    container.innerHTML = keywords.map(kw => {
        const normalizedSize = kw.frequency / maxFreq;
        let sizeClass = 'size-small';
        if (normalizedSize > 0.7) sizeClass = 'size-large';
        else if (normalizedSize > 0.3) sizeClass = 'size-medium';

        let colorClass = '';
        if (kw.sentiment_label === 'positive') colorClass = 'style="background: #E8F5E9; border-color: #A5D6A7; color: #2E7D32;"';
        else if (kw.sentiment_label === 'negative') colorClass = 'style="background: #FFEBEE; border-color: #EF9A9A; color: #C62828;"';

        return `<span class="keyword-tag ${sizeClass}" ${colorClass} title="${kw.frequency} mentions">${kw.keyword}</span>`;
    }).join('');
}

// ============================================================
// Engagement by Drink Chart
// ============================================================

function renderEngagementChart(data) {
    if (!data || !data.drinks) return;
    
    const ctx = document.getElementById('engagementChart').getContext('2d');
    const drinks = Object.entries(data.drinks).slice(0, 10);
    const labels = drinks.map(d => d[0]);
    const scores = drinks.map(d => d[1].avg_engagement_score);

    destroyChart('engagementChart');
    charts.engagementChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Engagement Score',
                data: scores,
                backgroundColor: COLORS.primaryLight,
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(111,78,55,0.06)' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

// ============================================================
// Heatmap
// ============================================================

function renderHeatmap(data) {
    if (!data || !data.data) return;
    
    const container = document.getElementById('heatmap-container');
    container.innerHTML = '';
    
    const heatmapData = data.data;
    const dayLabels = data.day_labels;
    const hourLabels = data.hour_labels;
    const maxValue = data.max_value || 1;

    // Create heatmap using Plotly
    const z = heatmapData;
    const x = hourLabels;
    const y = dayLabels;

    Plotly.newPlot(container, [{
        z: z,
        x: x,
        y: y,
        type: 'heatmap',
        colorscale: [
            [0, '#FDF8F3'],
            [0.25, '#F5E6D3'],
            [0.5, '#D4A574'],
            [0.75, '#A67B5B'],
            [1, '#4A3228']
        ],
        hoverongaps: false,
        hovertemplate: '%{y} %{x}:00<br>%{z} posts<extra></extra>'
    }], {
        margin: { t: 10, r: 20, b: 30, l: 50 },
        height: 280,
        xaxis: {
            title: 'Hour of Day',
            tickfont: { size: 10 }
        },
        yaxis: {
            tickfont: { size: 11 }
        }
    }, {
        responsive: true
    });
}

// ============================================================
// Source Breakdown Chart
// ============================================================

function renderSourceChart(data) {
    if (!data) return;
    
    const ctx = document.getElementById('sourceChart').getContext('2d');
    const sources = Object.keys(data);
    const counts = sources.map(s => data[s].count);
    const engagements = sources.map(s => data[s].avg_engagement);

    destroyChart('sourceChart');
    charts.sourceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sources.map(s => s.charAt(0).toUpperCase() + s.slice(1)),
            datasets: [
                {
                    label: 'Posts',
                    data: counts,
                    backgroundColor: COLORS.accent,
                    borderRadius: 4
                },
                {
                    label: 'Avg Engagement',
                    data: engagements,
                    backgroundColor: COLORS.primary,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(111,78,55,0.06)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

// ============================================================
// Sentiment Over Time
// ============================================================

function renderSentimentTimeChart(data) {
    if (!data || !data.data) return;
    
    const ctx = document.getElementById('sentimentTimeChart').getContext('2d');
    const dates = data.data.map(d => d.date);
    const positive = data.data.map(d => d.positive);
    const neutral = data.data.map(d => d.neutral);
    const negative = data.data.map(d => d.negative);

    destroyChart('sentimentTimeChart');
    charts.sentimentTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Positive',
                    data: positive,
                    borderColor: COLORS.success,
                    backgroundColor: 'rgba(76,175,80,0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3
                },
                {
                    label: 'Neutral',
                    data: neutral,
                    borderColor: COLORS.warning,
                    backgroundColor: 'rgba(255,152,0,0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3
                },
                {
                    label: 'Negative',
                    data: negative,
                    borderColor: COLORS.danger,
                    backgroundColor: 'rgba(244,67,54,0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { padding: 12 } },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(111,78,55,0.06)' } },
                x: { grid: { display: false }, ticks: { font: { size: 10 } } }
            }
        }
    });
}

// ============================================================
// Posts Table
// ============================================================

function renderPostsTable(data) {
    const tbody = document.getElementById('posts-tbody');
    if (!data || !data.posts) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:40px;">No posts available. Trigger a scrape to collect data.</td></tr>';
        return;
    }

    tbody.innerHTML = data.posts.map(post => {
        const drinks = (post.drink_types || []).join(', ') || '—';
        const time = post.timestamp ? new Date(post.timestamp).toLocaleString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        }) : '—';
        
        return `
            <tr>
                <td><span class="source-badge ${post.source}">${post.source}</span></td>
                <td class="post-text" title="${escapeHtml(post.text || '')}">${escapeHtml(truncate(post.text || '', 80))}</td>
                <td>${drinks}</td>
                <td><span class="sentiment-badge ${post.sentiment}">${post.sentiment}</span></td>
                <td>${formatNumber(post.engagement_score || 0)}</td>
                <td>${time}</td>
            </tr>
        `;
    }).join('');
}

async function loadPosts() {
    const source = document.getElementById('filter-source').value;
    const sentiment = document.getElementById('filter-sentiment').value;
    
    let url = `/api/posts?limit=50&source=${source}&sentiment=${sentiment}`;
    try {
        const data = await fetchJSON(url);
        renderPostsTable(data);
    } catch (error) {
        console.error('Error loading posts:', error);
    }
}

// ============================================================
// Scrape Control
// ============================================================

async function triggerScrape() {
    if (isScraping) return;
    isScraping = true;

    const btn = document.getElementById('btn-scrape');
    const statusText = document.getElementById('status-text');
    const statusDot = document.querySelector('.status-dot');

    btn.disabled = true;
    btn.style.opacity = '0.7';
    statusText.textContent = 'Scraping...';
    statusDot.className = 'status-dot active';

    try {
        const result = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force: true })
        });
        const data = await result.json();
        statusText.textContent = data.status === 'skipped' ? 'Skipped' : 'Scraping...';
    } catch (error) {
        statusText.textContent = 'Error';
        statusDot.className = 'status-dot error';
    }

    // Check status after delay
    setTimeout(() => {
        isScraping = false;
        btn.disabled = false;
        btn.style.opacity = '1';
        statusText.textContent = 'Idle';
        statusDot.className = 'status-dot idle';
        
        // Refresh dashboard
        loadDashboard();
    }, 5000);
}

// ============================================================
// Utility Functions
// ============================================================

function destroyChart(chartId) {
    if (charts[chartId]) {
        charts[chartId].destroy();
        delete charts[chartId];
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, length) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}
