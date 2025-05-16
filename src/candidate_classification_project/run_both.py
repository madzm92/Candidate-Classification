import pandas as pd
from candidate_classification_project.nlp_script import process_nlp_responses
from candidate_classification_project.openai_script import process_llm_responses
from candidate_classification_project import OPEN_API_KEY

def main(file_name, api_key, row_start, row_end):
    nlp_df = process_nlp_responses(file_name)
    llm_df = process_llm_responses(file_name, api_key, row_start, row_end)
    final_df = pd.merge(nlp_df, llm_df, on='Full name')

    # Save the final output
    final_df.to_excel("all_columns.xlsx", index=False)
    print("✅ Done! Saved to all_columns.xlsx")

if __name__ == "__main__":
    file_name = "Anonymized Leads.xlsx"
    api_key = OPEN_API_KEY
    row_start = 0
    row_end = 1
    main(file_name, api_key, row_start, row_end)