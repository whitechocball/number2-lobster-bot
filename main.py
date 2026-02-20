"""
二號龍蝦 — Telegram AI 聊天機械人
透過 OpenRouter API 接入 GLM-4 / Claude Opus 4.5
"""

import os
import logging
from collections import defaultdict

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── 日誌設定 ───────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── 環境變數 ───────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

# ─── OpenRouter 設定 ────────────────────────────────────────
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/lobster-bot",
    "X-Title": "二號龍蝦 Telegram Bot",
}

# ─── 模型定義 ───────────────────────────────────────────────
MODELS = {
    "glm": {
        "id": "z-ai/glm-4.7",
        "name": "GLM-4（智譜）",
    },
    "opus": {
        "id": "anthropic/claude-opus-4.5",
        "name": "Claude Opus 4.5",
    },
}
DEFAULT_MODEL = "glm"

# ─── 系統提示詞 ─────────────────────────────────────────────
SYSTEM_PROMPT = (
    "你係「二號龍蝦」，一個友善、幽默嘅 AI 助手。"
    "你主要用廣東話（粵語）回覆用戶，語氣自然親切，好似同朋友傾偈咁。"
    "如果用戶用其他語言同你講嘢，你都可以用返嗰種語言回覆，但預設用廣東話。"
    "你嘅回覆要簡潔實用，唔好太長氣，除非用戶要求詳細解釋。"
)

# ─── 對話上下文長度限制 ──────────────────────────────────────
MAX_HISTORY_MESSAGES = 40  # 最多保留 40 條訊息（20 輪對話）

# ─── 每個用戶嘅狀態 ─────────────────────────────────────────
user_histories: dict[int, list[dict]] = defaultdict(list)
user_models: dict[int, str] = defaultdict(lambda: DEFAULT_MODEL)


# ═══════════════════════════════════════════════════════════
#  OpenRouter API 呼叫
# ═══════════════════════════════════════════════════════════
def call_openrouter(user_id: int, user_message: str) -> str:
    """將用戶訊息連同歷史記錄發送到 OpenRouter，返回 AI 回覆。"""

    model_key = user_models[user_id]
    model_id = MODELS[model_key]["id"]

    # 加入用戶訊息到歷史
    user_histories[user_id].append({"role": "user", "content": user_message})

    # 裁剪歷史長度
    if len(user_histories[user_id]) > MAX_HISTORY_MESSAGES:
        user_histories[user_id] = user_histories[user_id][-MAX_HISTORY_MESSAGES:]

    # 組裝完整訊息列表
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_histories[user_id]

    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers=OPENROUTER_HEADERS,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        # 提取回覆內容
        assistant_message = data["choices"][0]["message"]["content"]

        # 將 AI 回覆加入歷史
        user_histories[user_id].append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message

    except requests.exceptions.Timeout:
        return "⏳ 哎呀，AI 諗咗太耐都未覆，請你遲啲再試下啦！"
    except requests.exceptions.HTTPError as e:
        logger.error("OpenRouter HTTP error: %s — %s", e, resp.text)
        return f"❌ API 出錯咗：{resp.status_code}。請檢查下你嘅 API Key 同模型設定。"
    except Exception as e:
        logger.error("OpenRouter unexpected error: %s", e)
        return "❌ 出咗啲意外狀況，請遲啲再試下。"


# ═══════════════════════════════════════════════════════════
#  Telegram 指令處理
# ═══════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /start 指令 — 歡迎訊息。"""
    welcome = (
        "🦞 *你好！我係「二號龍蝦」！*\n\n"
        "我係一個 AI 聊天機械人，可以用廣東話同你傾偈 💬\n\n"
        "📌 *可用指令：*\n"
        "• /glm — 切換到 GLM\\-4 模型（預設）\n"
        "• /opus — 切換到 Claude Opus 4\\.5（處理困難任務）\n"
        "• /clear — 清除對話歷史，重新開始\n"
        "• /model — 查看而家用緊邊個模型\n"
        "• /help — 顯示呢個幫助訊息\n\n"
        "直接打字同我傾偈就得啦！🎉"
    )
    await update.message.reply_text(welcome, parse_mode="MarkdownV2")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /help 指令。"""
    await cmd_start(update, context)


async def cmd_glm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /glm 指令 — 切換到 GLM-4。"""
    user_id = update.effective_user.id
    user_models[user_id] = "glm"
    await update.message.reply_text(
        "✅ 已經切換到 *GLM\\-4（智譜）* 模型！\n呢個係預設模型，適合日常對話。",
        parse_mode="MarkdownV2",
    )


async def cmd_opus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /opus 指令 — 切換到 Claude Opus 4.5。"""
    user_id = update.effective_user.id
    user_models[user_id] = "opus"
    await update.message.reply_text(
        "✅ 已經切換到 *Claude Opus 4\\.5* 模型！\n"
        "呢個模型更加強大，適合處理困難任務，但回覆可能會慢少少。",
        parse_mode="MarkdownV2",
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /clear 指令 — 清除對話歷史。"""
    user_id = update.effective_user.id
    user_histories[user_id].clear()
    await update.message.reply_text("🗑️ 對話歷史已經清除！我哋可以重新開始傾偈啦。")


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /model 指令 — 顯示當前模型。"""
    user_id = update.effective_user.id
    model_key = user_models[user_id]
    model_name = MODELS[model_key]["name"]
    model_id = MODELS[model_key]["id"]
    await update.message.reply_text(
        f"🤖 而家用緊嘅模型：\n"
        f"名稱：{model_name}\n"
        f"ID：{model_id}"
    )


# ═══════════════════════════════════════════════════════════
#  文字訊息處理
# ═══════════════════════════════════════════════════════════
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理用戶發送嘅普通文字訊息。"""
    user_id = update.effective_user.id
    user_message = update.message.text

    logger.info(
        "收到用戶 %s 嘅訊息（模型：%s）：%s",
        user_id,
        user_models[user_id],
        user_message[:80],
    )

    # 發送「正在輸入」狀態
    await update.message.chat.send_action("typing")

    # 呼叫 OpenRouter API
    reply = call_openrouter(user_id, user_message)

    # 如果回覆太長，Telegram 有 4096 字元限制，需要分段發送
    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        # 分段發送
        for i in range(0, len(reply), 4096):
            chunk = reply[i : i + 4096]
            await update.message.reply_text(chunk)


# ═══════════════════════════════════════════════════════════
#  錯誤處理
# ═══════════════════════════════════════════════════════════
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """全局錯誤處理。"""
    logger.error("發生錯誤：%s", context.error)


# ═══════════════════════════════════════════════════════════
#  主程式入口
# ═══════════════════════════════════════════════════════════
def main() -> None:
    """啟動 Bot。"""
    logger.info("🦞 二號龍蝦正在啟動...")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 註冊指令處理器
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("glm", cmd_glm))
    app.add_handler(CommandHandler("opus", cmd_opus))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("model", cmd_model))

    # 註冊文字訊息處理器（排除指令）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 註冊錯誤處理器
    app.add_error_handler(error_handler)

    logger.info("🦞 二號龍蝦已經準備好，開始接收訊息！")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
