"""
=============================================================
 battery_monitor.py  –  Windows Laptop Battery Monitor v1
 Author : (your name)
 Purpose: Alert user when battery is too low (<= 20%)
          or fully charged / overcharging (>= 80%)
=============================================================

HOW IT WORKS (plain English)
──────────────────────────────
1. Every 60 seconds the script reads the battery level with psutil.
2. If the level crosses a threshold (20% or 80%) AND we haven't
   already alerted for that threshold, a Windows toast notification
   pops up and the "alerted" flag is set to True.
3. When the battery moves away from the threshold zone the flag
   resets, so the next crossing will alert again.
4. The script runs forever until you close the terminal (Ctrl+C).
"""

# ── stdlib / third-party imports ────────────────────────────
import time          # for time.sleep() – keeps CPU usage low
import sys           # for sys.exit() – clean exit on error

try:
    import psutil    # reads hardware data (battery, CPU, RAM …) ...I
except ImportError:
    print("[ERROR] psutil is not installed.")
    print("        Run:  pip install psutil")
    sys.exit(1)

try:
    from plyer import notification   # cross-platform toast notifications
except ImportError:
    print("[ERROR] plyer is not installed.")
    print("        Run:  pip install plyer")
    sys.exit(1)


# ── configuration ────────────────────────────────────────────
LOW_THRESHOLD  = 25   # (%) alert when battery falls to or below this
HIGH_THRESHOLD = 80   # (%) alert when battery rises to or above this
CHECK_INTERVAL = 60   # (seconds) how often to poll the battery


# ── helper: send a Windows toast notification ────────────────
def send_notification(title: str, message: str) -> None:
    """
    Displays a Windows desktop toast notification.

    Parameters
    ----------
    title   : bold heading shown in the notification
    message : body text of the notification
    """
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Battery Monitor",
            timeout=10,          # notification stays visible for 10 s
        )
    except Exception as e:
        # Notification may fail if the OS blocks it – just print instead
        print(f"[WARN] Could not show notification: {e}")
        print(f"       >>> {title}: {message}")


# ── helper: read battery info ────────────────────────────────
def get_battery():
    """
    Returns psutil's battery named-tuple, or None if no battery found.

    Named-tuple fields we use
    ─────────────────────────
    battery.percent   – current charge level  (0–100)
    battery.power_plugged – True if charger is connected
    """
    battery = psutil.sensors_battery()
    if battery is None:
        print("[ERROR] No battery detected. "
              "Are you running this on a desktop PC?")
    return battery


# ── main monitoring loop ─────────────────────────────────────
def monitor():
    """
    Infinite loop that checks the battery every CHECK_INTERVAL seconds.

    State tracking
    ──────────────
    alerted_low  – True  = we already fired the "Low Battery" alert
                          this discharge cycle; don't fire again until
                          the battery climbs back above LOW_THRESHOLD.
    alerted_high – same idea for the "Unplug Charger" alert.
    """

    print("=" * 52)
    print("  Battery Monitor v1 – running (Ctrl+C to stop)")
    print(f"  Low threshold  : {LOW_THRESHOLD}%")
    print(f"  High threshold : {HIGH_THRESHOLD}%")
    print(f"  Check interval : {CHECK_INTERVAL}s")
    print("=" * 52)

    # ── state flags (prevent repeated / spammy alerts) ───────
    alerted_low  = False
    alerted_high = False

    while True:
        try:
            battery = get_battery()

            if battery is None:
                # No battery – wait and retry (maybe it's a brief read error)
                time.sleep(CHECK_INTERVAL)
                continue

            pct     = battery.percent
            plugged = battery.power_plugged

            # Human-readable status for the console log
            status = "Plugged in" if plugged else "On battery"
            print(f"[{time.strftime('%H:%M:%S')}] Battery: {pct:.0f}%  |  {status}")

            # ── LOW BATTERY check ─────────────────────────────
            if pct <= LOW_THRESHOLD and not plugged:
                if not alerted_low:
                    send_notification(
                        title="⚠️  Low Battery",
                        message=f"Battery is at {pct:.0f}%. "
                                "Please plug in your charger now!",
                    )
                    alerted_low = True
                    print(f"  → Low-battery alert sent ({pct:.0f}%)")
            else:
                # Battery rose above threshold – reset flag
                alerted_low = False

            # ── HIGH BATTERY / OVERCHARGE check ──────────────
            if pct >= HIGH_THRESHOLD and plugged:
                if not alerted_high:
                    send_notification(
                        title="🔋  Battery High – Unplug Charger",
                        message=f"Battery is at {pct:.0f}%. "
                                "Unplug the charger to protect battery health.",
                    )
                    alerted_high = True
                    print(f"  → High-battery alert sent ({pct:.0f}%)")
            else:
                # Battery dropped below threshold or charger unplugged – reset
                alerted_high = False

        except KeyboardInterrupt:
            # User pressed Ctrl+C – exit gracefully
            print("\n[INFO] Battery Monitor stopped by user. Goodbye!")
            sys.exit(0)

        except Exception as e:
            # Any unexpected error – log it and keep running
            print(f"[ERROR] Unexpected error: {e}")

        # ── sleep to keep CPU usage near 0 % ─────────────────
        time.sleep(CHECK_INTERVAL)


# ── entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    monitor()
