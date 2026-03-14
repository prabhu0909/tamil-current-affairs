from transformers import pipeline

summarizer = pipeline("summarization")

def summarize(text):

    try:
        result = summarizer(text, max_length=60, min_length=20)

        return result[0]["summary_text"]

    except:
        return text[:200]
