# backend/app/llm/compose.py

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load system prompt
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "answer.txt")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def compose_answer(question: str, snippets: list[str]) -> str:
    try:
        """
        Sends the question + retrieved snippets to the LLM and returns a composed answer.
        """
        if not snippets:
            return "I couldn't find relevant educational material."
    
        # Combine snippets as numbered text
        context = "\n\n".join([f"[[{i+1}]] {s}" for i, s in enumerate(snippets)])

        #Create chat completion request
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}\n\nSnippets:\n{context}"}
            ],
            temperature=0.4,
        )

        return completion.choices[0].message.content.strip()
    
    except RateLimitError:
        return ("Sorry, I'm temporarily unable to generate an answer.")