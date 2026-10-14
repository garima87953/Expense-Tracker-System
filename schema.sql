-- ============================================================
-- EXPENSE TRACKER DATABASE SCHEMA (MySQL 8.0+ & SQL Standards)
-- ============================================================

CREATE DATABASE IF NOT EXISTS expense_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE expense_tracker;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. CATEGORIES TABLE
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'expense', -- 'expense' or 'income'
    icon VARCHAR(50) NOT NULL DEFAULT 'tag',
    color VARCHAR(20) NOT NULL DEFAULT '#6366f1',
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_category_user (user_id),
    INDEX idx_category_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. EXPENSES TABLE
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    description VARCHAR(255) DEFAULT '',
    date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL DEFAULT 'Credit Card',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_expense_user_date (user_id, date),
    INDEX idx_expense_user_category (user_id, category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. INCOME TABLE
CREATE TABLE IF NOT EXISTS income (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    source VARCHAR(100) NOT NULL,
    description VARCHAR(255) DEFAULT '',
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_income_user_date (user_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. BUDGETS TABLE
CREATE TABLE IF NOT EXISTS budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NULL, -- NULL represents total monthly budget, non-null represents category budget
    amount DECIMAL(10, 2) NOT NULL,
    month_year VARCHAR(7) NOT NULL, -- Format 'YYYY-MM'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_cat_month (user_id, category_id, month_year),
    INDEX idx_budget_user_month (user_id, month_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. GOALS TABLE (Savings Goals & Piggy Banks)
CREATE TABLE IF NOT EXISTS goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    target_amount DECIMAL(10, 2) NOT NULL,
    saved_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    target_date DATE NULL,
    icon VARCHAR(50) NOT NULL DEFAULT '🐷',
    color VARCHAR(20) NOT NULL DEFAULT '#ec4899',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_goal_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- SEED DATA: Default Categories
-- ============================================================
INSERT INTO categories (user_id, name, type, icon, color, is_default) VALUES
(NULL, 'Food & Dining', 'expense', 'utensils', '#ef4444', TRUE),
(NULL, 'Shopping', 'expense', 'shopping-bag', '#f59e0b', TRUE),
(NULL, 'Transportation', 'expense', 'car', '#3b82f6', TRUE),
(NULL, 'Rent & Housing', 'expense', 'home', '#8b5cf6', TRUE),
(NULL, 'Bills & Utilities', 'expense', 'zap', '#06b6d4', TRUE),
(NULL, 'Entertainment', 'expense', 'film', '#ec4899', TRUE),
(NULL, 'Healthcare', 'expense', 'heart-pulse', '#10b981', TRUE),
(NULL, 'Education', 'expense', 'book-open', '#14b8a6', TRUE),
(NULL, 'Travel', 'expense', 'plane', '#6366f1', TRUE),
(NULL, 'Other', 'expense', 'more-horizontal', '#64748b', TRUE),
(NULL, 'Salary', 'income', 'briefcase', '#10b981', TRUE),
(NULL, 'Freelance', 'income', 'laptop', '#3b82f6', TRUE),
(NULL, 'Investments', 'income', 'trending-up', '#8b5cf6', TRUE),
(NULL, 'Gifts & Other', 'income', 'gift', '#f59e0b', TRUE)
ON DUPLICATE KEY UPDATE name=name;

-- ============================================================
-- SAMPLE DATA (Demo User & Transactions)
-- Default Demo User: demo@example.com / Password: Password123!
-- PBKDF2 hashed password for 'Password123!'
-- ============================================================
INSERT INTO users (id, username, email, password_hash, currency) VALUES
(1, 'demouser', 'demo@example.com', 'scrypt:32768:8:1$Kq1Zg6hZ0wA1$1169e5d4cb058e5f223789a6ea8d4baee1c7cb3fa0f670f55cf5ad943261621f3d8f8a85f850e50f38b2512a8838d2fef8b894bf8cbf85871dfa27170884d509', 'USD')
ON DUPLICATE KEY UPDATE username=username;

-- Demo Income
INSERT INTO income (user_id, category_id, amount, source, description, date) VALUES
(1, 11, 4500.00, 'Monthly Salary', 'Tech Corp Monthly Paycheck', '2026-10-01'),
(1, 12, 850.00, 'Freelance Client', 'Website redesign milestone 1', '2026-10-04'),
(1, 13, 175.50, 'Dividend Payout', 'Vanguard Total Stock Index', '2026-10-06');

-- Demo Expenses
INSERT INTO expenses (user_id, category_id, amount, description, date, payment_method) VALUES
(1, 4, 1400.00, 'Apartment Monthly Rent', '2026-10-01', 'Bank Transfer'),
(1, 1, 125.80, 'Weekly Grocery Haul', '2026-10-02', 'Credit Card'),
(1, 5, 85.50, 'Electric & Water Utility', '2026-10-03', 'Debit Card'),
(1, 3, 45.00, 'Metro Transit Pass', '2026-10-03', 'Credit Card'),
(1, 1, 34.50, 'Dinner with Colleagues', '2026-10-04', 'Cash'),
(1, 2, 89.99, 'Running Shoes on Sale', '2026-10-05', 'Credit Card'),
(1, 6, 19.99, 'Netflix & Spotify Subs', '2026-10-05', 'Credit Card'),
(1, 7, 50.00, 'Pharmacy prescription', '2026-10-06', 'Debit Card'),
(1, 1, 62.10, 'Weekend Sushi Dinner', '2026-10-07', 'Credit Card');

-- Demo Budgets for Month 2026-10
INSERT INTO budgets (user_id, category_id, amount, month_year) VALUES
(1, NULL, 3000.00, '2026-10'),
(1, 1, 500.00, '2026-10'),
(1, 2, 300.00, '2026-10'),
(1, 3, 200.00, '2026-10'),
(1, 4, 1500.00, '2026-10'),
(1, 6, 150.00, '2026-10');
