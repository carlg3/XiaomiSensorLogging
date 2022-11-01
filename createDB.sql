CREATE TABLE reading (
	timestamp DATE DEFAULT (datetime('now', 'localtime')) PRIMARY KEY,
	temperature REAL,
	humidity INT,
	battery_voltage REAL,
	battery_percent INT
)
