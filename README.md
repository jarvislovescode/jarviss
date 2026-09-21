# J.A.R.V.I.S Discord Bot

A witty, JARVIS-style AI assistant for your Discord server. Fully free stack:
discord.py + Groq (free LLM API) + SQLite, deployed on Render's free tier.

## Features

- `/ask <prompt>` — chat with JARVIS, or just @mention the bot
- `/roast @user` — playful roast mode (auto-blocks the owner and Rhodey)
- `/remind <when> <message>` — reminders (e.g. `10m`, `2h`, `1d`)
- `/note` and `/notes` — quick personal memory
- Owner and "Rhodey" (your bff) get special treatment baked into the persona

## 1. Discord setup

1. Go to https://discord.com/developers/applications → New Application
2. Bot tab → Reset Token → copy it (this is `DISCORD_TOKEN`)
3. Under **Privileged Gateway Intents**, enable **Message Content Intent** and
   **Server Members Intent**
4. OAuth2 → URL Generator → scopes: `bot`, `applications.commands` →
   permissions: Send Messages, Read Message History, Use Slash Commands →
   open the generated URL to invite the bot to your server

## 2. Get your IDs

Enable Developer Mode: Discord Settings → Advanced → Developer Mode.
Then right-click yourself and Rhodey in the server → Copy User ID.

## 3. Groq API key (free)

Sign up at https://console.groq.com → API Keys → create one. No credit card
required for the free tier.

## 4. Local setup

```bash
git clone <your-repo-url>
cd jarvis-bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then fill in your values
python main.py
```

## 5. Deploy on Render (free)

1. Push this folder to a GitHub repo
2. On https://render.com → New → Web Service → connect your repo
3. Runtime: Python 3
4. Build command: `pip install -r requirements.txt`
5. Start command: `python main.py`
6. Add environment variables (same as `.env`) in the Render dashboard
7. Deploy

Render's free web services spin down after ~15 min of no HTTP traffic. This
bot runs a tiny Flask server (`keep_alive.py`) with a `/health` endpoint —
point a free [UptimeRobot](https://uptimerobot.com) monitor at your Render
URL every 5 minutes to keep it awake.

⚠️ **Note on data persistence:** Render's free tier has an ephemeral
filesystem, so the SQLite file (`jarvis.db`) can reset on redeploys or
restarts. Fine for a first version — if you want notes/reminders to survive
long-term, swap `db.py` for a free hosted Postgres (Supabase or Neon both
have free tiers) instead.

## Customizing the persona

Edit `persona.py` to change how JARVIS talks, and `config.py`/`.env` to set
who the "owner" and "Rhodey" are.
