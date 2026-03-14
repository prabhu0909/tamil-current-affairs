from openai import OpenAI

client = OpenAI()

def summarize(text):

    prompt=f"""
    இந்த செய்தியை TNPSC தேர்வுக்கான முக்கிய குறிப்புகளாக தமிழில் சுருக்கவும்.

    செய்தி:
    {text}
    """

    response=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content
