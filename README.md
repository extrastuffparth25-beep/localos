# LOCALOS — AI-Powered Local SEO Agency

Welcome to the LOCALOS core repository. This platform is designed to run a highly profitable, fully automated Local SEO agency targeting businesses buried on Google Maps.

## 🚀 The Business Model
- **Find**: Automatically scrape Google Maps for local businesses (plumbers, dentists, etc.) not ranking in the top 3.
- **Score**: AI grades them (Tier A/B/C) based on rating, review count, and website SEO health.
- **Outreach**: AI generates human-sounding, hyper-personalized 5-step email sequences and Gmail drafts.
- **Deliver**: AI generates weekly GBP posts, review responses, and keyword strategies.
- **Manage**: Track everything in the built-in Kanban CRM and show clients their results via the dashboard.

## 📁 Repository Structure
- `website/`: The premium dark-themed agency website, CRM pipeline, and Client Dashboard.
  - Ready to be deployed to Cloudflare Pages for free.
- `prospector/`: The Python automation engine.
  - `main.py`: The daily orchestrator.
  - `prospector.py`: Multi-source search engine scraper.
  - `scorer.py`: AI qualification engine.
  - `drafter.py`: Gmail IMAP draft creator.
  - `emailer.py`: Daily HTML digest sender.
  - `gbp_agent/`: The service delivery tools (posts, reviews, keywords).
  - `outreach/`: The AI messaging templates (Email, LinkedIn, WhatsApp).

## 🛠️ Setup & Deployment

### 1. Website & CRM (Free)
1. Push this repository to GitHub.
2. Go to [Cloudflare Pages](https://pages.cloudflare.com/) -> Create Project -> Connect to Git.
3. Select the `website` directory as the build output.
4. Deploy! Your agency is now live.

### 2. Prospector Automation (Free)
The prospector runs automatically via GitHub Actions (`.github/workflows/daily_prospects.yml`).
You need to add the following **Repository Secrets** in GitHub:
- `GMAIL_USER`: Your main email (for receiving digests)
- `GMAIL_APP_PASSWORD`: App password for the main email
- `OUTREACH_GMAIL_USER`: The email account you send cold outreach from
- `OUTREACH_GMAIL_APP_PASSWORD`: App password for the outreach email
- `PAT_TOKEN`: A Personal Access Token (classic) with `repo` permissions to commit the CSV.

### 3. Running Locally
```bash
cd prospector
pip install -r requirements.txt

# Run the full pipeline
python main.py

# Run a test without sending emails
python main.py --dry-run

# See what the outreach emails look like
python main.py --preview-outreach
```

## 💰 Delivering the Service
When you close a client for $500/month:
1. Have them add your Google account as a "Manager" to their Google Business Profile.
2. Run the `gbp_agent/keyword_optimizer.py` to get their new categories and description. Update their profile.
3. Every week, run `gbp_agent/post_generator.py` to generate 2-4 posts. Copy-paste them into their GBP.
4. Run `gbp_agent/review_responder.py` to reply to any new reviews they got.
5. Watch their ranking climb and show them the `dashboard.html`!
