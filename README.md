# Discord Quote & Song Bot

A Discord bot for daily server quotes and music sharing, fully configurable via environment variables.

---

## **Features**

* **Daily Quote of the Day**: Renames your server and updates the icon at a scheduled time (default 4:00 AM EST), using a random quote and image from designated channels.
* **Daily Song Post**: Shares a random YouTube, SoundCloud, or Spotify link from your music channel at a scheduled time (default 10:00 AM EST).
* **Manual Triggers**: Use `!rename` and `!song` commands for instant updates.
* **Highly Configurable**: Enable/disable features, set times and channels, all via environment variables or Railway's Variables tab.

---

## **Setup**

1. **Clone this repository**

   ```bash
   git clone https://github.com/your-username/discord-quote-song-bot.git
   cd discord-quote-song-bot
   ```

2. **Install requirements**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   * Copy `.env.example` to `.env`:

     ```bash
     cp .env.example .env
     ```
   * Fill in your values for:

     * Bot token
     * Server (guild) ID
     * Channel IDs for each feature
     * Enable/disable toggles
     * Schedule times (in EST, 24h format)

4. **Run the bot**

   ```bash
   python bot.py
   ```

---

## **Deploying on Railway**

1. **Push your repo to GitHub.**
2. **Create a Railway account:** [railway.app](https://railway.app/)
3. **Create a New Project** → Deploy from your GitHub repo.
4. **Set environment variables:**

   * Go to the “Variables” tab.
   * Click “Raw Editor” and paste the contents of `.env.example` (fill in your real values).
5. **Set your Start Command:**

   ```
   python bot.py
   ```
6. **Deploy!**
   Railway will install requirements and start your bot automatically.

---

## **Environment Variables**

> See `.env.example` for all required variables.
> **All scheduled times are in EST (US/Eastern).**

```
DISCORD_TOKEN=
GUILD_ID=
QUOTE_CHANNEL_ID=
ICON_CHANNEL_ID=
POST_CHANNEL_ID=
MUSIC_CHANNEL_ID=
SONG_POST_CHANNEL_ID=
ENABLE_DAILY_QUOTE=true
ENABLE_DAILY_SONG=true
# Times in 24h format, e.g. 4:00 for 4AM, 13:00 for 1PM (EST)
QUOTE_TIME=4:00
SONG_TIME=10:00
```

---

## **Security & Best Practices**

* **Never commit your real `.env` file** or Discord token to GitHub!
  (It’s already ignored by `.gitignore`.)
* Use `.env.example` for sharing config structure.
* Grant your bot only the permissions it needs in your Discord server.

---

## **License**

MIT License. See [LICENSE](LICENSE) for details.

---

## **Contributing**

Pull requests and suggestions are welcome! Please open an issue first to discuss major changes.

---

