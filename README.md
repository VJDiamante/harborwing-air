# HarborWing Air Relational Database System

## System Overview
HarborWing Air is a regional airline. This project replaces spreadsheet tracking with an normalized 3rd Normal Form (3NF) relational database built in MySQL.

## Database Schema Structure
The schema contains 11 core tables:
- **booking_agent**: Optional travel agents handling bookings.
- **passenger**: Contact details for primary flight bookers.
- **reservation**: Core entity for booking statuses and party size.
- **payment**: Financial payment records.
- **airport**: Airport registry and location details.
- **flight_schedule**: Master flight routes and scheduled times.
- **flight_leg**: Executed physical flights with actual arrival/departure times.
- **calendar_date**: Reference date dimension for business tracking.
- **flight_cost**: Dynamic cost rules per aircraft type and validity period.
- **reservation_payment**: Many-to-many bridge table between reservations and payments.
- **reservation_leg**: Many-to-many bridge table connecting itineraries to flight legs.

## Strategic Design Decisions
1. **Linking Tables**: $M:N$ bridging tables allow single payments to cover multiple reservations and single reservations to contain multi-leg itineraries without data duplication.
2. **Scheduled vs. Actual Times**: Scheduled flight times remain unchanged in `flight_schedule`, while operational delays update `flight_leg`, preventing loss of baseline schedule data.
3. **Composite Primary Keys**: `flight_cost` uses `(flight_number, aircraft_type_code, valid_from_date)` to support seasonal and equipment-based price changes.
4. **Simplifying Assumption**: Uses `flight_number` as the schedule primary key. Production systems would require operational keys like `(flight_number, flight_date)` since numbers repeat daily.

## System Setup Instructions
1. Initialize Database Schema:
   `mysql -u root -p < schema.sql`
2. Seed Data (60 rows/table):
   `python seed.py`
3. Verify Query Results:
   `mysql -u root -p harborwing_air < queries.sql`

   ---

## Part 2: CRUD Application Setup

### Overview
A Python/Flask web application connected to the `harborwing_air` database to support full CRUD operations, reservation linkages, and business rules without raw SQL entry[cite: 2, 3].

### Installation & Startup Instructions
1. Navigate to the application folder[cite: 5]:
   ```cmd
   cd application