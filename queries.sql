-- Query 1: Viewing a reservation with its passenger, agent, payments, and legs
SELECT 
    r.reservation_id,
    r.creation_datetime,
    r.reservation_status_code,
    r.party_size,
    CONCAT(p.first_name, ' ', p.last_name) AS main_passenger,
    p.email_address AS passenger_email,
    COALESCE(a.agent_name, 'Direct Booking') AS booking_agent,
    COALESCE(pay_totals.total_paid, 0.00) AS total_amount_paid,
    COALESCE(leg_counts.total_legs, 0) AS total_legs_booked
FROM reservation r
JOIN passenger p ON r.main_passenger_id = p.passenger_id
LEFT JOIN booking_agent a ON r.booking_agent_id = a.agent_id
LEFT JOIN (
    SELECT rp.reservation_id, SUM(py.payment_amount) AS total_paid
    FROM reservation_payment rp
    JOIN payment py ON rp.payment_id = py.payment_id
    GROUP BY rp.reservation_id
) pay_totals ON r.reservation_id = pay_totals.reservation_id
LEFT JOIN (
    SELECT reservation_id, COUNT(leg_id) AS total_legs
    FROM reservation_leg
    GROUP BY reservation_id
) leg_counts ON r.reservation_id = leg_counts.reservation_id
LIMIT 1;

-- Query 2: Finding reservations using a particular leg
SELECT 
    fl.leg_id,
    fl.flight_number,
    fl.origin_airport_code,
    fl.destination_airport_code,
    r.reservation_id,
    CONCAT(p.first_name, ' ', p.last_name) AS passenger_name,
    r.reservation_status_code
FROM flight_leg fl
JOIN reservation_leg rl ON fl.leg_id = rl.leg_id
JOIN reservation r ON rl.reservation_id = r.reservation_id
JOIN passenger p ON r.main_passenger_id = p.passenger_id
LIMIT 1;

-- Query 3: Finding payments linked to a reservation
SELECT 
    r.reservation_id,
    p.payment_id,
    p.payment_date,
    p.payment_amount,
    p.payment_status_code
FROM reservation r
JOIN reservation_payment rp ON r.reservation_id = rp.reservation_id
JOIN payment p ON rp.payment_id = p.payment_id
LIMIT 1;

-- Query 4: Finding a flight cost for a flight, aircraft type, and date
SELECT 
    fc.flight_number,
    fc.aircraft_type_code,
    fc.valid_from_date,
    fc.valid_to_date,
    fc.cost_amount
FROM flight_cost fc
ORDER BY fc.valid_from_date ASC
LIMIT 1;