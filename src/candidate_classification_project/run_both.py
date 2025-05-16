import pandas as pd
from candidate_classification_project.nlp_script import process_nlp_responses
from candidate_classification_project.openai_script import process_llm_responses
from candidate_classification_project import OPEN_API_KEY
import argparse
import os

def main(file_name, api_key, row_start, row_end):
    nlp_df = process_nlp_responses(file_name)
    llm_df = process_llm_responses(file_name, api_key, row_start, row_end)
    final_df = pd.merge(nlp_df, llm_df, on='Full name')

    # Save the final output
    final_df.to_excel("all_columns.xlsx", index=False)
    print("✅ Done! Saved to all_columns.xlsx")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run lead processing script with parameters.")
    
    parser.add_argument(
        "--file_name", type=str, default="Anonymized Leads.xlsx",
        help="Name of the Excel file to process"
    )
    parser.add_argument(
        "--api_key", type=str, default=os.getenv("OPEN_API_KEY"),
        help="API key for authentication (default reads from OPEN_API_KEY env variable)"
    )
    parser.add_argument(
        "--row_start", type=int, default=None,
        help="Start row (inclusive)"
    )
    parser.add_argument(
        "--row_end", type=int, default=None,
        help="End row (exclusive)"
    )

    args = parser.parse_args()

    main(
        file_name=args.file_name,
        api_key=args.api_key,
        row_start=args.row_start,
        row_end=args.row_end
    )