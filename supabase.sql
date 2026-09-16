CREATE TABLE account (
    user_name TEXT PRIMARY KEY,
    cash TEXT NOT NULL
);

CREATE TABLE positions (
    user_name TEXT,
    symbol TEXT,
    shares TEXT NOT NULL,
    total_cost TEXT NOT NULL,
    PRIMARY KEY (user_name, symbol)
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    shares TEXT NOT NULL,
    price TEXT NOT NULL,
    total TEXT NOT NULL,
    notes TEXT
);

INSERT INTO account (user_name, cash) VALUES ('Juan David', '10000.00'), ('Sebastian', '10000.00');
