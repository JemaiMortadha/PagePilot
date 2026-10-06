# 🚀 PagePilot

A 100% free, fully autonomous AI pipeline that scrapes competitor Facebook pages, rewrites text, generates custom AI images, and auto-publishes to your page.

Designed to run continuously on a free tier, this script uses **Apify** for scraping, **Google Gemini** for OCR and intelligent text rewriting, **Pollinations.ai** for free AI image generation, and the **Facebook Graph API** for automated publishing.

---

## ✨ Features
- **100% Free to Run:** Operates entirely within the free tiers of Apify ($5/mo), Gemini (1500 req/day), and Pollinations (unlimited).
- **Fully Autonomous:** Just run `main.py` and it will loop continuously, checking for new competitor posts every hour.
- **Smart Deduplication:** Remembers what it has posted across different competitor pages and safely picks up exactly where it left off if your internet drops.
- **AI-Powered:** Uses Gemini Vision to read text directly off competitor images (OCR), rewrites the fact to make it engaging, and generates a stunning matching background.
- **Professional Watermarking & Style:** Automatically overlays the text in a consistent layout, adds a customized topic tag (SCIENCE, HISTORY, etc.), and brands the bottom with your Page name.

---

## 🛠 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/PagePilot.git
   cd PagePilot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment:**
   ```bash
   cp .env.example .env
   ```

---

## 🔑 Step-by-Step API Setup (100% Free)

You will need to fill out the `.env` file with three sets of credentials:

### 1. Gemini API (The Brains)
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in and click **"Get API Key"**.
3. Copy the key and paste it into `GEMINI_API_KEY` in your `.env` file.

### 2. Apify (The Scraper)
1. Go to [Apify](https://apify.com/) and create a free account.
2. Go to Settings > Integrations to find your personal API Token.
3. Paste it into `APIFY_API_TOKEN` in your `.env` file.

### 3. Facebook Graph API (The Publisher)
This is the most involved step, but you only have to do it once!
1. Go to [Meta for Developers](https://developers.facebook.com/) and click **My Apps** > **Create App**.
2. Select **"Other"** -> **"Business"**.
3. Under the app dashboard, set up the **Facebook Login for Business** or simply use the **Graph API Explorer** tool.
4. **Generate a Page Access Token:** 
   - Use the Graph API Explorer.
   - Select your App in the top right.
   - Click "Add a Permission" and add `pages_manage_posts`, `pages_read_engagement`, and `pages_show_list`.
   - Click **Generate Access Token**. When prompted, select your specific Facebook Page.
   - *Important:* Extend the token in the "Access Token Debugger" so it doesn't expire in 1 hour.
5. Paste this long-lived token into `FB_PAGE_ACCESS_TOKEN` and your Page ID into `FB_PAGE_ID`.

**🚨 CRITICAL: Putting the App in "Live Mode"**
If you don't do this, Facebook will hide your automated posts from the public!
- In your Meta Developer Dashboard, look at the top bar for the **App Mode** toggle.
- You must switch it from **Development** to **Live**.
- **Privacy Policy Workaround:** Facebook will ask for a Privacy Policy URL before going Live. Since this is a personal automation tool, you can simply create a public Google Doc with a single sentence (*"This app is a private automation tool and collects no user data."*), get the shareable link ("Anyone with the link can view"), and paste that into the Privacy Policy URL field.

---

## ⚙️ Configuration

In your `.env` file, configure the behavior of the bot:
- `COMPETITOR_PAGES`: A comma-separated list of Facebook pages you want to monitor (e.g., `https://www.facebook.com/competitor1,https://www.facebook.com/competitor2`).
- `PAGE_NAME`: The name of your page. This will be automatically watermarked onto the bottom of the generated images!
- `POSTS_TO_CHECK`: How deep the scraper should look (default is 5).

---

## 🚀 Usage

Once everything is set up, simply run:
```bash
python3 main.py
```

The script will launch as a resilient background service. It will:
1. Wake up and check your competitors.
2. If it finds a new post, it will process it, generate the art, and publish it.
3. Go to sleep for 1 hour.
4. Repeat indefinitely.

If your connection drops, simply run the script again. It uses `seen_posts.json` to keep track of exactly what has already been published, ensuring you never double-post!

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
