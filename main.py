import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests
from mock_data import TRAINS
from predictor import predict_confirmation_prob
from db_store import create_booking, get_booking

load_dotenv()

API_HOST = os.getenv("API_HOST","0.0.0.0")
API_PORT = int(os.getenv("API_PORT","8000"))
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
PAYMENT_SECRET = os.getenv("PAYMENT_SECRET","mock_secret")

app = FastAPI(title="Shayak Saarthi - Mock Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchReq(BaseModel):
    from_station: str
    to_station: str
    date: str

class BookLeg(BaseModel):
    train_id: str
    cls: str
    qty: int
    wl_position: int = 0

class BookReq(BaseModel):
    user_email: str
    legs: List[BookLeg]
    payment_token: str

class RescheduleReq(BaseModel):
    pnr: str
    leg_index: int
    new_train_id: str
    new_date: str

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/search")
def search(req: SearchReq):
    res = [t for t in TRAINS if t["from"].lower().strip()==req.from_station.lower().strip() and t["to"].lower().strip()==req.to_station.lower().strip()]
    if not res:
        return {"hint":"No exact matches - returning close trains", "trains": TRAINS}
    return {"trains": res}

@app.post("/predict-seat")
def predict_seat(train_id: str, cls: str, wl_position: int = 1):
    train = next((t for t in TRAINS if t["train_id"]==train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    prob = predict_confirmation_prob(train.get("wl_stats",{}), cls, wl_position)
    return {"train_id": train_id, "class": cls, "wl_position": wl_position, "probability": prob}

@app.post("/mock_payment")
def mock_payment(secret: str):
    if secret != PAYMENT_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"status":"success", "transaction_id":"MOCKTXN12345"}

@app.post("/book")
def book(req: BookReq):
    if req.payment_token != "MOCK_PAY_TOKEN":
        raise HTTPException(status_code=400, detail="Invalid/missing mock payment token")
    legs_out = []
    overall_status = "CONFIRMED"
    for leg in req.legs:
        train = next((t for t in TRAINS if t["train_id"]==leg.train_id), None)
        wl = leg.wl_position
        prob = 0.99 if wl<=0 else predict_confirmation_prob(train.get("wl_stats",{}), leg.cls, wl)
        leg_status = "CONFIRMED" if prob>0.5 else "WAITLIST"
        if leg_status=="WAITLIST":
            overall_status = "WAITLISTED"
        legs_out.append({
            "train_id": leg.train_id,
            "class": leg.cls,
            "qty": leg.qty,
            "wl_position": wl,
            "pred_prob": prob,
            "status": leg_status
        })
    booking = {
        "user_email": req.user_email,
        "legs": legs_out,
        "status": overall_status,
        "total_fare": sum((next((t for t in TRAINS if t["train_id"]==leg.train_id),{}).get("classes",{}).get(leg.cls,0) or 0)*leg.qty for leg in req.legs)
    }
    rec = create_booking(booking)
    return {"booking": rec}

@app.post("/reschedule")
def reschedule(req: RescheduleReq):
    rec = get_booking(req.pnr)
    if not rec:
        raise HTTPException(status_code=404, detail="PNR not found")
    leg_idx = req.leg_index
    try:
        old_leg = rec["legs"][leg_idx]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid leg index")
    old_leg["train_id"] = req.new_train_id
    old_leg["wl_position"] = 1
    train = next((t for t in TRAINS if t["train_id"]==req.new_train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="New train not found")
    old_leg["pred_prob"] = predict_confirmation_prob(train.get("wl_stats",{}), old_leg["class"], 1)
    rec["status"] = "WAITLISTED" if any(l["status"]=="WAITLIST" for l in rec["legs"]) else "CONFIRMED"
    return {"booking": rec}

@app.post("/intent")
def intent(text: dict):
    body = text
    txt = body.get("text","")
    if not txt:
        raise HTTPException(status_code=400, detail="Empty text")
    if not HF_API_TOKEN:
        low = txt.lower()
        if "book" in low or "ticket" in low:
            return {"intent":"book_trip", "confidence":0.6}
        if "resched" in low or "change" in low:
            return {"intent":"reschedule", "confidence":0.6}
        if "find" in low or "search" in low:
            return {"intent":"search_trains", "confidence":0.6}
        return {"intent":"unknown", "confidence":0.3}
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": txt, "parameters":{"candidate_labels":["search_trains","book_trip","reschedule","get_status","add_expense"]}}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    data = r.json()
    if "labels" in data and len(data["labels"])>0:
        return {"intent": data["labels"][0], "confidence": data["scores"][0]}
    return {"intent":"unknown","confidence":0.2}
