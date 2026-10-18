import random
from datetime import datetime, timedelta
from faker import Faker
import mysql.connector

# Fixed seed for 100% reproducible synthetic data
SEED = 42
fake = Faker()
fake.seed_instance(SEED)
random.seed(SEED)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root', 
    'database': 'harborwing_air',
    'autocommit': False
}

def seed_database():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("Connected to MySQL. Generating synthetic data...")

    # 1. Booking Agents (60 rows)
    agent_ids = []
    for _ in range(60):
        query = "INSERT INTO booking_agent (agent_name, agency_name, email, phone, details) VALUES (%s, %s, %s, %s, %s)"
        vals = (fake.name(), fake.company() + " Travel", fake.unique.email(), fake.phone_number()[:20], fake.sentence())
        cursor.execute(query, vals)
        agent_ids.append(cursor.lastrowid)

    # 2. Passengers (60 rows)
    passenger_ids = []
    for _ in range(60):
        query = """INSERT INTO passenger (first_name, second_name, last_name, phone_number, email_address, 
                   address_line1, address_line2, city, state_province, country, other_details) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        vals = (
            fake.first_name(),
            fake.first_name() if random.random() > 0.5 else None,
            fake.last_name(),
            fake.phone_number()[:20],
            fake.unique.email(),
            fake.street_address(),
            fake.secondary_address() if random.random() > 0.5 else None,
            fake.city(),
            fake.state(),
            "Philippines",
            fake.sentence()
        )
        cursor.execute(query, vals)
        passenger_ids.append(cursor.lastrowid)

    # 3. Reservations (60 rows)
    statuses = ['CONFIRMED', 'PENDING', 'CANCELLED', 'CHECKED_IN']
    ticket_types = ['ONE_WAY', 'ROUND_TRIP', 'MULTI_CITY']
    travel_classes = ['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS']
    reservation_ids = []
    
    for i in range(60):
        query = """INSERT INTO reservation (main_passenger_id, booking_agent_id, reservation_status_code, 
                   ticket_type_code, travel_class_code, creation_datetime, party_size) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        agent_id = random.choice(agent_ids) if random.random() > 0.3 else None
        vals = (
            random.choice(passenger_ids),
            agent_id,
            random.choice(statuses),
            random.choice(ticket_types),
            random.choice(travel_classes),
            fake.date_time_between(start_date='-60d', end_date='now'),
            random.randint(1, 6)
        )
        cursor.execute(query, vals)
        reservation_ids.append(cursor.lastrowid)

    # 4. Payments (60 rows)
    payment_statuses = ['COMPLETED', 'REFUNDED', 'PENDING_SETTLEMENT']
    payment_ids = []
    for _ in range(60):
        query = "INSERT INTO payment (payment_status_code, payment_date, payment_amount) VALUES (%s, %s, %s)"
        vals = (
            random.choice(payment_statuses),
            fake.date_time_between(start_date='-60d', end_date='now'),
            round(random.uniform(50.00, 1500.00), 2)
        )
        cursor.execute(query, vals)
        payment_ids.append(cursor.lastrowid)

    # 5. Airports (60 entries)
    airports = [
        ('MNL', 'Ninoy Aquino Intl', 'Manila, Philippines'),
        ('PPS', 'Puerto Princesa Intl', 'Palawan, Philippines'),
        ('CEB', 'Mactan-Cebu Intl', 'Cebu, Philippines'),
        ('DVO', 'Francisco Bangoy Intl', 'Davao, Philippines'),
        ('ILO', 'Iloilo Intl', 'Iloilo, Philippines'),
        ('BCD', 'Bacolod-Silay Airport', 'Bacolod, Philippines'),
        ('TAG', 'Bohol-Panglao Intl', 'Bohol, Philippines'),
        ('USM', 'Koh Samui Airport', 'Surat Thani, Thailand'),
        ('DPS', 'Ngurah Rai Intl', 'Bali, Indonesia'),
        ('BWN', 'Brunei Intl Airport', 'Bandar Seri Begawan, Brunei')
    ]
    for i in range(1, 51):
        airports.append((f"D{i:02d}", f"Demo Airport {i}", f"Demo Location {i}"))

    for code, name, loc in airports:
        query = "INSERT INTO airport (airport_code, name, location, other_details) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (code, name, loc, "Demonstration regional hub"))

    airport_codes = [a[0] for a in airports]

    # 6. Flight Schedules (60 rows)
    aircraft_types = ['AT72', 'Q400', 'A320', 'A321']
    flight_numbers = []
    for i in range(1, 61):
        fn = f"HW{100+i}"
        flight_numbers.append(fn)
        orig, dest = random.sample(airport_codes, 2)
        dep_time = fake.date_time_between(start_date='now', end_date='+30d')
        arr_time = dep_time + timedelta(hours=random.randint(1, 4))
        
        query = """INSERT INTO flight_schedule (flight_number, airline_code, usual_aircraft_type_code, 
                   origin_airport_code, destination_airport_code, scheduled_departure_time, scheduled_arrival_time) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (fn, 'HW', random.choice(aircraft_types), orig, dest, dep_time, arr_time))

    # 7. Flight Legs (60 rows)
    leg_ids = []
    for i in range(60):
        fn = flight_numbers[i]
        orig, dest = random.sample(airport_codes, 2)
        sched_dep = fake.date_time_between(start_date='-30d', end_date='now')
        if random.random() > 0.2:
            act_dep = sched_dep + timedelta(minutes=random.randint(-10, 45))
            act_arr = act_dep + timedelta(hours=random.randint(1, 3))
        else:
            act_dep, act_arr = None, None

        query = """INSERT INTO flight_leg (flight_number, origin_airport_code, destination_airport_code, 
                   actual_departure_time, actual_arrival_time) VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(query, (fn, orig, dest, act_dep, act_arr))
        leg_ids.append(cursor.lastrowid)

    # 8. Calendar Dates (60 continuous days)
    start_cal = datetime(2026, 5, 1).date()
    calendar_dates = []
    for i in range(60):
        cur_date = start_cal + timedelta(days=i)
        calendar_dates.append(cur_date)
        is_biz = 1 if cur_date.weekday() < 5 else 0
        query = "INSERT INTO calendar_date (calendar_date, day_of_month, business_day_indicator) VALUES (%s, %s, %s)"
        cursor.execute(query, (cur_date, cur_date.day, is_biz))

    # 9. Flight Costs (60 rows)
    for i in range(60):
        fn = flight_numbers[i]
        ac = random.choice(aircraft_types)
        v_from = calendar_dates[i % 30]
        v_to = calendar_dates[(i % 30) + 25]
        cost = round(random.uniform(120.00, 850.00), 2)

        query = """INSERT INTO flight_cost (flight_number, aircraft_type_code, valid_from_date, valid_to_date, cost_amount) 
                   VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(query, (fn, ac, v_from, v_to, cost))

    # 10. Reservation-Payment Links (60 unique pairs)
    res_pay_pairs = set()
    while len(res_pay_pairs) < 60:
        res_pay_pairs.add((random.choice(reservation_ids), random.choice(payment_ids)))

    for r_id, p_id in res_pay_pairs:
        query = "INSERT INTO reservation_payment (reservation_id, payment_id) VALUES (%s, %s)"
        cursor.execute(query, (r_id, p_id))

    # 11. Reservation-Leg Links (60 unique pairs)
    res_leg_pairs = set()
    while len(res_leg_pairs) < 60:
        res_leg_pairs.add((random.choice(reservation_ids), random.choice(leg_ids)))

    for r_id, l_id in res_leg_pairs:
        query = "INSERT INTO reservation_leg (reservation_id, leg_id) VALUES (%s, %s)"
        cursor.execute(query, (r_id, l_id))

    conn.commit()
    cursor.close()
    conn.close()
    print("Database successfully seeded with >= 60 rows per table!")

if __name__ == '__main__':
    seed_database()