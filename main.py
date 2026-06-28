from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
import asyncio
import re
from dotenv import load_dotenv
import os

# ================== ЗАГРУЗКА ТОКЕНА ==================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен не найден! Проверь файл .env")

print("✅ Токен успешно загружен из .env!")

# Импорт меню
import menu

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_suggestions = {}

# ================== ПОИСК ==================
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^а-яa-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def find_dish(query: str):
    if not query or len(query.strip()) < 2:
        return None, []

    query_norm = normalize(query)

    for dish_name, info in menu.menu_data.items():
        if query_norm == normalize(dish_name):
            return dish_name, info

    matches = []
    for dish_name, info in menu.menu_data.items():
        name_norm = normalize(dish_name)
        score = 0

        if query_norm in name_norm or name_norm in query_norm:
            score = 140
        else:
            common_count = len(set(query_norm.split()) & set(name_norm.split()))
            if common_count > 0:
                score = common_count * 35
                if common_count >= 2:
                    score += 50

        if score >= 60:
            matches.append((dish_name, info, score))

    if not matches:
        return None, []

    matches.sort(key=lambda x: x[2], reverse=True)

    if len(matches) == 1 or matches[0][2] - (matches[1][2] if len(matches) > 1 else 0) > 50:
        return matches[0][0], matches[0][1]
    
    return None, [m[0] for m in matches[:6]]


# ================== ОБРАБОТЧИКИ ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 Привет! Напишите название блюда.")


@dp.message(F.text)
async def reply_menu(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text.isdigit():
        num = int(text)
        if user_id in user_suggestions and 1 <= num <= len(user_suggestions[user_id]):
            chosen = user_suggestions[user_id][num-1]
            info = menu.menu_data[chosen]
            await message.answer(
                f"<b>✅ {chosen}</b>\n\n"
                f"📋 <b>Состав:</b>\n{info['состав']}\n\n"
                f"⚠️ <b>Аллергены:</b>\n{info['аллергены']}\n\n"
                f"🔗 <b>Товары-пары:</b>\n{info['пары']}",
                parse_mode="HTML"
            )
            return

    dish_name, result = find_dish(text)

    if dish_name and isinstance(result, dict):
        await message.answer(
            f"<b>✅ {dish_name}</b>\n\n"
            f"📋 <b>Состав:</b>\n{result['состав']}\n\n"
            f"⚠️ <b>Аллергены:</b>\n{result['аллергены']}\n\n"
            f"🔗 <b>Товары-пары:</b>\n{result['пары']}",
            parse_mode="HTML"
        )
    elif result:
        user_suggestions[user_id] = result
        variants = "\n".join([f"{i+1}. {name}" for i, name in enumerate(result)])
        await message.answer(f"🔍 Найдено несколько вариантов:\n\n{variants}\n\nНапишите номер или полное название.")
    else:
        await message.answer("😔 Блюдо не найдено. Попробуйте написать точнее.")


async def main():
    print(f"🤖 Бот запущен! Загружено блюд: {len(menu.menu_data)}")
    await dp.start_polling(bot)

print("✅ Обработчики зарегистрированы. Ожидание сообщений...")

if __name__ == "__main__":
    asyncio.run(main())