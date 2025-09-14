# Mock trains and stations for predictable demos
TRAINS = [
    {
        "train_id": "12301",
        "name": "DELHI EXPRESS",
        "from": "Bhopal Jn",
        "to": "New Delhi",
        "departure": "2025-10-01T08:00:00",
        "arrival": "2025-10-01T15:00:00",
        "classes": {"SL": 200, "3A": 600, "2A": 1200},
        "wl_stats": {"SL": 0.4, "3A": 0.3, "2A": 0.15}
    },
    {
        "train_id": "12450",
        "name": "MP MAIL",
        "from": "Bhopal Jn",
        "to": "Indore",
        "departure": "2025-10-01T09:00:00",
        "arrival": "2025-10-01T12:00:00",
        "classes": {"SL":100, "3A":400},
        "wl_stats": {"SL": 0.6, "3A": 0.5}
    },
    {
        "train_id": "12520",
        "name": "MAHARASHTRA SF",
        "from": "Indore",
        "to": "Mumbai CSMT",
        "departure": "2025-10-02T06:00:00",
        "arrival": "2025-10-02T16:00:00",
        "classes": {"3A":700, "2A":1500},
        "wl_stats": {"3A": 0.25, "2A": 0.1}
    }
]
