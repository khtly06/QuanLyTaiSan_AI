CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff',
    full_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    user_name TEXT,
    purchase_date TEXT,
    value REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    location TEXT,
    notes TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS inventory_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    expected_status TEXT,
    actual_status TEXT,
    variance_note TEXT,
    FOREIGN KEY (inventory_id) REFERENCES inventory(id),
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    from_department_id INTEGER NOT NULL,
    to_department_id INTEGER NOT NULL,
    transfer_date TEXT NOT NULL,
    reason TEXT,
    notes TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (from_department_id) REFERENCES departments(id),
    FOREIGN KEY (to_department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    request_date TEXT NOT NULL,
    repair_date TEXT,
    status TEXT DEFAULT 'pending',
    description TEXT NOT NULL,
    cost REAL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE TABLE IF NOT EXISTS disposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    disposal_date TEXT NOT NULL,
    reason TEXT NOT NULL,
    liquidation_value REAL DEFAULT 0,
    status TEXT DEFAULT 'requested',
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);
