import os
import pandas as pd
import google.generativeai as genai
import re

GEMINI_API_KEY = "AIzaSyA2zJEBibJuH4Of7wxp0InifK0uw9gNMzE"
genai.configure(api_key=GEMINI_API_KEY)

CSV_PATH_1 = os.path.join('data', 'analysis_results.csv')
CSV_PATH_2 = os.path.join('data', 'ANALYSIS.csv')
df1 = pd.read_csv(CSV_PATH_1)
df2 = pd.read_csv(CSV_PATH_2)
df = pd.concat([df1, df2], ignore_index=True)
# CSV_PATH = os.path.join('data', 'analysis_results.csv')
# df = pd.read_csv(CSV_PATH)

# Helper: extract keywords (words, quoted phrases, names)
def extract_keywords(query):
    # Extract quoted phrases or words
    return re.findall(r'"([^"]+)"|(\w+)', query.lower())

def retrieve_relevant_rows(query):
    # Use all words and quoted phrases as keywords
    raw_keywords = extract_keywords(query)
    keywords = [k[0] if k[0] else k[1] for k in raw_keywords]
    def row_match(row):
        row_str = str(row).lower()
        return any(kw in row_str for kw in keywords if kw)
    mask = df.apply(row_match, axis=1)
    return df[mask]

def format_context(rows, max_rows=10):
    if rows.empty:
        return ""
    # Limit to max_rows for prompt size
    rows = rows.head(max_rows)
    return rows.to_csv(index=False)

def generate_gemini_answer(question, context):
    model = genai.GenerativeModel('gemini-2.0-flash')
    if context.strip():
        prompt = (
            "You are a data assistant. Given the following CSV data rows as background information, "
            "answer the question concisely and do NOT repeat or enumerate the CSV rows in your answer. "
            "Do NOT mention the frequency or number of occurrences of any entry. "
            "Use the data only for reference and provide a clear, direct answer.\n"
            f"{context}\n\nAnswer the question: {question}"
        )
    else:
        prompt = (
            "You are a data assistant. There is no relevant data in the CSV for the question. "
            "Please answer the question using your own knowledge and reasoning: "
            f"{question}"
        )
    response = model.generate_content(prompt)
    answer = response.text.strip() if hasattr(response, 'text') else str(response)
    # Remove Markdown bold (**...**) from the answer
    answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)
    return answer