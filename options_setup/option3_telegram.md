# 📱 Option 3 Setup Guide: Telegram Command Center Integration

This guide provides instructions to hook your ISF-Core engine up with a Telegram Bot. This enables you to send prompts, monitor active execution loops, and receive instant alerts and browser screenshots directly on your phone.

## Why Setup Telegram Integration?
* **On-the-go Tasking:** Send requests to your AI workers while away from your computer.
* **Real-time Notifications:** Receive instant notifications when a background cron job finishes or when a self-healing loop runs into an exception.
* **Visual Verification:** Receive high-resolution screenshots of browser agent runs (e.g., eLeave claims or automated test states) as push messages on your phone.

---

## Step 1: Create a Telegram Bot

You must register a bot on Telegram to obtain an API access token:

1. Open Telegram on your phone or desktop and search for **@BotFather** (the official bot-creation bot).
2. Start a chat and send `/newbot`.
3. Follow the instructions to give your bot a **name** (e.g., `My ISF Factory Bot`) and a **username** (e.g., `isf_factory_my_bot`).
4. Copy the generated **HTTP API Token** (it looks like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

---

## Step 2: Retrieve Your Telegram Chat ID

To prevent random users from interacting with your AI engine, the bot will only reply to your specific Telegram account. You must find your unique Chat ID:

1. Search Telegram for **@userinfobot** or **@chatIDrobot**.
2. Start a chat with the bot.
3. It will instantly reply with your numeric **Id** (e.g., `987654321`). Copy this number.

---

## Step 3: Configure Environment Variables

Update your `.env` file at the root of your `isf-core` directory to include your Telegram credentials:

1. Open `.env`:
   ```bash
   nano .env
   ```
2. Enable and fill in the Telegram variables:
   ```env
   # Telegram Bot Integration
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ_your_token
   TELEGRAM_CHAT_ID=987654321_your_chat_id
   ```

---

## Step 4: Restart and Verify Connection

1. Rebuild and restart your container stack to apply the new credentials:
   ```bash
   docker compose down
   ```
   ```bash
   docker compose up -d
   ```
2. Open Telegram, open the chat with your newly created bot, and click `/start`.
3. Test communication by sending a message like:
   `Status` or `Run Morning Briefing`
4. The bot will respond with your active factory stats, confirming that your secure mobile command center is active and listening!



---

## 💡 Pro-Tips

* **Contextual Session Replies:** You can use Telegram's native "Reply" feature directly from your mobile device to reply to a specific message sent by the bot. ISF-Core will automatically route your reply as user chat input for that specific, ongoing chat session! This allows you to seamlessly provide feedback or continue complex workflows without ever needing to open the web dashboard.