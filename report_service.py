"""
report_service.py
-----------------
Campus-level reports (requirement 7.1) and the cross-campus comparison
(requirement 7.2). Results are plain dictionaries and lists so the GUI
can show them in tables and charts.
"""
import csv
from datetime import date, timedelta

from utils.timeutils import format_days, format_duration, minutes_to_hhmm


class ReportService:
    def __init__(self, db, campus_service):
        self.db = db
        self.campuses = campus_service

    # ------------------------------------------------------ one campus
    def campus_report(self, campus_id):
        campus = self.campuses.get(campus_id)
        policy = campus.policy

        resources = self.db.query(
            "SELECT id, resource_code, name, resource_type, status FROM resources "
            "WHERE campus_id = ? AND status != 'Removed'", (campus_id,))
        bookings = self.db.query(
            "SELECT b.booking_date, b.duration_minutes, b.status, r.id AS rid, "
            "r.resource_code, r.name AS rname, r.resource_type "
            "FROM bookings b JOIN resources r ON r.id = b.resource_id WHERE b.campus_id = ?",
            (campus_id,))

        # dictionary: resource id -> usage numbers
        usage = {r["id"]: {"code": r["resource_code"], "name": r["name"],
                           "bookings": 0, "minutes": 0} for r in resources}
        by_weekday = [0] * 7
        by_type = {}
        weekly = {}
        total = cancelled = total_minutes = minutes_30_days = 0

        today = date.today()
        window_start = today - timedelta(days=29)

        for row in bookings:
            if row["status"] == "Cancelled":
                cancelled += 1
                continue
            day = date.fromisoformat(row["booking_date"])
            minutes = row["duration_minutes"]
            total += 1
            total_minutes += minutes
            by_weekday[day.weekday()] += 1
            by_type[row["resource_type"]] = by_type.get(row["resource_type"], 0) + 1
            monday = day - timedelta(days=day.weekday())
            weekly[monday] = weekly.get(monday, 0) + 1
            if window_start <= day <= today:
                minutes_30_days += minutes
            item = usage.setdefault(row["rid"], {"code": row["resource_code"], "name": row["rname"],
                                                 "bookings": 0, "minutes": 0})
            item["bookings"] += 1
            item["minutes"] += minutes

        # Utilisation = booked time / time the campus could have offered (last 30 days)
        open_days = sum(1 for i in range(30)
                        if (window_start + timedelta(days=i)).weekday() in policy.allowed_weekdays)
        active_resources = sum(1 for r in resources if r["status"] == "Active")
        offered = active_resources * (policy.close_minutes - policy.open_minutes) * open_days
        utilisation = 100 * minutes_30_days / offered if offered else 0

        # Last 6 weeks (Monday to Sunday), oldest first
        this_monday = today - timedelta(days=today.weekday())
        weeks = [this_monday - timedelta(days=7 * i) for i in range(5, -1, -1)]
        weekly_trend = [(w.strftime("%d %b"), weekly.get(w, 0)) for w in weeks]

        ranked = sorted(usage.values(), key=lambda u: (-u["bookings"], -u["minutes"]))
        return {
            "campus": campus,
            "total": total,
            "cancelled": cancelled,
            "avg_minutes": total_minutes / total if total else 0,
            "total_hours": total_minutes / 60,
            "utilisation": utilisation,
            "resource_count": len(resources),
            "top_resources": ranked[:5],
            "all_resources": ranked,
            "by_weekday": by_weekday,
            "by_type": by_type,
            "weekly_trend": weekly_trend,
        }

    # -------------------------------------------------- all campuses
    def comparison(self):
        """One summary row per campus (list of dictionaries)."""
        rows = []
        for campus in self.campuses.all():
            rep = self.campus_report(campus.campus_id)
            policy = campus.policy
            weekend = rep["by_weekday"][5] + rep["by_weekday"][6]
            rows.append({
                "campus": campus.name,
                "policy": policy.name,
                "max_session": policy.max_duration_minutes,
                "hours": f"{minutes_to_hhmm(policy.open_minutes)}-{minutes_to_hhmm(policy.close_minutes)}",
                "days": format_days(policy.allowed_weekdays),
                "resources": rep["resource_count"],
                "bookings": rep["total"],
                "cancelled": rep["cancelled"],
                "avg_minutes": rep["avg_minutes"],
                "utilisation": rep["utilisation"],
                "weekend_pct": 100 * weekend / rep["total"] if rep["total"] else 0,
                "top_resource": rep["top_resources"][0]["name"] if rep["top_resources"] and rep["total"] else "-",
                "by_type": rep["by_type"],
            })
        return rows

    def usage_by_type(self, rows):
        """Matrix for the comparison table: resource type -> {campus: bookings}."""
        types = sorted({t for row in rows for t in row["by_type"]})
        return {t: {row["campus"]: row["by_type"].get(t, 0) for row in rows} for t in types}

    def insights(self, rows):
        """Plain-English observations about how campus rules shape usage."""
        rows = [r for r in rows if r["bookings"]]
        if len(rows) < 2:
            return ["Not enough booking data yet to compare campuses."]
        notes = []

        busiest = max(rows, key=lambda r: r["bookings"])
        quietest = min(rows, key=lambda r: r["bookings"])
        notes.append(f"{busiest['campus']} has the most bookings ({busiest['bookings']}), "
                     f"while {quietest['campus']} has the fewest ({quietest['bookings']}).")

        longest = max(rows, key=lambda r: r["avg_minutes"])
        shortest = min(rows, key=lambda r: r["avg_minutes"])
        notes.append(f"Sessions are longest at {longest['campus']} (average "
                     f"{format_duration(longest['avg_minutes'])}, limit {format_duration(longest['max_session'])}) "
                     f"and shortest at {shortest['campus']} (average "
                     f"{format_duration(shortest['avg_minutes'])}, limit {format_duration(shortest['max_session'])}).")

        best = max(rows, key=lambda r: r["utilisation"])
        worst = min(rows, key=lambda r: r["utilisation"])
        notes.append(f"Utilisation over the last 30 days is highest at {best['campus']} "
                     f"({best['utilisation']:.0f}%) and lowest at {worst['campus']} ({worst['utilisation']:.0f}%).")

        for r in rows:
            if r["weekend_pct"] > 0:
                notes.append(f"{r['campus']} allows weekend bookings ({r['days']}); "
                             f"{r['weekend_pct']:.0f}% of its bookings fall on a weekend.")

        cancel_rate = max(rows, key=lambda r: r["cancelled"] / (r["bookings"] + r["cancelled"]))
        share = 100 * cancel_rate["cancelled"] / (cancel_rate["bookings"] + cancel_rate["cancelled"])
        notes.append(f"{cancel_rate['campus']} has the highest cancellation rate ({share:.0f}%).")
        return notes

    def export_comparison_csv(self, path):
        """Save the cross-campus comparison table to a CSV file."""
        rows = self.comparison()
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Campus", "Policy", "Max session (min)", "Booking hours", "Booking days",
                             "Resources", "Bookings", "Cancelled", "Avg duration (min)",
                             "Utilisation % (30 days)", "Weekend share %", "Most used resource"])
            for r in rows:
                writer.writerow([r["campus"], r["policy"], r["max_session"], r["hours"], r["days"],
                                 r["resources"], r["bookings"], r["cancelled"],
                                 round(r["avg_minutes"], 1), round(r["utilisation"], 1),
                                 round(r["weekend_pct"], 1), r["top_resource"]])
