import csv
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

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

OUTBOUND_DATE = "2026-05-29"
OUTBOUND_RANGE = 5   # days ± around outbound date

RETURN_DATE   = "2026-06-10"
RETURN_RANGE  = 5   # days ± around return date

ALERT_PRICE = 300

from dotenv import load_dotenv
load_dotenv()

EMAIL_SENDER   = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

CSV_FILE = "prices_round.csv"
# ───────────────────────────────────────────────────────


def get_date_range(center_date: str, days: int):
    """Generate dates within ±days of center_date."""
    center = datetime.strptime(center_date, "%Y-%m-%d")
    return [
        (center + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(-days, days + 1)
    ]


def search_round_trip(outbound_date: str, return_date: str):
    """Search round-trip flights for the given dates, return cheapest total price."""
    filters = FlightSearchFilters(
        trip_type=TripType.ROUND_TRIP,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[
            FlightSegment(
                departure_airport=[[ORIGIN, 0]],
                arrival_airport=[[DESTINATION, 0]],
                travel_date=outbound_date,
            ),
            FlightSegment(
                departure_airport=[[DESTINATION, 0]],
                arrival_airport=[[ORIGIN, 0]],
                travel_date=return_date,
            ),
        ],
        seat_type=SeatType.ECONOMY,
        stops=MaxStops.NON_STOP,
        sort_by=SortBy.CHEAPEST,
    )

    search = SearchFlights()
    results = search.search(filters)

    if not results:
        return None

    outbound, return_flight = results[0]  # unpack the tuple
    return outbound.price + return_flight.price  # total round-trip price


def find_best_round_trips():
    """Search all outbound × return date combinations, return sorted list."""
    outbound_dates = get_date_range(OUTBOUND_DATE, OUTBOUND_RANGE)
    return_dates   = get_date_range(RETURN_DATE,   RETURN_RANGE)

    results = []
    total = len(outbound_dates) * len(return_dates)
    idx = 0

    for out_date in outbound_dates:
        for ret_date in return_dates:
            if ret_date <= out_date:
                idx += 1
                continue  # return must be after outbound

            idx += 1
            print(f"[{idx}/{total}] {out_date} → {ret_date} ...")
            price = search_round_trip(out_date, ret_date)

            if price is not None:
                print(f"  → ${price}")
                results.append((out_date, ret_date, price))
            else:
                print(f"  → No flights found")

    results.sort(key=lambda x: x[2])
    return results


def save_to_csv(results):
    """Save today's search results to the CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["timestamp", "outbound_date", "return_date", "price"])

        for out_date, ret_date, price in results:
            writer.writerow([timestamp, out_date, ret_date, price])

    print(f"Saved {len(results)} results to {CSV_FILE}")


def send_email(results):
    """Send an email alert with the top 3 cheapest round-trip combinations."""
    top3 = results[:3]

    lines = ["Good news! Round-trip prices are looking good:\n"]
    for i, (out_date, ret_date, price) in enumerate(top3, start=1):
        lines.append(f"  #{i}  {out_date} → {ret_date}  |  ${price}")

    lines.append(f"\nYour alert threshold: ${ALERT_PRICE}")
    lines.append("Check Google Flights to book!")
    body = "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = (
        f"✈️ Round-Trip Alert: {ORIGIN.value} ↔ {DESTINATION.value} from ${top3[0][2]}"
    )
    msg["From"] = EMAIL_SENDER
    msg["To"]   = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

    print("Alert email sent!")


# ── THIS MUST BE AT THE LEFTMOST INDENTATION LEVEL ─────
if __name__ == "__main__":
    out_count = OUTBOUND_RANGE * 2 + 1
    ret_count = RETURN_RANGE   * 2 + 1

    print(f"\n{'='*50}")
    print(f"Round-Trip Flight Tracker — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Route: {ORIGIN.value} ↔ {DESTINATION.value}")
    print(f"Outbound: {out_count} dates around {OUTBOUND_DATE}")
    print(f"Return:   {ret_count} dates around {RETURN_DATE}")
    print(f"{'='*50}\n")

    results = find_best_round_trips()

    if not results:
        print("No direct round-trip flights found for any date combination.")
    else:
        print(f"\n🏆 Top 3 cheapest combinations:")
        for i, (out_date, ret_date, price) in enumerate(results[:3], start=1):
            print(f"  #{i}  {out_date} → {ret_date}  |  ${price}")

        save_to_csv(results)

        best_price = results[0][2]
        if best_price < ALERT_PRICE:
            print(f"\n💰 Price alert triggered! ${best_price} is under ${ALERT_PRICE}")
            send_email(results)
        else:
            print(f"\nNo alert sent. Best price ${best_price} is above threshold ${ALERT_PRICE}")

    print("\nDone!")
