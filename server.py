from aiohttp import web
from aiogram import Bot
from datetime import datetime
import os

BOT_TOKEN = "8762627545:AAECV_X-SyhUzJiwop6pvQOjGCF9Mhz2F10"
ADMIN_CHAT_ID = 1003740556524  

def format_won(value: int) -> str:
    return f"{int(value):,} ₩"

def generate_order_code() -> str:
    return f"WEB{int(datetime.now().timestamp())}"

async def checkout(request: web.Request):
    try:
        data = await request.json()

        cart = data.get("cart", [])
        total = int(data.get("total", 0))
        user = data.get("user") or {}

        if not cart:
            return web.json_response({"error": "Cart is empty"}, status=400)

        user_id = user.get("id")
        first_name = user.get("first_name", "Mini App User")
        username = user.get("username", "")

        order_code = generate_order_code()

        text = "🛍 Mini App buyurtma:\n\n"
        text += f"🆔 Order: {order_code}\n"
        text += f"👤 Mijoz: {first_name}\n"

        if username:
            text += f"🔗 Username: @{username}\n"

        if user_id:
            text += f"🧾 User ID: {user_id}\n"

        text += "\n📦 Mahsulotlar:\n"

        for item in cart:
            name = item.get("name", "Item")
            qty = int(item.get("qty", 1))
            price = int(item.get("price", 0))
            line_total = price * qty
            text += f"• {name} x{qty} — {format_won(line_total)}\n"

        text += f"\n💰 Jami: {format_won(total)}"

        bot: Bot = request.app["bot"]
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)

        if user_id:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Buyurtmangiz qabul qilindi!\n\n🆔 Order: {order_code}\n💰 Jami: {format_won(total)}"
                )
            except Exception:
                pass

        return web.json_response({
            "ok": True,
            "order_code": order_code
        })

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def health(request: web.Request):
    return web.Response(text="OK")

async def create_app():
    app = web.Application()
    app["bot"] = Bot(token=BOT_TOKEN)
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_post("/api/checkout", checkout)
    return app

def main():
    port = int(os.environ.get("PORT", 10000))
    web.run_app(create_app(), host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()