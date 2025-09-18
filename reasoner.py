# reasoner.py
from ollama import chat
from retriever import retrieve

def generate_plan(query):
    logs = retrieve(query)

    context = "\n".join([
        f"Title: {log['title']}\nFix Steps: {', '.join(log['fix_steps'])}\n"
        for log in logs
    ])

    prompt = f"""You are an Outlook troubleshooting expert.
Based on the following logs, generate a numbered step-by-step fix plan for: "{query}"

Logs:
{context}

Respond with numbered steps only.
"""

    response = chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"].strip()

if __name__ == "__main__":
    query = "Outlook won't open"
    plan = generate_plan(query)
    print("🧠 Troubleshooting Plan:\n")
    print(plan)