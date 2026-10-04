CREATE DATABASE IF NOT EXISTS smart_parking;

USE smart_parking;


-- =====================================================
-- USERS
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);


INSERT IGNORE INTO users
(username, password)
VALUES
('admin', 'admin123');


-- =====================================================
-- PARKING SLOTS
-- =====================================================

CREATE TABLE IF NOT EXISTS parking_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slot_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL DEFAULT 'Any',
    status VARCHAR(20) NOT NULL DEFAULT 'Available'
);


-- =====================================================
-- VEHICLES
-- =====================================================

CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(30) UNIQUE NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    owner_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- PARKING RECORDS
-- =====================================================

CREATE TABLE IF NOT EXISTS parking_records (
    id INT AUTO_INCREMENT PRIMARY KEY,

    vehicle_id INT NOT NULL,

    slot_id INT NOT NULL,

    entry_time DATETIME NOT NULL,

    exit_time DATETIME NULL,

    duration VARCHAR(50),

    parking_fee DECIMAL(10,2) DEFAULT 0,

    payment_status VARCHAR(20) DEFAULT 'Pending',

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(id)
        ON DELETE CASCADE,

    FOREIGN KEY (slot_id)
        REFERENCES parking_slots(id)
        ON DELETE CASCADE
);


-- =====================================================
-- SAMPLE PARKING SLOTS
-- =====================================================

INSERT IGNORE INTO parking_slots
(slot_number, vehicle_type, status)
VALUES
('A01', 'Car', 'Available'),
('A02', 'Car', 'Available'),
('A03', 'Car', 'Available'),
('B01', 'Bike', 'Available'),
('B02', 'Bike', 'Available'),
('B03', 'Bike', 'Available'),
('C01', 'SUV', 'Available'),
('C02', 'Any', 'Available'),
('C03', 'Any', 'Available');