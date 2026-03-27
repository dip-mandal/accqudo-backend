import json
import ollama


def validate_with_ai(data):

    prompt = f"""
Validate and clean this academic CV JSON.

Do not invent new data.

Return valid JSON only.

DATA:
{json.dumps(data)}
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role":"user","content":prompt}],
        format="json"
    )

    return json.loads(response["message"]["content"])