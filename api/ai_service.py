

import random

def get_ai_triage_for_symptoms(symptom_text):
    """
    Simulates an AI model with improved logic to check for severity modifiers.
    """
    symptom_lower = symptom_text.lower()

    urgency = "Low"  # Default urgency
    category = "General Inquiry"
    summary = f"Patient reports: {symptom_text}"

    # --- Expanded Keyword-Based Logic ---

    # ✅ MODIFIED: Added severity modifiers
    severity_modifiers = ["severe", "unbearable", "extreme", "intense"]

    high_urgency_keywords = [
        "can't breathe", "breathing difficulty", "chest pain", "bleeding",
        "unconscious", "choking", "seizure", "head injury", "swallowing"
    ]

    moderate_urgency_keywords = [
        "fever", "vomiting", "headache", "dizzy", "migraine",
        "cough", "rash", "stomach cramps", "back pain"
    ]

    # ✅ IMPROVED LOGIC: Check for severity modifiers first
    if any(modifier in symptom_lower for modifier in severity_modifiers) and any(keyword in symptom_lower for keyword in ["pain", "headache", "bleeding"]):
        urgency = "High"
    elif any(word in symptom_lower for word in high_urgency_keywords):
        urgency = "High"
    elif any(word in symptom_lower for word in moderate_urgency_keywords):
        urgency = "Moderate"

    # Category Keywords (can be expanded similarly)
    if any(word in symptom_lower for word in ["cough", "fever", "cold", "flu", "sore throat", "breathing"]):
        category = "Respiratory Issue"
    elif any(word in symptom_lower for word in ["stomach", "nausea", "vomiting", "diarrhea"]):
        category = "Digestive Issue"
    elif any(word in symptom_lower for word in ["cut", "bleeding", "wound", "bruise", "injury", "pain"]):
        category = "Injury / Pain"

    summary = f"Patient reports symptoms consistent with a {category.lower()}, including: {symptom_text}. Urgency has been assessed as {urgency}."

    return {
        "ai_urgency": urgency,
        "ai_category": category,
        "ai_summary": summary
    }