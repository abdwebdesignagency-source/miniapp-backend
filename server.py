from fastapi import FastAPI, Request
import requests

app = FastAPI()

BOT_TOKEN = "8762627545:AAECV_X-SyhUzJiwop6pvQOjGCF9Mhz2F10"
ADMIN_CHAT_ID = -1003740556524  # chat id канала/группы

@app.get("/health")
def health():
    return "OK"

@app.post("/api/checkout")
async def checkout(req: Request):
    try:
        data = await req.json()

        cart = data.get("cart", [])
        total = data.get("total", 0)
        user = data.get("user") or {}

        if not cart:
            return {"ok": False, "error": "Cart is empty"}

        first_name = user.get("first_name", "Mini App User")
        username = user.get("username")
        user_id = user.get("id")

        text = "📦 Новый заказ из Mini App:\n\n"
        text += f"👤 Клиент: {first_name}\n"

        if username:
            text += f"🔗 Username: @{username}\n"

        if user_id:
            text += f"🆔 User ID: {user_id}\n"

        text += "\n🛒 Корзина:\n"
        for item in cart:
            name = item.get("name", "Item")
            qty = int(item.get("qty", 1))
            price = int(item.get("price", 0))
            line_total = price * qty
            text += f"• {name} x{qty} = {line_total:,} ₩\n"

        text += f"\n💰 Итого: {int(total):,} ₩"

        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": ADMIN_CHAT_ID,
                "text": text
            },
            timeout=20
        )

        if r.status_code != 200:
            return {"ok": False, "error": r.text}

        return {"ok": True}

    except Exception as e:
        return {"ok": False, "error": str(e)}