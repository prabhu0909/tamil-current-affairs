import random

def generate_quiz(news):

    q = f"""
    {news}

    இந்த செய்தி எந்த துறையை சேர்ந்தது?
    """

    options = [
    "தமிழ்நாடு",
    "இந்தியா",
    "உலகம்",
    "பொருளாதாரம்"
    ]

    answer = random.choice(options)

    return {
        "question": q,
        "options": options,
        "answer": answer
    }
