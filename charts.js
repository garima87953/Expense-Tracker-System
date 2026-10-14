/**
 * EXPENSE TRACKER - DATA VISUALIZATION ENGINE (Chart.js)
 */

function getChartThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    return {
        text: isDark ? '#94a3b8' : '#475569',
        grid: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
        tooltipBg: isDark ? '#1e293b' : '#ffffff',
        tooltipText: isDark ? '#f8fafc' : '#0f172a',
        tooltipBorder: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
    };
}

// Category Breakdown Doughnut Chart
let categoryChartInstance = null;
function createCategoryDoughnutChart(canvasId, labels, data, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    const theme = getChartThemeColors();

    if (!data || data.length === 0) {
        // Fallback display
        labels = ['No Expenses Yet'];
        data = [1];
        colors = ['#334155'];
    }

    categoryChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: document.documentElement.getAttribute('data-theme') === 'light' ? '#ffffff' : '#1e293b',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: theme.text,
                        font: { family: 'Inter', size: 12 },
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: theme.tooltipBg,
                    titleColor: theme.tooltipText,
                    bodyColor: theme.tooltipText,
                    borderColor: theme.tooltipBorder,
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const val = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: $${val.toLocaleString()} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '72%'
        }
    });
}

// Cash Flow Trend Bar Chart (Income vs Expense)
let cashFlowChartInstance = null;
function createCashFlowBarChart(canvasId, monthlyTrend) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (cashFlowChartInstance) {
        cashFlowChartInstance.destroy();
    }

    const theme = getChartThemeColors();
    const labels = monthlyTrend.map(item => item.month);
    const incomeData = monthlyTrend.map(item => item.income);
    const expenseData = monthlyTrend.map(item => item.expense);

    cashFlowChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: '#10b981',
                    borderRadius: 6,
                    barPercentage: 0.6,
                    categoryPercentage: 0.8
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    backgroundColor: '#ef4444',
                    borderRadius: 6,
                    barPercentage: 0.6,
                    categoryPercentage: 0.8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: theme.text,
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: theme.tooltipBg,
                    titleColor: theme.tooltipText,
                    bodyColor: theme.tooltipText,
                    borderColor: theme.tooltipBorder,
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: theme.text, font: { family: 'Inter' } }
                },
                y: {
                    grid: { color: theme.grid },
                    ticks: {
                        color: theme.text,
                        font: { family: 'Inter' },
                        callback: function(val) { return '$' + val; }
                    }
                }
            }
        }
    });
}
