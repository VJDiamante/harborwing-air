USE harborwing_air;

-- 1. Row Count Verification for all 11 tables
SELECT 'booking_agent' AS table_name, COUNT(*) AS row_count FROM booking_agent
UNION ALL SELECT 'passenger', COUNT(*) FROM passenger
UNION ALL SELECT 'reservation', COUNT(*) FROM reservation
UNION ALL SELECT 'payment', COUNT(*) FROM payment
UNION ALL SELECT 'airport', COUNT(*) FROM airport
UNION ALL SELECT 'flight_schedule', COUNT(*) FROM flight_schedule
UNION ALL SELECT 'flight_leg', COUNT(*) FROM flight_leg
UNION ALL SELECT 'calendar_date', COUNT(*) FROM calendar_date
UNION ALL SELECT 'flight_cost', COUNT(*) FROM flight_cost
UNION ALL SELECT 'reservation_payment', COUNT(*) FROM reservation_payment
UNION ALL SELECT 'reservation_leg', COUNT(*) FROM reservation_leg;

-- 2. View a full reservation (Uses subqueries to avoid double-counting payments/legs)
SELECT 
    r.reservation_id,
    r.creation_datetime,
    r.reservation_status_code,
    r.party_size,
    CONCAT(p.first_name, ' ', COALESCE(CONCAT(p.second_name, ' '), ''), p.last_name) AS main_passenger,
    p.email_address AS passenger_email,
    COALESCE(ba.agent_name, 'Direct Booking (No Agent)') AS booking_agent,
    COALESCE(pay_summary.total_paid, 0.00) AS total_amount_paid,
    COALESCE(leg_summary.leg_count, 0) AS total_legs_booked
FROM reservation r
JOIN passenger p ON r.main_passenger_id = p.passenger_id
LEFT JOIN booking_agent ba ON r.booking_agent_id = ba.agent_id
LEFT JOIN (
    SELECT rp.reservation_id, SUM(pay.payment_amount) AS total_paid
    FROM reservation_payment rp
    JOIN payment pay ON rp.payment_id = pay.payment_id
    GROUP BY rp.reservation_id
) pay_summary ON r.reservation_id = pay_summary.reservation_id
LEFT JOIN (
    SELECT rl.reservation_id, COUNT(rl.leg_id) AS leg_count
    FROM reservation_leg rl
    GROUP BY rl.reservation_id
) leg_summary ON r.reservation_id = leg_summary.reservation_id
WHERE r.reservation_id = 1;

-- 3. Find reservations using a particular leg (Leg ID = 5)
SELECT 
    rl.leg_id,
    fl.flight_number,
    fl.origin_airport_code,
    fl.destination_airport_code,
    r.reservation_id,
    CONCAT(p.first_name, ' ', p.last_name) AS passenger_name,
    r.reservation_status_code
FROM reservation_leg rl
JOIN reservation r ON rl.reservation_id = r.reservation_id
JOIN passenger p ON r.main_passenger_id = p.passenger_id
JOIN flight_leg fl ON rl.leg_id = fl.leg_id
WHERE rl.leg_id = 5;

-- 4. Find payments linked to a reservation (Reservation ID = 1)
SELECT 
    rp.reservation_id,
    p.payment_id,
    p.payment_date,
    p.payment_amount,
    p.payment_status_code
FROM reservation_payment rp
JOIN payment p ON rp.payment_id = p.payment_id
WHERE rp.reservation_id = 1;

-- 5. Find flight cost for a flight, aircraft type, and target date
SELECT 
    fc.flight_number,
    fc.aircraft_type_code,
    fc.cost_amount,
    fc.valid_from_date,
    fc.valid_to_date
FROM flight_cost fc
WHERE fc.flight_number = 'HW101'
  AND fc.aircraft_type_code = 'AT72'
  AND '2026-05-15' BETWEEN fc.valid_from_date AND fc.valid_to_date;