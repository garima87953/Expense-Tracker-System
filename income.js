/**
 * EXPENSE TRACKER - INCOME MANAGEMENT SCRIPT
 */

let currentEditIncomeId = null;

async function loadIncome() {
    const search = document.getElementById('incomeSearch')?.value || '';
    const startDate = document.getElementById('incomeStartDate')?.value || '';
    const endDate = document.getElementById('incomeEndDate')?.value || '';
    const sortBy = document.getElementById('incomeSortBy')?.value || 'date_desc';

    const params = new URLSearchParams({
        search: search,
        start_date: startDate,
        end_date: endDate,
        sort_by: sortBy
    });

    try {
        const data = await apiRequest(`/api/income?${params.toString()}`);
        renderIncomeTable(data.incomes);

        const totalElem = document.getElementById('totalIncomeSum');
        if (totalElem) totalElem.textContent = formatCurrency(data.total_amount);

        const countElem = document.getElementById('incomeCount');
        if (countElem) countElem.textContent = `${data.incomes.length} records`;
    } catch (err) {
        console.error('Failed to load income:', err);
    }
}

function renderIncomeTable(incomes) {
    const tbody = document.getElementById('incomeTableBody');
    if (!tbody) return;

    if (!incomes || incomes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align:center;padding:3rem;color:var(--text-muted);">
                    <div style="font-size:2rem;margin-bottom:0.5rem;">💵</div>
                    <p>No income streams logged yet.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = incomes.map(inc => `
        <tr>
            <td style="font-weight:500;color:var(--text-secondary);">${formatDate(inc.date)}</td>
            <td style="font-weight:600;color:var(--text-primary);">${inc.source}</td>
            <td>
                <span class="category-pill">
                    <span class="category-dot" style="background-color: ${inc.category_color};"></span>
                    ${inc.category_name}
                </span>
            </td>
            <td style="color:var(--text-secondary);">${inc.description || '—'}</td>
            <td style="font-weight:700;font-size:1.05rem;color:var(--success);text-align:right;">
                +${formatCurrency(inc.amount)}
            </td>
            <td style="text-align:right;">
                <div style="display:inline-flex;gap:0.4rem;">
                    <button class="btn btn-outline btn-sm" onclick="editIncome(${inc.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteIncomeRecord(${inc.id})">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function editIncome(id) {
    try {
        const inc = await apiRequest(`/api/income/${id}`);
        currentEditIncomeId = id;

        document.getElementById('incomeModalTitle').textContent = 'Edit Income Stream';
        document.getElementById('incAmount').value = inc.amount;
        document.getElementById('incSource').value = inc.source;
        document.getElementById('incCategory').value = inc.category_id || '';
        document.getElementById('incDesc').value = inc.description;
        document.getElementById('incDate').value = inc.date;

        openModal('incomeModal');
    } catch (err) {
        // Handled
    }
}

function openAddIncomeModal() {
    currentEditIncomeId = null;
    document.getElementById('incomeModalTitle').textContent = 'Add Income Stream';
    const form = document.getElementById('incomeForm');
    if (form) form.reset();
    document.getElementById('incDate').value = new Date().toISOString().split('T')[0];
    openModal('incomeModal');
}

async function deleteIncomeRecord(id) {
    if (!confirm('Are you sure you want to delete this income record?')) return;
    try {
        await apiRequest(`/api/income/${id}`, { method: 'DELETE' });
        showToast('Income entry deleted.', 'success');
        loadIncome();
    } catch (err) {
        // Handled
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadIncome();

    const searchInput = document.getElementById('incomeSearch');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(window.incomeTimer);
            window.incomeTimer = setTimeout(loadIncome, 300);
        });
    }

    ['incomeStartDate', 'incomeEndDate', 'incomeSortBy'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', loadIncome);
    });

    const incomeForm = document.getElementById('incomeForm');
    if (incomeForm) {
        incomeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = incomeForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;

            const payload = {
                amount: parseFloat(document.getElementById('incAmount').value),
                source: document.getElementById('incSource').value,
                category_id: document.getElementById('incCategory').value ? parseInt(document.getElementById('incCategory').value) : null,
                description: document.getElementById('incDesc').value,
                date: document.getElementById('incDate').value
            };

            try {
                if (currentEditIncomeId) {
                    await apiRequest(`/api/income/${currentEditIncomeId}`, {
                        method: 'PUT',
                        body: JSON.stringify(payload)
                    });
                    showToast('Income updated successfully!', 'success');
                } else {
                    await apiRequest('/api/income', {
                        method: 'POST',
                        body: JSON.stringify(payload)
                    });
                    showToast('Income added successfully!', 'success');
                }
                closeModal('incomeModal');
                loadIncome();
            } catch (err) {
                // Handled
            } finally {
                submitBtn.disabled = false;
            }
        });
    }
});
