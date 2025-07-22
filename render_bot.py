
#!/usr/bin/env python3
"""
Production bot for Render.com deployment - Updated 2025
Includes bot conflict prevention and cleanup
"""
import os
import logging
import sys
import signal
import time
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from compteur import get_compteurs, update_compteurs, reset_compteurs_canal
from style import afficher_compteurs_canal
import re
import json

# Track processed messages per channel
processed_messages = set()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
style_affichage = 1
app_instance = None

def save_bot_status(running, message=None, error=None):
    """Save status to file"""
    status = {
        "running": running,
        "last_message": message,
        "error": error
    }
    try:
        with open("bot_status.json", "w") as f:
            json.dump(status, f)
    except Exception as e:
        logger.error(f"Could not save status: {e}")

def is_message_processed(message_key):
    """Check if message was already processed"""
    return message_key in processed_messages

def mark_message_processed(message_key):
    """Mark message as processed"""
    processed_messages.add(message_key)
    
def load_processed_messages():
    """Load processed messages from file"""
    global processed_messages
    try:
        with open("processed_messages.json", "r") as f:
            processed_messages = set(json.load(f))
    except:
        processed_messages = set()

def save_processed_messages():
    """Save processed messages to file"""
    try:
        with open("processed_messages.json", "w") as f:
            json.dump(list(processed_messages), f)
    except:
        pass

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutting down bot gracefully...")
    save_bot_status(False, "Bot stopped")
    if app_instance:
        app_instance.stop()
    sys.exit(0)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and edited messages"""
    global style_affichage
    
    try:
        # Get message from any source (including edited messages)
        msg = update.message or update.channel_post or update.edited_channel_post or update.edited_message
        if not msg or not msg.text:
            return
        
        text = msg.text
        chat_id = msg.chat_id
        
        # Detect if this is an edited message
        is_edited = update.edited_channel_post or update.edited_message
        
        logger.info(f"Channel {chat_id}: {'[EDITED] ' if is_edited else ''}{text[:80]}")
        
        # Check for message number
        match_numero = re.search(r"#n(\d+)", text)
        if not match_numero:
            # Find FIRST parentheses only for messages without number
            match = re.search(r'\(([^()]*)\)', text)
            if not match:
                return
            content = match.group(1)
        else:
            numero = int(match_numero.group(1))
            message_key = f"{chat_id}_{numero}"
            
            # Check for progress indicators
            progress_indicators = ['⏰', '▶', '🕐', '➡️']
            confirmation_symbols = ['✅', '🔰']
            
            has_progress = any(indicator in text for indicator in progress_indicators)
            has_confirmation = any(symbol in text for symbol in confirmation_symbols)
            
            # If message has progress indicators without confirmation, wait for final version
            if has_progress and not has_confirmation:
                logger.info(f"Message #{numero} has progress indicators, waiting for final version")
                return
            
            # For final messages: check if already processed unless edited
            if is_message_processed(message_key):
                if not is_edited:
                    logger.info(f"Message #{numero} already processed and not edited, skipping")
                    return
                else:
                    logger.info(f"Message #{numero} was edited, reprocessing...")
            
            # Mark as processed
            mark_message_processed(message_key)
            save_processed_messages()
            
            # Find FIRST parentheses only
            match = re.search(r'\(([^()]*)\)', text)
            if not match:
                return
            content = match.group(1)
        
        logger.info(f"Channel {chat_id} - Content: '{content}'")
        
        # Count ALL card symbols in the content (including both heart symbols)
        cards_found = {}
        total_cards = 0
        
        # Check for hearts (both symbols)
        heart_count = content.count("❤️") + content.count("♥️")
        if heart_count > 0:
            update_compteurs(chat_id, "❤️", heart_count)
            cards_found["❤️"] = heart_count
            total_cards += heart_count
        
        # Check other symbols
        for symbol in ["♦️", "♣️", "♠️"]:
            count = content.count(symbol)
            if count > 0:
                update_compteurs(chat_id, symbol, count)
                cards_found[symbol] = count
                total_cards += count
        
        if not cards_found:
            logger.info(f"No card symbols found in: '{content}'")
            return
        
        logger.info(f"Channel {chat_id} - Cards counted: {cards_found}")
        save_bot_status(True, f"Channel {chat_id}: {cards_found}")
        
        # Get updated counters and send response
        compteurs_updated = get_compteurs(chat_id)
        response = afficher_compteurs_canal(compteurs_updated, style_affichage)
        await msg.reply_text(response)
        logger.info(f"Response sent to channel {chat_id}")
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset command"""
    try:
        if not update.message:
            return
            
        chat_id = update.message.chat_id
        reset_compteurs_canal(chat_id)
        
        # Clear processed messages for this channel
        global processed_messages
        processed_messages = {key for key in processed_messages if not key.startswith(f"{chat_id}_")}
        save_processed_messages()
        
        await update.message.reply_text("✅ Reset done for this channel")
        save_bot_status(True, f"Reset completed for channel {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in reset command: {e}")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    try:
        welcome_msg = (
            "🤖 **Bot de Comptage de Cartes** 🃏\n\n"
            "Bonjour ! Je compte les cartes séparément pour chaque canal.\n\n"
            "📝 **Comment ça marche :**\n"
            "• Envoyez un message avec des cartes entre parenthèses\n"
            "• Exemple : Résultat du tirage (❤️♦️♣️♠️)\n\n"
            "🎯 **Symboles reconnus :**\n"
            "❤️ Cœurs • ♦️ Carreaux • ♣️ Trèfles • ♠️ Piques\n\n"
            "📊 **Compteurs séparés par canal !**\n"
            "⚡ Bot actif et prêt !"
        )
        await update.message.reply_text(welcome_msg)
        
        chat_id = update.message.chat_id
        save_bot_status(True, f"Bot started in channel {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check command for monitoring"""
    try:
        await update.message.reply_text("🟢 Bot is running perfectly!")
        save_bot_status(True, "Health check passed")
    except Exception as e:
        logger.error(f"Health check failed: {e}")

async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a group or channel"""
    try:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                welcome_msg = (
                    "👋 **Salut tout le monde !** 🃏\n\n"
                    "Je suis le **Bot de Comptage de Cartes** !\n\n"
                    "🎯 **Ma mission :**\n"
                    "Compter automatiquement les symboles de cartes "
                    "dans vos messages entre parenthèses.\n\n"
                    "📊 **Compteurs séparés par canal !**\n"
                    "Chaque canal aura ses propres totaux.\n\n"
                    "🃏 **Cartes reconnues :**\n"
                    "❤️ Cœurs • ♦️ Carreaux • ♣️ Trèfles • ♠️ Piques\n\n"
                    "💡 Commandes :\n"
                    "• /reset - Réinitialiser ce canal\n"
                    "• /start - Aide\n"
                    "• /health - État du bot"
                )
                
                await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=welcome_msg
                )
                
                chat_id = update.message.chat_id
                save_bot_status(True, f"Bot added to channel {chat_id}")
                logger.info(f"Bot added to chat: {chat_id}")
                break
                
    except Exception as e:
        logger.error(f"Error handling new chat member: {e}")

def main():
    """Main function"""
    global app_instance
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        save_bot_status(False, error="No token")
        sys.exit(1)
    
    logger.info("🤖 Starting bot optimized for Render.com...")
    logger.info(f"Python version: {sys.version}")
    
    # Wait to allow any previous instances to shut down (Render.com optimization)  
    time.sleep(3)
    logger.info("✅ Ready to start bot polling")
    
    logger.info("Starting Telegram bot...")
    save_bot_status(True, "Starting...")
    
    try:
        # Create application
        app_instance = Application.builder().token(token).build()
        
        # Add handlers
        app_instance.add_handler(CommandHandler("start", start_cmd))
        app_instance.add_handler(CommandHandler("reset", reset_cmd))
        app_instance.add_handler(CommandHandler("health", health_check))
        app_instance.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
        app_instance.add_handler(MessageHandler(filters.ALL, handle_message))
        
        logger.info("Bot ready - starting polling...")
        save_bot_status(True, "Bot online and polling")
        
        # Load processed messages
        load_processed_messages()
        
        # Run bot with edited messages support and conflict prevention
        app_instance.run_polling(
            drop_pending_updates=True,  # Clear old messages to prevent conflicts
            allowed_updates=["message", "edited_message", "channel_post", "edited_channel_post"],
            close_loop=False  # Prevent event loop conflicts
        )
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        save_bot_status(False, error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
