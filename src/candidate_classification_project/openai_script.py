import pandas as pd
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio
import json
import argparse
import os
import time
from datetime import datetime
import asyncio
import anthropic

def build_batch_prompts(df, batch):
    """Builds a single prompt string for a batch of candidate profiles."""
    profiles = []
    for _, row in batch.iterrows():
        fields = "\n".join([f"**{col}**: {row[col]}" for col in df.columns])
        profiles.append(fields)
    combined_profiles = "\n\n---\n\n".join(profiles)
    return f"""
You are a data summarization model. For each candidate below, return a JSON list where each element corresponds to one candidate.

Each element should be an object with the following keys:
- "Summary": A concise, factual, one-sentence summary (max ~100 words) describing their professional and educational background only. DO NOT focus on race, religion, color, national origin, gender, sexual orientation, or any other legally protected status. 

- "Career_Goals": A short (≤100 words) summary of their intended next career steps based on the “Path to impact” field.

Do not guess or add information that isn't present. Be neutral and factual.
Return only valid JSON — a list of objects, one per candidate.

Candidate Profiles:
{combined_profiles}
    """

def get_claude_batch_response_sync(client, prompt, batch_idx):
    """
    Synchronous call to Claude API for a batch.
    """
    try:
        claude_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
        start_time = time.time()
        response = client.completions.create(
            model="claude-4.1",
            prompt=claude_prompt,
            max_tokens_to_sample=2000,
        )
        end_time = time.time()
        duration = end_time - start_time

        content = response.completion.strip()

        # Try parsing JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print(f"⚠️ JSON parse failed — batch {batch_idx}, attempting cleanup")
            content_clean = content[content.find("["): content.rfind("]") + 1]
            data = json.loads(content_clean)

        token_info = {
            "input_tokens": getattr(response, "prompt_tokens", None),
            "output_tokens": getattr(response, "completion_tokens", None),
            "total_tokens": getattr(response, "total_tokens", None),
            "duration_sec": round(duration, 2),
        }
        breakpoint()
        return batch_idx, data, token_info

    except Exception as e:
        print(f"❌ Error in batch {batch_idx}: {e}")
        return batch_idx, [], {"error": str(e)}


async def get_claude_batch_response(client, prompt, batch_idx, semaphore):
    """
    Async wrapper that runs Claude's synchronous API in a thread for parallelization.
    """
    async with semaphore:
        return await asyncio.to_thread(get_claude_batch_response_sync, client, prompt, batch_idx)



async def get_chatgpt_batch_response(client, prompt, batch_idx, semaphore):
    """Send a batch prompt to GPT-5 asynchronously and return JSON + token info."""
    async with semaphore:
        try:
            start_time = time.time()

            response = await client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a precise JSON generator for candidate summaries."},
                    {"role": "user", "content": prompt},
                ],
            )
            end_time = time.time()
            duration = end_time - start_time

            content = response.choices[0].message.content.strip()
            usage = response.usage

            # Try parsing JSON directly
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                print(f"⚠️ JSON parse failed — batch {batch_idx} attempting cleanup")
                content_clean = content[content.find("[") : content.rfind("]") + 1]
                data = json.loads(content_clean)

            token_info = {
                "input_tokens": usage.prompt_tokens if usage else None,
                "output_tokens": usage.completion_tokens if usage else None,
                "total_tokens": usage.total_tokens if usage else None,
                "duration_sec": round(duration, 2),
            }
            
            return batch_idx, data, token_info

        except Exception as e:
            print(f"❌ Error in batch {batch_idx}: {e}")
            return batch_idx, [], {"error": str(e)}


async def process_llm_responses(file_name: str, api_key: str, batch_size: int = 10,
                                row_start: int = None, row_end: int = None, concurrency: int = 3):
    """Processes candidates in batches using GPT-5 asynchronously and saves incremental output."""
    client = AsyncOpenAI(api_key=api_key)
    # client = anthropic.Client(api_key=os.getenv("CLAUDE_API_KEY"))
    df = pd.read_excel(file_name)
    df = df.drop(columns=['Name', 'Email', 'Data sharing consent'], errors="ignore")

    if row_start or row_end:
        df = df.iloc[row_start:row_end]

    output_file = "llm_results.xlsx"
    token_log_file = "token_log.csv"

    # Prepare log file if not exists
    if not os.path.exists(token_log_file):
        pd.DataFrame(columns=["timestamp", "batch_start", "batch_end",
                              "input_tokens", "output_tokens", "total_tokens",
                              "duration_sec"]).to_csv(token_log_file, index=False)

    # Load existing results if partial file exists
    existing = pd.read_excel(output_file) if os.path.exists(output_file) else pd.DataFrame()

    semaphore = asyncio.Semaphore(concurrency)
    tasks = []

    print(f"🚀 Starting parallel batch processing | batch_size={batch_size} | concurrency={concurrency}")

    batches = [df.iloc[i:i + batch_size] for i in range(0, len(df), batch_size)]

    for batch_idx, batch in enumerate(batches):
        prompt = build_batch_prompts(df, batch)
        tasks.append(get_chatgpt_batch_response(client, prompt, batch_idx, semaphore))
        # tasks.append(get_claude_batch_response(client, prompt, batch_idx, semaphore))

    start_time = time.time()
    results = await tqdm_asyncio.gather(*tasks)
    total_duration = round(time.time() - start_time, 2)

    for batch_idx, responses, token_info in results:
        batch = batches[batch_idx]

        if isinstance(responses, list):
            batch_out = pd.DataFrame(responses)
        else:
            batch_out = pd.DataFrame([responses])

        batch_out.reset_index(drop=True, inplace=True)
        batch.reset_index(drop=True, inplace=True)

        df_out = pd.concat([batch, batch_out], axis=1)
        existing = pd.concat([existing, df_out], ignore_index=True)
        existing.to_excel(output_file, index=False)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "batch_start": batch_idx * batch_size,
            "batch_end": batch_idx * batch_size + len(batch),
            **token_info
        }
        pd.DataFrame([log_entry]).to_csv(token_log_file, mode='a', header=False, index=False)

        print(f"✅ Batch {batch_idx} done | Tokens: {token_info.get('total_tokens')} | Time: {token_info.get('duration_sec')}s")

    print(f"🏁 All batches processed successfully in {total_duration}s!")
    print(f"Results saved to: {output_file}")
    print(f"Token usage log saved to: {token_log_file}")


def main():
    parser = argparse.ArgumentParser(description="Run GPT-5 batch summarization.")
    parser.add_argument("--file_name", type=str, default="test_crm.xlsx", help="Excel file to process")
    parser.add_argument("--api_key", type=str, default=os.getenv("OPEN_API_KEY"), help="OpenAI API key")
    parser.add_argument("--batch_size", type=int, default=10, help="Batch size (default=5)")
    parser.add_argument("--row_start", type=int, default=None)
    parser.add_argument("--row_end", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=3, help="Number of parallel requests (default=3)")

    args = parser.parse_args()

    asyncio.run(process_llm_responses(
        file_name=args.file_name,
        api_key=args.api_key,
        batch_size=args.batch_size,
        row_start=args.row_start,
        row_end=args.row_end,
        concurrency=args.concurrency
    ))


if __name__ == "__main__":
    main()
