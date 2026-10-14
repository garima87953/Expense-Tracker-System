/**
 * EXPENSE TRACKER - DASHBOARD LOGIC
 */

let dashboardDataCache = null;

async function loadDashboardData() {
    try {
        const stats = await apiRequest('/api/dashboard/stats');
        dashboardDataCache = stats;

        // Update KPI Cards
        document.getElementById('kpiIncome').textContent = formatCurrency(stats.total_income);
        document.getElementById('kpiExpenses').textContent = formatCurrency(stats.total_expenses);
        
        const balanceElem = document.getElementById('kpiBalance');
        balanceElem.textContent = formatCurrency(stats.current_balance);
        if (stats.current_balance < 0) {
            balanceElem.style.color = 'var(--danger)';
        } else {
            balanceElem.style.color = 'var(--success)';
        }

        document.getElementById('kpiMonthlyExpense').textContent = formatCurrency(stats.monthly_expenses);
        document.getElementById('kpiTxCount').textContent = stats.total_transactions;

        // Update Budget Meter
        const budgetLimit = stats.budget_limit;
        const budgetPct = stats.budget_used_pct;
        const budgetBar = document.getElementById('dashboardBudgetBar');
        const budgetPctText = document.getElementById('dashboardBudgetPct');
        const budgetStatusText = document.getElementById('dashboardBudgetStatus');

        if (budgetLimit > 0) {
            budgetPctText.textContent = `${budgetPct}% used`;
            budgetBar.style.width = `${Math.min(budgetPct, 100)}%`;

            if (budgetPct >= 100) {
                budgetBar.className = 'progress-bar progress-danger';
                budgetStatusText.innerHTML = `<span style="color:var(--danger)">⚠️ Over budget by ${formatCurrency(stats.monthly_expenses - budgetLimit)}</span>`;
            } else if (budgetPct >= 80) {
                budgetBar.className = 'progress-bar progress-warning';
                budgetStatusText.innerHTML = `<span style="color:var(--warning)">Approaching limit (${formatCurrency(budgetLimit - stats.monthly_expenses)} left)</span>`;
            } else {
                budgetBar.className = 'progress-bar progress-safe';
                budgetStatusText.innerHTML = `<span style="color:var(--success)">On track (${formatCurrency(budgetLimit - stats.monthly_expenses)} remaining)</span>`;
            }
        } else {
            budgetPctText.textContent = 'No budget set';
            budgetBar.style.width = '0%';
            budgetStatusText.innerHTML = `<a href="/budgets" style="color:var(--primary);text-decoration:underline;">Set monthly budget &rarr;</a>`;
        }

        // Render Charts
        if (stats.category_breakdown) {
            createCategoryDoughnutChart(
                'categoryChart',
                stats.category_breakdown.labels,
                stats.category_breakdown.values,
                stats.category_breakdown.colors
            );
        }

        if (stats.monthly_trend) {
            createCashFlowBarChart('trendChart', stats.monthly_trend);
        }

        // Render Recent Transactions
        renderRecentTransactions(stats.recent_transactions);

        // Load AI Insights card
        loadQuickAiInsights();

    } catch (err) {
        console.error('Failed to load dashboard data:', err);
    }
}

function renderRecentTransactions(transactions) {
    const tableBody = document.getElementById('recentTransactionsBody');
    if (!tableBody) return;

    if (!transactions || transactions.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--text-muted);">No transactions recorded yet. Click '+ Add Expense' to get started!</td></tr>`;
        return;
    }

    tableBody.innerHTML = transactions.map(tx => {
        const isExpense = tx.type === 'expense';
        const sign = isExpense ? '-' : '+';
        const color = isExpense ? 'var(--danger)' : 'var(--success)';
        const badgeClass = isExpense ? 'badge-expense' : 'badge-income';

        return `
            <tr>
                <td>
                    <div style="font-weight:600;color:var(--text-primary);">${tx.title}</div>
                    <div style="font-size:0.8rem;color:var(--text-muted);">${formatDate(tx.date)}</div>
                </td>
                <td>
                    <span class="category-pill">
                        <span class="category-dot" style="background-color: ${tx.category_color};"></span>
                        ${tx.category}
                    </span>
                </td>
                <td>
                    <span class="badge ${badgeClass}">${tx.type.toUpperCase()}</span>
                </td>
                <td style="color:var(--text-secondary);font-size:0.9rem;">${tx.payment_method}</td>
                <td style="text-align:right;font-weight:700;font-size:1.05rem;color:${color};">
                    ${sign}${formatCurrency(tx.amount)}
                </td>
            </tr>
        `;
    }).join('');
}

async function loadQuickAiInsights() {
    const aiWidget = document.getElementById('aiQuickSummary');
    if (!aiWidget) return;

    try {
        const res = await apiRequest('/api/ai-insights');
        if (res.success && res.data) {
            const data = res.data;
            let tipHtml = '';
            if (data.saving_suggestions && data.saving_suggestions.length > 0) {
                tipHtml = `<strong>💡 Key Saving Tip:</strong> ${data.saving_suggestions[0]}`;
            } else {
                tipHtml = `<strong>💡 AI Tip:</strong> Keep logging daily spending to get automated cost-saving recommendations.`;
            }

            aiWidget.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
                    <div>
                        <div style="font-size:1.05rem;font-weight:700;color:var(--text-primary);margin-bottom:0.35rem;">
                            Health Score: <span style="color:var(--success);">${data.financial_health_score}/100</span>
                        </div>
                        <div style="font-size:0.9rem;color:var(--text-secondary);max-width:800px;">
                            ${data.monthly_summary}
                        </div>
                        <div style="margin-top:0.75rem;font-size:0.9rem;color:var(--primary);background:var(--primary-light);padding:0.5rem 0.85rem;border-radius:var(--radius-sm);display:inline-block;">
                            ${tipHtml}
                        </div>
                    </div>
                    <div>
                        <a href="/analytics" class="btn btn-outline btn-sm">Deep AI Analytics &rarr;</a>
                    </div>
                </div>
            `;
        }
    } catch (err) {
        aiWidget.innerHTML = `<p style="color:var(--text-muted);font-size:0.85rem;">Insights will appear here once more transactions are logged.</p>`;
    }
}

// Global hook to re-render charts when switching dark/light mode
window.renderAllCharts = function() {
    if (dashboardDataCache) {
        if (dashboardDataCache.category_breakdown) {
            createCategoryDoughnutChart(
                'categoryChart',
                dashboardDataCache.category_breakdown.labels,
                dashboardDataCache.category_breakdown.values,
                dashboardDataCache.category_breakdown.colors
            );
        }
        if (dashboardDataCache.monthly_trend) {
            createCashFlowBarChart('trendChart', dashboardDataCache.monthly_trend);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});
