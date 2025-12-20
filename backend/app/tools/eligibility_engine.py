import random

def check_eligibility(data: dict):
    """
    Simulated eligibility engine.
    Random failure included intentionally.
    """

    if random.random() < 0.3:
        return None

    return "आपण शासकीय योजनेसाठी पात्र आहात."
