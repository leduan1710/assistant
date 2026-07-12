import sys

from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
\u2022 Tone: helpful, factual, concise.
\u2022 Only answer using the uploaded docs.
\u2022 Max 5 bullet points; else link to the doc.
\u2022 Cite up to 3 "Article URL:" lines per reply."""

MODEL = "gemini-3.1-flash-lite"

client = genai.Client()


def main():
    if len(sys.argv) < 3:
        print('Usage: python scripts/query_bot.py "<file_search_store_name>" "your question"')
        sys.exit(1)

    store_name = sys.argv[1]
    question = sys.argv[2]

    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[store_name]))],
        ),
    )

    print(response.text)

if __name__ == "__main__":
    main()
