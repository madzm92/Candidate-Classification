import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
import string

# Download NLTK resources if needed
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))

# Keyword sets
EA_KEYWORDS = {"80,000 hours", "80k", "gwwc", "giving what we can", "10% pledge"}
X_SENSITIVE = {"ai x-risk", "agi safety", "existential risk"}
SOCIAL_TERMS = {"justice", "equity", "inequality", "marginalized", "oppression", "social concern"}
MGMT_TERMS = {"manage", "supervise", "lead", "led", "managed", "oversaw", "directed", "organized", "coordinated"}

# Preprocess text
def preprocess(text):
    if not isinstance(text, str):
        return ""
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum() and t not in stop_words]
    return " ".join(tokens)

# Return list of keywords found in text
def find_keywords(text, keywords, preprocess_text=False):
    text_to_check = preprocess(text) if preprocess_text else text.lower()
    found = [kw for kw in keywords if kw in text_to_check]
    return found

# Naive summarizer: return first 1–2 sentences
def summarize(text, n=2):
    if not isinstance(text, str):
        return ""
    sentences = sent_tokenize(text)
    return " ".join(sentences[:n])

# Process each row of the DataFrame
def process_row(row):
    profile_text = " ".join(str(row[col]) for col in row.index if pd.notna(row[col]))
    clean_text = preprocess(profile_text)

    # Check and collect found keywords
    mgmt_found = find_keywords(clean_text, MGMT_TERMS, preprocess_text=False)
    ea_found = find_keywords(profile_text, EA_KEYWORDS)
    xs_found = find_keywords(profile_text, X_SENSITIVE)
    social_found = find_keywords(profile_text, SOCIAL_TERMS)

    return {
        "Management": bool(mgmt_found),
        "MgmtTermsFound": ", ".join(mgmt_found),
        "EA_Adjacent": bool(ea_found),
        "EATermsFound": ", ".join(ea_found),
        "XSensitive": bool(xs_found),
        "XSensitiveTermsFound": ", ".join(xs_found),
        "SocialConcern": bool(social_found),
        "SocialTermsFound": ", ".join(social_found),
    }

def process_nlp_responses(input_file_name: str):
    """This script reads in the Anonymized Leads file
    searches for key words,and returns a dataframe with 
    the new boolean columns, and key words found for each category"""

    # Load and process
    df = pd.read_excel(input_file_name)
    df = df.drop(columns=['Name', 'Email', 'Data sharing consent'])
    results = df.apply(process_row, axis=1, result_type="expand")
    df_out = pd.concat([df, results], axis=1)

    # Drop original columns
    df_out = df_out.drop(columns=['Career level', 'Profile URL', 'Other profile URL','Job title', 'Organisation', 'Profession', 'Profession (other)','Field of study', 'Field of study (other)', 'Path to impact','Experience', 'Skills', 'Impressive project', 'Course (single select)'])
    
    #renames full name column
    df_out = df_out.rename(columns={'[*] Full name':'Full name'})

    # exports file
    df_out.to_excel('nlp_results.xlsx')
    print("✅ Done! Saved to nlp_results.xlsx")
    
    return df_out

if __name__ == "__main__":
    process_nlp_responses("Anonymized Leads.xlsx")