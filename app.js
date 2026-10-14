/**
 * EXPENSE TRACKER - CORE FRONTEND JAVASCRIPT
 * Global utilities, theme manager, toast system, modals, and shared API helpers.
 */

// Theme Management (Supports: dark, light, and cute Sakura mode)
function initTheme() {
    const savedTheme = localStorage.getItem('et_theme') || 'cute'; // Default to cute Sakura for aesthetic delight!
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'cute';
            let nextTheme = 'cute';
            if (currentTheme === 'dark') nextTheme = 'light';
            else if (currentTheme === 'light') nextTheme = 'cute';
            else nextTheme = 'dark';

            document.documentElement.setAttribute('data-theme', nextTheme);
            localStorage.setItem('et_theme', nextTheme);
            updateThemeIcon(nextTheme);
            
            showToast(`Theme switched to ${nextTheme === 'cute' ? '🌸 Pastel Sakura' : (nextTheme === 'dark' ? '🌙 Dark Cyber' : '☀️ Crisp Light')}`, 'info', 2000);

            // Re-render charts with new theme colors if Chart.js is active
            if (window.renderAllCharts) {
                window.renderAllCharts();
            }
        });
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (icon) {
        if (theme === 'cute') icon.textContent = '🌸';
        else if (theme === 'light') icon.textContent = '☀️';
        else icon.textContent = '🌙';
    }
}

// Sidebar Mobile Toggle
function initSidebar() {
    const toggleBtn = document.getElementById('menuToggleBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
}

// Toast Notifications System
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconMap = {
        success: '✓',
        danger: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.75rem;">
            <span style="font-weight:700;font-size:1.1rem;">${iconMap[type] || 'ℹ'}</span>
            <span>${message}</span>
        </div>
        <button style="background:none;border:none;color:inherit;cursor:pointer;font-size:1.1rem;margin-left:1rem;" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Modal Helpers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Formatters
function formatCurrency(amount, currency = null) {
    const symbol = window.APP_CURRENCY_SYMBOL || '$';
    const num = parseFloat(amount || 0);
    return `${symbol}${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

// API Request Wrapper
async function apiRequest(url, options = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };

    options.headers = { ...defaultHeaders, ...(options.headers || {}) };

    try {
        const response = await fetch(url, options);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || `Request failed (${response.status})`);
        }
        return data;
    } catch (err) {
        showToast(err.message, 'danger');
        throw err;
    }
}

// Global Quick Action Modals (Add Expense & Add Income)
function initGlobalModals() {
    // Populate today's date on all date fields
    const todayStr = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"]').forEach(inp => {
        if (!inp.value) inp.value = todayStr;
    });

    // Close modals on clicking backdrop
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                backdrop.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });

    // Global Add Expense Form Submit
    const quickExpenseForm = document.getElementById('quickExpenseForm');
    if (quickExpenseForm) {
        quickExpenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = quickExpenseForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';

            const payload = {
                amount: parseFloat(document.getElementById('quickExpAmount').value),
                category_id: parseInt(document.getElementById('quickExpCategory').value),
                description: document.getElementById('quickExpDesc').value,
                date: document.getElementById('quickExpDate').value,
                payment_method: document.getElementById('quickExpPayment').value
            };

            try {
                await apiRequest('/api/expenses', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                triggerConfetti();
                showToast('Expense logged successfully! ✨', 'success');
                closeModal('quickExpenseModal');
                quickExpenseForm.reset();
                document.getElementById('quickExpDate').value = todayStr;

                // Reload current view data if functions exist
                if (window.loadDashboardData) window.loadDashboardData();
                if (window.loadExpenses) window.loadExpenses();
                if (window.loadBudgets) window.loadBudgets();
            } catch (err) {
                // Handled in apiRequest
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Add Expense';
            }
        });
    }

    // Global Add Income Form Submit
    const quickIncomeForm = document.getElementById('quickIncomeForm');
    if (quickIncomeForm) {
        quickIncomeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = quickIncomeForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';

            const payload = {
                amount: parseFloat(document.getElementById('quickIncAmount').value),
                source: document.getElementById('quickIncSource').value,
                category_id: document.getElementById('quickIncCategory').value ? parseInt(document.getElementById('quickIncCategory').value) : null,
                description: document.getElementById('quickIncDesc').value,
                date: document.getElementById('quickIncDate').value
            };

            try {
                await apiRequest('/api/income', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                triggerConfetti();
                showToast('Income added successfully! 💰✨', 'success');
                closeModal('quickIncomeModal');
                quickIncomeForm.reset();
                document.getElementById('quickIncDate').value = todayStr;

                if (window.loadDashboardData) window.loadDashboardData();
                if (window.loadIncome) window.loadIncome();
            } catch (err) {
                // Handled in apiRequest
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Add Income';
            }
        });
    }
}

// Pure Vanilla JS Confetti Animation
function triggerConfetti() {
    const count = 35;
    const colors = ['#f43f5e', '#ec4899', '#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#fb7185', '#38bdf8'];

    for (let i = 0; i < count; i++) {
        const conf = document.createElement('div');
        conf.style.position = 'fixed';
        conf.style.zIndex = '99999';
        conf.style.left = `${Math.random() * 100}vw`;
        conf.style.top = '-10px';
        conf.style.width = `${Math.random() * 8 + 6}px`;
        conf.style.height = `${Math.random() * 8 + 6}px`;
        conf.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        conf.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
        conf.style.pointerEvents = 'none';
        conf.style.opacity = '0.9';
        conf.style.transform = `rotate(${Math.random() * 360}deg)`;
        conf.style.transition = `transform ${Math.random() * 1.6 + 1.2}s cubic-bezier(0.25, 1, 0.5, 1), top ${Math.random() * 1.6 + 1.2}s cubic-bezier(0.25, 1, 0.5, 1), opacity 1.6s ease-out`;

        document.body.appendChild(conf);

        requestAnimationFrame(() => {
            conf.style.top = `${Math.random() * 70 + 40}vh`;
            conf.style.transform = `translateX(${(Math.random() - 0.5) * 180}px) rotate(${Math.random() * 720}deg)`;
            conf.style.opacity = '0';
        });

        setTimeout(() => conf.remove(), 2600);
    }
}

// Quick Preset Helper
function quickAddPreset(amount, categoryId, desc) {
    const amtInput = document.getElementById('quickExpAmount');
    const catInput = document.getElementById('quickExpCategory');
    const descInput = document.getElementById('quickExpDesc');

    if (amtInput) amtInput.value = amount;
    if (catInput) catInput.value = categoryId;
    if (descInput) descInput.value = desc;

    openModal('quickExpenseModal');
    showToast(`Preset ready: ${desc} ($${amount}) 🌸`, 'info', 2000);
}

// Mascot Companion Interactive Fortune / Affirmation
const PIGGY_FORTUNES = [
    "Penny the Piggy says: Every dollar saved is a step closer to your dream adventure! 🌸✈️",
    "Penny whisper: Skipped an impulse purchase today? You are an absolute superstar! 🍓✨",
    "Penny wisdom: Peace of mind begins with a happy emergency fund! Keep glowing! 💖",
    "Penny reminder: Treating yourself is allowed, just budget for boba first! 🧋🍰",
    "Penny cheer: Your financial habits are looking extra cute today! 🐷🎉",
    "Penny fortune: Mindful spenders attract abundance and lucky coin showers! 🍀💰"
];

function interactWithMascot() {
    const avatar = document.getElementById('mascotAvatar');
    const bubble = document.getElementById('mascotBubbleMsg');
    if (!bubble) return;

    triggerConfetti();
    const fortune = PIGGY_FORTUNES[Math.floor(Math.random() * PIGGY_FORTUNES.length)];
    bubble.innerHTML = `<strong>✨ Penny says:</strong> ${fortune}`;

    if (avatar) {
        avatar.style.transform = 'scale(1.25) rotate(15deg)';
        setTimeout(() => {
            avatar.style.transform = '';
        }, 400);
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSidebar();
    initGlobalModals();
});
