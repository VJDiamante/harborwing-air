-- HarborWing Air Relational Database Schema Creation Script
-- Target Engine: MySQL 8.0+ / InnoDB

DROP DATABASE IF EXISTS harborwing_air;
CREATE DATABASE harborwing_air CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE harborwing_air;

-- 1. Booking Agent Table
CREATE TABLE booking_agent (
    agent_id INT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    agency_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL,
    details TEXT NULL
) ENGINE=InnoDB;

-- 2. Passenger Table
CREATE TABLE passenger (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    second_name VARCHAR(50) NULL,
    last_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(30) NOT NULL,
    email_address VARCHAR(100) NOT NULL UNIQUE,
    address_line1 VARCHAR(150) NOT NULL,
    address_line2 VARCHAR(150) NULL,
    city VARCHAR(50) NOT NULL,
    state_province VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,
    other_details TEXT NULL
) ENGINE=InnoDB;

-- 3. Reservation Table
CREATE TABLE reservation (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    main_passenger_id INT NOT NULL,
    booking_agent_id INT NULL,
    reservation_status_code VARCHAR(20) NOT NULL,
    ticket_type_code VARCHAR(20) NOT NULL,
    travel_class_code VARCHAR(20) NOT NULL,
    creation_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    party_size INT NOT NULL,
    CONSTRAINT chk_party_size CHECK (party_size > 0),
    CONSTRAINT fk_res_passenger FOREIGN KEY (main_passenger_id) 
        REFERENCES passenger(passenger_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_res_agent FOREIGN KEY (booking_agent_id) 
        REFERENCES booking_agent(agent_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4. Payment Table
CREATE TABLE payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_status_code VARCHAR(20) NOT NULL,
    payment_date DATETIME NOT NULL,
    payment_amount DECIMAL(10,2) NOT NULL,
    CONSTRAINT chk_payment_amount CHECK (payment_amount > 0.00)
) ENGINE=InnoDB;

-- 5. Airport Table
CREATE TABLE airport (
    airport_code CHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    other_details TEXT NULL
) ENGINE=InnoDB;

-- 6. Flight Schedule Table
CREATE TABLE flight_schedule (
    flight_number VARCHAR(10) PRIMARY KEY,
    airline_code CHAR(2) NOT NULL,
    usual_aircraft_type_code VARCHAR(20) NOT NULL,
    origin_airport_code CHAR(3) NOT NULL,
    destination_airport_code CHAR(3) NOT NULL,
    scheduled_departure_time DATETIME NOT NULL,
    scheduled_arrival_time DATETIME NOT NULL,
    CONSTRAINT fk_sched_origin FOREIGN KEY (origin_airport_code) 
        REFERENCES airport(airport_code) ON DELETE RESTRICT,
    CONSTRAINT fk_sched_dest FOREIGN KEY (destination_airport_code) 
        REFERENCES airport(airport_code) ON DELETE RESTRICT,
    CONSTRAINT chk_schedule_airports CHECK (origin_airport_code <> destination_airport_code),
    CONSTRAINT chk_schedule_times CHECK (scheduled_arrival_time > scheduled_departure_time)
) ENGINE=InnoDB;

-- 7. Flight Leg Table
CREATE TABLE flight_leg (
    leg_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    origin_airport_code CHAR(3) NOT NULL,
    destination_airport_code CHAR(3) NOT NULL,
    actual_departure_time DATETIME NULL,
    actual_arrival_time DATETIME NULL,
    CONSTRAINT fk_leg_flight FOREIGN KEY (flight_number) 
        REFERENCES flight_schedule(flight_number) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_leg_origin FOREIGN KEY (origin_airport_code) 
        REFERENCES airport(airport_code) ON DELETE RESTRICT,
    CONSTRAINT fk_leg_dest FOREIGN KEY (destination_airport_code) 
        REFERENCES airport(airport_code) ON DELETE RESTRICT,
    CONSTRAINT chk_leg_airports CHECK (origin_airport_code <> destination_airport_code)
) ENGINE=InnoDB;

-- 8. Calendar Date Table
CREATE TABLE calendar_date (
    calendar_date DATE PRIMARY KEY,
    day_of_month INT NOT NULL,
    business_day_indicator TINYINT(1) NOT NULL,
    CONSTRAINT chk_day_of_month CHECK (day_of_month BETWEEN 1 AND 31),
    CONSTRAINT chk_business_day CHECK (business_day_indicator IN (0, 1))
) ENGINE=InnoDB;

-- 9. Flight Cost Table
CREATE TABLE flight_cost (
    flight_number VARCHAR(10) NOT NULL,
    aircraft_type_code VARCHAR(20) NOT NULL,
    valid_from_date DATE NOT NULL,
    valid_to_date DATE NOT NULL,
    cost_amount DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (flight_number, aircraft_type_code, valid_from_date),
    CONSTRAINT chk_validity_dates CHECK (valid_to_date >= valid_from_date),
    CONSTRAINT chk_cost_positive CHECK (cost_amount >= 0.00),
    CONSTRAINT fk_cost_flight FOREIGN KEY (flight_number) 
        REFERENCES flight_schedule(flight_number) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cost_valid_from FOREIGN KEY (valid_from_date) 
        REFERENCES calendar_date(calendar_date) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_cost_valid_to FOREIGN KEY (valid_to_date) 
        REFERENCES calendar_date(calendar_date) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 10. Reservation-Payment Link Table (M:N)
CREATE TABLE reservation_payment (
    reservation_id INT NOT NULL,
    payment_id INT NOT NULL,
    PRIMARY KEY (reservation_id, payment_id),
    CONSTRAINT fk_rp_reservation FOREIGN KEY (reservation_id) 
        REFERENCES reservation(reservation_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rp_payment FOREIGN KEY (payment_id) 
        REFERENCES payment(payment_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 11. Reservation-Leg Link Table (M:N)
CREATE TABLE reservation_leg (
    reservation_id INT NOT NULL,
    leg_id INT NOT NULL,
    PRIMARY KEY (reservation_id, leg_id),
    CONSTRAINT fk_rl_reservation FOREIGN KEY (reservation_id) 
        REFERENCES reservation(reservation_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rl_leg FOREIGN KEY (leg_id) 
        REFERENCES flight_leg(leg_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Indexes for performance optimization
CREATE INDEX idx_passenger_name ON passenger(last_name, first_name);
CREATE INDEX idx_reservation_passenger ON reservation(main_passenger_id);
CREATE INDEX idx_reservation_agent ON reservation(booking_agent_id);
CREATE INDEX idx_leg_flight ON flight_leg(flight_number);
CREATE INDEX idx_schedule_route ON flight_schedule(origin_airport_code, destination_airport_code);