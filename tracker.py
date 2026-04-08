import csv
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from dotenv import load_dotenv
load_dotenv()

from fli.search import SearchFlights
from fli.models import (
    FlightSearchFilters,
    FlightSegment,
    Airport,
    SeatType,
    TripType,
    PassengerInfo,
    SortBy,
    MaxStops,
)

# ── CONFIGURATION ──────────────────────────────────────
ORIGIN      = Airport.LAX
DESTINATION = Airport.AGU
TARGET_DATE = "2026-05-29"
DATE_RANGE  = 5
ALERT_PRICE = 150

EMAIL_SENDER   = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

CSV_FILE = "prices.csv"
# ───────────────────────────────────────────────────────


def get_date_range():
    """Generate all dates to search: target date ± DATE_RANGE days."""
    center = datetime.strptime(TARGET_DATE, "%Y-%m-%d")
    dates = []
    for i in range(-DATE_RANGE, DATE_RANGE + 1):
        d = center + timedelta(days=i)
        dates.append(d.strftime("%Y-%m-%d"))
    return dates


def search_date(date):
    """Search direct flights for a single date, return cheapest price."""
    filters = FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[ORIGIN, 0]],
                arrival_airport=[[DESTINATION, 0]],
                travel_date=date,
            )
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.NON_STOP,
        sort_by=SortBy.CHEAPEST,
    )

    search = SearchFlights()
    results = search.search(filters)

    if not results:
        return None

    return results[0].price


def find_best_dates():
    """Search all dates in range, return sorted list of (date, price)."""
    dates = get_date_range()
    results = []

    for date in dates:
        print(f"Searching {date}...")
        price = search_date(date)
        if price is not None:
            print(f"  → ${price}")
            results.append((date, price))
        else:
            print(f"  → No direct flights found")

    results.sort(key=lambda x: x[1])
    return results


def save_to_csv(results):
    """Save today's search results to the CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["timestamp", "date", "price"])

        for date, price in results:
            writer.writerow([timestamp, date, price])

    print(f"Saved {len(results)} results to {CSV_FILE}")


def send_email(results):
    """Send an email alert with the top 3 cheapest dates."""
    top3 = results[:3]

    lines = ["Good news! Prices are looking good for your trip:\n"]
    for i, (date, price) in enumerate(top3, start=1):
        lines.append(f"  #{i}  {date}  →  ${price}")

    lines.append(f"\nYour alert threshold: ${ALERT_PRICE}")
    lines.append("Check Google Flights to book!")
    body = "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = f"✈️ Flight Alert: {ORIGIN.value} → {DESTINATION.value} from ${top3[0][1]}"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

    print("Alert email sent!")


# ── THIS MUST BE AT THE LEFTMOST INDENTATION LEVEL ─────
if __name__ == "__main__":
    print(f"\n{'='*40}")
    print(f"Flight Tracker — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Route: {ORIGIN.value} → {DESTINATION.value}")
    print(f"Scanning {DATE_RANGE*2+1} dates around {TARGET_DATE}")
    print(f"{'='*40}\n")

    results = find_best_dates()

    if not results:
        print("No direct flights found for any date in range.")
    else:
        print(f"\n🏆 Top 3 cheapest dates:")
        for i, (date, price) in enumerate(results[:3], start=1):
            print(f"  #{i}  {date}  →  ${price}")

        save_to_csv(results)

        best_price = results[0][1]
        if best_price < ALERT_PRICE:
            print(f"\n💰 Price alert triggered! ${best_price} is under ${ALERT_PRICE}")
            send_email(results)
        else:
            print(f"\nNo alert sent. Best price ${best_price} is above threshold ${ALERT_PRICE}")

    print("\nDone!")