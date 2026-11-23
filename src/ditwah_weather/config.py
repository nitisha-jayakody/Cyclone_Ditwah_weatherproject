"""Project configuration constants and Sri Lankan grid locations."""

from dataclasses import dataclass

EVENT_START = "2025-11-26"
EVENT_END = "2025-11-30"
BASELINE_START = 1940
BASELINE_END = 2024

@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    region: str

LOCATIONS = [
    Location("Dankotuwa", 7.3497, 79.8533, "Western"),
    Location("Negombo", 7.2083, 79.8358, "Western"),
    Location("Colombo", 6.9271, 79.8612, "Western"),
    Location("Kandy", 7.2906, 80.6337, "Central"),
    Location("Nuwara Eliya", 6.9497, 80.7891, "Central"),
    Location("Ratnapura", 6.6828, 80.3992, "Sabaragamuwa"),
    Location("Galle", 6.0535, 80.2210, "Southern"),
    Location("Batticaloa", 7.7170, 81.7000, "Eastern"),
    Location("Trincomalee", 8.5874, 81.2152, "Eastern"),
    Location("Anuradhapura", 8.3114, 80.4037, "North Central"),
]