import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "harborwing_secret_key_123")


# --- HOMEPAGE / DASHBOARD ROUTE ---
@app.route('/')
def index():
    conn = get_db_connection()
    conn.commit()  # Forces connection sync
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT passenger_id, first_name, last_name FROM passenger ORDER BY passenger_id DESC LIMIT 20")
    passengers = cursor.fetchall()

    cursor.execute("SELECT leg_id, flight_number, origin_airport_code, destination_airport_code FROM flight_leg LIMIT 30")
    legs = cursor.fetchall()

    cursor.execute("SELECT reservation_id FROM reservation ORDER BY reservation_id DESC LIMIT 30")
    reservation_options = cursor.fetchall()

    cursor.execute("""
        SELECT 
            r.reservation_id, 
            COALESCE(CONCAT(p.first_name, ' ', p.last_name), 'Unassigned') AS passenger_name, 
            r.party_size, 
            r.reservation_status_code,
            r.creation_datetime
        FROM reservation r 
        LEFT JOIN passenger p ON r.main_passenger_id = p.passenger_id 
        ORDER BY r.reservation_id DESC 
        LIMIT 10
    """)
    reservations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'index.html', 
        passengers=passengers, 
        legs=legs, 
        reservation_options=reservation_options,
        reservations=reservations
    )


# --- 1 & 2. WORKFLOW STEP 1 & 2: CREATE PASSENGER & RESERVATION ---
@app.route('/create_reservation', methods=['POST'])
def create_reservation():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone = request.form['phone']
    party_size = request.form['party_size']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO passenger 
            (first_name, last_name, email_address, phone_number, address_line1, city, state_province, country) 
            VALUES (%s, %s, %s, %s, '123 Main St', 'Manila', 'NCR', 'Philippines')
            """,
            (first_name, last_name, email, phone)
        )
        passenger_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO reservation 
            (main_passenger_id, booking_agent_id, reservation_status_code, ticket_type_code, travel_class_code, creation_datetime, party_size) 
            VALUES (%s, NULL, 'CONFIRMED', 'ONE_WAY', 'ECONOMY', NOW(), %s)
            """,
            (passenger_id, party_size)
        )
        reservation_id = cursor.lastrowid

        conn.commit()
        flash(f"Success! Created Passenger #{passenger_id} and Reservation #{reservation_id}.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Database Error: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))


# --- 3. WORKFLOW STEP 3: LINK FLIGHT LEG ---
@app.route('/link_leg', methods=['POST'])
def link_leg():
    reservation_id = request.form['reservation_id']
    leg_id = request.form['leg_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO reservation_leg (reservation_id, leg_id) VALUES (%s, %s)",
            (reservation_id, leg_id)
        )
        conn.commit()
        flash(f"Flight Leg #{leg_id} linked successfully to Reservation #{reservation_id}!", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062:
            flash(f"Error: Flight Leg #{leg_id} is ALREADY linked to Reservation #{reservation_id}!", "danger")
        else:
            flash(f"Database Error: {err.msg}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))


# --- 4. WORKFLOW STEP 4: CREATE & LINK PAYMENT ---
@app.route('/add_payment', methods=['POST'])
def add_payment():
    reservation_id = request.form['reservation_id']
    amount = request.form['amount']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO payment (payment_date, payment_amount, payment_status_code) VALUES (NOW(), %s, 'COMPLETED')",
            (amount,)
        )
        payment_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO reservation_payment (reservation_id, payment_id) VALUES (%s, %s)",
            (reservation_id, payment_id)
        )
        conn.commit()
        flash(f"Payment #{payment_id} of ${amount} successfully linked to Reservation #{reservation_id}!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error linking payment: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))


# --- 5. WORKFLOW STEP 5: VIEW COMPLETE RESERVATION ---
@app.route('/reservation/<int:reservation_id>')
def view_reservation(reservation_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            r.reservation_id, r.reservation_status_code, r.ticket_type_code,
            r.travel_class_code, r.party_size, r.creation_datetime,
            p.passenger_id, CONCAT(p.first_name, ' ', p.last_name) AS main_passenger_name,
            p.email_address, p.phone_number
        FROM reservation r
        JOIN passenger p ON r.main_passenger_id = p.passenger_id
        WHERE r.reservation_id = %s
    """, (reservation_id,))
    reservation = cursor.fetchone()

    if not reservation:
        flash(f"Reservation #{reservation_id} not found!", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute("""
        SELECT fl.leg_id, fl.flight_number, fl.origin_airport_code, fl.destination_airport_code
        FROM reservation_leg rl
        JOIN flight_leg fl ON rl.leg_id = fl.leg_id
        WHERE rl.reservation_id = %s
    """, (reservation_id,))
    linked_legs = cursor.fetchall()

    cursor.execute("""
        SELECT p.payment_id, p.payment_amount, p.payment_status_code, p.payment_date
        FROM reservation_payment rp
        JOIN payment p ON rp.payment_id = p.payment_id
        WHERE rp.reservation_id = %s
    """, (reservation_id,))
    linked_payments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('reservation_detail.html', reservation=reservation, legs=linked_legs, payments=linked_payments)


# --- 6. WORKFLOW STEP 6: UPDATE A RECORD ---
@app.route('/update_reservation', methods=['POST'])
def update_reservation():
    reservation_id = request.form['reservation_id']
    status_code = request.form['status_code']
    party_size = request.form['party_size']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE reservation 
            SET reservation_status_code = %s, party_size = %s 
            WHERE reservation_id = %s
            """,
            (status_code, party_size, reservation_id)
        )
        conn.commit()
        flash(f"Reservation #{reservation_id} updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error updating reservation: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))


# --- 7. WORKFLOW STEP 7: REMOVE LINK (UNLINK LEG) ---
@app.route('/unlink_leg', methods=['POST'])
def unlink_leg():
    reservation_id = request.form['reservation_id']
    leg_id = request.form['leg_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM reservation_leg WHERE reservation_id = %s AND leg_id = %s",
            (reservation_id, leg_id)
        )
        conn.commit()
        flash(f"Flight Leg #{leg_id} unlinked from Reservation #{reservation_id} (Master Flight Leg record intact).", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error unlinking leg: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))


# --- 8 & 9. WORKFLOW STEP 8 & 9: SAFELY DELETE RECORD & HANDLE ERROR ---
@app.route('/delete_passenger', methods=['POST'])
def delete_passenger():
    passenger_id = request.form['passenger_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM passenger WHERE passenger_id = %s", (passenger_id,))
        conn.commit()
        flash(f"Passenger #{passenger_id} deleted successfully.", "success")
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1451:
            flash(f"Cannot delete Passenger #{passenger_id}: Active reservations exist for this passenger!", "danger")
        else:
            flash(f"Error deleting record: {err.msg}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)