import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from config import BOT_TOKEN, ADMIN_CHAT_ID
try:
    from config import ADMIN_USERNAME
except Exception:
    ADMIN_USERNAME = None

from fastapi import FastAPI, Request
import requests

app = FastAPI()

ADMIN_CHAT_ID = 123456789  # ⚠️ СЮДА СВОЙ ID
BOT_TOKEN = "ТВОЙ_ТОКЕН"

@app.get("/health")
def health():
    return "OK"


@app.post("/api/checkout")
async def checkout(req: Request):
    data = await req.json()

    cart = data.get("cart", [])
    total = data.get("total", 0)

    text = "📦 Новый заказ:\n\n"

    for item in cart:
        name = item["name"]
        qty = item["qty"]
        price = item["price"]

        text += f"{name} x{qty} = {price * qty} ₩\n"

    text += f"\n💰 Итого: {total} ₩"

    # отправка админу
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": ADMIN_CHAT_ID,
            "text": text
        }
    )

    return {"ok": True}

router = Router()

DB_PATH = "orders.db"
ITEMS_PER_PAGE = 6

# =========================
# MENU
# =========================
MENU = {
    "main": {
        "title": "🍖 Основное меню",
        "categories": {
            "bread": {
                "title": "🥖 Хлеб",
                "items": [
                    ("Хлеб", 4000),
                    ("Патир", 4000),
                    ("Большой Патир", 7000),
                    ("Лаваш", 3000),
                    ("Хлебной набор Ассорти", 12000),
                    ("Черный Хлеб", 7000),
                ],
            },
            "fastfood": {
                "title": "🍔 Фаст Фуд",
                "items": [
                    ("Тандыр Самса", 5000),
                    ("Самарканд Самса", 6000),
                    ("Самса", 4000),
                    ("Бургер сет", 15000),
                    ("Шаурма Шашлык", 15000),
                    ("Чебурек с сыром", 12000),
                ],
            },
            "salad": {
                "title": "🥗 Салаты",
                "items": [
                    ("Овощная нарезка", 11000),
                    ("Французский", 13000),
                    ("Селедка по шубой", 13000),
                    ("Соленья Тузлама", 10000),
                    ("Салат Самарканд", 10000),
                    ("Греческий салат", 12000),
                    ("Салат Каприз", 12000),
                    ("Салат Цезарь", 13000),
                    ("Салат Оливье", 10000),
                    ("Ачучук", 7000),
                    ("Жаренные баклажаны", 14000),
                    ("Салат Смак", 11000),
                ],
            },
            "soup": {
                "title": "🍲 Супы",
                "items": [
                    ("Лагман", 12000),
                    ("Шурпа из баранины", 12000),
                    ("Окрошка", 11000),
                    ("Борщ", 12000),
                    ("Мастава", 12000),
                    ("Шурпа из говядины", 12000),
                    ("Пельмени с бульоном", 12000),
                    ("Суп с фрикадельками", 12000),
                ],
            },
            "second": {
                "title": "🍛 Второе блюдо",
                "items": [
                    ("Манты", 14000),
                    ("Уйгурский лагман", 14000),
                    ("Ханум", 14000),
                    ("Жаренный лагман", 14000),
                    ("Хинкали", 17000),
                    ("Жаренные пельмени", 14000),
                    ("Нарын", 16000),
                    ("Бешбармак", 17000),
                    ("Жаркое из говядины с гарниром", 15000),
                    ("Целая курица с картошкой фри", 15000),
                    ("Долма с говядиной", 14000),
                    ("Куртоб", 17000),
                    ("Бифштекс", 14000),
                    ("Мошкчири", 15000),
                    ("Туй кабоб", 15000),
                    ("Котлеты с сыром на мангале", 18000),
                    ("Казан кебаб", 15000),
                    ("Жаренная баранина с картошкой фри", 16000),
                    ("Жаренная говядина с картошкой фри", 17000),
                    ("Баранья корейка на гриле", 48000),
                    ("Жареный сазан", 15000),
                    ("Стейк из сёмги с гарниром", 19000),
                    ("Баранье ребра с рисом и картошкой", 18000),
                    ("Бараньи ребрышки 1кг", 90000),
                    ("Самаркандский плов", 14000),
                    ("Плов с долмой и казы", 16000),
                    ("Самаркандский плов Сет 1чл", 20000),
                ],
            },
            "bbq": {
                "title": "🔥 Барбекю",
                "items": [
                    ("Стейк из говядины", 21000),
                    ("Стейк из баранины", 19000),
                    ("Стейк Рибай с костью", 35000),
                    ("Стейк рибай", 30000),
                    ("Рулет шашлык говядина", 13000),
                    ("Куриный шашлык", 9000),
                    ("Овощи на гриле", 10000),
                    ("Шашлык из бараньей корейки", 24000),
                    ("Сет Шашлык 6шт + овощи", 60000),
                    ("Наполеон шашлык", 14000),
                    ("Медальон шашлык", 14000),
                    ("Молотый шашлык", 10000),
                    ("Кусковой шашлык баранина", 11000),
                    ("Куриные крылашки", 9000),
                    ("Шашлык из говяжьей печени", 9000),
                    ("Шашлык из говяжего филе", 12000),
                    ("Курдюк шашлык", 14000),
                    ("Универсальный рулет", 10000),
                    ("Meat Set", 155000),
                    ("Meat Set Big", 195000),
                    ("Dastirxan Bbq set", 90000),
                    ("Dastirxan BBQ Set Big", 125000),
                    ("Томатный соус", 3000),
                    ("Чесночный соус", 3000),
                ],
            },
        },
    },
    "desserts": {
        "title": "🍰 Десерты и напитки",
        "categories": {
            "desserts": {
                "title": "🍰 Десерты",
                "items": [
                    ("Большое фруктовое ассорти", 30000),
                    ("Ферреро роше", 13000),
                    ("Молочная девочка", 12000),
                    ("Чизкейк", 12000),
                    ("Пахлава", 11000),
                    ("Наполеон", 13000),
                    ("Медовик", 12000),
                    ("Красный бархат", 12000),
                    ("Шоколодный торт орео", 12000),
                    ("Фруктовый салат с шоколадом", 13000),
                    ("Мороженное", 12000),
                ],
            },
            "coffee": {
                "title": "☕ Кофе",
                "items": [
                    ("Американо", 5000),
                    ("Капучино", 6000),
                    ("Флет уайт", 6000),
                    ("Латта с корицей и медом", 7000),
                    ("Горячий шоколад", 7000),
                    ("Матча латте", 7000),
                    ("Айс американо", 5000),
                    ("Айс латте", 6000),
                    ("Сансет", 9000),
                    ("Клубничный матча латте", 9000),
                    ("Айс матча", 7000),
                ],
            },
            "fresh": {
                "title": "🍊 Свежий сок",
                "items": [
                    ("Апельсиновый фреш", 10000),
                    ("Лимонный фреш", 10000),
                    ("Киви щавель", 10000),
                    ("Морковный фреш", 6000),
                    ("Апельсиново морковный фреш", 8000),
                    ("Киви сельдерей", 10000),
                ],
            },
            "lemonade": {
                "title": "🥤 Лимонад",
                "items": [
                    ("Тропический 1л", 14000),
                    ("Лимонный 1л", 14000),
                    ("Клубничный мохито 1л", 14000),
                    ("Классический мохито 1л", 14000),
                    ("Манго маракуйя 1л", 16000),
                    ("Тархун 1л", 16000),
                    ("Мохито с маракуйей 1л", 16000),
                    ("Кампот вишневый 1л", 11000),
                    ("Ягодный 0.5л", 7000),
                    ("Лимоный 0.5л", 7000),
                    ("Тропический 0.5л", 7000),
                    ("Классик мохито 0.5л", 7000),
                    ("Манго маракуйя 0.5л", 8000),
                    ("Клубничный мохито 0.5л", 7000),
                    ("Мохито с маракуйей 0.5л", 8000),
                    ("Тархун 0.5л", 8000),
                ],
            },
            "tea": {
                "title": "🍵 Чай",
                "items": [
                    ("Марокканский", 12000),
                    ("Жасминовый", 8000),
                    ("Горный", 8000),
                    ("Турецкий", 12000),
                    ("Ягодный", 13000),
                    ("Тропический", 12000),
                    ("Имбирно марокканский", 13000),
                    ("Имбирно ягодный", 12000),
                    ("Эрл грей", 8000),
                ],
            },
        },
    },
}

# =========================
# PHOTO FILES
# =========================
PHOTO_BY_ITEM = {
    # soups
    "Лагман": "photos/lagman.png",
    "Шурпа из баранины": "photos/lambshurpa.png",
    "Окрошка": "photos/okroshka.png",
    "Борщ": "photos/borscht.png",
    "Мастава": "photos/mastava.png",
    "Шурпа из говядины": "photos/beefshurpa.png",
    "Пельмени с бульоном": "photos/dumplingssoup.png",
    "Суп с фрикадельками": "photos/soupwithmeatballs.png",

    # bread
    "Хлеб": "photos/lepeshka.png",
    "Патир": "photos/patir.png",
    "Большой Патир": "photos/largepatir.png",
    "Лаваш": "photos/lavash.png",
    "Хлебной набор Ассорти": "photos/assortibread.png",
    "Черный Хлеб": "photos/blackbread.png",

    # fast food
    "Тандыр Самса": "photos/tandirsomsa.png",
    "Самарканд Самса": "photos/samarkandsomsa.png",
    "Самса": "photos/samsa.png",
    "Бургер сет": "photos/burgerset.png",
    "Шаурма Шашлык": "photos/shawarmashashlik.png",
    "Чебурек с сыром": "photos/chubarekwithcheese.png",

    # salad
    "Овощная нарезка": "photos/vegetableslices.png",
    "Французский": "photos/french.png",
    "Селедка по шубой": "photos/herringundersalad.png",
    "Соленья Тузлама": "photos/tuzlamasalad.png",
    "Салат Самарканд": "photos/samarkandsalad.png",
    "Греческий салат": "photos/greek.png",
    "Салат Каприз": "photos/caprice.png",
    "Салат Цезарь": "photos/caesar.png",
    "Салат Оливье": "photos/olivier.png",
    "Ачучук": "photos/tomatoandcucumber.png",
    "Жаренные баклажаны": "photos/friedeggplant.png",
    "Салат Смак": "photos/smak.png",

    # second meal
    "Манты": "photos/dumplings.png",
    "Уйгурский лагман": "photos/uygurlagman.png",
    "Ханум": "photos/khanum.png",
    "Жаренный лагман": "photos/friedlagman.png",
    "Хинкали": "photos/khinkalii.png",
    "Жаренные пельмени": "photos/frieddumplings.png",
    "Нарын": "photos/naryn.png",
    "Бешбармак": "photos/beshbarmak.png",
    "Жаркое из говядины с гарниром": "photos/beefroastgarnish.png",
    "Целая курица с картошкой фри": "photos/fullchickenandfrenchfries.png",
    "Долма с говядиной": "photos/beefdolma.png",
    "Куртоб": "photos/qurotb.png",
    "Бифштекс": "photos/beefcutlet.png",
    "Мошкчири": "photos/moshkichiri.png",
    "Туй кабоб": "photos/tuykabob.png",
    "Котлеты с сыром на мангале": "photos/cutletswithcheese.png",
    "Казан кебаб": "photos/kazankebab.png",
    "Жаренная баранина с картошкой фри": "photos/friedlambwithfrenchfries.png",
    "Жаренная говядина с картошкой фри": "photos/friedbeefandfrenchfries.png",
    "Баранья корейка на гриле": "photos/barbequelambribs.png",
    "Жареный сазан": "photos/friedcarbfish.png",
    "Стейк из сёмги с гарниром": "photos/salmansteakandgarnish.png",
    "Баранье ребра с рисом и картошкой": "photos/lambribsandrice.png",
    "Бараньи ребрышки 1кг": "photos/barbequelambribs1kg.png",
    "Самаркандский плов": "photos/samarkandpilaf.png",
    "Плов с долмой и казы": "photos/pilafwithdolmaandkazi.png",
    "Самаркандский плов Сет 1чл": "photos/pilaf1personset.png",

    # bbq
    "Стейк из говядины": "photos/beefsteak.png",
    "Стейк из баранины": "photos/lambsteak.png",
    "Стейк Рибай с костью": "photos/ribeyesteakonbone.png",
    "Стейк рибай": "photos/ribeyesteak.png",
    "Рулет шашлык говядина": "photos/beefshashlikroll.png",
    "Куриный шашлык": "photos/chickenshashlik.png",
    "Овощи на гриле": "photos/grilledvegetables.png",
    "Шашлык из бараньей корейки": "photos/lambribshashlik.png",
    "Сет Шашлык 6шт + овощи": "photos/shashlikset.png",
    "Наполеон шашлык": "photos/napoleonshashlik.png",
    "Медальон шашлык": "photos/medaleonshashlik.png",
    "Молотый шашлык": "photos/mincedbeef.png",
    "Кусковой шашлык баранина": "photos/lambshashlik.png",
    "Куриные крылашки": "photos/chickenwings.png",
    "Шашлык из говяжьей печени": "photos/beeflivershashlik.png",
    "Шашлык из говяжего филе": "photos/beeffileshashlik.png",
    "Курдюк шашлык": "photos/kurdukshashlik.png",
    "Универсальный рулет": "photos/universalroll.png",
    "Meat Set": "photos/meatset.png",
    "Meat Set Big": "photos/meatsetbig.png",
    "Dastirxan Bbq set": "photos/dastirxanbbqset.png",
    "Dastirxan BBQ Set Big": "photos/dastirxanbbqsetbig.png",
    "Томатный соус": "photos/tomatosouce.png",
    "Чесночный соус": "photos/garlicsouce.png",

    # desserts
    "Большое фруктовое ассорти": "photos/largefruitassorti.png",
    "Ферреро роше": "photos/ferreroroche.png",
    "Молочная девочка": "photos/milkcake.png",
    "Чизкейк": "photos/cheesecake.png",
    "Пахлава": "photos/traditionalbaklava.png",
    "Наполеон": "photos/napoleoncake.png",
    "Медовик": "photos/honeycake.png",
    "Красный бархат": "photos/redvelvet.png",
    "Шоколодный торт орео": "photos/chocolateoreocake.png",
    "Фруктовый салат с шоколадом": "photos/chocolatefruits.png",
    "Мороженное": "photos/icecream.png",

    # coffee
    "Американо": "photos/americano.png",
    "Капучино": "photos/cappucino.png",
    "Флет уайт": "photos/flatwhite.png",
    "Латта с корицей и медом": "photos/lattewithcinnamon.png",
    "Горячий шоколад": "photos/hotchocolate.png",
    "Матча латте": "photos/matchalatte.png",
    "Айс американо": "photos/iceamericano.png",
    "Айс латте": "photos/icedlatte.png",
    "Сансет": "photos/sunset.png",
    "Клубничный матча латте": "photos/strawberrymatchalatte.png",
    "Айс матча": "photos/icedmatcha.png",

    # fresh juice
    "Апельсиновый фреш": "photos/orangefreshjuice.png",
    "Лимонный фреш": "photos/lemonfresh.png",
    "Киви щавель": "photos/kiwisorrel.png",
    "Морковный фреш": "photos/carrottfresh.png",
    "Апельсиново морковный фреш": "photos/orangecarrotfresh.png",
    "Киви сельдерей": "photos/kiwicelery.png",

    # lemonade
    "Тропический 1л": "photos/tropical1l.png",
    "Лимонный 1л": "photos/lemon1l.png",
    "Клубничный мохито 1л": "photos/strawberrymojito1L.png",
    "Классический мохито 1л": "photos/classicmojito.png",
    "Манго маракуйя 1л": "photos/mangopassionfruit.png",
    "Тархун 1л": "photos/tarkhuna.png",
    "Мохито с маракуйей 1л": "photos/passionfruitmojito.png",
    "Кампот вишневый 1л": "photos/naturaljuice1l.png",
    "Ягодный 0.5л": "photos/berrysmall.png",
    "Лимоный 0.5л": "photos/lemonsmall.png",
    "Тропический 0.5л": "photos/tropicalsmall.png",
    "Классик мохито 0.5л": "photos/classicmojitosmall.png",
    "Манго маракуйя 0.5л": "photos/magopassionssmall.png",
    "Клубничный мохито 0.5л": "photos/strawberrymojito0,5.png",
    "Мохито с маракуйей 0.5л": "photos/passionfruitmojitosmall.png",
    "Тархун 0.5л": "photos/tarkhunasmall.png",

    # tea
    "Марокканский": "photos/maroccantea.png",
    "Жасминовый": "photos/jasminetea.png",
    "Горный": "photos/mountaintea.png",
    "Турецкий": "photos/turkishtea.png",
    "Ягодный": "photos/berrytea.png",
    "Тропический": "photos/tropical.png",
    "Имбирно марокканский": "photos/gingermoroccantea.png",
    "Имбирно ягодный": "photos/gingerberrytea.png",
    "Эрл грей": "photos/earlgrey.png",
}

# =========================
# DESCRIPTIONS
# =========================
DESC_BY_ITEM = {
    # soups
    "Лагман": "Домашний лагман с говядиной, овощами и густым ароматным насыщенным бульоном.",
    "Шурпа из баранины": "Наваристая шурпа с бараниной, картофелем и ярким мясным вкусом.",
    "Окрошка": "Освежающая холодная окрошка со свежими овощами и лёгким натуральным вкусом.",
    "Борщ": "Классический борщ с насыщенным вкусом, овощами и домашней сытной подачей.",
    "Мастава": "Сытная мастава с рисом, мясом и мягким домашним вкусом.",
    "Шурпа из говядины": "Горячая шурпа с говядиной, картофелем и ароматным бульоном.",
    "Пельмени с бульоном": "Домашние пельмени в горячем бульоне с нежной мясной начинкой.",
    "Суп с фрикадельками": "Лёгкий суп с фрикадельками, овощами и приятным домашним вкусом.",

    # bread
    "Хлеб": "Свежий хлеб с мягкой серединой и аппетитной румяной корочкой.",
    "Патир": "Традиционный патир с насыщенным вкусом и ароматной хрустящей корочкой.",
    "Большой Патир": "Большой патир для общего стола с золотистой корочкой и мягкой серединой.",
    "Лаваш": "Тонкий свежий лаваш, идеально подходящий к мясу и горячим блюдам.",
    "Хлебной набор Ассорти": "Ассорти свежего хлеба с разной текстурой и богатой подачей.",
    "Черный Хлеб": "Плотный чёрный хлеб с насыщенным вкусом и мягкой текстурой.",

    # fast food
    "Тандыр Самса": "Горячая тандыр самса с сочной мясной начинкой и румяной корочкой.",
    "Самарканд Самса": "Самаркандская самса с насыщенной начинкой и аппетитной домашней выпечкой.",
    "Самса": "Классическая самса с сочной начинкой и золотистой хрустящей корочкой.",
    "Бургер сет": "Сытный бургер сет с яркой подачей и насыщенным аппетитным вкусом.",
    "Шаурма Шашлык": "Сочная шаурма с мясом, овощами и насыщенным пряным вкусом.",
    "Чебурек с сыром": "Хрустящий чебурек с тянущимся сыром и горячей румяной корочкой.",

    # salad
    "Овощная нарезка": "Свежая овощная нарезка с натуральным вкусом и яркой подачей.",
    "Французский": "Нежный французский салат с мягким вкусом и красивой подачей.",
    "Селедка по шубой": "Классическая селёдка под шубой с насыщенным домашним вкусом.",
    "Соленья Тузлама": "Пикантные соленья с ярким вкусом и аппетитной домашней подачей.",
    "Салат Самарканд": "Свежий салат Самарканд с сочными ингредиентами и насыщенным вкусом.",
    "Греческий салат": "Лёгкий греческий салат со свежими овощами и мягким вкусом.",
    "Салат Каприз": "Нежный салат Каприз с гармоничным вкусом и аккуратной подачей.",
    "Салат Цезарь": "Аппетитный Цезарь с насыщенным соусом и свежими ингредиентами.",
    "Салат Оливье": "Домашний Оливье с классическим вкусом и нежной текстурой.",
    "Ачучук": "Свежий ачучук из томатов и огурцов с лёгким натуральным вкусом.",
    "Жаренные баклажаны": "Жареные баклажаны с мягкой текстурой и насыщенным ароматным вкусом.",
    "Салат Смак": "Салат Смак с ярким вкусом, свежими ингредиентами и красивой подачей.",

    # second meal
    "Манты": "Нежные манты с сочной начинкой и мягким домашним вкусом.",
    "Уйгурский лагман": "Уйгурский лагман с мясом, овощами и ярким насыщенным вкусом.",
    "Ханум": "Нежный ханум с аппетитной начинкой и мягкой домашней текстурой.",
    "Жаренный лагман": "Жареный лагман с мясом, овощами и насыщенным ароматом сковороды.",
    "Хинкали": "Сочные хинкали с ароматной начинкой и насыщенным мясным вкусом.",
    "Жаренные пельмени": "Жареные пельмени с хрустящей корочкой и сочной мясной начинкой.",
    "Нарын": "Традиционный нарын с насыщенным вкусом и аккуратной аппетитной подачей.",
    "Бешбармак": "Сытный бешбармак с мягким мясом и насыщенным домашним вкусом.",
    "Жаркое из говядины с гарниром": "Жаркое из говядины с гарниром, сочным мясом и насыщенным вкусом.",
    "Целая курица с картошкой фри": "Аппетитная целая курица с картошкой фри и золотистой корочкой.",
    "Долма с говядиной": "Нежная долма с говядиной, ароматной начинкой и домашним вкусом.",
    "Куртоб": "Традиционный куртоб с насыщенным вкусом и мягкой текстурой подачи.",
    "Бифштекс": "Сочный бифштекс с аппетитной подачей и ярким мясным вкусом.",
    "Мошкчири": "Сытный мошкичири с насыщенным вкусом и домашней подачей.",
    "Туй кабоб": "Нежный туй кабоб с насыщенным вкусом и ароматной подачей.",
    "Котлеты с сыром на мангале": "Сочные котлеты с сыром на мангале и аппетитным ароматом.",
    "Казан кебаб": "Казан кебаб с насыщенным вкусом, мясом и аппетитной подачей.",
    "Жаренная баранина с картошкой фри": "Жареная баранина с картошкой фри и насыщенным сочным вкусом.",
    "Жаренная говядина с картошкой фри": "Жареная говядина с картошкой фри и сытной аппетитной подачей.",
    "Баранья корейка на гриле": "Баранья корейка с ярким мясным вкусом и ароматом гриля.",
    "Жареный сазан": "Жареный сазан с хрустящей корочкой и нежным вкусом рыбы.",
    "Стейк из сёмги с гарниром": "Стейк из сёмги с гарниром и мягким насыщенным вкусом.",
    "Баранье ребра с рисом и картошкой": "Бараньи рёбра с рисом и картошкой, сытно и очень аппетитно.",
    "Бараньи ребрышки 1кг": "Большая порция бараньих рёбрышек с ярким насыщенным мясным вкусом.",
    "Самаркандский плов": "Традиционный самаркандский плов с глубоким ароматом и насыщенным вкусом.",
    "Плов с долмой и казы": "Сытный плов с долмой и казы, яркий праздничный вкус блюда.",
    "Самаркандский плов Сет 1чл": "Порционный самаркандский плов сет с насыщенным традиционным вкусом.",

    # bbq
    "Стейк из говядины": "Сочный стейк из говядины с ярким мясным вкусом и подачей.",
    "Стейк из баранины": "Нежный стейк из баранины с насыщенным вкусом и ароматом.",
    "Стейк Рибай с костью": "Рибай с костью, сочный стейк с глубоким мясным вкусом.",
    "Стейк рибай": "Нежный рибай с насыщенным вкусом и аппетитной мясной подачей.",
    "Рулет шашлык говядина": "Говяжий рулет шашлык с ярким вкусом и сочной подачей.",
    "Куриный шашлык": "Нежный куриный шашлык с ароматом гриля и сочной текстурой.",
    "Овощи на гриле": "Овощи на гриле с лёгким вкусом и аппетитным ароматом.",
    "Шашлык из бараньей корейки": "Сочный шашлык из бараньей корейки с насыщенным мясным вкусом.",
    "Сет Шашлык 6шт + овощи": "Большой сет шашлыков с овощами для сытного общего стола.",
    "Наполеон шашлык": "Наполеон шашлык с многослойной подачей и насыщенным вкусом.",
    "Медальон шашлык": "Нежный медальон шашлык с сочной текстурой и аппетитной подачей.",
    "Молотый шашлык": "Молотый шашлык с ярким мясным вкусом и ароматом гриля.",
    "Кусковой шашлык баранина": "Кусковой шашлык из баранины с сочным мясом и ароматом.",
    "Куриные крылашки": "Сочные куриные крылышки с золотистой корочкой и ярким вкусом.",
    "Шашлык из говяжьей печени": "Нежный шашлык из печени с насыщенным вкусом и ароматом.",
    "Шашлык из говяжего филе": "Шашлык из говяжьего филе с сочной текстурой и ярким вкусом.",
    "Курдюк шашлык": "Курдюк шашлык с насыщенным вкусом и аппетитной мясной подачей.",
    "Универсальный рулет": "Универсальный рулет с насыщенным вкусом и красивой подачей.",
    "Meat Set": "Большой мясной сет с разными вкусами для хорошей компании.",
    "Meat Set Big": "Большой мясной сет с богатой подачей и насыщенным вкусом.",
    "Dastirxan Bbq set": "Фирменный BBQ сет Dastirxan с аппетитной мясной подачей.",
    "Dastirxan BBQ Set Big": "Большой фирменный BBQ сет для компании и общего стола.",
    "Томатный соус": "Насыщенный томатный соус, идеально подходящий к мясу и закускам.",
    "Чесночный соус": "Ароматный чесночный соус с ярким вкусом для ваших блюд.",

    # desserts
    "Большое фруктовое ассорти": "Большое фруктовое ассорти со свежей подачей и ярким натуральным вкусом.",
    "Ферреро роше": "Нежный десерт с шоколадным вкусом и красивой праздничной подачей.",
    "Молочная девочка": "Мягкий молочный торт с нежным вкусом и лёгкой текстурой.",
    "Чизкейк": "Нежный чизкейк с бархатистой текстурой и мягким сливочным вкусом.",
    "Пахлава": "Слоёная пахлава с насыщенной сладостью и аппетитной восточной подачей.",
    "Наполеон": "Классический Наполеон с тонкими слоями и нежным кремовым вкусом.",
    "Медовик": "Медовик с мягкими коржами и насыщенным медовым вкусом.",
    "Красный бархат": "Яркий красный бархат с нежной текстурой и мягким сливочным вкусом.",
    "Шоколодный торт орео": "Шоколадный торт орео с насыщенным вкусом и аппетитной подачей.",
    "Фруктовый салат с шоколадом": "Свежие фрукты с шоколадом в ярком сладком сочетании вкусов.",
    "Мороженное": "Прохладное мороженое с нежной текстурой и освежающим сладким вкусом.",

    # coffee
    "Американо": "Классический американо с чистым кофейным вкусом и лёгким ароматом.",
    "Капучино": "Нежный капучино с мягкой молочной пенкой и кофейным вкусом.",
    "Флет уайт": "Флет уайт с насыщенным эспрессо и бархатистой молочной текстурой.",
    "Латта с корицей и медом": "Ароматный латте с корицей и мёдом в мягком сочетании.",
    "Горячий шоколад": "Плотный горячий шоколад с насыщенным вкусом и мягкой сладостью.",
    "Матча латте": "Матча латте с мягким травяным вкусом и нежной молочной текстурой.",
    "Айс американо": "Освежающий айс американо с чистым вкусом и холодной подачей.",
    "Айс латте": "Холодный айс латте с мягким кофейно-молочным сочетанием вкуса.",
    "Сансет": "Яркий кофейный напиток с необычной подачей и насыщенным вкусом.",
    "Клубничный матча латте": "Клубничный матча латте с нежной сладостью и свежим вкусом.",
    "Айс матча": "Освежающий айс матча с мягким травяным вкусом и прохладой.",

    # fresh juice
    "Апельсиновый фреш": "Свежий апельсиновый фреш с ярким цитрусовым вкусом и свежестью.",
    "Лимонный фреш": "Бодрящий лимонный фреш с яркой кислинкой и свежим вкусом.",
    "Киви щавель": "Необычный фреш из киви и щавеля с освежающим зелёным вкусом.",
    "Морковный фреш": "Натуральный морковный фреш с мягкой сладостью и свежестью.",
    "Апельсиново морковный фреш": "Сочный фреш из апельсина и моркови с мягким балансом вкуса.",
    "Киви сельдерей": "Освежающий фреш из киви и сельдерея с натуральным вкусом.",

    # lemonade
    "Тропический 1л": "Тропический лимонад с ярким фруктовым вкусом и большой подачей.",
    "Лимонный 1л": "Большой лимонный лимонад с бодрящей свежестью и лёгкой кислинкой.",
    "Клубничный мохито 1л": "Клубничный мохито с яркой сладостью и свежей мятной подачей.",
    "Классический мохито 1л": "Классический мохито с мятой, лаймом и освежающим вкусом.",
    "Манго маракуйя 1л": "Манго-маракуйя с ярким тропическим вкусом и сочной подачей.",
    "Тархун 1л": "Тархун с освежающим травяным вкусом и насыщенным ароматом.",
    "Мохито с маракуйей 1л": "Мохито с маракуйей с яркой свежестью и фруктовой кислинкой.",
    "Кампот вишневый 1л": "Домашний вишнёвый компот с мягкой сладостью и ягодным вкусом.",
    "Ягодный 0.5л": "Ягодный лимонад с насыщенным вкусом и освежающей подачей.",
    "Лимоный 0.5л": "Небольшой лимонный лимонад с бодрящей кислинкой и свежестью.",
    "Тропический 0.5л": "Тропический лимонад в удобной порции с ярким фруктовым вкусом.",
    "Классик мохито 0.5л": "Классический мохито в компактной порции с мятной свежестью.",
    "Манго маракуйя 0.5л": "Манго-маракуйя в небольшой порции с насыщенным тропическим вкусом.",
    "Клубничный мохито 0.5л": "Клубничный мохито с мягкой сладостью и приятной свежестью.",
    "Мохито с маракуйей 0.5л": "Мохито с маракуйей в лёгкой освежающей фруктовой подаче.",
    "Тархун 0.5л": "Тархун в небольшой порции с мягким травяным освежающим вкусом.",

    # tea
    "Марокканский": "Марокканский чай с насыщенным ароматом и приятной согревающей подачей.",
    "Жасминовый": "Жасминовый чай с тонким цветочным ароматом и мягким вкусом.",
    "Горный": "Горный чай с натуральным ароматом и спокойным насыщенным вкусом.",
    "Турецкий": "Турецкий чай с крепким вкусом и классической насыщенной подачей.",
    "Ягодный": "Ягодный чай с ярким ароматом и мягким фруктовым вкусом.",
    "Тропический": "Тропический чай с фруктовыми нотами и тёплой ароматной подачей.",
    "Имбирно марокканский": "Имбирно-марокканский чай с пряной теплотой и насыщенным ароматом.",
    "Имбирно ягодный": "Имбирно-ягодный чай с яркой кислинкой и тёплым согревающим вкусом.",
    "Эрл грей": "Эрл грей с благородным ароматом бергамота и мягким вкусом.",
}

# =========================
# FALLBACK DESCRIPTION
# =========================
def fallback_desc(item_name: str) -> str:
    return f"{item_name} с аппетитной подачей и приятным насыщенным вкусом."

# =========================
# ITEM LISTS / INDEXES
# =========================
ITEM_PRICES = {}
ALL_ITEMS = []

for root_data in MENU.values():
    for category_data in root_data["categories"].values():
        for item_name, price in category_data["items"]:
            ITEM_PRICES[item_name] = price
            ALL_ITEMS.append(item_name)

ITEM_INDEX = {item_name: idx for idx, item_name in enumerate(ALL_ITEMS)}
INDEX_TO_ITEM = {idx: item_name for idx, item_name in enumerate(ALL_ITEMS)}

# =========================
# RUNTIME DATA
# =========================
user_carts: dict[int, dict[str, int]] = {}
user_states: dict[int, str | None] = {}
user_data: dict[int, dict] = {}
last_prompt_messages: dict[int, int] = {}
PHOTO_FILE_IDS: dict[str, str] = {}
PHOTO_CACHE_FILE = Path("photo_file_ids.json")
photo_cache_lock = asyncio.Lock()

# =========================
# KEYBOARDS
# =========================
TEXTS = {
    "ru": {
        "choose_language": "🌐 Выберите язык / Tilni tanlang:",
        "choose_language_again": "Пожалуйста, выберите язык / Iltimos, tilni tanlang:",
        "welcome": "🍽 Добро пожаловать!\n\nВыбери меню 👇",
        "main_menu": "🍖 Основное меню",
        "desserts_menu": "🍰 Десерты и напитки",
        "cart": "🛒 Корзина",
        "my_orders": "📦 Мои заказы",
        "delivery": "🚚 Доставка",
        "pickup": "🏃 Самовывоз",
        "send_location": "📍 Отправить локацию",
        "enter_address_text": "✍️ Ввести адрес текстом",
        "cash": "💵 Наличными",
        "bank_transfer": "💳 Банковским переводом",
        "confirm_yes": "✅ Да, оформить",
        "confirm_edit": "✏️ Нет, изменить",
        "edit_name": "👤 Изменить имя",
        "edit_phone": "📞 Изменить номер",
        "edit_address": "📍 Изменить адрес",
        "edit_delivery": "🚚 Изменить способ получения",
        "edit_payment": "💳 Изменить оплату",
        "back_to_confirm": "⬅️ Назад к подтверждению",
        "back_to_menu": "🏠 В меню",
        "categories": "📂 Категории",
        "choose_category": "Выберите категорию 👇",
        "main_menu_prompt": "Главное меню 👇",
        "history_empty": "📭 История заказов пуста!",
        "your_orders": "📦 Ваши заказы:\n\n",
        "choose_button": "Выбери кнопку 👇",
        "receipt_sent": "✅ Чек получен и отправлен на проверку администратору.",
        "receipt_request": "🧾 Пожалуйста, отправьте чек как ФАЙЛ или ФОТО.",
        "enter_name_prompt": "👤 Введите ваше имя:",
        "enter_phone_prompt": "📞 Введите номер телефона:",
        "choose_delivery_prompt": "📦 Как получить заказ?",
        "choose_delivery_invalid": "Пожалуйста, выберите: доставка или самовывоз",
        "send_address_prompt": "📍 Отправьте локацию или введите адрес текстом:",
        "enter_address_prompt": "✍️ Введите адрес текстом:",
        "choose_payment_prompt": "💳 Как оплатите заказ?",
        "choose_payment_invalid": "Пожалуйста, выберите способ оплаты",
        "choose_bank_invalid": "Пожалуйста, выберите банк кнопкой ниже",
        "bank_pay_instructions": "💳 Оплатите по удобному вам методу.\n\n{bank}\nНомер счёта для оплаты:\n{account}\n\nПосле оплаты отправьте СКРИНШОТ ЧЕКА как ФАЙЛ или ФОТО.",
        "edit_what": "✏️ Что хотите изменить?",
        "edit_choose": "Пожалуйста, выберите, что хотите изменить:",
        "enter_new_name": "👤 Введите новое имя:",
        "enter_new_phone": "📞 Введите новый номер телефона:",
        "address_only_delivery": "📍 Адрес нужен только для доставки. Сначала выберите способ получения.",
        "send_new_address": "📍 Отправьте новую локацию или введите новый адрес:",
        "choose_new_delivery": "🚚 Выберите новый способ получения:",
        "choose_new_payment": "💳 Выберите новый способ оплаты:",
        "choose_delivery_or_pickup": "Пожалуйста, выберите: доставка или самовывоз",
        "choose_payment_method": "Пожалуйста, выберите способ оплаты",
        "check_order": "📋 Проверьте заказ:\n\n🛒 Корзина:\n",
        "total": "💰 Итого",
        "name_label": "👤 Имя",
        "phone_label": "📞 Телефон",
        "delivery_label": "🚚 Способ получения",
        "address_label": "📍 Адрес",
        "payment_label": "💳 Оплата",
        "all_correct": "Всё верно?",
        "cart_empty": "🛒 Корзина пустая",
        "your_cart": "🛒 Ваша корзина:\n\n",
        "checkout": "✅ Оформить заказ",
        "clear_cart": "🧹 Очистить корзину",
        "cart_empty_alert": "Корзина пустая",
        "checkout_start": "✅ Переходим к оформлению заказа...",
        "cart_updated": "Корзина обновлена",
        "cart_cleared": "Корзина очищена",
        "order_done": "✅ Ваш заказ {order_code} оформлен!",
        "payment_confirmed_client": "💰 Ваш заказ {order_code} отмечен как оплаченный.",
        "order_cancelled_client": "❌ Ваш заказ {order_code} отменён.",
        "status_accept_client": "✅ Ваш заказ {order_code} принят!",
        "status_cooking_client": "👨‍🍳 Ваш заказ {order_code} готовится",
        "status_delivery_client": "🚗 Курьер уже выехал по заказу {order_code}!",
        "status_done_client": "🏁 Заказ {order_code} завершён. Приятного аппетита!",
        "choose_bank_prompt": "🏦 Выберите банк для перевода:",
        "location_prefix": "Локация",
        "pickup_address": "Самовывоз",
        "contact_admin": "📞 Связаться с нами",
        "contact_admin_text": "📞 <b>Свяжитесь с нами</b>\n\nНажмите кнопку ниже, чтобы открыть чат с администратором.",
        "contact_admin_button": "💬 Написать администратору",
        "courier_note_prompt": (
            "🏡 <b>Почти готово!</b>\n\n"
            "📌 <b>Введите информацию, которая будет полезна курьеру:</b>\n"
            "• номер квартиры\n"
            "• подъезд\n"
            "• этаж\n"
            "• домофон\n"
            "• ориентир\n\n"
            "✨ <i>Например: 3 подъезд, 7 этаж, кв. 54</i>\n\n"
            "🙏 Спасибо!"
        ),
        "courier_note_skip": "⏭ Пропустить",
        "courier_note_empty": "—",
        "courier_note_label": "📝 Комментарий курьеру",
    },
    "uz": {
        "choose_language": "🌐 Tilni tanlang / Выберите язык:",
        "choose_language_again": "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        "welcome": "🍽 Xush kelibsiz!\n\nMenyuni tanlang 👇",
        "main_menu": "🍖 Asosiy menyu",
        "desserts_menu": "🍰 Desertlar va ichimliklar",
        "cart": "🛒 Savat",
        "my_orders": "📦 Buyurtmalarim",
        "delivery": "🚚 Yetkazib berish",
        "pickup": "🏃 Olib ketish",
        "send_location": "📍 Lokatsiyani yuborish",
        "enter_address_text": "✍️ Manzilni matn bilan kiritish",
        "cash": "💵 Naqd pul",
        "bank_transfer": "💳 Bank o'tkazmasi",
        "confirm_yes": "✅ Ha, rasmiylashtirish",
        "confirm_edit": "✏️ Yo‘q, o‘zgartirish",
        "edit_name": "👤 Ismni o‘zgartirish",
        "edit_phone": "📞 Raqamni o‘zgartirish",
        "edit_address": "📍 Manzilni o‘zgartirish",
        "edit_delivery": "🚚 Yetkazish turini o‘zgartirish",
        "edit_payment": "💳 To‘lovni o‘zgartirish",
        "back_to_confirm": "⬅️ Tasdiqlashga qaytish",
        "back_to_menu": "🏠 Menyuga",
        "categories": "📂 Kategoriyalar",
        "choose_category": "Kategoriyani tanlang 👇",
        "main_menu_prompt": "Asosiy menyu 👇",
        "history_empty": "📭 Buyurtmalar tarixi bo‘sh!",
        "your_orders": "📦 Buyurtmalaringiz:\n\n",
        "choose_button": "Tugmani tanlang 👇",
        "receipt_sent": "✅ Chek qabul qilindi va administratorga yuborildi.",
        "receipt_request": "🧾 Iltimos, chekni FAYL yoki FOTO sifatida yuboring.",
        "enter_name_prompt": "👤 Ismingizni kiriting:",
        "enter_phone_prompt": "📞 Telefon raqamingizni kiriting:",
        "choose_delivery_prompt": "📦 Buyurtmani qanday olasiz?",
        "choose_delivery_invalid": "Iltimos, yetkazib berish yoki olib ketishni tanlang",
        "send_address_prompt": "📍 Lokatsiyani yuboring yoki manzilni matn bilan kiriting:",
        "enter_address_prompt": "✍️ Manzilni matn bilan kiriting:",
        "choose_payment_prompt": "💳 To‘lov turini tanlang:",
        "choose_payment_invalid": "Iltimos, to‘lov turini tanlang",
        "choose_bank_invalid": "Iltimos, quyidagi usullardan birini tanlang:",
        "bank_pay_instructions": "💳 Qulay usul orqali to‘lov qiling.\n\n{bank}\nTo‘lov uchun hisob raqami:\n{account}\n\nTo‘lovdan so‘ng CHEK SKRINSHOTINI FAYL yoki FOTO sifatida yuboring.",
        "edit_what": "✏️ Nimani o‘zgartirmoqchisiz?",
        "edit_choose": "Iltimos, nimani o‘zgartirishni tanlang:",
        "enter_new_name": "👤 Yangi ismni kiriting:",
        "enter_new_phone": "📞 Yangi telefon raqamini kiriting:",
        "address_only_delivery": "📍 Manzil faqat yetkazib berish uchun kerak. Avval yetkazish turini o‘zgartiring.",
        "send_new_address": "📍 Yangi lokatsiyani yuboring yoki yangi manzilni kiriting:",
        "choose_new_delivery": "🚚 Yangi yetkazish turini tanlang:",
        "choose_new_payment": "💳 Yangi to‘lov turini tanlang:",
        "choose_delivery_or_pickup": "Iltimos, yetkazib berish yoki olib ketishni tanlang.",
        "choose_payment_method": "Iltimos, to‘lov turini tanlang.",
        "check_order": "📋 Buyurtmani tekshiring:\n\n🛒 Savat:\n",
        "total": "💰 Jami",
        "name_label": "👤 Ism",
        "phone_label": "📞 Telefon",
        "delivery_label": "🚚 Olish usuli",
        "address_label": "📍 Manzil",
        "payment_label": "💳 To‘lov",
        "all_correct": "Hammasi to‘g‘rimi?",
        "cart_empty": "🛒 Savat bo‘sh",
        "your_cart": "🛒 Savatingiz:\n\n",
        "checkout": "✅ Buyurtma berish",
        "clear_cart": "🧹 Savatni tozalash",
        "cart_empty_alert": "Savat bo‘sh",
        "checkout_start": "✅ Buyurtmani rasmiylashtirishga o‘tamiz...",
        "cart_updated": "Savat yangilandi",
        "cart_cleared": "Savat tozalandi",
        "order_done": "✅ Sizning buyurtmangiz {order_code} rasmiylashtirildi!",
        "payment_confirmed_client": "💸 To‘lov tasdiqlandi! Buyurtmangiz {order_code} muvaffaqiyatli to‘landi. ✅",
        "order_cancelled_client": "❌ Afsus, buyurtmangiz {order_code} bekor qilindi.",
        "status_accept_client": "🎉 Buyurtmangiz {order_code} qabul qilindi!",
        "status_cooking_client": "👨‍🍳 Buyurtmangiz {order_code} tayyorlanmoqda.",
        "status_delivery_client": "🚗 Kuryer buyurtmangiz {order_code} bilan yo‘lga chiqdi!",
        "status_done_client": "🏁 Buyurtmangiz {order_code} yakunlandi. Yoqimli ishtaha!",
        "choose_bank_prompt": "🏦 Qulay bank o‘tkazmasi usulini tanlang:",
        "location_prefix": "Lokatsiya",
        "pickup_address": "Olib ketish",
        "contact_admin": "📞 Biz bilan bog'laning",
        "contact_admin_text": "📞 <b>Biz bilan bog'laning</b>\n\nAdministrator bilan bog'lanish uchun quyidagi tugmani bosing.",
        "contact_admin_button": "💬 Administratorga yozish",
        "courier_note_prompt": (
            "🏡 <b>Deyarli tayyor!</b>\n\n"
            "📌 <b>Kuryer uchun foydali bo'ladigan ma'lumotni kiriting:</b>\n"
            "• xonadon raqami\n"
            "• подъезд / kirish qismi\n"
            "• qavat\n"
            "• domofon\n"
            "• mo'ljal\n\n"
            "✨ <i>Masalan: 3-kirish, 7-qavat, 54-xonadon</i>\n\n"
            "🙏 Rahmat!"
        ),
        "courier_note_skip": "⏭ O'tkazib yuborish",
        "courier_note_empty": "—",
        "courier_note_label": "📝 Kuryer uchun izoh",
    },
}

ROOT_TITLES = {
    "main": {"ru": "🍖 Основное меню", "uz": "🍖 Asosiy menyu"},
    "desserts": {"ru": "🍰 Десерты и напитки", "uz": "🍰 Desertlar va ichimliklar"},
}

CATEGORY_TITLES = {
    "bread": {"ru": "🥖 Хлеб", "uz": "🥖 Non"},
    "fastfood": {"ru": "🍔 Фаст Фуд", "uz": "🍔 Fast Food"},
    "salad": {"ru": "🥗 Салаты", "uz": "🥗 Salatlar"},
    "soup": {"ru": "🍲 Супы", "uz": "🍲 Sho‘rvalar"},
    "second": {"ru": "🍛 Второе блюдо", "uz": "🍛 Asosiy taomlar"},
    "bbq": {"ru": "🔥 Барбекю", "uz": "🔥 Barbekyu"},
    "desserts": {"ru": "🍰 Десерты", "uz": "🍰 Desertlar"},
    "coffee": {"ru": "☕ Кофе", "uz": "☕ Qahva"},
    "fresh": {"ru": "🍊 Свежий сок", "uz": "🍊 Fresh sharbat"},
    "lemonade": {"ru": "🥤 Лимонад", "uz": "🥤 Limonad"},
    "tea": {"ru": "🍵 Чай", "uz": "🍵 Choy"},
}


ITEM_NAME_UZ = {
    "Хлеб": "Non",
    "Патир": "Patir",
    "Большой Патир": "Katta patir",
    "Лаваш": "Lavash",
    "Хлебной набор Ассорти": "Assorti non to‘plami",
    "Черный Хлеб": "Qora non",
    "Тандыр Самса": "Tandir somsa",
    "Самарканд Самса": "Samarqand somsasi",
    "Самса": "Somsa",
    "Бургер сет": "Burger set",
    "Шаурма Шашлык": "Shashlik shoarma",
    "Чебурек с сыром": "Pishloqli cheburek",
    "Овощная нарезка": "Sabzavot assortisi",
    "Французский": "Fransuzcha salat",
    "Селедка по шубой": "Shuba ostidagi seld",
    "Соленья Тузлама": "Tuzlama",
    "Салат Самарканд": "Samarqand salati",
    "Греческий салат": "Grekcha salat",
    "Салат Каприз": "Kapriz salati",
    "Салат Цезарь": "Sezar salati",
    "Салат Оливье": "Olivye salati",
    "Ачучук": "Achchiq-chuchuk",
    "Жаренные баклажаны": "Qovurilgan baqlajon",
    "Салат Смак": "Smak salati",
    "Лагман": "Lag‘mon",
    "Шурпа из баранины": "Qo‘y go‘shtidan sho‘rva",
    "Окрошка": "Okroshka",
    "Борщ": "Borsh",
    "Мастава": "Mastava",
    "Шурпа из говядины": "Mol go‘shtidan sho‘rva",
    "Пельмени с бульоном": "Bulyonli chuchvara",
    "Суп с фрикадельками": "Frikadelli sho‘rva",
    "Манты": "Manti",
    "Уйгурский лагман": "Uyg‘ur lag‘moni",
    "Ханум": "Xonim",
    "Жаренный лагман": "Qovurilgan lag‘mon",
    "Хинкали": "Xinkali",
    "Жаренные пельмени": "Qovurilgan chuchvara",
    "Нарын": "Norin",
    "Бешбармак": "Beshbarmoq",
    "Жаркое из говядины с гарниром": "Garnirli mol go‘shti qovurmasi",
    "Целая курица с картошкой фри": "Butun tovuq fri kartoshka bilan",
    "Долма с говядиной": "Mol go‘shtli dolma",
    "Куртоб": "Qurutob",
    "Бифштекс": "Bifshteks",
    "Мошкчири": "Moshkichiri",
    "Туй кабоб": "To‘y kabob",
    "Котлеты с сыром на мангале": "Mangalda pishloqli kotlet",
    "Казан кебаб": "Qozon kabob",
    "Жаренная баранина с картошкой фри": "Qo‘y go‘shti fri kartoshka bilan",
    "Жаренная говядина с картошкой фри": "Mol go‘shti fri kartoshka bilan",
    "Баранья корейка на гриле": "Grildagi qo‘y karre",
    "Жареный сазан": "Qovurilgan sazan",
    "Стейк из сёмги с гарниром": "Garnirli losos steyki",
    "Баранье ребра с рисом и картошкой": "Qo‘y qovurg‘asi guruch va kartoshka bilan",
    "Бараньи ребрышки 1кг": "Qo‘y qovurg‘asi 1 kg",
    "Самаркандский плов": "Samarqand oshi",
    "Плов с долмой и казы": "Dolma va qazi bilan osh",
    "Самаркандский плов Сет 1чл": "Samarqand oshi set 1 kishilik",
    "Стейк из говядины": "Mol go‘shti steyki",
    "Стейк из баранины": "Qo‘y go‘shti steyki",
    "Стейк Рибай с костью": "Suyakli ribay steyk",
    "Стейк рибай": "Ribay steyk",
    "Рулет шашлык говядина": "Mol go‘shtli rulet shashlik",
    "Куриный шашлык": "Tovuq shashligi",
    "Овощи на гриле": "Grildagi sabzavotlar",
    "Шашлык из бараньей корейки": "Qo‘y karresidan shashlik",
    "Сет Шашлык 6шт + овощи": "Shashlik set 6 dona + sabzavot",
    "Наполеон шашлык": "Napoleon shashlik",
    "Медальон шашлык": "Medalyon shashlik",
    "Молотый шашлык": "Qiyma shashlik",
    "Кусковой шашлык баранина": "Qo‘y go‘shtidan bo‘lakcha shashlik",
    "Куриные крылашки": "Tovuq qanotchalari",
    "Шашлык из говяжьей печени": "Mol jigari shashligi",
    "Шашлык из говяжего филе": "Mol filesi shashligi",
    "Курдюк шашлык": "Dumba shashlik",
    "Универсальный рулет": "Universal rulet",
    "Meat Set": "Meat Set",
    "Meat Set Big": "Meat Set Big",
    "Dastirxan Bbq set": "Dastirxan BBQ Set",
    "Dastirxan BBQ Set Big": "Dastirxan BBQ Set Big",
    "Томатный соус": "Pomidor sousi",
    "Чесночный соус": "Sarimsoq sousi",
    "Большое фруктовое ассорти": "Katta meva assortisi",
    "Ферреро роше": "Ferrero Rocher",
    "Молочная девочка": "Molochnaya devochka",
    "Чизкейк": "Cheesecake",
    "Пахлава": "Paxlava",
    "Наполеон": "Napoleon",
    "Медовик": "Medovik",
    "Красный бархат": "Qizil baxmal",
    "Шоколодный торт орео": "Oreo shokoladli tort",
    "Фруктовый салат с шоколадом": "Shokoladli meva salati",
    "Мороженное": "Muzqaymoq",
    "Американо": "Americano",
    "Капучино": "Cappuccino",
    "Флет уайт": "Flat White",
    "Латта с корицей и медом": "Asal va dolchinli latte",
    "Горячий шоколад": "Issiq shokolad",
    "Матча латте": "Matcha latte",
    "Айс американо": "Iced Americano",
    "Айс латте": "Iced Latte",
    "Сансет": "Sunset",
    "Клубничный матча латте": "Qulupnayli matcha latte",
    "Айс матча": "Iced Matcha",
    "Апельсиновый фреш": "Apelsin fresh",
    "Лимонный фреш": "Limon fresh",
    "Киви щавель": "Kivi va shovul fresh",
    "Морковный фреш": "Sabzili fresh",
    "Апельсиново морковный фреш": "Apelsin-sabzili fresh",
    "Киви сельдерей": "Kivi va selderey fresh",
    "Тропический 1л": "Tropik 1 l",
    "Лимонный 1л": "Limonli 1 l",
    "Клубничный мохито 1л": "Qulupnayli mojito 1 l",
    "Классический мохито 1л": "Klassik mojito 1 l",
    "Манго маракуйя 1л": "Mango-marakuya 1 l",
    "Тархун 1л": "Tarxun 1 l",
    "Мохито с маракуйей 1л": "Marakuyali mojito 1 l",
    "Кампот вишневый 1л": "Gilos kompoti 1 l",
    "Ягодный 0.5л": "Rezavor 0.5 l",
    "Лимоный 0.5л": "Limonli 0.5 l",
    "Тропический 0.5л": "Tropik 0.5 l",
    "Классик мохито 0.5л": "Klassik mojito 0.5 l",
    "Манго маракуйя 0.5л": "Mango-marakuya 0.5 l",
    "Клубничный мохито 0.5л": "Qulupnayli mojito 0.5 l",
    "Мохито с маракуйей 0.5л": "Marakuyali mojito 0.5 l",
    "Тархун 0.5л": "Tarxun 0.5 l",
    "Марокканский": "Marokash choyi",
    "Жасминовый": "Yasmin choyi",
    "Горный": "Tog‘ choyi",
    "Турецкий": "Turk choyi",
    "Ягодный": "Rezavor choy",
    "Тропический": "Tropik choy",
    "Имбирно марокканский": "Zanjabilli Marokash choyi",
    "Имбирно ягодный": "Zanjabilli rezavor choy",
    "Эрл грей": "Earl Grey"
}


DESC_UZ_OVERRIDES = {
    "Самаркандский плов": "An’anaviy Samarqand oshi chuqur hid va boy ta’m bilan tayyorlanadi.",
    "Плов с долмой и казы": "Dolma va qazi bilan osh bayramona kayfiyat va to‘yimli ta’mni birlashtiradi.",
    "Самаркандский плов Сет 1чл": "Bir kishilik Samarqand oshi seti an’anaviy va to‘yimli ta’m bilan taqdim etiladi.",
    "Бараньи ребрышки 1кг": "Katta porsiyadagi qo‘y qovurg‘alari boy go‘sht ta’mi va ishtahaochar hidga ega.",
    "Баранье ребра с рисом и картошкой": "Qo‘y qovurg‘alari guruch va kartoshka bilan birga to‘yimli va juda ishtahaochar taom.",
    "Латта с корицей и медом": "Dolchin va asal qo‘shilgan latte mayin va xushbo‘y uyg‘unlikni beradi.",
    "Киви щавель": "Kivi va shovuldan tayyorlangan noodatiy fresh yengil va tetiklashtiruvchi ta’mga ega.",
    "Киви сельдерей": "Kivi va seldereydan tayyorlangan fresh tabiiy va tetiklashtiruvchi ta’m beradi.",
    "Шоколодный торт орео": "Oreo bilan tayyorlangan shokoladli tort boy ta’m va chiroyli taqdimotga ega.",
}

DESC_REPLACEMENTS = [
    ("Домашний", "Uy uslubidagi"), ("домашний", "uy uslubidagi"),
    ("Наваристая", "To‘yimli"), ("наваристая", "to‘yimli"),
    ("Освежающая", "Tetiklashtiruvchi"), ("освежающая", "tetiklashtiruvchi"),
    ("Классический", "Klassik"), ("классический", "klassik"),
    ("Классическая", "Klassik"), ("классическая", "klassik"),
    ("Сытная", "To‘yimli"), ("сытная", "to‘yimli"),
    ("Горячая", "Issiq"), ("горячая", "issiq"),
    ("Лёгкий", "Yengil"), ("лёгкий", "yengil"),
    ("Лёгкая", "Yengil"), ("лёгкая", "yengil"),
    ("Свежая", "Yangi"), ("свежая", "yangi"),
    ("Свежий", "Yangi"), ("свежий", "yangi"),
    ("Свежие", "Yangi"), ("свежие", "yangi"),
    ("Традиционный", "An’anaviy"), ("традиционный", "an’anaviy"),
    ("Традиционная", "An’anaviy"), ("традиционная", "an’anaviy"),
    ("Нежные", "Nozik"), ("нежные", "nozik"),
    ("Нежный", "Nozik"), ("нежный", "nozik"),
    ("Нежная", "Nozik"), ("нежная", "nozik"),
    ("Жареный", "Qovurilgan"), ("жареный", "qovurilgan"),
    ("Жареная", "Qovurilgan"), ("жареная", "qovurilgan"),
    ("Жареные", "Qovurilgan"), ("жареные", "qovurilgan"),
    ("Жаренная", "Qovurilgan"), ("жаренная", "qovurilgan"),
    ("Жаренные", "Qovurilgan"), ("жаренные", "qovurilgan"),
    ("Аппетитный", "Ishtahaochar"), ("аппетитный", "ishtahaochar"),
    ("Аппетитная", "Ishtahaochar"), ("аппетитная", "ishtahaochar"),
    ("Аппетитное", "Ishtahaochar"), ("аппетитное", "ishtahaochar"),
    ("Аппетитные", "Ishtahaochar"), ("аппетитные", "ishtahaochar"),
    ("Сочный", "Sersuv"), ("сочный", "sersuv"),
    ("Сочная", "Sersuv"), ("сочная", "sersuv"),
    ("Сочные", "Sersuv"), ("сочные", "sersuv"),
    ("Большой", "Katta"), ("большой", "katta"),
    ("Большая", "Katta"), ("большая", "katta"),
    ("Большое", "Katta"), ("большое", "katta"),
    ("Насыщенный", "Boy"), ("насыщенный", "boy"),
    ("Насыщенная", "Boy"), ("насыщенная", "boy"),
    ("Румяной", "oltinrang"), ("румяной", "oltinrang"),
    ("Хрустящей", "qarsildoq"), ("хрустящей", "qarsildoq"),
    ("Золотистой", "oltinrang"), ("золотистой", "oltinrang"),
    ("Сладостью", "shirinlik"), ("сладостью", "shirinlik"),
    ("Согревающей", "isituvchi"), ("согревающей", "isituvchi"),
    ("Вкусом", "ta’m bilan"), ("вкусом", "ta’m bilan"),
    ("Подачей", "taqdimot bilan"), ("подачей", "taqdimot bilan"),
    ("Ароматом", "hid bilan"), ("ароматом", "hid bilan"),
    ("Текстурой", "tekstura bilan"), ("текстурой", "tekstura bilan"),
    ("Начинкой", "ichlik bilan"), ("начинкой", "ichlik bilan"),
    ("Мясной", "go‘shtli"), ("мясной", "go‘shtli"),
    ("Мясом", "go‘sht bilan"), ("мясом", "go‘sht bilan"),
    ("Говядиной", "mol go‘shti bilan"), ("говядиной", "mol go‘shti bilan"),
    ("Бараниной", "qo‘y go‘shti bilan"), ("бараниной", "qo‘y go‘shti bilan"),
    ("Картофелем", "kartoshka bilan"), ("картофелем", "kartoshka bilan"),
    ("Картошкой", "kartoshka bilan"), ("картошкой", "kartoshka bilan"),
    ("Овощами", "sabzavotlar bilan"), ("овощами", "sabzavotlar bilan"),
    ("Ингредиентами", "masalliqlar bilan"), ("ингредиентами", "masalliqlar bilan"),
    ("Сливочным", "qaymoqli"), ("сливочным", "qaymoqli"),
    ("Шоколадом", "shokolad bilan"), ("шоколадом", "shokolad bilan"),
    ("Фруктами", "mevalar bilan"), ("фруктами", "mevalar bilan"),
    ("Имбирно", "Zanjabilli "), ("имбирно", "zanjabilli "),
    ("Марокканский", "Marokash"), ("марокканский", "marokash"),
    ("Тропический", "Tropik"), ("тропический", "tropik"),
    ("Турецкий", "Turk"), ("турецкий", "turk"),
    ("Жасминовый", "Yasmin"), ("жасминовый", "yasmin"),
    ("Бодрящий", "Tetiktiruvchi"), ("бодрящий", "tetiktiruvchi"),
    ("Необычный", "Noodatiy"), ("необычный", "noodatiy"),
    ("Прохладное", "Sovuq"), ("прохладное", "sovuq"),
    ("Прохладой", "sovuqlik"), ("прохладой", "sovuqlik"),
]

def auto_translate_desc_uz(item_name: str, desc_ru: str) -> str:
    if item_name in DESC_UZ_OVERRIDES:
        return DESC_UZ_OVERRIDES[item_name]

    text = desc_ru
    for ru_name, uz_name in sorted(ITEM_NAME_UZ.items(), key=lambda x: len(x[0]), reverse=True):
        text = text.replace(ru_name, uz_name)
    for src, dst in DESC_REPLACEMENTS:
        text = text.replace(src, dst)

    cleanup = {
        " и ": " va ",
        " с ": " bilan ",
        " со ": " bilan ",
        " для ": " uchun ",
        " из ": " ",
        "Из ": "",
        "  ": " ",
        " ,": ",",
    }
    for src, dst in cleanup.items():
        text = text.replace(src, dst)

    if not text.endswith("."):
        text += "."
    return text.strip()


def localize_item_name_by_lang(lang: str, item_name: str) -> str:
    if lang == "uz":
        return ITEM_NAME_UZ.get(item_name, item_name)
    return item_name


def localize_item_desc_by_lang(lang: str, item_name: str) -> str:
    desc = DESC_BY_ITEM.get(item_name, fallback_desc(item_name))
    if lang == "uz":
        return auto_translate_desc_uz(item_name, desc)
    return desc


def localize_item_name(user_id: int, item_name: str) -> str:
    return localize_item_name_by_lang(get_lang(user_id), item_name)


def public_order_code_from_id(order_id: int) -> str:
    code_num = ((order_id * 7919 + 1234) % 9999) + 1
    return f"{code_num:04d}"


async def assign_missing_order_codes():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute("SELECT id FROM orders WHERE order_code IS NULL OR order_code = '' ORDER BY id")).fetchall()
        for row in rows:
            order_id = int(row["id"])
            code = public_order_code_from_id(order_id)
            await db.execute("UPDATE orders SET order_code = ? WHERE id = ?", (code, order_id))
        await db.commit()


def _extract_order_code_from_obj(order_row_or_code) -> str:
    if isinstance(order_row_or_code, str):
        return order_row_or_code
    if isinstance(order_row_or_code, dict):
        code = order_row_or_code.get("order_code")
        if code:
            return str(code)
        return public_order_code_from_id(int(order_row_or_code["id"]))
    try:
        code = order_row_or_code["order_code"]
        if code:
            return str(code)
    except Exception:
        pass
    return public_order_code_from_id(int(order_row_or_code["id"]))


def client_order_code(order_row_or_code) -> str:
    return f"#{_extract_order_code_from_obj(order_row_or_code)}"


def admin_order_code(order_row_or_code) -> str:
    return f"DSTRXN#{_extract_order_code_from_obj(order_row_or_code)}"


def get_lang(user_id: int) -> str:
    return user_data.get(user_id, {}).get("lang", "ru")


def t(user_id: int, key: str, **kwargs) -> str:
    lang = get_lang(user_id)
    template = TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    return template.format(**kwargs)


def t_lang(lang: str, key: str, **kwargs) -> str:
    template = TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    return template.format(**kwargs)


def root_title(root_id: str, user_id: int) -> str:
    lang = get_lang(user_id)
    return ROOT_TITLES.get(root_id, {}).get(lang, MENU[root_id]["title"])


def localized_category_title(root_id: str, cat_id: str, user_id: int) -> str:
    lang = get_lang(user_id)
    return CATEGORY_TITLES.get(cat_id, {}).get(lang, MENU[root_id]["categories"][cat_id]["title"])


def is_delivery_value(user_id: int, value: str) -> bool:
    return value in {TEXTS["ru"]["delivery"], TEXTS["uz"]["delivery"]}


def is_cash_value(value: str) -> bool:
    return value in {TEXTS["ru"]["cash"], TEXTS["uz"]["cash"]}


def is_bank_transfer_value(value: str) -> bool:
    return value in {TEXTS["ru"]["bank_transfer"], TEXTS["uz"]["bank_transfer"]}


def get_language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇺🇿 O'zbekcha")],
        ],
        resize_keyboard=True,
    )


def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(user_id, "main_menu")),
                KeyboardButton(text=t(user_id, "desserts_menu")),
            ],
            [
                KeyboardButton(text=t(user_id, "cart")),
                KeyboardButton(text=t(user_id, "my_orders")),
            ],
            [KeyboardButton(text=t(user_id, "contact_admin"))],
        ],
        resize_keyboard=True,
    )


def get_delivery_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "delivery"))],
            [KeyboardButton(text=t(user_id, "pickup"))],
        ],
        resize_keyboard=True,
    )


def get_location_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "send_location"), request_location=True)],
            [KeyboardButton(text=t(user_id, "enter_address_text"))],
        ],
        resize_keyboard=True,
    )


def get_courier_note_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(user_id, "courier_note_skip"))]],
        resize_keyboard=True,
    )


def get_payment_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "cash"))],
            [KeyboardButton(text=t(user_id, "bank_transfer"))],
        ],
        resize_keyboard=True,
    )


def get_bank_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Shinhan Card")],
            [KeyboardButton(text="Toss Bank")],
            [KeyboardButton(text="Visa / Mastercard")],
        ],
        resize_keyboard=True,
    )


def get_confirm_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "confirm_yes"))],
            [KeyboardButton(text=t(user_id, "confirm_edit"))],
        ],
        resize_keyboard=True,
    )


def get_edit_order_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(user_id, "edit_name"))],
            [KeyboardButton(text=t(user_id, "edit_phone"))],
            [KeyboardButton(text=t(user_id, "edit_address"))],
            [KeyboardButton(text=t(user_id, "edit_delivery"))],
            [KeyboardButton(text=t(user_id, "edit_payment"))],
            [KeyboardButton(text=t(user_id, "back_to_confirm"))],
        ],
        resize_keyboard=True,
    )

BANK_OPTIONS = {
    "Shinhan Card": "0987654321",
    "Toss Bank": "0987654321",
    "Visa / Mastercard": "0987654321",
}

# =========================
# DB
# =========================

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                items_json TEXT NOT NULL,
                total INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                delivery_type TEXT NOT NULL,
                address TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'unpaid',
                bank_method TEXT,
                bank_account TEXT,
                check_status TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                channel_message_id INTEGER,
                order_code TEXT,
                lang TEXT,
                courier_note TEXT
            )
        """)
        columns = [row[1] for row in await (await db.execute("PRAGMA table_info(orders)")).fetchall()]
        if "order_code" not in columns:
            await db.execute("ALTER TABLE orders ADD COLUMN order_code TEXT")
        if "lang" not in columns:
            await db.execute("ALTER TABLE orders ADD COLUMN lang TEXT DEFAULT 'ru'")
        if "courier_note" not in columns:
            await db.execute("ALTER TABLE orders ADD COLUMN courier_note TEXT")
        await db.commit()

    await assign_missing_order_codes()



async def create_order_record(
    user_id: int,
    username: str | None,
    items_json: str,
    total: int,
    name: str,
    phone: str,
    delivery_type: str,
    address: str,
    payment_method: str,
    payment_status: str,
    bank_method: str | None,
    bank_account: str | None,
    check_status: str | None,
    status: str,
    created_at: str,
    lang: str,
    courier_note: str | None,
) -> tuple[int, str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO orders (
                user_id, username, items_json, total, name, phone,
                delivery_type, address, payment_method, payment_status,
                bank_method, bank_account, check_status, status, created_at, lang, courier_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                items_json,
                total,
                name,
                phone,
                delivery_type,
                address,
                payment_method,
                payment_status,
                bank_method,
                bank_account,
                check_status,
                status,
                created_at,
                lang,
                courier_note,
            ),
        )
        order_id = cursor.lastrowid
        order_code = public_order_code_from_id(order_id)
        await db.execute("UPDATE orders SET order_code = ? WHERE id = ?", (order_code, order_id))
        await db.commit()
        return order_id, order_code


async def set_channel_message_id(order_id: int, channel_message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET channel_message_id = ? WHERE id = ?",
            (channel_message_id, order_id),
        )
        await db.commit()


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
        await db.commit()


async def update_payment_status(order_id: int, payment_status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET payment_status = ? WHERE id = ?",
            (payment_status, order_id),
        )
        await db.commit()


async def update_order_bank_info(order_id: int, bank_method: str, bank_account: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET bank_method = ?, bank_account = ? WHERE id = ?",
            (bank_method, bank_account, order_id),
        )
        await db.commit()


async def update_order_check_status(order_id: int, check_status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET check_status = ? WHERE id = ?",
            (check_status, order_id),
        )
        await db.commit()


async def get_order(order_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()


async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, order_code, total, status, payment_status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_orders_for_stats(start_date: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT id, items_json, total, payment_status, status, created_at
            FROM orders
            WHERE status != 'cancelled'
        """
        params = []
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        query += " ORDER BY id DESC"
        cursor = await db.execute(query, tuple(params))
        return await cursor.fetchall()


def _period_start(period: str) -> str | None:
    now = datetime.now()
    if period == 'day':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start = now - timedelta(days=7)
    elif period == 'month':
        start = now - timedelta(days=30)
    elif period == 'alltime':
        return None
    else:
        raise ValueError(f'Unknown period: {period}')
    return start.strftime('%Y-%m-%d %H:%M:%S')


async def build_revenue_stats_text(period: str) -> str:
    labels = {
        'day': 'сегодня',
        'week': 'последние 7 дней',
        'month': 'последние 30 дней',
        'alltime': 'всё время',
    }
    rows = await get_orders_for_stats(_period_start(period))
    total_revenue = sum(int(row['total'] or 0) for row in rows)
    orders_count = len(rows)
    paid_count = sum(1 for row in rows if row['payment_status'] == 'paid')
    unpaid_count = orders_count - paid_count

    return (
        f"📊 Касса за {labels[period]}\n\n"
        f"💰 Выручка: {total_revenue:,} ₩\n"
        f"📦 Заказов: {orders_count}\n"
        f"✅ Оплачено: {paid_count}\n"
        f"⏳ Не оплачено: {unpaid_count}"
    )


async def build_topmenu_text(limit: int = 10) -> str:
    rows = await get_orders_for_stats()
    totals: dict[str, int] = {}

    for row in rows:
        try:
            items = json.loads(row['items_json'])
        except Exception:
            continue
        for item_name, qty in items.items():
            try:
                qty_int = int(qty)
            except Exception:
                qty_int = 0
            totals[item_name] = totals.get(item_name, 0) + qty_int

    if not totals:
        return '📭 Пока нет данных по заказам.'

    sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
    text = '🔥 Топ блюд\n\n'
    for i, (item_name, qty) in enumerate(sorted_items, start=1):
        text += f'{i}. {item_name} — {qty} шт\n'
    return text


def is_admin_channel_message(message: Message) -> bool:
    return message.chat.id == ADMIN_CHAT_ID

# =========================
# HELPERS
# =========================
def status_title(status_key: str) -> str:
    mapping = {
        "accept": "Заказ принят",
        "cooking": "Готовится",
        "delivery": "Курьер выехал",
        "done": "Заказ завершён",
        "cancelled": "Отменён",
    }
    return mapping.get(status_key, status_key)


def payment_status_title(payment_status: str) -> str:
    mapping = {
        "unpaid": "Не оплачен",
        "paid": "Оплачен",
    }
    return mapping.get(payment_status, payment_status)


def status_title_localized(user_id: int, status_key: str) -> str:
    if get_lang(user_id) == "uz":
        mapping = {
            "accept": "Buyurtma qabul qilindi",
            "cooking": "Tayyorlanmoqda",
            "delivery": "Kuryer yo‘lga chiqdi",
            "done": "Buyurtma yakunlandi",
            "cancelled": "Bekor qilindi",
        }
        return mapping.get(status_key, status_key)
    return status_title(status_key)


def payment_status_title_localized(user_id: int, payment_status: str) -> str:
    if get_lang(user_id) == "uz":
        mapping = {
            "unpaid": "To‘lanmagan",
            "paid": "To‘langan",
        }
        return mapping.get(payment_status, payment_status)
    return payment_status_title(payment_status)


def get_order_lang(order) -> str:
    try:
        lang = order["lang"]
        if lang in TEXTS:
            return lang
    except Exception:
        pass
    return "ru"


def is_closed_status(status: str) -> bool:
    return status in ["cancelled", "done"]


def calculate_total(user_id: int) -> int:
    cart = user_carts.get(user_id, {})
    total = 0
    for item_name, qty in cart.items():
        total += ITEM_PRICES.get(item_name, 0) * qty
    return total


def reset_order_state(user_id: int):
    user_states[user_id] = None
    current = user_data.get(user_id, {})
    lang = current.get("lang", "ru")
    user_data[user_id] = {"lang": lang}



def find_item(root_id: str, cat_id: str, item_idx: int, user_id: int | None = None) -> dict:
    item_name, price = MENU[root_id]["categories"][cat_id]["items"][item_idx]
    lang = get_lang(user_id) if user_id is not None else "ru"
    return {
        "name_key": item_name,
        "name": localize_item_name_by_lang(lang, item_name),
        "price": price,
        "desc": localize_item_desc_by_lang(lang, item_name),
        "photo": PHOTO_BY_ITEM.get(item_name),
    }


async def delete_last_prompt(message: Message, user_id: int):
    old_message_id = last_prompt_messages.get(user_id)
    if old_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=old_message_id,
            )
        except Exception:
            pass


async def send_clean_prompt(message: Message, user_id: int, text: str, reply_markup=None, parse_mode=None):
    await delete_last_prompt(message, user_id)
    sent = await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    last_prompt_messages[user_id] = sent.message_id


async def load_photo_file_ids():
    global PHOTO_FILE_IDS
    if PHOTO_CACHE_FILE.exists():
        try:
            PHOTO_FILE_IDS = json.loads(PHOTO_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            PHOTO_FILE_IDS = {}


async def save_photo_file_ids():
    async with photo_cache_lock:
        PHOTO_CACHE_FILE.write_text(
            json.dumps(PHOTO_FILE_IDS, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def get_root_categories_keyboard(root_id: str, user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for cat_id in MENU[root_id]["categories"].keys():
        keyboard.append([
            InlineKeyboardButton(
                text=localized_category_title(root_id, cat_id, user_id),
                callback_data=f"cat:{root_id}:{cat_id}:0"
            )
        ])
    keyboard.append([InlineKeyboardButton(text=t(user_id, "back_to_menu"), callback_data="mainmenu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_items_page(root_id: str, cat_id: str, page: int):
    items = MENU[root_id]["categories"][cat_id]["items"]
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end]


def get_category_page_keyboard(root_id: str, cat_id: str, page: int, user_id: int) -> InlineKeyboardMarkup:
    items = MENU[root_id]["categories"][cat_id]["items"]
    page_items = get_items_page(root_id, cat_id, page)
    keyboard = []

    start_idx = page * ITEMS_PER_PAGE

    for i, (item_name, price) in enumerate(page_items):
        item_idx = start_idx + i
        keyboard.append([
            InlineKeyboardButton(
                text=f"{localize_item_name(user_id, item_name)} — {price} ₩",
                callback_data=f"dish:{root_id}:{cat_id}:{page}:{item_idx}"
            )
        ])

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"cat:{root_id}:{cat_id}:{page-1}"
            )
        )

    nav.append(
        InlineKeyboardButton(
            text=t(user_id, "categories"),
            callback_data=f"root:{root_id}"
        )
    )

    if (page + 1) * ITEMS_PER_PAGE < len(items):
        nav.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"cat:{root_id}:{cat_id}:{page+1}"
            )
        )

    keyboard.append(nav)
    keyboard.append([InlineKeyboardButton(text=t(user_id, "back_to_menu"), callback_data="mainmenu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_dish_card_keyboard(
    root_id: str,
    cat_id: str,
    page: int,
    item_idx: int,
    qty: int,
    user_id: int,
) -> InlineKeyboardMarkup:
    back_text = "⬅️ Назад" if get_lang(user_id) == "ru" else "⬅️ Orqaga"
    add_to_cart_text = "🛒 Добавить в корзину" if get_lang(user_id) == "ru" else "🛒 Savatga qo'shish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➖",
                    callback_data=f"dishqty:minus:{root_id}:{cat_id}:{page}:{item_idx}:{qty}"
                ),
                InlineKeyboardButton(text=str(qty), callback_data="dishnoop"),
                InlineKeyboardButton(
                    text="➕",
                    callback_data=f"dishqty:plus:{root_id}:{cat_id}:{page}:{item_idx}:{qty}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=add_to_cart_text,
                    callback_data=f"dishadd:{root_id}:{cat_id}:{page}:{item_idx}:{qty}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=back_text,
                    callback_data=f"dishback:{root_id}:{cat_id}:{page}"
                )
            ],
        ]
    )


async def send_dish_card(target_message: Message, root_id: str, cat_id: str, page: int, item_idx: int, qty: int, user_id: int):
    dish = find_item(root_id, cat_id, item_idx, user_id)
    price_label = "Narxi" if get_lang(user_id) == "uz" else "Цена"
    caption = (
        f"🍽 <b>{dish['name']}</b>\n\n"
        f"💬 {dish['desc']}\n\n"
        f"💰 {price_label}: {dish['price']} ₩"
    )
    keyboard = get_dish_card_keyboard(root_id, cat_id, page, item_idx, qty, user_id)

    photo_path = dish.get("photo")
    if not photo_path:
        await target_message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    cached_file_id = PHOTO_FILE_IDS.get(photo_path)
    if cached_file_id:
        await target_message.answer_photo(
            photo=cached_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    sent = await target_message.answer_photo(
        photo=FSInputFile(photo_path),
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    if sent.photo:
        PHOTO_FILE_IDS[photo_path] = sent.photo[-1].file_id
        await save_photo_file_ids()



def get_cart_message_and_keyboard(user_id: int):
    cart = user_carts.get(user_id, {})

    if not cart:
        text = t(user_id, "cart_empty")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t(user_id, "back_to_menu"), callback_data="cartmenu")]]
        )
        return text, keyboard

    text = t(user_id, "your_cart")
    total = 0
    keyboard = []

    for item_name, qty in cart.items():
        price = ITEM_PRICES.get(item_name, 0)
        item_total = price * qty
        total += item_total
        item_idx = ITEM_INDEX[item_name]
        display_name = localize_item_name(user_id, item_name)

        text += f"{display_name} x{qty} — {item_total} ₩\n"

        keyboard.append([
            InlineKeyboardButton(text=f"{display_name} x{qty}", callback_data="cartnoop")
        ])
        keyboard.append([
            InlineKeyboardButton(text="➖", callback_data=f"cartminus:{item_idx}"),
            InlineKeyboardButton(text="➕", callback_data=f"cartplus:{item_idx}"),
            InlineKeyboardButton(text="❌", callback_data=f"cartremove:{item_idx}"),
        ])

    text += f"\n{t(user_id, 'total')}: {total} ₩"

    keyboard.append([InlineKeyboardButton(text=t(user_id, "checkout"), callback_data="cartcheckout")])
    keyboard.append([InlineKeyboardButton(text=t(user_id, "clear_cart"), callback_data="cartclear")])
    keyboard.append([InlineKeyboardButton(text=t(user_id, "back_to_menu"), callback_data="cartmenu")])

    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)



def build_order_summary(user_id: int) -> str:
    cart = user_carts.get(user_id, {})
    data = user_data.get(user_id, {})
    total = calculate_total(user_id)

    text = t(user_id, "check_order")
    for item_name, qty in cart.items():
        item_total = ITEM_PRICES.get(item_name, 0) * qty
        text += f"{localize_item_name(user_id, item_name)} x{qty} — {item_total} ₩\n"

    text += f"\n{t(user_id, 'total')}: {total} ₩"
    text += f"\n\n{t(user_id, 'name_label')}: {data.get('name', '-')}"
    text += f"\n{t(user_id, 'phone_label')}: {data.get('phone', '-')}"
    text += f"\n{t(user_id, 'delivery_label')}: {data.get('delivery_type', '-')}"

    if is_delivery_value(user_id, data.get("delivery_type", "")):
        text += f"\n{t(user_id, 'address_label')}: {data.get('address', '-')}"
        text += f"\n{t(user_id, 'courier_note_label')}: {data.get('courier_note', t(user_id, 'courier_note_empty'))}"

    text += f"\n{t(user_id, 'payment_label')}: {data.get('payment_method', '-')}"
    text += f"\n\n{t(user_id, 'all_correct')}"
    return text



def build_channel_order_text_from_row(order_row) -> str:
    items = json.loads(order_row["items_json"])
    text = f"🆔 {admin_order_code(order_row)}\n📦 Новый заказ:\n\n"

    for item_name, qty in items.items():
        item_total = ITEM_PRICES.get(item_name, 0) * qty
        text += f"{item_name} x{qty} — {item_total} ₩\n"

    text += f"\n💰 Итого: {order_row['total']} ₩"
    text += f"\n\n👤 Имя: {order_row['name']}"
    text += f"\n📞 Телефон: {order_row['phone']}"
    text += f"\n🚚 Способ получения: {order_row['delivery_type']}"

    if order_row["delivery_type"] in {TEXTS['ru']['delivery'], TEXTS['uz']['delivery']}:
        text += f"\n📍 Адрес: {order_row['address']}"
        text += f"\n📝 Комментарий курьеру: {order_row['courier_note'] or '-'}"

    text += f"\n💳 Метод оплаты: {order_row['payment_method']}"
    text += f"\n💰 Статус оплаты: {'✅ Оплачен' if order_row['payment_status'] == 'paid' else '⏳ Не оплачен'}"
    text += f"\n📌 Статус заказа: {status_title(order_row['status'])}"

    if order_row["payment_method"] in {TEXTS['ru']['bank_transfer'], TEXTS['uz']['bank_transfer']}:
        text += f"\n🏦 Банк: {order_row['bank_method'] or '-'}"
        text += f"\n🔢 Счёт: {order_row['bank_account'] or '-'}"
        text += f"\n🧾 Чек: {order_row['check_status'] or 'ожидается проверка'}"

    if order_row["username"]:
        text += f"\n\n🆔 Telegram: @{order_row['username']}"

    return text


def get_admin_order_keyboard(order) -> InlineKeyboardMarkup:
    current_status = order["status"]
    payment_status = order["payment_status"]
    pay_icon = "✅" if payment_status == "paid" else "💰"

    if current_status == "cancelled":
        keyboard = [
            [InlineKeyboardButton(text=f"{pay_icon} Оплачен", callback_data="locked")],
            [InlineKeyboardButton(text="⛔ Заказ принят", callback_data="locked")],
            [InlineKeyboardButton(text="⛔ Готовится", callback_data="locked")],
            [InlineKeyboardButton(text="⛔ Курьер выехал", callback_data="locked")],
            [InlineKeyboardButton(text="⛔ Заказ завершён", callback_data="locked")],
            [InlineKeyboardButton(text="✅ Заказ отменён", callback_data="locked")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    if current_status == "done":
        keyboard = [
            [InlineKeyboardButton(text=f"{pay_icon} Оплачен", callback_data="locked")],
            [InlineKeyboardButton(text="✅ Заказ принят", callback_data="locked")],
            [InlineKeyboardButton(text="✅ Готовится", callback_data="locked")],
            [InlineKeyboardButton(text="✅ Курьер выехал", callback_data="locked")],
            [InlineKeyboardButton(text="✅ Заказ завершён", callback_data="locked")],
            [InlineKeyboardButton(text="⛔ Отменить заказ", callback_data="locked")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    status_flow = ["accept", "cooking", "delivery", "done"]
    current_index = status_flow.index(current_status) if current_status in status_flow else 0

    labels = {
        "accept": "Заказ принят",
        "cooking": "Готовится",
        "delivery": "Курьер выехал",
        "done": "Заказ завершён",
    }

    keyboard = [
        [InlineKeyboardButton(text=f"{pay_icon} Оплачен", callback_data=f"pay:{order['id']}:{order['user_id']}")]
    ]

    for i, key in enumerate(status_flow):
        icon = "✅" if i <= current_index else "⏳"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} {labels[key]}",
                callback_data=f"status:{order['id']}:{order['user_id']}:{key}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="❌ Отменить заказ",
            callback_data=f"cancel:{order['id']}:{order['user_id']}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def refresh_channel_order_message(bot: Bot, order_id: int):
    order = await get_order(order_id)
    if not order or not order["channel_message_id"]:
        return

    await bot.edit_message_text(
        chat_id=ADMIN_CHAT_ID,
        message_id=order["channel_message_id"],
        text=build_channel_order_text_from_row(order),
        reply_markup=get_admin_order_keyboard(order),
    )

# =========================
# MESSAGE HANDLERS
# =========================
@router.channel_post(Command("topmenu"))
async def topmenu_command(message: Message):
    if not is_admin_channel_message(message):
        return
    await message.answer(await build_topmenu_text())


@router.channel_post(Command("day"))
async def day_command(message: Message):
    if not is_admin_channel_message(message):
        return
    await message.answer(await build_revenue_stats_text("day"))


@router.channel_post(Command("week"))
async def week_command(message: Message):
    if not is_admin_channel_message(message):
        return
    await message.answer(await build_revenue_stats_text("week"))


@router.channel_post(Command("month"))
async def month_command(message: Message):
    if not is_admin_channel_message(message):
        return
    await message.answer(await build_revenue_stats_text("month"))


@router.channel_post(Command("alltime"))
async def alltime_command(message: Message):
    if not is_admin_channel_message(message):
        return
    await message.answer(await build_revenue_stats_text("alltime"))


@router.channel_post(Command("stats"))
async def stats_command(message: Message):
    if not is_admin_channel_message(message):
        return

    day_text = await build_revenue_stats_text("day")
    week_text = await build_revenue_stats_text("week")
    month_text = await build_revenue_stats_text("month")
    alltime_text = await build_revenue_stats_text("alltime")

    await message.answer(
        f"{day_text}\n\n"
        f"{week_text}\n\n"
        f"{month_text}\n\n"
        f"{alltime_text}"
    )


@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    user_carts[user_id] = {}
    current_lang = user_data.get(user_id, {}).get("lang", "ru")
    user_data[user_id] = {"lang": current_lang}
    user_states[user_id] = "choose_language"
    await message.answer(t(user_id, "choose_language"), reply_markup=get_language_keyboard())

@router.message()
async def handle_buttons(message: Message):
    user_id = message.from_user.id
    text = message.text or ""

    user_carts.setdefault(user_id, {})
    user_states.setdefault(user_id, None)
    user_data.setdefault(user_id, {})
    user_data[user_id].setdefault("lang", "ru")

    if user_states[user_id] == "choose_language":
        if text == "🇷🇺 Русский":
            user_data[user_id]["lang"] = "ru"
            user_states[user_id] = None
            await message.answer(t(user_id, "welcome"), reply_markup=get_main_keyboard(user_id))
            return

        if text == "🇺🇿 O'zbekcha":
            user_data[user_id]["lang"] = "uz"
            user_states[user_id] = None
            await message.answer(t(user_id, "welcome"), reply_markup=get_main_keyboard(user_id))
            return

        await message.answer(t(user_id, "choose_language_again"), reply_markup=get_language_keyboard())
        return

    if user_states[user_id] in ["address", "edit_address"] and message.location:
        user_data[user_id]["address"] = f"{t(user_id, 'location_prefix')}: {message.location.latitude}, {message.location.longitude}"

        if user_states[user_id] == "edit_address":
            user_states[user_id] = "confirm"
            await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        else:
            user_states[user_id] = "courier_note"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "courier_note_prompt"),
                reply_markup=get_courier_note_keyboard(user_id),
                parse_mode="HTML",
            )
        return

    if user_states[user_id] == "receipt" and (message.document or message.photo):
        order_id = user_data[user_id].get("order_id")
        order_code = user_data[user_id].get("order_code") or public_order_code_from_id(order_id)
        order_channel_message_id = user_data[user_id].get("order_channel_message_id")

        await delete_last_prompt(message, user_id)

        if order_channel_message_id:
            if message.document:
                await message.bot.send_document(
                    chat_id=ADMIN_CHAT_ID,
                    document=message.document.file_id,
                    caption=f"🧾 Чек оплаты по заказу DSTRXN#{order_code}",
                    reply_to_message_id=order_channel_message_id,
                )
            else:
                await message.bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=message.photo[-1].file_id,
                    caption=f"🧾 Чек оплаты по заказу DSTRXN#{order_code}",
                    reply_to_message_id=order_channel_message_id,
                )

        try:
            await message.delete()
        except Exception:
            pass

        await message.answer(t(user_id, "receipt_sent"), reply_markup=get_main_keyboard(user_id))
        user_carts[user_id] = {}
        reset_order_state(user_id)
        return

    if user_states[user_id] == "receipt":
        await send_clean_prompt(
            message,
            user_id,
            t(user_id, "receipt_request"),
            reply_markup=get_main_keyboard(user_id),
        )
        return

    if user_states[user_id] == "name":
        user_data[user_id]["name"] = text
        user_states[user_id] = "phone"
        await send_clean_prompt(message, user_id, t(user_id, "enter_phone_prompt"))
        return

    if user_states[user_id] == "phone":
        user_data[user_id]["phone"] = text
        user_states[user_id] = "delivery_type"
        await send_clean_prompt(message, user_id, t(user_id, "choose_delivery_prompt"), reply_markup=get_delivery_keyboard(user_id))
        return

    if user_states[user_id] == "delivery_type":
        if text not in [t(user_id, "delivery"), t(user_id, "pickup")]:
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_delivery_invalid"),
                reply_markup=get_delivery_keyboard(user_id),
            )
            return

        user_data[user_id]["delivery_type"] = text

        if text == t(user_id, "delivery"):
            user_states[user_id] = "address"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "send_address_prompt"),
                reply_markup=get_location_keyboard(user_id),
            )
        else:
            user_data[user_id]["address"] = t(user_id, "pickup_address")
            user_states[user_id] = "payment"
            await send_clean_prompt(message, user_id, t(user_id, "choose_payment_prompt"), reply_markup=get_payment_keyboard(user_id))
        return

    if user_states[user_id] == "address":
        if text == t(user_id, "enter_address_text"):
            prompt_key = "enter_address_prompt"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, prompt_key),
                reply_markup=get_location_keyboard(user_id),
            )
            return

        user_data[user_id]["address"] = text
        user_states[user_id] = "courier_note"
        await send_clean_prompt(
            message,
            user_id,
            t(user_id, "courier_note_prompt"),
            reply_markup=get_courier_note_keyboard(user_id),
            parse_mode="HTML",
        )
        return

    if user_states[user_id] == "courier_note":
        if text == t(user_id, "courier_note_skip"):
            user_data[user_id]["courier_note"] = t(user_id, "courier_note_empty")
        else:
            note = (text or "").strip()
            user_data[user_id]["courier_note"] = note or t(user_id, "courier_note_empty")

        user_states[user_id] = "payment"
        await send_clean_prompt(message, user_id, t(user_id, "choose_payment_prompt"), reply_markup=get_payment_keyboard(user_id))
        return

    if user_states[user_id] == "payment":
        if text not in [t(user_id, "cash"), t(user_id, "bank_transfer")]:
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_payment_invalid"),
                reply_markup=get_payment_keyboard(user_id),
            )
            return

        user_data[user_id]["payment_method"] = text
        if is_cash_value(text):
            user_data[user_id]["bank_method"] = None
            user_data[user_id]["bank_account"] = None

        user_states[user_id] = "confirm"
        await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        return

    if user_states[user_id] == "edit_menu":
        if text == t(user_id, "edit_name"):
            user_states[user_id] = "edit_name"
            await send_clean_prompt(message, user_id, t(user_id, "enter_new_name"))
            return

        if text == t(user_id, "edit_phone"):
            user_states[user_id] = "edit_phone"
            await send_clean_prompt(message, user_id, t(user_id, "enter_new_phone"))
            return

        if text == t(user_id, "edit_address"):
            if not is_delivery_value(user_id, user_data[user_id].get("delivery_type", "")):
                await send_clean_prompt(
                    message,
                    user_id,
                    t(user_id, "address_only_delivery"),
                    reply_markup=get_edit_order_keyboard(user_id),
                )
                return

            user_states[user_id] = "edit_address"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "send_new_address"),
                reply_markup=get_location_keyboard(user_id),
            )
            return

        if text == t(user_id, "edit_delivery"):
            user_states[user_id] = "edit_delivery_type"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_new_delivery"),
                reply_markup=get_delivery_keyboard(user_id),
            )
            return

        if text == t(user_id, "edit_payment"):
            user_states[user_id] = "edit_payment_method"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_new_payment"),
                reply_markup=get_payment_keyboard(user_id),
            )
            return

        if text == t(user_id, "back_to_confirm"):
            user_states[user_id] = "confirm"
            await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
            return

        await send_clean_prompt(
            message,
            user_id,
            t(user_id, "edit_choose"),
            reply_markup=get_edit_order_keyboard(user_id),
        )
        return

    if user_states[user_id] == "edit_name":
        user_data[user_id]["name"] = text
        user_states[user_id] = "confirm"
        await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        return

    if user_states[user_id] == "edit_phone":
        user_data[user_id]["phone"] = text
        user_states[user_id] = "confirm"
        await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        return

    if user_states[user_id] == "edit_address":
        if text == t(user_id, "enter_address_text"):
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "enter_address_prompt"),
                reply_markup=get_location_keyboard(user_id),
            )
            return

        user_data[user_id]["address"] = text
        user_states[user_id] = "confirm"
        await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        return

    if user_states[user_id] == "edit_delivery_type":
        if text not in [t(user_id, "delivery"), t(user_id, "pickup")]:
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_delivery_invalid"),
                reply_markup=get_delivery_keyboard(user_id),
            )
            return

        user_data[user_id]["delivery_type"] = text

        if text == t(user_id, "delivery"):
            user_states[user_id] = "edit_address"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "send_new_address"),
                reply_markup=get_location_keyboard(user_id),
            )
        else:
            user_data[user_id]["address"] = t(user_id, "pickup_address")
            user_states[user_id] = "confirm"
            await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        return

    if user_states[user_id] == "edit_payment_method":
        if text not in [t(user_id, "cash"), t(user_id, "bank_transfer")]:
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_payment_invalid"),
                reply_markup=get_payment_keyboard(user_id),
            )
            return

        user_data[user_id]["payment_method"] = text
        if is_cash_value(text):
            user_data[user_id]["bank_method"] = None
            user_data[user_id]["bank_account"] = None

        user_states[user_id] = "confirm"
        await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        return

    if user_states[user_id] == "bank_method":
        selected_bank = text.strip()

        if selected_bank not in BANK_OPTIONS:
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_bank_invalid"),
                reply_markup=get_bank_keyboard(user_id),
            )
            return

        user_data[user_id]["bank_method"] = selected_bank
        user_data[user_id]["bank_account"] = BANK_OPTIONS[selected_bank]

        order_id = user_data[user_id]["order_id"]
        await update_order_bank_info(order_id, selected_bank, BANK_OPTIONS[selected_bank])
        await refresh_channel_order_message(message.bot, order_id)

        user_states[user_id] = "receipt"
        await send_clean_prompt(
            message,
            user_id,
            t(
                user_id,
                "bank_pay_instructions",
                bank=selected_bank,
                account=BANK_OPTIONS[selected_bank],
            ),
            reply_markup=get_main_keyboard(user_id),
        )
        return

    if user_states[user_id] == "confirm":
        if text == t(user_id, "confirm_edit"):
            user_states[user_id] = "edit_menu"
            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "edit_what"),
                reply_markup=get_edit_order_keyboard(user_id),
            )
            return

        if text == t(user_id, "confirm_yes"):
            await delete_last_prompt(message, user_id)

            total = calculate_total(user_id)
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = message.from_user.username
            payment_method = user_data[user_id].get("payment_method", "-")

            payment_status = "unpaid"
            status = "accept"
            check_status = "Не требуется" if is_cash_value(payment_method) else "⏳ Ожидается проверка"

            order_id, order_code = await create_order_record(
                user_id=user_id,
                username=username,
                items_json=json.dumps(user_carts[user_id], ensure_ascii=False),
                total=total,
                name=user_data[user_id].get("name", "-"),
                phone=user_data[user_id].get("phone", "-"),
                delivery_type=user_data[user_id].get("delivery_type", "-"),
                address=user_data[user_id].get("address", "-"),
                payment_method=payment_method,
                payment_status=payment_status,
                bank_method=user_data[user_id].get("bank_method"),
                bank_account=user_data[user_id].get("bank_account"),
                check_status=check_status,
                status=status,
                created_at=created_at,
                lang=get_lang(user_id),
                courier_note=user_data[user_id].get("courier_note", t(user_id, "courier_note_empty")),
            )

            order_preview = {
                "id": order_id,
                "user_id": user_id,
                "username": username,
                "items_json": json.dumps(user_carts[user_id], ensure_ascii=False),
                "total": total,
                "name": user_data[user_id].get("name", "-"),
                "phone": user_data[user_id].get("phone", "-"),
                "delivery_type": user_data[user_id].get("delivery_type", "-"),
                "address": user_data[user_id].get("address", "-"),
                "payment_method": payment_method,
                "payment_status": payment_status,
                "bank_method": user_data[user_id].get("bank_method"),
                "bank_account": user_data[user_id].get("bank_account"),
                "check_status": check_status,
                "status": status,
                "order_code": order_code,
                "lang": get_lang(user_id),
                "courier_note": user_data[user_id].get("courier_note", t(user_id, "courier_note_empty")),
            }

            channel_message = await message.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=build_channel_order_text_from_row(order_preview),
            )

            await set_channel_message_id(order_id, channel_message.message_id)
            await refresh_channel_order_message(message.bot, order_id)

            if is_cash_value(payment_method):
                await message.answer(t(user_id, "order_done", order_code=client_order_code(order_code)), reply_markup=get_main_keyboard(user_id))
                user_carts[user_id] = {}
                reset_order_state(user_id)
                return

            user_data[user_id]["order_id"] = order_id
            user_data[user_id]["order_code"] = order_code
            user_data[user_id]["order_channel_message_id"] = channel_message.message_id
            user_states[user_id] = "bank_method"

            await send_clean_prompt(
                message,
                user_id,
                t(user_id, "choose_bank_prompt"),
                reply_markup=get_bank_keyboard(user_id),
            )
            return

        await send_clean_prompt(message, user_id, build_order_summary(user_id), reply_markup=get_confirm_keyboard(user_id))
        return

    if text == t(user_id, "main_menu"):
        await message.answer(t(user_id, "choose_category"), reply_markup=get_root_categories_keyboard("main", user_id))
        return

    if text == t(user_id, "desserts_menu"):
        await message.answer(t(user_id, "choose_category"), reply_markup=get_root_categories_keyboard("desserts", user_id))
        return

    
    if text == t(user_id, "contact_admin"):
        admin_url = "https://t.me/abdurahmonov_bobur"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t(user_id, "contact_admin_button"), url=admin_url)]]
        )
        await message.answer(t(user_id, "contact_admin_text"), reply_markup=kb, parse_mode="HTML")
        return

    if text == t(user_id, "my_orders"):
        orders = await get_user_orders(user_id)

        if not orders:
            await message.answer(t(user_id, "history_empty"), reply_markup=get_main_keyboard(user_id))
            return

        result = t(user_id, "your_orders")
        for order_id, order_code, total, status, payment_status, created_at in orders:
            public_code = client_order_code(order_code or public_order_code_from_id(order_id))
            if get_lang(user_id) == "uz":
                result += (
                    f"🆔 Buyurtma {public_code}\n"
                    f"📅 {created_at}\n"
                    f"💰 {total} ₩\n"
                    f"📌 Buyurtma holati: {status_title_localized(user_id, status)}\n"
                    f"💳 To‘lov holati: {payment_status_title_localized(user_id, payment_status)}\n\n"
                )
            else:
                result += (
                    f"🆔 Заказ {public_code}\n"
                    f"📅 {created_at}\n"
                    f"💰 {total} ₩\n"
                    f"📌 Статус заказа: {status_title_localized(user_id, status)}\n"
                    f"💳 Статус оплаты: {payment_status_title_localized(user_id, payment_status)}\n\n"
                )

        await message.answer(result, reply_markup=get_main_keyboard(user_id))
        return

    if text == t(user_id, "cart"):
        cart_text, cart_inline = get_cart_message_and_keyboard(user_id)
        await message.answer(cart_text, reply_markup=cart_inline)
        return

    await message.answer(t(user_id, "choose_button"), reply_markup=get_main_keyboard(user_id))

# =========================
# CALLBACKS
# =========================
@router.callback_query()
async def handle_callbacks(callback: CallbackQuery):
    data = callback.data or ""

    if data == "locked":
        await callback.answer("Этот заказ уже закрыт")
        return

    if data == "dishnoop":
        await callback.answer()
        return

    if data == "mainmenu":
        await callback.message.answer(t(callback.from_user.id, "main_menu_prompt"), reply_markup=get_main_keyboard(callback.from_user.id))
        await callback.answer()
        return

    if data.startswith("root:"):
        _, root_id = data.split(":")
        await callback.message.edit_text(
            t(callback.from_user.id, "choose_category"),
            reply_markup=get_root_categories_keyboard(root_id, callback.from_user.id),
        )
        await callback.answer()
        return

    if data.startswith("cat:"):
        _, root_id, cat_id, page_str = data.split(":")
        page = int(page_str)
        category_title = localized_category_title(root_id, cat_id, callback.from_user.id)

        await callback.message.edit_text(
            category_title,
            reply_markup=get_category_page_keyboard(root_id, cat_id, page, callback.from_user.id),
        )
        await callback.answer()
        return

    if data.startswith("dish:"):
        _, root_id, cat_id, page_str, item_idx_str = data.split(":")
        page = int(page_str)
        item_idx = int(item_idx_str)

        try:
            await callback.message.delete()
        except Exception:
            pass

        await send_dish_card(callback.message, root_id, cat_id, page, item_idx, 1, callback.from_user.id)
        await callback.answer()
        return

    if data.startswith("dishqty:"):
        _, action, root_id, cat_id, page_str, item_idx_str, qty_str = data.split(":")
        page = int(page_str)
        item_idx = int(item_idx_str)
        qty = int(qty_str)

        if action == "plus":
            qty += 1
        elif action == "minus" and qty > 1:
            qty -= 1

        dish = find_item(root_id, cat_id, item_idx, callback.from_user.id)
        price_label = "Narxi" if get_lang(callback.from_user.id) == "uz" else "Цена"
        caption = (
            f"🍽 <b>{dish['name']}</b>\n\n"
            f"💬 {dish['desc']}\n\n"
            f"💰 {price_label}: {dish['price']} ₩"
        )
        keyboard = get_dish_card_keyboard(root_id, cat_id, page, item_idx, qty, callback.from_user.id)

        if callback.message.photo:
            try:
                await callback.message.edit_caption(
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception:
                pass
        else:
            try:
                await callback.message.edit_text(
                    caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception:
                pass

        await callback.answer()
        return

    if data.startswith("dishadd:"):
        _, root_id, cat_id, page_str, item_idx_str, qty_str = data.split(":")
        item_idx = int(item_idx_str)
        qty = int(qty_str)
        user_id = callback.from_user.id

        dish = find_item(root_id, cat_id, item_idx, user_id)
        user_carts.setdefault(user_id, {})
        item_key = dish["name_key"]
        user_carts[user_id][item_key] = user_carts[user_id].get(item_key, 0) + qty

        await callback.answer(f"{dish['name']} x{qty}", show_alert=True)
        return

    if data.startswith("dishback:"):
        _, root_id, cat_id, page_str = data.split(":")
        page = int(page_str)

        try:
            await callback.message.delete()
        except Exception:
            pass

        await callback.message.answer(
            localized_category_title(root_id, cat_id, callback.from_user.id),
            reply_markup=get_category_page_keyboard(root_id, cat_id, page, callback.from_user.id),
        )
        await callback.answer()
        return

    if data == "cartnoop":
        await callback.answer()
        return

    if data == "cartclear":
        user_id = callback.from_user.id
        user_carts[user_id] = {}
        cart_text, cart_inline = get_cart_message_and_keyboard(user_id)
        await callback.message.edit_text(cart_text, reply_markup=cart_inline)
        await callback.answer(t(user_id, "cart_cleared"))
        return

    if data == "cartmenu":
        await callback.message.answer(t(callback.from_user.id, "main_menu_prompt"), reply_markup=get_main_keyboard(callback.from_user.id))
        await callback.answer()
        return

    if data == "cartcheckout":
        user_id = callback.from_user.id

        if not user_carts.get(user_id):
            cart_text, cart_inline = get_cart_message_and_keyboard(user_id)
            await callback.message.edit_text(cart_text, reply_markup=cart_inline)
            await callback.answer(t(user_id, "cart_empty_alert"))
            return

        user_states[user_id] = "name"
        lang = user_data.get(user_id, {}).get("lang", "ru")
        user_data[user_id] = {"lang": lang}

        await callback.message.edit_text(t(user_id, "checkout_start"))
        await send_clean_prompt(callback.message, user_id, t(user_id, "enter_name_prompt"))
        await callback.answer()
        return

    if data.startswith("cartplus:"):
        item_idx = int(data.replace("cartplus:", "", 1))
        item_name = INDEX_TO_ITEM[item_idx]
        user_id = callback.from_user.id
        user_carts.setdefault(user_id, {})
        if item_name in user_carts[user_id]:
            user_carts[user_id][item_name] += 1

        cart_text, cart_inline = get_cart_message_and_keyboard(user_id)
        await callback.message.edit_text(cart_text, reply_markup=cart_inline)
        await callback.answer(t(user_id, "cart_updated"))
        return

    if data.startswith("cartminus:"):
        item_idx = int(data.replace("cartminus:", "", 1))
        item_name = INDEX_TO_ITEM[item_idx]
        user_id = callback.from_user.id
        user_carts.setdefault(user_id, {})
        if item_name in user_carts[user_id]:
            user_carts[user_id][item_name] -= 1
            if user_carts[user_id][item_name] <= 0:
                del user_carts[user_id][item_name]

        cart_text, cart_inline = get_cart_message_and_keyboard(user_id)
        await callback.message.edit_text(cart_text, reply_markup=cart_inline)
        await callback.answer(t(user_id, "cart_updated"))
        return

    if data.startswith("cartremove:"):
        item_idx = int(data.replace("cartremove:", "", 1))
        item_name = INDEX_TO_ITEM[item_idx]
        user_id = callback.from_user.id
        user_carts.setdefault(user_id, {})
        user_carts[user_id].pop(item_name, None)

        cart_text, cart_inline = get_cart_message_and_keyboard(user_id)
        await callback.message.edit_text(cart_text, reply_markup=cart_inline)
        await callback.answer("O‘chirildi" if get_lang(user_id) == "uz" else "Удалено")
        return

    if data.startswith("pay:"):
        _, order_id_str, user_id_str = data.split(":")
        order_id = int(order_id_str)
        user_id = int(user_id_str)

        order = await get_order(order_id)
        if not order:
            await callback.answer("Заказ не найден")
            return

        if is_closed_status(order["status"]):
            await callback.answer("Закрытый заказ менять нельзя")
            return

        if order["payment_status"] != "paid":
            await update_payment_status(order_id, "paid")

            if order["payment_method"] in {TEXTS["ru"]["bank_transfer"], TEXTS["uz"]["bank_transfer"]}:
                await update_order_check_status(order_id, "✅ Чек подтверждён")

            await refresh_channel_order_message(callback.bot, order_id)

            try:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=t_lang(get_order_lang(order), "payment_confirmed_client", order_code=client_order_code(order)),
                )
            except Exception:
                pass

            await callback.answer("Оплата подтверждена")
        else:
            await callback.answer("Уже оплачено")
        return

    if data.startswith("cancel:"):
        _, order_id_str, user_id_str = data.split(":")
        order_id = int(order_id_str)
        user_id = int(user_id_str)

        order = await get_order(order_id)
        if not order:
            await callback.answer("Заказ не найден")
            return

        if is_closed_status(order["status"]):
            await callback.answer("Этот заказ уже закрыт")
            return

        await update_order_status(order_id, "cancelled")
        await refresh_channel_order_message(callback.bot, order_id)

        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=t_lang(get_order_lang(order), "order_cancelled_client", order_code=client_order_code(order)),
            )
        except Exception:
            pass

        await callback.answer("Заказ отменён")
        return

    if data.startswith("status:"):
        _, order_id_str, user_id_str, status = data.split(":")
        order_id = int(order_id_str)
        user_id = int(user_id_str)

        order = await get_order(order_id)
        if not order:
            await callback.answer("Заказ не найден")
            return

        if is_closed_status(order["status"]):
            await callback.answer("Закрытый заказ менять нельзя")
            return

        await update_order_status(order_id, status)
        await refresh_channel_order_message(callback.bot, order_id)

        status_texts = {
            "accept": t_lang(get_order_lang(order), "status_accept_client", order_code=client_order_code(order)),
            "cooking": t_lang(get_order_lang(order), "status_cooking_client", order_code=client_order_code(order)),
            "delivery": t_lang(get_order_lang(order), "status_delivery_client", order_code=client_order_code(order)),
            "done": t_lang(get_order_lang(order), "status_done_client", order_code=client_order_code(order)),
        }

        if status in status_texts:
            try:
                await callback.bot.send_message(chat_id=user_id, text=status_texts[status])
            except Exception:
                pass

        await callback.answer("Статус обновлён")
        return

    await callback.answer()

# =========================
# # =========================
# ADMIN ANALYTICS (CHANNEL)
# =========================

from datetime import datetime, timedelta

@router.channel_post()
async def admin_channel_commands(message: Message):
    if not message.text:
        return

    text = message.text.strip().lower()

    try:
        async with aiosqlite.connect(DB_PATH) as db:

            # 🔥 ТОП БЛЮД
            if text == "/topmenu":
                cursor = await db.execute("""
                    SELECT item_name, SUM(quantity) as total
                    FROM order_items
                    GROUP BY item_name
                    ORDER BY total DESC
                    LIMIT 5
                """)
                rows = await cursor.fetchall()

                if not rows:
                    await message.answer("❌ Нет данных")
                    return

                result = "🔥 ТОП продающихся блюд:\n\n"
                for i, (name, total) in enumerate(rows, 1):
                    result += f"{i}. {name} — {total} шт\n"

                await message.answer(result)
                return

            # 📊 КАССА
            async def get_sum(start_time):
                cursor = await db.execute("""
                    SELECT SUM(total)
                    FROM orders
                    WHERE created_at >= ?
                """, (start_time,))
                row = await cursor.fetchone()
                return row[0] or 0

            now = datetime.now()

            if text == "/day":
                start = now.replace(hour=0, minute=0, second=0)
                total = await get_sum(start)
                await message.answer(f"📊 Касса за сегодня: {total:,} ₩")
                return

            if text == "/week":
                start = now - timedelta(days=7)
                total = await get_sum(start)
                await message.answer(f"📊 Касса за неделю: {total:,} ₩")
                return

            if text == "/month":
                start = now - timedelta(days=30)
                total = await get_sum(start)
                await message.answer(f"📊 Касса за месяц: {total:,} ₩")
                return

            if text == "/alltime":
                start = datetime(2000, 1, 1)
                total = await get_sum(start)
                await message.answer(f"📊 Общая касса: {total:,} ₩")
                return

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
# =========================
# MAIN
# =========================
async def main():
    await init_db()
    await load_photo_file_ids()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

