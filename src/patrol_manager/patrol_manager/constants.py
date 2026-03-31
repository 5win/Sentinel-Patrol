import math

# ── Waypoints (x, y, yaw) ──
WAYPOINTS: list[tuple[float, float, float]] = [
    (1.0, 0.0, 0.0),
    (1.0, 2.0, 0.0),
    (0.0, 2.0, 0.0),
]

# ── Timer ──
TIMER_PERIOD_SEC: float = 0.1

# ── Timeout ──
EMERGENCY_TIMEOUT_SEC: float = 5.0
SAFE_CONFIRM_SEC: float = 3.0
ACTION_SERVER_TIMEOUT_SEC: float = 5.0

# ── Spin (Avoidance) ──
SPIN_TIME_ALLOWANCE_SEC: int = 15