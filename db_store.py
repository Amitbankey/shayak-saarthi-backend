import os
import uuid
from typing import Dict, Any

STORE = {
    "users": {},
    "bookings": {}
}

def create_booking(booking: Dict[str,Any]):
    pnr = str(uuid.uuid4())[:8].upper()
    booking_record = {**booking, "pnr": pnr, "status": "WAITLIST", "created_at": None}
    STORE["bookings"][pnr] = booking_record
    return booking_record

def get_booking(pnr):
    return STORE["bookings"].get(pnr)
