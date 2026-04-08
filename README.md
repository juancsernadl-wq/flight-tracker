# ✈️ Flight Price Tracker

Automated flight price tracker that monitors Google Flights in real time, logs historical prices, sends email alerts when prices drop, and visualizes trends in a browser dashboard.

Built as a personal tool to track LAX → AGU (Aguascalientes) flights while learning Python automation.

---

## Features

- 🔍 Searches direct flights across a ±N day range around a target date
- 🔄 Supports both one-way and round-trip searches
- 📊 Logs all results to CSV for historical tracking
- 💰 Sends Gmail email alerts when prices drop below a threshold
- 📈 Browser dashboard with price history chart and results table
- ⏰ Runs automatically via cron job (Tue, Wed, Fri — 8am, 1pm, 7pm)

---

## Tech Stack

- **Python** — core scripting
- **fli** — reverse-engineered Google Flights API access
- **smtplib** — built-in Python email library
- **python-dotenv** — secure credential management
- **Chart.js** — browser-based price visualization
- **crontab** — Mac task scheduling

---

## Project Structure

```
flight-tracker/
├── tracker.py           # One-way flight tracker
├── tracker_round.py     # Round-trip variant
├── dashboard.html       # Browser dashboard (Chart.js)
├── .env                 # Credentials (not committed)
├── prices.csv           # Price history log (not committed)
└── prices_round.csv     # Round-trip price log (not committed)
```

---

## Setup

**1. Install dependencies:**
```bash
pip3 install flights python-dotenv
```

**2. Create a `.env` file:**
```
EMAIL_SENDER=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=your_gmail@gmail.com
```
> Use a [Gmail App Password](https://myaccount.google.com/apppasswords), not your real password.

**3. Configure your search** in `tracker.py`:
```python
ORIGIN      = Airport.LAX
DESTINATION = Airport.BOS
TARGET_DATE = "2026-05-29"
DATE_RANGE  = 5        # ±5 days around target date
ALERT_PRICE = 150      # Email alert threshold
```

**4. Run manually:**
```bash
python3 tracker.py
```

**5. View the dashboard:**
```bash
python3 -m http.server 8000
# Then open http://localhost:8000/dashboard.html
```

**6. Schedule with cron** (runs automatically):
```bash
crontab -e
# Add this line:
0 8,13,19 * * 2,3,5 cd ~/Documents/flight-tracker && python3 tracker.py >> tracker.log 2>&1
```

---

## Skills Demonstrated

`API Integration` `Task Automation` `Data Logging` `Email Alerting` `Data Visualization` `Cron Scheduling` `Secure Credential Management`