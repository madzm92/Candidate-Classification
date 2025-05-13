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

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# Define keyword sets
EA_KEYWORDS = {"80,000 hours", "80k", "gwwc", "giving what we can", "10% pledge"}
X_SENSITIVE = {"ai x-risk", "agi safety", "existential risk", "ai alignment"}
SOCIAL_TERMS = {"justice", "equity", "inequality", "marginalized", "oppression", "social concern"}
MGMT_TERMS = {"manage", "supervise", "lead", "led", "managed", "oversaw", "directed", "organized", "coordinated"}

# Preprocess text
def preprocess(text):
    if not isinstance(text, str):
        return ""
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum() and t not in stop_words]
    return " ".join(tokens)

# Check if any keywords are present in text
def contains_keywords(text, keywords):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

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
    
    return {
        "Summary": summarize(profile_text, n=2),
        "Career_Goals": summarize(str(row.get("Path to Impact", "")), n=1),
        "Management": contains_keywords(clean_text, MGMT_TERMS),
        "EA_Adjacent": contains_keywords(profile_text, EA_KEYWORDS),
        "XSensitive": contains_keywords(profile_text, X_SENSITIVE),
        "SocialConcern": contains_keywords(profile_text, SOCIAL_TERMS),
    }

# Load data and process
df = pd.read_excel("Anonymized Leads.xlsx")  # Or pd.read_excel("candidates.xlsx")
df = df.drop(columns=['Name', 'Email', 'Data sharing consent'])
results = df.apply(process_row, axis=1, result_type="expand")
df_out = pd.concat([df, results], axis=1)
df_out = df_out[['[*] Full name', 'Summary', 'Career_Goals', 'Management', 'EA_Adjacent', 'XSensitive', 'SocialConcern']]

# Save the result
df_out.to_csv("nlp_enriched_candidates.csv", index=False)
print("✅ Done! Saved to nlp_enriched_candidates.csv")
