from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
import os
import json
from datetime import datetime
import asyncio
from typing import Optional
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '6467050584:AAHhM8xo_VT-Ublz3A_2u3pU34k525b2lNg')
USERSBOX_TOKEN = os.environ.get('USERSBOX_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoxNzUyMzE2OTI3LCJhcHBfaWQiOjE3NTIzMTY5Mjd9.sYYS5fKjwzKXLb5FwWCqdkxXvaoljYGM-hHHvkREdgI')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'telegram_bot_db')

# Global variables
db = None
http_client = None

@app.on_event("startup")
async def startup_db_client():
    global db, http_client
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    http_client = httpx.AsyncClient()
    print("Database and HTTP client initialized")

@app.on_event("shutdown")
async def shutdown_db_client():
    global http_client
    if http_client:
        await http_client.aclose()

# Telegram Bot Functions
async def send_telegram_message(chat_id: int, text: str, parse_mode: str = "Markdown"):
    """Send message to Telegram chat"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        response = await http_client.post(url, json=payload)
        response.raise_for_status()
        
        # Log message to database
        await db.messages.insert_one({
            "id": str(uuid.uuid4()),
            "chat_id": chat_id,
            "text": text,
            "direction": "outgoing",
            "timestamp": datetime.utcnow(),
            "status": "sent"
        })
        
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        raise

# Usersbox API Functions
async def usersbox_request(endpoint: str, params: dict = None):
    """Make request to usersbox API"""
    try:
        base_url = "https://api.usersbox.ru/v1"
        url = f"{base_url}/{endpoint}"
        
        headers = {
            "Authorization": USERSBOX_TOKEN
        }
        
        print(f"Making usersbox request: {url}")
        print(f"Params: {params}")
        print(f"Headers: {headers}")
        
        response = await http_client.get(url, headers=headers, params=params)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            response_text = await response.aread()
            print(f"Error response: {response_text.decode()}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error making usersbox request to {url}: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {await e.response.aread()}")
        raise

async def get_app_info():
    """Get usersbox app information"""
    return await usersbox_request("getMe")

async def get_sources():
    """Get available data sources"""
    return await usersbox_request("sources")

async def search_all_databases(query: str):
    """Search across all databases"""
    return await usersbox_request("search", {"q": query})

async def explain_search(query: str):
    """Get count of search results without actual data"""
    return await usersbox_request("explain", {"q": query})

# Bot Command Handlers
async def handle_start_command(chat_id: int):
    """Handle /start command"""
    welcome_text = """
🔍 *Добро пожаловать в бота поиска по базам данных!*

Я помогу вам найти информацию по номерам телефонов, email, именам и другим данным.

*Доступные команды:*
📱 `/search <запрос>` - поиск по всем базам
📊 `/sources` - список доступных баз данных  
💰 `/balance` - проверка баланса
❓ `/help` - помощь

*Примеры поиска:*
• `+79123456789` - поиск по номеру телефона
• `example@mail.ru` - поиск по email
• `Иван Петров` - поиск по имени

Просто отправьте любой текст для поиска!
    """
    await send_telegram_message(chat_id, welcome_text)

def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 format"""
    # Remove all non-digit characters except +
    import re
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # If starts with 8, replace with +7
    if cleaned.startswith('8'):
        cleaned = '+7' + cleaned[1:]
    # If starts with 7 without +, add +
    elif cleaned.startswith('7') and not cleaned.startswith('+7'):
        cleaned = '+' + cleaned
    # If starts with 9 and is 10 digits, add +7
    elif cleaned.startswith('9') and len(cleaned) == 10:
        cleaned = '+7' + cleaned
    
    return cleaned

def format_search_query(query: str) -> str:
    """Format search query according to usersbox API requirements"""
    query = query.strip()
    
    # Check if it looks like a phone number
    import re
    phone_pattern = r'[\+]?[0-9\s\-\(\)]{10,15}'
    if re.match(phone_pattern, query):
        return normalize_phone_number(query)
    
    # For other queries, just clean up extra spaces
    return ' '.join(query.split())

async def handle_search_command(chat_id: int, query: str):
    """Handle search command"""
    if not query.strip():
        await send_telegram_message(chat_id, "❌ Пожалуйста, укажите запрос для поиска.")
        return
    
    try:
        # Format the query properly
        formatted_query = format_search_query(query)
        
        # Show processing message
        await send_telegram_message(chat_id, f"🔍 Ищу информацию по запросу: `{formatted_query}`")
        
        # First, get count of results
        explain_result = await explain_search(formatted_query)
        total_count = explain_result.get("data", {}).get("count", 0)
        
        if total_count == 0:
            await send_telegram_message(chat_id, f"❌ По запросу `{formatted_query}` ничего не найдено.")
            return
        
        # Get actual search results
        search_result = await search_all_databases(formatted_query)
        
        if search_result.get("status") == "success":
            data = search_result.get("data", {})
            results_count = data.get("count", 0)
            items = data.get("items", [])
            
            if results_count == 0:
                await send_telegram_message(chat_id, f"❌ По запросу `{query}` ничего не найдено.")
                return
            
            # Format results
            response_text = f"🎯 *Найдено результатов: {total_count}*\n\n"
            
            for i, source_item in enumerate(items[:3]):  # Show first 3 sources
                source = source_item.get("source", {})
                hits = source_item.get("hits", {})
                
                db_name = source.get("database", "Unknown")
                collection_name = source.get("collection", "Unknown")
                hits_count = hits.get("hitsCount", 0)
                
                response_text += f"📁 *База: {db_name}/{collection_name}*\n"
                response_text += f"📊 Найдено: {hits_count} записей\n"
                
                # Show first few records
                hit_items = hits.get("items", [])
                for j, record in enumerate(hit_items[:2]):  # Show first 2 records per source
                    response_text += f"\n🔸 *Запись {j+1}:*\n"
                    
                    # Format record fields
                    for key, value in record.items():
                        if key.startswith("_"):
                            continue
                        if isinstance(value, dict):
                            continue
                        if len(str(value)) > 50:
                            value = str(value)[:50] + "..."
                        response_text += f"• {key}: `{value}`\n"
                
                response_text += "\n" + "─" * 30 + "\n\n"
            
            if len(items) > 3:
                response_text += f"... и еще {len(items) - 3} источников\n\n"
            
            response_text += f"💡 Всего найдено в {total_count} базах данных"
            
            # Split message if too long
            if len(response_text) > 4000:
                parts = response_text.split("─" * 30)
                for part in parts[:3]:  # Send first 3 parts
                    if part.strip():
                        await send_telegram_message(chat_id, part.strip())
            else:
                await send_telegram_message(chat_id, response_text)
        
        # Log search to database
        await db.searches.insert_one({
            "id": str(uuid.uuid4()),
            "chat_id": chat_id,
            "query": formatted_query,
            "original_query": query,
            "results_count": total_count,
            "timestamp": datetime.utcnow()
        })
        
    except Exception as e:
        error_msg = f"❌ Ошибка при поиске: {str(e)}"
        
        # Add more detailed error information
        if "400" in str(e):
            error_msg += f"\n\n💡 Попробуйте другой формат запроса:\n"
            error_msg += f"• Телефон: `+79123456789` (без пробелов)\n"
            error_msg += f"• Email: `user@domain.com`\n"
            error_msg += f"• Имя: `Иван Петров`"
        elif "401" in str(e) or "403" in str(e):
            error_msg += f"\n\n🔑 Проблема с авторизацией API"
        elif "429" in str(e):
            error_msg += f"\n\n⏱️ Превышен лимит запросов. Попробуйте позже."
        elif "500" in str(e):
            error_msg += f"\n\n⚠️ Проблема на сервере API. Попробуйте позже."
        
        await send_telegram_message(chat_id, error_msg)
        print(f"Search error for query '{query}' -> '{formatted_query}': {e}")

async def handle_sources_command(chat_id: int):
    """Handle /sources command"""
    try:
        sources = await get_sources()
        
        if sources.get("status") == "success":
            data = sources.get("data", {})
            total_count = data.get("count", 0)
            items = data.get("items", [])
            
            response_text = f"📊 *Доступно баз данных: {total_count}*\n\n"
            response_text += "*Топ-10 крупнейших баз:*\n\n"
            
            # Sort by count and show top 10
            sorted_items = sorted(items, key=lambda x: x.get("count", 0), reverse=True)
            
            for i, item in enumerate(sorted_items[:10]):
                title = item.get("title", "Unknown")
                count = item.get("count", 0)
                database = item.get("database", "")
                collection = item.get("collection", "")
                
                response_text += f"{i+1}. *{title}*\n"
                response_text += f"   📁 `{database}/{collection}`\n"
                response_text += f"   📊 Записей: {count:,}\n\n"
            
            response_text += f"💡 Используйте `/search <запрос>` для поиска по всем базам"
            
            await send_telegram_message(chat_id, response_text)
        else:
            await send_telegram_message(chat_id, "❌ Ошибка получения списка баз данных")
            
    except Exception as e:
        error_msg = f"❌ Ошибка получения источников: {str(e)}"
        await send_telegram_message(chat_id, error_msg)

async def handle_balance_command(chat_id: int):
    """Handle /balance command"""
    try:
        app_info = await get_app_info()
        
        if app_info.get("status") == "success":
            data = app_info.get("data", {})
            balance = data.get("balance", 0)
            title = data.get("title", "Unknown")
            is_active = data.get("is_active", False)
            
            status_emoji = "✅" if is_active else "❌"
            
            response_text = f"""
💰 *Информация о балансе*

🏷️ Приложение: `{title}`
{status_emoji} Статус: {'Активно' if is_active else 'Неактивно'}
💳 Баланс: *{balance} ₽*

📊 *Тарифы:*
• Поиск по базе: 0.005 ₽ за документ
• Поиск по всем базам: 2.5 ₽
• Проверка количества: Бесплатно

💡 Пополните баланс через команду /api в @usersbox_bot
            """
            
            await send_telegram_message(chat_id, response_text)
        else:
            await send_telegram_message(chat_id, "❌ Ошибка получения информации о балансе")
            
    except Exception as e:
        error_msg = f"❌ Ошибка получения баланса: {str(e)}"
        await send_telegram_message(chat_id, error_msg)

async def handle_help_command(chat_id: int):
    """Handle /help command"""
    help_text = """
❓ *Справка по командам*

*🤖 Основные команды:*
• `/start` - приветствие и инструкции
• `/search <запрос>` - поиск по всем базам
• `/sources` - список доступных баз данных
• `/balance` - проверка баланса приложения
• `/help` - эта справка

*🔍 Форматы поиска:*
• Телефон: `+79123456789` или `79123456789`
• Email: `example@mail.ru`
• Имя: `Иван Петров`
• IP-адрес: `192.168.1.1`
• Любой текст для поиска

*💡 Советы:*
• Просто отправьте любой текст для быстрого поиска
• Для точных результатов форматируйте телефоны в формате E.164
• Бот ищет по 20+ миллиардам документов
• Поиск платный - проверяйте баланс командой /balance

*⚠️ Важно:*
Используйте бота только в законных целях!
    """
    await send_telegram_message(chat_id, help_text)

# Webhook handler
@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates"""
    try:
        update_data = await request.json()
        print(f"Received update: {update_data}")
        
        message = update_data.get("message")
        if not message:
            return {"status": "ok"}
        
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not chat_id or not text:
            return {"status": "ok"}
        
        # Log incoming message
        await db.messages.insert_one({
            "id": str(uuid.uuid4()),
            "chat_id": chat_id,
            "text": text,
            "direction": "incoming",
            "timestamp": datetime.utcnow(),
            "update_data": update_data
        })
        
        # Handle commands
        if text.startswith("/start"):
            await handle_start_command(chat_id)
        elif text.startswith("/search"):
            query = text[7:].strip()  # Remove "/search" prefix
            await handle_search_command(chat_id, query)
        elif text.startswith("/sources"):
            await handle_sources_command(chat_id)
        elif text.startswith("/balance"):
            await handle_balance_command(chat_id)
        elif text.startswith("/help"):
            await handle_help_command(chat_id)
        else:
            # Treat any other text as search query
            await handle_search_command(chat_id, text)
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

# API endpoints for frontend
@app.get("/api/")
async def root():
    return {"message": "Telegram Bot API Server", "status": "running"}

@app.get("/api/stats")
async def get_stats():
    """Get bot usage statistics"""
    try:
        total_messages = await db.messages.count_documents({})
        total_searches = await db.searches.count_documents({})
        
        # Get recent activity
        recent_messages = await db.messages.find(
            {}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        recent_searches = await db.searches.find(
            {}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        return {
            "total_messages": total_messages,
            "total_searches": total_searches,
            "recent_messages": recent_messages,
            "recent_searches": recent_searches
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-usersbox")
async def test_usersbox():
    """Test usersbox API connection"""
    try:
        result = await get_app_info()
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/set-webhook")
async def set_webhook():
    """Set Telegram webhook URL"""
    try:
        webhook_url = "https://3312ad11-8248-4d7e-86f5-1571a6d10e5d.preview.emergentagent.com/api/webhook"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        payload = {
            "url": webhook_url
        }
        
        response = await http_client.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return {"status": "success", "webhook_url": webhook_url, "telegram_response": result}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)