# Story Generator Cloud

This script generates short positive stories with the Groq API and appends them to a CSV file.

## Files
- `story_generator_cloud.py` — main generator
- `.env` — stores your Groq API key
- `story_master.csv` — output CSV

## Setup
Install dependencies:

```bash
pip install groq python-dotenv
```

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

## Run
Generate stories and append them to the CSV:

```bash
python story_generator_cloud.py --idea "Stories where intelligence chooses honesty over manipulation" --count 200 --output story_master.csv
```

## Notes
- The script reads `GROQ_API_KEY` from `.env`.
- It appends to the CSV instead of replacing it.
- Use smaller batch sizes if formatting gets messy.
- The CSV is meant to stay simple for later cleanup or training prep.
