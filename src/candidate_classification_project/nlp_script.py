import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
import os
import argparse

# Download NLTK resources if needed
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
# nltk.download('punkt_tab')

def preprocess(text):
    """Preprocess text"""

    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    if not isinstance(text, str):
        return ""
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum() and t not in stop_words]
    return " ".join(tokens)

def find_keywords(text, keywords, preprocess_text=False):
    """Return list of keywords found in text"""

    text_to_check = preprocess(text) if preprocess_text else text.lower()
    found = [kw for kw in keywords if kw in text_to_check]
    return found

def summarize(text, n=2):
    """Naive summarizer: return first 1–2 sentences"""

    if not isinstance(text, str):
        return ""
    sentences = sent_tokenize(text)
    return " ".join(sentences[:n])

def process_row(row, categories: dict):
    """Process each row of the DataFrame using dynamic keyword categories"""

    profile_text = " ".join(str(row[col]) for col in row.index if pd.notna(row[col]))
    clean_text = preprocess(profile_text)

    results = {}
    for cat_name, keywords in categories.items():
        found = find_keywords(clean_text, keywords, preprocess_text=False)
        results[cat_name] = bool(found)
        results[f"{cat_name} Terms Found"] = ", ".join(found)

    return results

def process_nlp_responses(file_name: str, categories: dict):
    df = pd.read_excel(file_name)
    df = df.drop(columns=['Name', 'Email', 'Data sharing consent'])

    # Run NLP
    results = df.apply(lambda row: process_row(row, categories), axis=1, result_type="expand")
    df_out = pd.concat([df, results], axis=1)

    # Keep only full name + NLP output columns
    nlp_columns = list(categories.keys())
    terms_columns = [f"{cat} Terms Found" for cat in categories.keys()]
    columns_to_keep = ['[*] Full name'] + nlp_columns + terms_columns

    df_out = df_out[[col for col in columns_to_keep if col in df_out.columns]]

    # Export
    output_file = os.path.join(os.path.expanduser("~"), "Desktop", "nlp_results.xlsx")
    df_out.to_excel(output_file, index=False)
    print(f"✅ Done! Saved to {output_file}")

    return df_out

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run lead processing script with parameters.")
    
    parser.add_argument(
        "--file_name", type=str, default="Anonymized Leads.xlsx",
        help="Name of the Excel file to process"
    )

    args = parser.parse_args()

    process_nlp_responses(
        file_name=args.file_name,
    )