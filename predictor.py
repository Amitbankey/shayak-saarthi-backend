import math

def predict_confirmation_prob(train_wl_stats, cls, wl_position):
    base = train_wl_stats.get(cls, 0.2)
    if wl_position <= 0:
        return 0.98
    penalty = max(0.05, 1 - math.log10(wl_position + 1) / 4.0)
    prob = base * penalty
    prob = max(0.01, min(prob, 0.99))
    return round(prob, 3)
