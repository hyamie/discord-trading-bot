"""
Discord Bot Service - Gateway Integration
Listens to Discord messages and forwards to n8n webhook
"""
import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

# Bot setup with message content intent
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is now online and listening!')
    print(f'📡 Connected to {len(bot.guilds)} server(s)')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Ignore messages from other bots
    if message.author.bot:
        return

    # Only process messages that start with $ or !ticker
    # Examples: $SPY, !ticker AAPL
    content = message.content.strip()
    if not (content.startswith('$') or content.lower().startswith('!ticker ')):
        # Allow other commands to work (like !ping, !health)
        await bot.process_commands(message)
        return

    # Prepare message data for n8n (wrapped in 'body' for n8n compatibility)
    payload = {
        'body': {
            'content': message.content,
            'author': {
                'id': str(message.author.id),
                'username': message.author.name,
                'bot': message.author.bot
            },
            'channel_id': str(message.channel.id),
            'id': str(message.id),
            'guild_id': str(message.guild.id) if message.guild else None,
            'timestamp': message.created_at.isoformat()
        }
    }

    print(f'📨 Processing ticker request from {message.author.name}: {message.content}')

    try:
        # Forward to n8n webhook
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            # Get response from n8n
            result = response.json()

            # Check if n8n returned a response to send back
            if 'response' in result:
                # Send reply to Discord
                await message.reply(result['response'])
                print(f'✅ Sent response to Discord')
            else:
                print(f'ℹ️  n8n processed but no response needed')
        else:
            print(f'⚠️  n8n webhook returned status {response.status_code}')
            await message.reply(f'⚠️ Error: Webhook returned {response.status_code}')

    except requests.exceptions.Timeout:
        print(f'⏱️  n8n webhook timeout (analysis may take longer)')
        await message.reply('⏳ Analysis in progress... this may take a moment.')
    except Exception as e:
        print(f'❌ Error forwarding to n8n: {e}')
        await message.reply(f'⚠️ Error processing request. Please try again.')

    # Allow commands to still work
    await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    """Test command to check if bot is responding"""
    await ctx.send(f'🏓 Pong! Latency: {round(bot.latency * 1000)}ms')

@bot.command(name='health')
async def health(ctx):
    """Check bot health status"""
    await ctx.send(f'✅ Bot is online\n📡 Connected to {len(bot.guilds)} servers\n⚡ Latency: {round(bot.latency * 1000)}ms')

if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        print('❌ Error: DISCORD_BOT_TOKEN not set in environment')
        exit(1)

    if not N8N_WEBHOOK_URL:
        print('❌ Error: N8N_WEBHOOK_URL not set in environment')
        exit(1)

    print('🚀 Starting Discord bot...')
    bot.run(DISCORD_BOT_TOKEN)
