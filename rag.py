import json

from clients import client
from config import CHAT_MODEL


def build_context(results):
    context_parts = []

    for index, (score, record) in enumerate(results, start=1):
        context_parts.append(
            f"[Context {index}]\n"
            f"Source: {record['source']}\n"
            f"Page: {record['page']}\n"
            f"Text:\n{record['text']}"
        )

    return "\n\n---\n\n".join(context_parts)


def generate_answer(question, results):
    context = build_context(results)

    prompt = f"""
You are a helpful document assistant.

Answer the user's question using only the provided context.

Return ONLY valid JSON in this exact structure:

{{
  "answer": "A concise markdown answer.",
  "citations": [
    {{
      "source": "filename.pdf",
      "page": 1,
      "quote": "Exact sentence copied from the context."
    }}
  ]
}}

Rules:
- The answer must be based only on the context.
- Each citation quote must be copied exactly from the context.
- Each quote should be one sentence where possible.
- Do not mention chunk numbers.
- Do not invent sources, pages, or quotes.
- Include every citation necessary to support your answer.
- Do not artifically limit the number of citations.
- If different parts of your answer are supported by different sections of the documents, include a citation for each supporting quote.
- If the answer is not in the context, return:
  {{
    "answer": "I could not find this in the uploaded documents.",
    "citations": []
  }}

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```json"):
        content = content.removeprefix("```json").removesuffix("```").strip()
    elif content.startswith("```"):
        content = content.removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "answer": content,
            "citations": [],
        }
