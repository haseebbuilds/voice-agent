"""
Personal Injury practice area questions
"""
PERSONAL_INJURY_QUESTIONS = [
    {
        "key": "incident_type",
        "question": "What type of incident was it? Options are: car accident, slip and fall, workplace, or other.",
        "type": "choice"
    },
    {
        "key": "incident_date",
        "question": "When did it happen? Please provide the date.",
        "type": "date"
    },
    {
        "key": "incident_location",
        "question": "Where did it happen? Please provide the city and state.",
        "type": "text"
    },
    {
        "key": "injuries",
        "question": "Were you injured? If yes, what injuries did you sustain?",
        "type": "text"
    },
    {
        "key": "medical_treatment",
        "question": "Did you get medical treatment?",
        "type": "yes_no"
    },
    {
        "key": "police_report",
        "question": "Was a police report made?",
        "type": "yes_no_unsure"
    },
    {
        "key": "insurance_involved",
        "question": "Is there insurance involved? Options are: your insurance, other party's insurance, both, or not sure.",
        "type": "choice"
    }
]

