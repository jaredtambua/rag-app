import json

from clients import client
from config import CHAT_MODEL
from models import ContextBlock


def build_context(context_blocks: list[ContextBlock]) -> str:
    """
    Convert retrieved context blocks into structured evidence
    for the LLM while preserving the page associated with
    each individual chunk.
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
    Generate a grounded answer from retrieved document evidence.
    """

    if not context_blocks:
        return {
            "answer": "I could not find this in the uploaded documents.",
            "citations": [],
        }

    context = build_context(context_blocks)

    prompt = f"""
You are a document assistant. Answer the user's question using only
the evidence retrieved from the uploaded documents.

Adapt your response to the question:
- For simple factual questions, answer directly and concisely.
- For questions asking for an explanation, provide enough detail to
  clearly explain the relevant concepts.
- For comparison questions, clearly explain the relevant similarities
  and differences.
- For summary questions, synthesize the important information from the
  available evidence.
- Use paragraphs, bullet points, or headings when they genuinely improve
  clarity.
- Do not add unnecessary detail simply to make an answer longer.

You may explain, summarize, and synthesize the evidence in your own words,
but do not introduce factual claims that are not supported by the evidence.

Return ONLY valid JSON in this exact structure:

{{
  "answer": "A markdown-formatted answer appropriate to the user's question.",
  "citations": [
    {{
      "source": "filename.pdf",
      "page": 1,
      "quote": "Exact supporting text copied from the evidence."
    }}
  ]
}}

Citation rules:
- Citations must support factual claims made in the answer.
- Each citation quote must be copied exactly from the provided evidence.
- Keep citation quotes focused; use one sentence where practical.
- Each evidence chunk is labelled with its original page.
- The citation page must match the page label of the quoted text.
- The citation source must match the source of its evidence group.
- Do not invent sources, pages, or quotes.
- Do not mention internal evidence-group or chunk numbers in the answer.
- Include the citations needed to support the answer, but avoid redundant
  citations that support exactly the same point.

If the evidence does not contain enough information to answer the question,
return:

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

    # Remove Markdown code fences if the model wraps the JSON.
    if content.startswith("```json"):
        content = content.removeprefix("```json").removesuffix("```").strip()

    elif content.startswith("```"):
        content = content.removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(content)

    except json.JSONDecodeError as error:
        print("\n--- RAW LLM RESPONSE ---")
        print(content)
        print("--- END RAW LLM RESPONSE ---\n")

        raise ValueError(f"LLM returned invalid JSON: {error}")
