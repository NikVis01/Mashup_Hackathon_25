# Bull Data Scraper & Uploader: Backend

![diagram (4)](https://github.com/user-attachments/assets/7183c00f-ab85-4559-973f-087b247dd55c)

### 📊 Bull Reports
With all bull data stored in a structured, type-safe format in Supabase, you can easily generate rich, data-driven bull reports for breeding, analytics, or presentation—directly from your database.

## Environment Setup

1. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```
2. **Create a `.env` file** in the project root with the following variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SUPABASE_URL=https://yourprojectid.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key_here
   ```
3. Set up your Supabase table** with columns matching the merged JSON keys.

   Make sure percentage columns can take floats & cappa_casein, beta_casein can take text (str)

## How to Run

1. **Edit `main.py`** to set the URLs you want to scrape.
2. **Run the script**:
   ```bash
   python main.py
   ```

- The Bulli scraper uses Playwright to render JavaScript-heavy pages and take a full-page screenshot.
- The Bulli data is extracted using GPT-4o Vision, so you need access to OpenAI's vision models.
- The script automatically renames the `aAa` field to `aaa` to match Postgres column naming conventions.
- All environment variables are loaded from `.env` for security and flexibility.

