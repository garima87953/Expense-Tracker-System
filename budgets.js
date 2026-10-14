/**
 * EXPENSE TRACKER - BUDGET MANAGEMENT SCRIPT
 */

async function loadBudgets() {
    const monthPicker = document.getElementById('budgetMonthPicker');
    const selectedMonth = monthPicker ? monthPicker.value : new Date().toISOString().slice(0, 7);

    try {
        const data = await apiRequest(`/api/budgets?month_year=${selectedMonth}`);
        renderOverallBudget(data.overall_budget, data.total_spent_month);
        renderCategoryBudgets(data.category_budgets);
    } catch (err) {
        console.error('Failed to load budgets:', err);
    }
}

function renderOverallBudget(overall, totalSpent) {
    const container = document.getElementById('overallBudgetContainer');
    if (!container) return;

    if (!overall) {
        container.innerHTML = `
            <div class="card" style="border-left: 4px solid var(--primary);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
                <div>
                    <h3 style="font-size:1.2rem;font-weight:700;">Overall Monthly Budget Not Set</h3>
                    <p style="color:var(--text-secondary);font-size:0.9rem;margin-top:0.25rem;">
                        You have spent <strong>${formatCurrency(totalSpent)}</strong> so far this month. Set a monthly limit to prevent overspending.
                    </p>
                </div>
                <button class="btn btn-primary" onclick="openSetBudgetModal(null)">Set Monthly Budget</button>
            </div>
        `;
        return;
    }

    const pct = overall.percentage;
    let statusBadgeClass = 'badge-income';
    let statusText = 'On Track';
    let barClass = 'progress-safe';

    if (overall.status === 'danger') {
        statusBadgeClass = 'badge-expense';
        statusText = 'Limit Exceeded';
        barClass = 'progress-danger';
    } else if (overall.status === 'warning') {
        statusBadgeClass = 'badge-warning';
        statusText = 'Nearing Limit';
        barClass = 'progress-warning';
    }

    container.innerHTML = `
        <div class="card" style="border-left: 5px solid ${overall.status === 'danger' ? 'var(--danger)' : (overall.status === 'warning' ? 'var(--warning)' : 'var(--success)')};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;flex-wrap:wrap;gap:0.5rem;">
                <div>
                    <span class="badge ${statusBadgeClass}" style="margin-bottom:0.4rem;">${statusText} (${pct}%)</span>
                    <h3 style="font-size:1.3rem;font-weight:800;">Total Monthly Spending Limit</h3>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.6rem;font-weight:800;">${formatCurrency(overall.spent)} <span style="font-size:1rem;color:var(--text-muted);font-weight:500;">/ ${formatCurrency(overall.limit)}</span></div>
                    <div style="font-size:0.85rem;color:${overall.remaining < 0 ? 'var(--danger)' : 'var(--text-secondary)'};">
                        ${overall.remaining < 0 ? `Over by ${formatCurrency(Math.abs(overall.remaining))}` : `${formatCurrency(overall.remaining)} remaining`}
                    </div>
                </div>
            </div>

            <div class="progress-container" style="height:14px;">
                <div class="progress-bar ${barClass}" style="width: ${Math.min(pct, 100)}%;"></div>
            </div>

            <div style="display:flex;justify-content:flex-end;gap:0.5rem;margin-top:1rem;">
                <button class="btn btn-outline btn-sm" onclick="openSetBudgetModal(null, ${overall.limit})">Adjust Budget</button>
                <button class="btn btn-danger btn-sm" onclick="deleteBudgetEntry(${overall.id})">Remove</button>
            </div>
        </div>
    `;
}

function renderCategoryBudgets(catBudgets) {
    const container = document.getElementById('categoryBudgetsGrid');
    if (!container) return;

    if (!catBudgets || catBudgets.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1;text-align:center;padding:3rem;background:var(--bg-card);border-radius:var(--radius-lg);border:1px solid var(--border-color);">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">🎯</div>
                <h4 style="font-size:1.15rem;font-weight:700;">No Category Budgets Configured</h4>
                <p style="color:var(--text-secondary);font-size:0.9rem;margin:0.5rem 0 1.25rem;">
                    Allocate budget caps to specific categories like Dining, Shopping, or Travel for pinpoint financial control.
                </p>
                <button class="btn btn-primary btn-sm" onclick="openSetBudgetModal()">+ Add Category Budget</button>
            </div>
        `;
        return;
    }

    container.innerHTML = catBudgets.map(b => {
        let barClass = 'progress-safe';
        let badgeClass = 'badge-income';
        let statusLabel = 'Safe';

        if (b.status === 'danger') {
            barClass = 'progress-danger';
            badgeClass = 'badge-expense';
            statusLabel = 'Exceeded';
        } else if (b.status === 'warning') {
            barClass = 'progress-warning';
            badgeClass = 'badge-warning';
            statusLabel = 'Alert';
        }

        return `
            <div class="budget-card">
                <div>
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
                        <span class="category-pill">
                            <span class="category-dot" style="background-color: ${b.category_color};"></span>
                            ${b.category_name}
                        </span>
                        <span class="badge ${badgeClass}">${statusLabel} (${b.percentage}%)</span>
                    </div>

                    <div style="display:flex;justify-content:space-between;align-items:baseline;margin:0.5rem 0;">
                        <span style="font-size:1.25rem;font-weight:700;">${formatCurrency(b.spent)}</span>
                        <span style="font-size:0.85rem;color:var(--text-muted);">Cap: ${formatCurrency(b.limit)}</span>
                    </div>

                    <div class="progress-container">
                        <div class="progress-bar ${barClass}" style="width: ${Math.min(b.percentage, 100)}%;"></div>
                    </div>

                    <div style="font-size:0.8rem;color:${b.remaining < 0 ? 'var(--danger)' : 'var(--text-secondary)'};">
                        ${b.remaining < 0 ? `Over by ${formatCurrency(Math.abs(b.remaining))}` : `${formatCurrency(b.remaining)} remaining`}
                    </div>
                </div>

                <div style="display:flex;justify-content:flex-end;gap:0.4rem;margin-top:1.25rem;padding-top:0.75rem;border-top:1px solid var(--border-color);">
                    <button class="btn btn-outline btn-sm" onclick="openSetBudgetModal(${b.category_id}, ${b.limit})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteBudgetEntry(${b.id})">Remove</button>
                </div>
            </div>
        `;
    }).join('');
}

function openSetBudgetModal(categoryId = '', defaultAmount = '') {
    const monthPicker = document.getElementById('budgetMonthPicker');
    const selectedMonth = monthPicker ? monthPicker.value : new Date().toISOString().slice(0, 7);

    document.getElementById('budgetCategorySelect').value = categoryId !== null ? categoryId : '';
    document.getElementById('budgetAmountInput').value = defaultAmount || '';
    document.getElementById('budgetMonthInput').value = selectedMonth;

    openModal('setBudgetModal');
}

async function deleteBudgetEntry(id) {
    if (!confirm('Remove this budget limit?')) return;
    try {
        await apiRequest(`/api/budgets/${id}`, { method: 'DELETE' });
        showToast('Budget deleted successfully.', 'success');
        loadBudgets();
    } catch (err) {
        // Handled
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const monthPicker = document.getElementById('budgetMonthPicker');
    if (monthPicker) {
        monthPicker.value = new Date().toISOString().slice(0, 7);
        monthPicker.addEventListener('change', loadBudgets);
    }

    loadBudgets();

    const budgetForm = document.getElementById('budgetForm');
    if (budgetForm) {
        budgetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = budgetForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;

            const categoryVal = document.getElementById('budgetCategorySelect').value;
            const payload = {
                category_id: categoryVal === '' ? null : parseInt(categoryVal),
                amount: parseFloat(document.getElementById('budgetAmountInput').value),
                month_year: document.getElementById('budgetMonthInput').value
            };

            try {
                await apiRequest('/api/budgets', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                showToast('Budget configured successfully!', 'success');
                closeModal('setBudgetModal');
                loadBudgets();
            } catch (err) {
                // Handled
            } finally {
                submitBtn.disabled = false;
            }
        });
    }
});
