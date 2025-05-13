import pandas as pd
from openai import OpenAI

import pandas as pd
import os
from openai import OpenAI
from tqdm import tqdm
import json
from candidate_classification_project import OPEN_API_KEY

# Load your OpenAI API key from environment variable or hardcode for testing
client = OpenAI(api_key=OPEN_API_KEY)  # or client = OpenAI(api_key="your-key")

# Load candidate data from CSV (adjust path/format as needed)
df = pd.read_excel("Anonymized Leads.xlsx")  # Or pd.read_excel("candidates.xlsx")
df = df.drop(columns=['Name', 'Email', 'Data sharing consent'])

# Function to build the structured prompt from a candidate row
def build_prompt(row):
    fields = "\n".join([f"**{col}**: {row[col]}" for col in df.columns])
    return f"""
Given the following candidate profile, return a JSON object with these keys:
- "Summary": A 2–3 sentence summary of the candidate.
- "Career_Goals": A <100-word description of their next career steps based on “Path to Impact”.
- "Management": TRUE if they mention managing a team/project/program, FALSE otherwise.
- "EA_Adjacent": TRUE if they mention 80,000 Hours, 80K, GWWC, or 10% pledge. FALSE otherwise.
- "XSensitive": TRUE if “Path to Impact” includes AI x-risk, AGI safety, or existential risk. FALSE otherwise.
- "SocialConcern": TRUE if it mentions justice, equity, inequality, or marginalized communities. FALSE otherwise.

Candidate Info:
{fields}

Return valid JSON only.
"""

# Function to call the ChatGPT API
def get_chatgpt_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error: {e}")
        return {
            "Summary": None,
            "Career_Goals": None,
            "Management": None,
            "EA_Adjacent": None,
            "XSensitive": None,
            "SocialConcern": None
        }

# Process all rows
results = []
for _, row in tqdm(df.iterrows(), total=len(df)):
    prompt = build_prompt(row)
    parsed = get_chatgpt_response(prompt)
    breakpoint()
    results.append(parsed)

# Combine original data with extracted results
df_out = pd.concat([df, pd.DataFrame(results)], axis=1)

# Save the final output
df_out.to_csv("enriched_candidates.csv", index=False)
print("✅ Done! Saved to enriched_candidates.csv")
