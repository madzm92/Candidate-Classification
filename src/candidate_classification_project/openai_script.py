import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import json
from candidate_classification_project import OPEN_API_KEY

def get_chatgpt_response(client, prompt):
    """Calls the llm with the desired prompt and retirms a dictionary with the column names and response values.
    If the llm call does not work, a dictionary is still return but the values are None."""

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
        }
    
def build_prompt(df: pd.DataFrame, row):
    """Function to build the structured prompt from a candidate row
    takes in the dataframe, and a single row of the dataframe.
    Returns the prompt for the llm."""

    fields = "\n".join([f"**{col}**: {row[col]}" for col in df.columns])
    return f"""
    Given the following candidate profile, return a JSON object with these keys:
    - "Summary": Please give me a short one-sentence summary of a job candidate's profile data, 
    around 100 words or less. Focus on describing their professional track record, not complimenting them. 
    Your summary should be firm and no-nonsense, and not try to sugarcoat things or inflate your evaluation of 
    people just to be nice. Be fair but discerning. Focus on their educational and professional information. 
    DO NOT focus on race, religion, color, national origin, gender, sexual orientation, or any other legally protected status. 
    The summary should be accurate and not make up or guess facts.
    - "Career_Goals": Based on the “Path to impact” field, summarize in less than 100 words what the person’s intended next career steps are.

    Candidate Info:
    {fields}

    Return valid JSON only.
    """

def process_llm_responses(file_name: str, api_key: str, row_start: int = None, row_end: int = None):
    """This script reads in the cadidate leads file, and retuns a dataframe with 3 columns: the candidates name, a summary of the candidates experience 
    and their career goals. The responses are generated using openais llm.
    file_name: name of file"""

    # Load your OpenAI API key from environment variable or hardcode for testing
    client = OpenAI(api_key=api_key)  # or client = OpenAI(api_key="your-key")

    # Load candidate data from CSV (adjust path/format as needed)
    df = pd.read_excel(file_name)
    df = df.drop(columns=['Name', 'Email', 'Data sharing consent'])

    if not row_start:
        row_start = 0
    if not row_end:
        row_end = -1
    df = df.iloc[row_start:row_end]

    # Process all rows
    results = []
    for _, row in tqdm(df.iterrows(), total=len(df)):
        prompt = build_prompt(df, row)
        parsed = get_chatgpt_response(client, prompt)
        results.append(parsed)

    # Combine original data with extracted results
    df_out = pd.concat([df, pd.DataFrame(results)], axis=1)

    # Drop original columns
    df_out = df_out.drop(columns=['Career level', 'Profile URL', 'Other profile URL','Job title', 'Organisation', 'Profession', 'Profession (other)','Field of study', 'Field of study (other)', 'Path to impact','Experience', 'Skills', 'Impressive project', 'Course (single select)'])

    #renames full name column
    df_out = df_out.rename(columns={'[*] Full name':'Full name'})

    # Save the final output
    df_out.to_excel("llm_results.xlsx", index=False)
    print("✅ Done! Saved to llm_results.xlsx")

    return df_out

if __name__ == "__main__":
    file_name = "Anonymized Leads.xlsx"
    api_key = OPEN_API_KEY
    row_start = 0
    row_end = 1
    process_llm_responses(file_name, api_key, row_start, row_end)