
This repo is used for creating summaries for candidates, and identifying whether or not they fall into specific categories based of certain words in their responses. To run the code in this repo you first must download python and vscode. Once everything is set up you can run these steps:


Watch Videos:
- set_up MUST always be done before any other steps, all others can be done in any order, or individually

1. In terminal run <git pull>

2. To set up the environment and install all necessary packages run <poetry shell> then <poetry install>

3. Add the Leads file to the base of the repo. If you name it <Anonymized Leads.xlsx> no changes will need to be made to hte script, if it is named something else, you will have to update some parts of the script

4. Add the OPEN_API_KEY: run this command in the terminal: everything not including < >

<export OPEN_API_KEY=>


4. To run the NLP portion of the script, and return just the results for columns 3-6, in your terminal run 

<python src/candidate_classification_project/nlp_script.py --file_name "Anonymized Leads.xlsx">

This returns a file with the Candidates name, and 8 additional columns for the 4 categories (Management, EA_Adjacent, XSensitive, SocialConcern), and 4 coulmns flagging which values were found

4.b To edit the categories, update the values listed in rows 48-51 in nlp_script.py

5. To run the llm portion of the script, and return columns 1-2 (Summary, Career Goals), in your terminal run 

<python src/candidate_classification_project/openai_script.py --file_name "Anonymized Leads.xlsx" --row_start 0 --row_end 5>

5.b To update the prompt, edit lines 17-24 in openai_script.py

5.c To run the script on the entire file run: 

<python src/candidate_classification_project/openai_script.py --file_name "Anonymized Leads.xlsx">

5.d To run the script on a different sub-set, adjust the --row_start 0 --row_end 10 values, example of running on 100 rows

<python src/candidate_classification_project/openai_script.py --file_name "Anonymized Leads.xlsx" --row_start 0 --row_end 100>

6. To run both scripts, adn return a file with all output columns, in your terminal run 

<python src/candidate_classification_project/run_both.py --file_name "Anonymized Leads.xlsx" --row_start 0 --row_end 5>

- To update the summary and career goals prompt, go to the openai_script.py file, and see notes there
- To update the nlp key word search, go to the nlp_script.py and see notes there


Additional Notes on what each column represents
Summary: Please give me a short one-sentence summary of a job candidate's profile data, around 100 words or less. Focus on describing their professional track record, not complimenting them. Your summary should be firm and no-nonsense, and not try to sugarcoat things or inflate your evaluation of people just to be nice. Be fair but discerning. Focus on their educational and professional information. DO NOT focus on race, religion, color, national origin, gender, sexual orientation, or any other legally protected status. The summary should be accurate and not make up or guess facts.
Career_Goals: Based on the “Path to impact” field, summarize in less than 100 words what the person’s intended next career steps are. 
Management (TRUE/FALSE)
TRUE if the lead explicitly mentions managing a project, team, or program. FALSE otherwise.
EA_Adjacent (TRUE/FALSE)
 TRUE if the lead mentions “80,000 Hours,” “80K,” “GWWC,” or “10% pledge.” FALSE otherwise.
XSensitive (TRUE/FALSE)
 TRUE if the “Path to Impact” field includes concern about AI-related global catastrophic or existential risks, including terms like AI x-risk, AGI safety, or longtermist threats. FALSE otherwise.
SocialConcern (TRUE/FALSE)
 TRUE if the “Path to Impact” field mentions justice, equity, systemic inequality, or marginalized communities (e.g., racial justice, decolonization, gender equity, economic justice). FALSE otherwise.