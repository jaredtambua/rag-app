import json

from clients import client
from config import CHAT_MODEL
from models import ContextBlock


def build_context(context_blocks: list[ContextBlock]) -> str:
    """
    Convert ContextBlocks into structured evidence for the LLM
    while preserving the page associated with each chunk.
    """
    context_parts = []

    for block_index, block in enumerate(context_blocks, start=1):
        chunk_parts = []

        for chunk in block.chunks:
            chunk_parts.append(f"[Page {chunk.page}]\n" f"{chunk.text}")

        block_text = "\n\n".join(chunk_parts)

        context_parts.append(
            f"[Evidence Group {block_index}]\n"
            f"Source: {block.source}\n\n"
            f"{block_text}"
        )

    return "\n\n---\n\n".join(context_parts)


def generate_answer(
    question: str,
    context_blocks: list[ContextBlock],
):
    """
    Generate an answer using retrieved evidence.
    """

    # If retrieval found nothing useful, don't ask the LLM
    # to answer from its own general knowledge.
    if not context_blocks:
        return {
            "answer": "I could not find this in the uploaded documents.",
            "citations": [],
        }

    context = build_context(context_blocks)

    prompt = f"""
You are a helpful document assistant.

Answer the user's question using only the provided evidence.

Return ONLY valid JSON in this exact structure:

{{
  "answer": "A concise markdown answer.",
  "citations": [
    {{
      "source": "filename.pdf",
      "page": 1,
      "quote": "Exact sentence copied from the evidence."
    }}
  ]
}}

Rules:
- The answer must be based only on the provided evidence.
- Each citation quote must be copied exactly from the evidence.
- Each quote should be one sentence where possible.
- Do not mention chunk numbers.
- Do not invent sources, pages, or quotes.
- Include every citation necessary to support your answer.
- Do not artificially limit the number of citations.
- If different parts of your answer are supported by different evidence, include a citation for each supporting quote.
- If the answer is not supported by the evidence, return:
  {{
    "answer": "I could not find this in the uploaded documents.",
    "citations": []
  }}

Evidence:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    # Occasionally models wrap JSON in Markdown code fences.
    # Remove those before attempting to parse the JSON.
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
