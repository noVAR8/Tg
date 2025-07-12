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
import hashlib
import random
import string

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
USERSBOX_TOKEN = os.environ.get('USERSBOX_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoxNzUyMzE3OTcwLCJhcHBfaWQiOjE3NTIzMTc5NzB9.yQb2nFHs7B-UZ-UvxhyQty7Zuu9QjZ5yWH-s-LEgd90')
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

# Utility Functions
def generate_referral_code(user_id: int) -> str:
    """Generate unique referral code for user"""
    # Create a hash based on user_id and some random data
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    code_data = f"{user_id}_{random_part}"
    hash_obj = hashlib.md5(code_data.encode())
    return hash_obj.hexdigest()[:8].upper()

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

# User Profile Management
async def get_or_create_user_profile(user_id: int, username: str = None, first_name: str = None):
    """Get existing user profile or create new one"""
    try:
        # Try to find existing user
        user = await db.users.find_one({"user_id": user_id})
        
        if user:
            # Update last activity
            await db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "last_activity": datetime.utcnow(),
                        "username": username,
                        "first_name": first_name
                    }
                }
            )
            return user
        else:
            # Create new user profile
            referral_code = generate_referral_code(user_id)
            new_user = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "referral_code": referral_code,
                "free_attempts": 1,  # 1 free attempt for new users
                "total_searches": 0,
                "total_referrals": 0,
                "referred_by": None,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "is_active": True
            }
            
            await db.users.insert_one(new_user)
            print(f"Created new user profile for {user_id} with referral code {referral_code}")
            return new_user
            
    except Exception as e:
        print(f"Error managing user profile: {e}")
        return None

async def use_attempt(user_id: int) -> bool:
    """Use one attempt for user, return True if successful"""
    try:
        user = await db.users.find_one({"user_id": user_id})
        if not user:
            return False
            
        if user.get("free_attempts", 0) > 0:
            # Use free attempt
            await db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"free_attempts": -1, "total_searches": 1}}
            )
            return True
        else:
            return False  # No attempts left
            
    except Exception as e:
        print(f"Error using attempt: {e}")
        return False

async def add_referral_attempt(user_id: int):
    """Add attempt for successful referral"""
    try:
        await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"free_attempts": 1, "total_referrals": 1}}
        )
        print(f"Added referral attempt for user {user_id}")
    except Exception as e:
        print(f"Error adding referral attempt: {e}")

async def process_referral(new_user_id: int, referral_code: str):
    """Process referral when new user joins"""
    try:
        # Find referrer by code
        referrer = await db.users.find_one({"referral_code": referral_code})
        if not referrer:
            return False
            
        referrer_id = referrer["user_id"]
        
        # Update new user with referrer info
        await db.users.update_one(
            {"user_id": new_user_id},
            {"$set": {"referred_by": referrer_id}}
        )
        
        # Add attempt to referrer
        await add_referral_attempt(referrer_id)
        
        # Log referral
        await db.referrals.insert_one({
            "referrer_id": referrer_id,
            "referred_id": new_user_id,
            "referral_code": referral_code,
            "timestamp": datetime.utcnow()
        })
        
        return True
        
    except Exception as e:
        print(f"Error processing referral: {e}")
        return False

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
        
        response = await http_client.get(url, headers=headers, params=params)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            response_text = await response.aread()
            print(f"Error response: {response_text.decode()}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error making usersbox request to {url}: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
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
async def handle_start_command(chat_id: int, username: str = None, first_name: str = None):
    """Handle /start command"""
    try:
        # Create or get user profile
        user = await get_or_create_user_profile(chat_id, username, first_name)
        
        if not user:
            await send_telegram_message(chat_id, "❌ Ошибка создания профиля. Попробуйте позже.")
            return
        
        attempts = user.get("free_attempts", 0)
        is_new_user = user.get("created_at", datetime.utcnow()).replace(tzinfo=None) > (datetime.utcnow() - datetime.timedelta(minutes=5)).replace(tzinfo=None)
        
        if is_new_user:
            welcome_text = f"""
🎉 *Добро пожаловать в бота поиска по базам данных!*

Вы получили *1 бесплатную попытку* для поиска!

🔍 *Что я умею:*
• Поиск по 20+ миллиардам документов
• Поиск по телефонам, email, именам, IP
• Быстрые и точные результаты

💎 *Оставшиеся попытки: {attempts}*

*Основные команды:*
📱 `/search <запрос>` - поиск по всем базам
👤 `/profile` - ваш профиль и статистика
🎁 `/referral` - пригласить друзей и получить попытки
💰 `/balance` - баланс API
❓ `/help` - подробная помощь

*Примеры поиска:*
• `+79123456789` - поиск по телефону
• `example@mail.ru` - поиск по email
• `Иван Петров` - поиск по имени

🎁 *Получите больше попыток:*
Приглашайте друзей командой `/referral` - за каждого +1 попытка!
            """
        else:
            welcome_text = f"""
👋 *С возвращением!*

💎 *Оставшиеся попытки: {attempts}*

*Быстрые команды:*
🔍 Просто отправьте запрос для поиска
👤 `/profile` - ваш профиль
🎁 `/referral` - пригласить друзей (+1 попытка за каждого)

Нужны еще попытки? Приглашайте друзей! 🚀
            """
        
        await send_telegram_message(chat_id, welcome_text)
        
    except Exception as e:
        print(f"Error in start command: {e}")
        await send_telegram_message(chat_id, "❌ Ошибка обработки команды. Попробуйте позже.")

async def handle_profile_command(chat_id: int):
    """Handle /profile command"""
    try:
        user = await db.users.find_one({"user_id": chat_id})
        if not user:
            await send_telegram_message(chat_id, "❌ Профиль не найден. Используйте /start для создания.")
            return
        
        # Get referral stats
        referrals_count = await db.referrals.count_documents({"referrer_id": chat_id})
        
        profile_text = f"""
👤 *Ваш профиль*

🆔 ID: `{user['user_id']}`
👑 Имя: {user.get('first_name', 'Не указано')}
📝 Username: @{user.get('username', 'не указан')}

💎 *Статистика:*
• Попытки: *{user.get('free_attempts', 0)}*
• Всего поисков: *{user.get('total_searches', 0)}*
• Приглашено друзей: *{referrals_count}*

🎯 *Реферальный код:* `{user.get('referral_code', 'N/A')}`

📅 Регистрация: {user.get('created_at', datetime.utcnow()).strftime('%d.%m.%Y')}
⏱️ Последняя активность: {user.get('last_activity', datetime.utcnow()).strftime('%d.%m.%Y %H:%M')}

🎁 *Получить больше попыток:*
Используйте `/referral` чтобы пригласить друзей!
За каждого нового пользователя вы получите +1 попытку.
        """
        
        await send_telegram_message(chat_id, profile_text)
        
    except Exception as e:
        print(f"Error in profile command: {e}")
        await send_telegram_message(chat_id, "❌ Ошибка получения профиля.")

async def handle_referral_command(chat_id: int):
    """Handle /referral command"""
    try:
        user = await db.users.find_one({"user_id": chat_id})
        if not user:
            await send_telegram_message(chat_id, "❌ Профиль не найден. Используйте /start для создания.")
            return
        
        referral_code = user.get('referral_code')
        bot_username = "YourBotUsername"  # Replace with actual bot username
        
        # Get referral stats
        total_referrals = await db.referrals.count_documents({"referrer_id": chat_id})
        
        referral_text = f"""
🎁 *Реферальная программа*

*Ваш реферальный код:* `{referral_code}`

🔗 *Реферальная ссылка:*
`https://t.me/{bot_username}?start={referral_code}`

📊 *Ваша статистика:*
• Приглашено друзей: *{total_referrals}*
• Получено попыток: *{total_referrals}*

🎯 *Как это работает:*
1. Поделитесь ссылкой с друзьями
2. Они переходят по ссылке и запускают бота
3. Вы получаете +1 попытку за каждого нового пользователя
4. Они получают свою 1 бесплатную попытку

💡 *Совет:* Скопируйте ссылку и отправьте друзьям в любом мессенджере!

🚀 Чем больше друзей - тем больше попыток для поиска!
        """
        
        await send_telegram_message(chat_id, referral_text)
        
    except Exception as e:
        print(f"Error in referral command: {e}")
        await send_telegram_message(chat_id, "❌ Ошибка получения реферальной информации.")

async def handle_invite_command(chat_id: int, referral_code: str):
    """Handle /invite command"""
    try:
        if not referral_code:
            await send_telegram_message(chat_id, "❌ Укажите реферальный код: `/invite КОД`")
            return
        
        # Check if user already exists and has referrer
        user = await db.users.find_one({"user_id": chat_id})
        if user and user.get("referred_by"):
            await send_telegram_message(chat_id, "❌ Вы уже использовали реферальный код ранее.")
            return
        
        # Process referral
        success = await process_referral(chat_id, referral_code.upper())
        
        if success:
            await send_telegram_message(chat_id, f"""
✅ *Реферальный код принят!*

🎉 Вы были приглашены в бота поиска по базам данных!
🎁 Ваш приглашатель получил +1 попытку

Используйте `/start` для начала работы!
            """)
        else:
            await send_telegram_message(chat_id, "❌ Неверный реферальный код или он уже использован.")
        
    except Exception as e:
        print(f"Error in invite command: {e}")
        await send_telegram_message(chat_id, "❌ Ошибка обработки реферального кода.")

async def handle_search_command(chat_id: int, query: str, username: str = None, first_name: str = None):
    """Handle search command"""
    if not query.strip():
        await send_telegram_message(chat_id, "❌ Пожалуйста, укажите запрос для поиска.")
        return
    
    try:
        # Get or create user profile
        user = await get_or_create_user_profile(chat_id, username, first_name)
        if not user:
            await send_telegram_message(chat_id, "❌ Ошибка создания профиля. Попробуйте /start.")
            return
        
        # Check if user has attempts
        attempts = user.get("free_attempts", 0)
        if attempts <= 0:
            await send_telegram_message(chat_id, f"""
❌ *У вас закончились попытки!*

💎 Текущие попытки: *0*

🎁 *Как получить больше попыток:*
• Пригласите друзей через `/referral` (+1 за каждого)
• Купите дополнительные попытки (скоро)

🚀 Поделитесь ботом с друзьями и получите бесплатные попытки!
            """)
            return
        
        # Use attempt
        if not await use_attempt(chat_id):
            await send_telegram_message(chat_id, "❌ Ошибка списания попытки. Попробуйте позже.")
            return
        
        # Format the query properly
        formatted_query = format_search_query(query)
        
        # Show processing message with remaining attempts
        remaining_attempts = attempts - 1
        await send_telegram_message(chat_id, f"""
🔍 *Поиск запущен!*

Запрос: `{formatted_query}`
💎 Осталось попыток: *{remaining_attempts}*

⏳ Обрабатываю запрос...
        """)
        
        # First, get count of results
        explain_result = await explain_search(formatted_query)
        total_count = explain_result.get("data", {}).get("count", 0)
        
        if total_count == 0:
            await send_telegram_message(chat_id, f"""
❌ *Результатов не найдено*

Запрос: `{formatted_query}`
💎 Осталось попыток: *{remaining_attempts}*

💡 *Попробуйте другой формат:*
• Телефон: `+79123456789`
• Email: `user@domain.com`
• Имя: `Иван Петров`
            """)
            return
        
        # Get actual search results
        search_result = await search_all_databases(formatted_query)
        
        if search_result.get("status") == "success":
            data = search_result.get("data", {})
            results_count = data.get("count", 0)
            items = data.get("items", [])
            
            if results_count == 0:
                await send_telegram_message(chat_id, f"""
❌ *Результатов не найдено*

Запрос: `{formatted_query}`
💎 Осталось попыток: *{remaining_attempts}*
                """)
                return
            
            # Format results
            response_text = f"🎯 *Результаты поиска*\n\n"
            response_text += f"📊 Найдено в *{total_count}* базах данных\n"
            response_text += f"💎 Осталось попыток: *{remaining_attempts}*\n\n"
            
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
            
            response_text += f"🎁 *Нужно больше попыток?*\n"
            response_text += f"Используйте `/referral` для приглашения друзей!"
            
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
            "attempts_used": 1,
            "remaining_attempts": remaining_attempts,
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
            
            response_text += f"💡 Используйте поиск для поиска по всем базам"
            
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
💰 *Информация о балансе API*

🏷️ Приложение: `{title}`
{status_emoji} Статус: {'Активно' if is_active else 'Неактивно'}
💳 Баланс: *{balance} ₽*

📊 *Тарифы:*
• Поиск по базе: 0.005 ₽ за документ
• Поиск по всем базам: 2.5 ₽
• Проверка количества: Бесплатно

💡 Пополните баланс через команду /api в @usersbox_bot

🎁 *Бесплатные попытки:*
Приглашайте друзей через `/referral` для получения бесплатных попыток!
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
• `/start` - приветствие и регистрация
• `/profile` - ваш профиль и статистика
• `/referral` - реферальная программа
• `/search <запрос>` - поиск по всем базам
• `/sources` - список доступных баз данных
• `/balance` - баланс API приложения
• `/help` - эта справка

*🔍 Форматы поиска:*
• Телефон: `+79123456789` или `79123456789`
• Email: `example@mail.ru`
• Имя: `Иван Петров`
• IP-адрес: `192.168.1.1`
• Любой текст для поиска

*🎁 Система попыток:*
• 1 бесплатная попытка при регистрации
• +1 попытка за каждого приглашенного друга
• Используйте `/referral` для получения ссылки

*💡 Советы:*
• Просто отправьте любой текст для быстрого поиска
• Форматируйте телефоны в международном формате
• Приглашайте друзей для получения бесплатных попыток
• Бот ищет по 20+ миллиардам документов

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
        user_info = message.get("from", {})
        username = user_info.get("username")
        first_name = user_info.get("first_name")
        
        if not chat_id or not text:
            return {"status": "ok"}
        
        # Log incoming message
        await db.messages.insert_one({
            "id": str(uuid.uuid4()),
            "chat_id": chat_id,
            "text": text,
            "direction": "incoming",
            "timestamp": datetime.utcnow(),
            "user_info": user_info,
            "update_data": update_data
        })
        
        # Handle commands and referral codes in /start
        if text.startswith("/start"):
            parts = text.split()
            if len(parts) > 1:
                # Handle referral code in /start command
                referral_code = parts[1]
                await handle_invite_command(chat_id, referral_code)
            await handle_start_command(chat_id, username, first_name)
        elif text.startswith("/profile"):
            await handle_profile_command(chat_id)
        elif text.startswith("/referral"):
            await handle_referral_command(chat_id)
        elif text.startswith("/invite"):
            parts = text.split()
            referral_code = parts[1] if len(parts) > 1 else ""
            await handle_invite_command(chat_id, referral_code)
        elif text.startswith("/search"):
            query = text[7:].strip()  # Remove "/search" prefix
            await handle_search_command(chat_id, query, username, first_name)
        elif text.startswith("/sources"):
            await handle_sources_command(chat_id)
        elif text.startswith("/balance"):
            await handle_balance_command(chat_id)
        elif text.startswith("/help"):
            await handle_help_command(chat_id)
        else:
            # Treat any other text as search query
            await handle_search_command(chat_id, text, username, first_name)
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

# API endpoints for frontend
@app.get("/api/")
async def root():
    return {"message": "Telegram Bot API Server with Referral System", "status": "running"}

@app.get("/api/stats")
async def get_stats():
    """Get bot usage statistics"""
    try:
        total_messages = await db.messages.count_documents({})
        total_searches = await db.searches.count_documents({})
        total_users = await db.users.count_documents({})
        total_referrals = await db.referrals.count_documents({})
        
        # Get recent activity
        recent_messages = await db.messages.find(
            {}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        recent_searches = await db.searches.find(
            {}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        # Get top users by searches
        pipeline = [
            {"$group": {"_id": "$chat_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_users = await db.searches.aggregate(pipeline).to_list(5)
        
        return {
            "total_messages": total_messages,
            "total_searches": total_searches,
            "total_users": total_users,
            "total_referrals": total_referrals,
            "recent_messages": recent_messages,
            "recent_searches": recent_searches,
            "top_users": top_users
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users")
async def get_users():
    """Get user statistics"""
    try:
        users = await db.users.find({}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/referrals")
async def get_referrals():
    """Get referral statistics"""
    try:
        referrals = await db.referrals.find({}, {"_id": 0}).sort("timestamp", -1).limit(20).to_list(20)
        return {"referrals": referrals}
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