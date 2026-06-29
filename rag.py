from clients import client
from config import CHAT_MODEL


# build context from retrieved chunks
def build_context(results):
    context_parts = []

    for score, record in results:
        context_parts.append(
            f"Source: {record['source']}, "
            f"page {record['page']}, "
            f"chunk {record['chunk_number']}\n"
            f"{record['text']}"
        )

    return "\n\n---\n\n".join(context_parts)


# generate an answer using the llm
def generate_answer(question, results):
    context = build_context(results)

    prompt = f"""
You are a helpful document assistant.

Answer the user's question using only the provided context.

Formatting rules:
- Use short paragraphs.
- Use bullet points or numbered lists when they make the answer clearer.
- Do not write one dense paragraph.
- Be concise but complete.
- If the answer is not in the context, say you could not find it in the uploaded documents.

Context:
{context}

Question:
{question}
"""
    response = client.chat.completions.create(
        model=CHAT_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0
    )

    return response.choices[0].message.content
