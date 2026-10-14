/**
 * EXPENSE TRACKER - EXPENSES MANAGEMENT SCRIPT
 */

let currentEditExpenseId = null;
let debounceTimer = null;

async function loadExpenses(page = 1) {
    const search = document.getElementById('expenseSearch')?.value || '';
    const categoryId = document.getElementById('filterCategory')?.value || '';
    const startDate = document.getElementById('filterStartDate')?.value || '';
    const endDate = document.getElementById('filterEndDate')?.value || '';
    const sortBy = document.getElementById('sortBy')?.value || 'date_desc';

    const params = new URLSearchParams({
        page: page,
        search: search,
        category_id: categoryId,
        start_date: startDate,
        end_date: endDate,
        sort_by: sortBy
    });

    try {
        const data = await apiRequest(`/api/expenses?${params.toString()}`);
        renderExpenseTable(data.expenses);
        renderPagination(data);

        // Update total visible sum
        const totalSum = data.expenses.reduce((acc, curr) => acc + curr.amount, 0);
        const countElem = document.getElementById('filteredCount');
        const sumElem = document.getElementById('filteredTotal');
        if (countElem) countElem.textContent = `${data.total} total transactions`;
        if (sumElem) sumElem.textContent = `Page Total: ${formatCurrency(totalSum)}`;

    } catch (err) {
        console.error('Failed to load expenses:', err);
    }
}

function renderExpenseTable(expenses) {
    const tbody = document.getElementById('expensesTableBody');
    if (!tbody) return;

    if (!expenses || expenses.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center;padding:3rem;color:var(--text-muted);">
                    <div style="font-size:2rem;margin-bottom:0.5rem;">🔍</div>
                    <p>No expense transactions match your filters.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = expenses.map(exp => `
        <tr>
            <td style="font-weight:500;color:var(--text-secondary);">${formatDate(exp.date)}</td>
            <td>
                <span class="category-pill">
                    <span class="category-dot" style="background-color: ${exp.category_color};"></span>
                    ${exp.category_name}
                </span>
            </td>
            <td style="font-weight:600;color:var(--text-primary);">${exp.description || '—'}</td>
            <td style="color:var(--text-secondary);font-size:0.9rem;">${exp.payment_method}</td>
            <td style="font-weight:700;font-size:1.05rem;color:var(--danger);text-align:right;">
                -${formatCurrency(exp.amount)}
            </td>
            <td style="text-align:right;">
                <div style="display:inline-flex;gap:0.4rem;">
                    <button class="btn btn-outline btn-sm" onclick="editExpense(${exp.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="confirmDeleteExpense(${exp.id})">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderPagination(data) {
    const container = document.getElementById('paginationContainer');
    if (!container) return;

    if (data.pages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = `<div style="display:flex;gap:0.5rem;align-items:center;justify-content:center;margin-top:1.5rem;">`;
    
    if (data.page > 1) {
        html += `<button class="btn btn-outline btn-sm" onclick="loadExpenses(${data.page - 1})">&larr; Previous</button>`;
    }

    html += `<span style="font-size:0.9rem;color:var(--text-secondary);margin:0 0.5rem;">Page ${data.page} of ${data.pages}</span>`;

    if (data.page < data.pages) {
        html += `<button class="btn btn-outline btn-sm" onclick="loadExpenses(${data.page + 1})">Next &rarr;</button>`;
    }

    html += `</div>`;
    container.innerHTML = html;
}

// Edit Expense
async function editExpense(id) {
    try {
        const exp = await apiRequest(`/api/expenses/${id}`);
        currentEditExpenseId = id;

        document.getElementById('expenseModalTitle').textContent = 'Edit Expense';
        document.getElementById('expAmount').value = exp.amount;
        document.getElementById('expCategory').value = exp.category_id;
        document.getElementById('expDesc').value = exp.description;
        document.getElementById('expDate').value = exp.date;
        document.getElementById('expPayment').value = exp.payment_method;

        openModal('expenseModal');
    } catch (err) {
        // Handled in apiRequest
    }
}

// Open modal for Adding new Expense
function openAddExpenseModal() {
    currentEditExpenseId = null;
    document.getElementById('expenseModalTitle').textContent = 'Add Expense';
    const form = document.getElementById('expenseForm');
    if (form) form.reset();
    document.getElementById('expDate').value = new Date().toISOString().split('T')[0];
    openModal('expenseModal');
}

// Delete Confirmation
let expenseToDeleteId = null;
function confirmDeleteExpense(id) {
    expenseToDeleteId = id;
    openModal('deleteExpenseModal');
}

async function executeDeleteExpense() {
    if (!expenseToDeleteId) return;
    try {
        await apiRequest(`/api/expenses/${expenseToDeleteId}`, { method: 'DELETE' });
        showToast('Expense removed successfully.', 'success');
        closeModal('deleteExpenseModal');
        expenseToDeleteId = null;
        loadExpenses();
    } catch (err) {
        // Handled in apiRequest
    }
}

// CSV Export
function exportExpenses() {
    window.location.href = '/api/expenses/export';
}

document.addEventListener('DOMContentLoaded', () => {
    // Load initial expenses
    loadExpenses();

    // Filter Listeners
    const searchInput = document.getElementById('expenseSearch');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => loadExpenses(1), 350);
        });
    }

    ['filterCategory', 'filterStartDate', 'filterEndDate', 'sortBy'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => loadExpenses(1));
    });

    // Reset Filters Button
    const resetBtn = document.getElementById('resetFiltersBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            document.getElementById('filterCategory').value = '';
            document.getElementById('filterStartDate').value = '';
            document.getElementById('filterEndDate').value = '';
            document.getElementById('sortBy').value = 'date_desc';
            loadExpenses(1);
        });
    }

    // Modal Form Submission
    const expenseForm = document.getElementById('expenseForm');
    if (expenseForm) {
        expenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = expenseForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;

            const payload = {
                amount: parseFloat(document.getElementById('expAmount').value),
                category_id: parseInt(document.getElementById('expCategory').value),
                description: document.getElementById('expDesc').value,
                date: document.getElementById('expDate').value,
                payment_method: document.getElementById('expPayment').value
            };

            try {
                if (currentEditExpenseId) {
                    await apiRequest(`/api/expenses/${currentEditExpenseId}`, {
                        method: 'PUT',
                        body: JSON.stringify(payload)
                    });
                    showToast('Expense updated successfully!', 'success');
                } else {
                    await apiRequest('/api/expenses', {
                        method: 'POST',
                        body: JSON.stringify(payload)
                    });
                    showToast('Expense added successfully!', 'success');
                }

                closeModal('expenseModal');
                loadExpenses();
            } catch (err) {
                // Handled
            } finally {
                submitBtn.disabled = false;
            }
        });
    }
});
