"""
二號龍蝦 — Telegram AI 聊天機械人
透過 OpenRouter API 接入 GLM-5 / Claude Opus 4.6
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
    "X-Title": "Lobster Bot 2",
}

# ─── 模型定義 ───────────────────────────────────────────────
MODELS = {
    "glm": {
        "id": "z-ai/glm-5",
        "name": "GLM-5",
    },
    "opus": {
        "id": "anthropic/claude-opus-4.6",
        "name": "Claude Opus 4.6",
    },
}
DEFAULT_MODEL = "glm"

# ─── 系統提示詞（簡短版，加快回覆速度）─────────────────────
SYSTEM_PROMPT = (
    "你係「二號龍蝦」，一個友善嘅 AI 助手。用廣東話回覆，簡潔實用。"
    "用戶叫你做「龍蝦」或「二號龍蝦」。"
)

# ─── 項目記憶（用 /memory 指令先載入）──────────────────────
PROJECT_MEMORY = """以下係用戶正在進行嘅項目記憶，當用戶提及項目名稱時，你要知道佢講緊咩：

=== 項目 1：Tryme ===
物理治療師推薦同預約平台。
- 用 Telegram Userbot 監察其他物理治療相關嘅群組，採集治療師評價同推薦資訊
- 採集到嘅圖片會自動去除別人水印，加上自己水印（用 AI 圖像修復工具 LaMa/IOPaint + Pillow）
- 自建網站展示內容，用 Headless CMS 架構（Directus + Next.js/Astro），透過 API 自動發佈
- 網站唔包含預約功能，只做內容展示
- 預約功能獨立處理：客戶透過 Telegram Bot 預約，系統透過企業微信（WeCom）聯繫國內物理治療師確認時間
- Telegram 群組用 Topics 功能分組（按場所分，每個場所有唔同治療師），AI 自動判斷內容發送到對應嘅話題分組
- 所有預約記錄存喺 Directus 數據庫
- 每日中午同晚上透過 Telegram Bot 自動發送預約報告
- 全部部署喺 Railway 上面

=== 項目 2：NIS ===
保險產品知識庫服務，針對香港理財顧問。
- 核心服務：持續更新保險產品數據包 + 提問技巧
- 理財顧問透過 WhatsApp 或 Telegram 提問，AI 用 RAG 回答
- 收費模式：首 5 次免費，之後收月費或季度費（用 Stripe 收費）
- WhatsApp 接入用 Twilio 或 360dialog
- 防止 RAG 搞混：每個產品獨立數據包，客戶先揀產品再提問
- 增值功能：幻燈片生成（OpenRouter AI + python-pptx 套模板出 PPT）
- 部署喺 Railway，接入 OpenRouter API

=== 項目 3：RDDR（Restaurant Dance Dance Revolution）===
餐廳舞蹈表演預約平台。
- 連接三方：餐廳、客人、舞蹈員
- 舞蹈員可報名，睇培訓課、加盟餐廳、表演排期
- 利潤來自客人同餐廳服務費差價
- 細節待定

=== 項目 4：EDYD（以單養單）===
派息基金配置網站，幫理財顧問展示客戶應配置幾多派息基金覆蓋每月開銷。
- 對接 Google Sheet（37 個 sheet，十幾隻保誠派息基金）
- 每隻基金喺 Sheet 入面有下載連結，AI 跟連結讀取最新資料
- 登入：手機號碼 + 驗證碼，只限 NIS 付費用戶
- 部署喺 Railway

=== 項目 5：二號龍蝦 ===
即係你自己！OpenRouter（GLM-5 / Claude Opus 4.6）+ Telegram Bot + Railway。

=== 技術棧 ===
部署：Railway | AI：OpenRouter | 代碼：GitHub
用戶一個人做，冇編程經驗，盡量少平台。"""

# ─── 對話上下文長度限制 ──────────────────────────────────────
MAX_HISTORY_MESSAGES = 40

# ─── 每個用戶嘅狀態 ─────────────────────────────────────────
user_histories: dict[int, list[dict]] = defaultdict(list)
user_models: dict[int, str] = defaultdict(lambda: DEFAULT_MODEL)
user_memory_loaded: dict[int, bool] = defaultdict(bool)


# ═══════════════════════════════════════════════════════════
#  OpenRouter API 呼叫
# ═══════════════════════════════════════════════════════════
def call_openrouter(user_id: int, user_message: str) -> str:

    model_key = user_models[user_id]
    model_id = MODELS[model_key]["id"]

    user_histories[user_id].append({"role": "user", "content": user_message})

    if len(user_histories[user_id]) > MAX_HISTORY_MESSAGES:
        user_histories[user_id] = user_histories[user_id][-MAX_HISTORY_MESSAGES:]

    # 如果已載入記憶，用完整 System Prompt；否則用簡短版
    if user_memory_loaded[user_id]:
        system_content = SYSTEM_PROMPT + "\n\n" + PROJECT_MEMORY
    else:
        system_content = SYSTEM_PROMPT

    messages = [{"role": "system", "content": system_content}] + user_histories[user_id]

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
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()

        assistant_message = data["choices"][0]["message"]["content"]

        user_histories[user_id].append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message

    except requests.exceptions.Timeout:
        return "AI 諗咗太耐都未覆，請你遲啲再試下啦！"
    except requests.exceptions.HTTPError as e:
        logger.error("OpenRouter HTTP error: %s — %s", e, resp.text)
        return f"API 出錯咗：{resp.status_code}。請檢查下你嘅 API Key 同模型設定。"
    except Exception as e:
        logger.error("OpenRouter unexpected error: %s", e)
        return f"出咗啲意外狀況：{e}"


# ═══════════════════════════════════════════════════════════
#  Telegram 指令處理
# ═══════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome = (
        "🦞 *你好！我係「二號龍蝦」！*\n\n"
        "我係一個 AI 聊天機械人，可以用廣東話同你傾偈 💬\n\n"
        "📌 *可用指令：*\n"
        "• /glm — 切換到 GLM\\-5 模型（預設）\n"
        "• /opus — 切換到 Claude Opus 4\\.6（處理困難任務）\n"
        "• /memory — 載入項目記憶（討論項目前用）\n"
        "• /forget — 卸載項目記憶（加快回覆速度）\n"
        "• /clear — 清除對話歷史，重新開始\n"
        "• /model — 查看而家用緊邊個模型\n"
        "• /help — 顯示呢個幫助訊息\n\n"
        "直接打字同我傾偈就得啦！🎉"
    )
    await update.message.reply_text(welcome, parse_mode="MarkdownV2")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_glm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_models[user_id] = "glm"
    await update.message.reply_text(
        "✅ 已經切換到 *GLM\\-5* 模型！\n呢個係預設模型，適合日常對話。",
        parse_mode="MarkdownV2",
    )


async def cmd_opus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_models[user_id] = "opus"
    await update.message.reply_text(
        "✅ 已經切換到 *Claude Opus 4\\.6* 模型！\n"
        "呢個模型更加強大，適合處理困難任務，但回覆可能會慢少少。",
        parse_mode="MarkdownV2",
    )


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """載入項目記憶。"""
    user_id = update.effective_user.id
    user_memory_loaded[user_id] = True
    await update.message.reply_text(
        "🧠 項目記憶已載入！而家你可以用項目名稱（Tryme、NIS、RDDR、EDYD）同我討論。\n"
        "傾完之後用 /forget 卸載記憶，回覆速度會快返。"
    )


async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """卸載項目記憶。"""
    user_id = update.effective_user.id
    user_memory_loaded[user_id] = False
    await update.message.reply_text(
        "💨 項目記憶已卸載！回覆速度會快返。\n"
        "需要討論項目嘅時候，再用 /memory 載入就得。"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_histories[user_id].clear()
    user_memory_loaded[user_id] = False
    await update.message.reply_text("🗑️ 對話歷史已清除，項目記憶已卸載！重新開始傾偈啦。")


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    model_key = user_models[user_id]
    model_name = MODELS[model_key]["name"]
    model_id = MODELS[model_key]["id"]
    memory_status = "已載入" if user_memory_loaded[user_id] else "未載入"
    await update.message.reply_text(
        f"而家用緊嘅模型：{model_name}\n"
        f"模型 ID：{model_id}\n"
        f"項目記憶：{memory_status}"
    )


# ═══════════════════════════════════════════════════════════
#  文字訊息處理
# ═══════════════════════════════════════════════════════════
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text

    logger.info(
        "收到用戶 %s 嘅訊息（模型：%s，記憶：%s）：%s",
        user_id,
        user_models[user_id],
        user_memory_loaded[user_id],
        user_message[:80],
    )

    await update.message.chat.send_action("typing")

    reply = call_openrouter(user_id, user_message)

    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        for i in range(0, len(reply), 4096):
            chunk = reply[i : i + 4096]
            await update.message.reply_text(chunk)


# ═══════════════════════════════════════════════════════════
#  錯誤處理
# ═══════════════════════════════════════════════════════════
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("發生錯誤：%s", context.error)


# ═══════════════════════════════════════════════════════════
#  主程式入口
# ═══════════════════════════════════════════════════════════
def main() -> None:
    logger.info("二號龍蝦正在啟動...")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("glm", cmd_glm))
    app.add_handler(CommandHandler("opus", cmd_opus))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("forget", cmd_forget))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("model", cmd_model))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(error_handler)

    logger.info("二號龍蝦已經準備好，開始接收訊息！")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
