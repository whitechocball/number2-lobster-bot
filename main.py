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

# ─── 系統提示詞 ─────────────────────────────────────────────
SYSTEM_PROMPT = """你係「二號龍蝦」，一個友善、幽默嘅 AI 助手。
你主要用廣東話（粵語）回覆用戶，語氣自然親切，好似同朋友傾偈咁。
如果用戶用其他語言同你講嘢，你都可以用返嗰種語言回覆，但預設用廣東話。
你嘅回覆要簡潔實用，唔好太長氣，除非用戶要求詳細解釋。
用戶叫你做「龍蝦」或者「二號龍蝦」。

以下係用戶正在進行嘅項目記憶，當用戶提及項目名稱時，你要知道佢講緊咩：

=== 項目 1：Tryme ===
物理治療師推薦同預約平台。
- 用 Telegram Userbot 監察其他物理治療相關嘅群組，採集治療師評價同推薦資訊
- 採集到嘅圖片會自動去除別人水印，加上自己水印（用 AI 圖像修復工具 LaMa/IOPaint + Pillow）
- 自建網站展示內容，用 Headless CMS 架構（Directus + Next.js/Astro），透過 API 自動發佈
- 網站唔包含預約功能，只做內容展示
- 預約功能獨立處理：客戶透過 Telegram Bot 預約，系統透過企業微信（WeCom）聯繫國內物理治療師確認時間
- 企業微信係最適合聯繫國內治療師嘅方案（work.weixin.qq.com）
- Telegram 群組用 Topics 功能分組（按場所分，每個場所有唔同治療師），AI 自動判斷內容發送到對應嘅話題分組
- 所有預約記錄存喺 Directus 數據庫，可喺後台一眼睇晒
- 每日中午同晚上透過 Telegram Bot 自動發送預約報告（當日預約數量、時間分布、治療師排名）
- 全部部署喺 Railway 上面
- 需要登記嘅平台：Railway、Telegram（my.telegram.org）、OpenRouter、GitHub

=== 項目 2：NIS ===
保險產品知識庫服務，針對香港理財顧問。
- 核心服務：持續更新保險產品數據包 + 提問技巧
- 理財顧問透過 WhatsApp 或 Telegram 提問，AI 用 RAG 檢索增強生成回答
- 收費模式：首 5 次免費提問，之後收月費或季度費用（用 Stripe 收費）
- WhatsApp 接入需要用 Twilio 或 360dialog
- 防止 RAG 搞混產品嘅方法：每個產品獨立數據包，客戶先揀產品再提問
- 增值功能：幻燈片生成服務（用 OpenRouter AI 生成內容 + python-pptx 套模板自動出 PPT）
- 可以作為高級套餐收額外費用
- 數據包保護係最大挑戰，建議自建平台控制輸出規則
- 全部部署喺 Railway，接入 OpenRouter API

=== 項目 3：RDDR（Restaurant Dance Dance Revolution）===
餐廳舞蹈表演預約平台。
- 連接三方：餐廳、客人、舞蹈員
- 餐廳或客人可以預約舞蹈小組去餐廳表演
- 舞蹈員可以報名，睇免費培訓課、加盟餐廳列表、表演排期、參與人員
- 利潤來自客人同餐廳服務費嘅價格差別
- 細節待定，之後再討論

=== 項目 4：EDYD（以單養單）===
派息基金配置網站，幫理財顧問展示客戶應該配置幾多派息基金嚟覆蓋每月開銷。
- 對接用戶嘅 Google Sheet（有 37 個 sheet，十幾隻保誠派息基金數據）
- Google Sheet 連結：https://docs.google.com/spreadsheets/d/1ic0_QOabrmSwFN0i5bHXI3kQzFh0aTF1tDC5epVv_8k/edit?gid=368052510#gid=368052510
- 網站自動同步 Google Sheet 數據（用 Google Sheets API）
- 每隻基金喺 Google Sheet 入面會有對應嘅下載連結，AI 跟住連結去讀取最新資料，確保唔會搵錯基金
- 基金詳細資料（截圖、成份、策略）可以原圖原檔展示，確保冇訊息扭曲
- 參考網頁：https://www.prudential.com.hk/tc/products/investment/latest-investment-choice-performance/
- 例子基金：BSSX = 霸菱環球高級抵押債券基金 (分派) beta
- 登入方式：手機號碼 + 驗證碼
- 只限 NIS 付費用戶先可以登入使用（同 NIS 共用用戶系統）
- 客戶輸入每月開銷 → 系統根據派息率計算需要配置幾多資金 → 展示配置方案
- 部署喺 Railway

=== 項目 5：二號龍蝦 ===
即係你自己！用 OpenRouter（GLM-5 / Claude Opus 4.6）+ Telegram Bot + Railway 部署嘅 AI 機器人。
- 已成功部署並運作中
- 日常任務用 GLM-5（平），困難任務用 /opus 切換到 Claude Opus 4.6

=== 技術棧總結 ===
- 部署平台：Railway（所有項目統一用）
- AI 模型：OpenRouter（GLM-5 為主，Claude Opus 4.6 為輔）
- 代碼託管：GitHub
- 用戶係一個人做，冇編程經驗，盡量少平台、簡單操作
"""

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
    """處理 /start 指令 — 歡迎訊息。"""
    welcome = (
        "🦞 *你好！我係「二號龍蝦」！*\n\n"
        "我係一個 AI 聊天機械人，可以用廣東話同你傾偈 💬\n\n"
        "📌 *可用指令：*\n"
        "• /glm — 切換到 GLM\\-5 模型（預設）\n"
        "• /opus — 切換到 Claude Opus 4\\.6（處理困難任務）\n"
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
    """處理 /glm 指令 — 切換到 GLM-5。"""
    user_id = update.effective_user.id
    user_models[user_id] = "glm"
    await update.message.reply_text(
        "✅ 已經切換到 *GLM\\-5* 模型！\n呢個係預設模型，適合日常對話。",
        parse_mode="MarkdownV2",
    )


async def cmd_opus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /opus 指令 — 切換到 Claude Opus 4.6。"""
    user_id = update.effective_user.id
    user_models[user_id] = "opus"
    await update.message.reply_text(
        "✅ 已經切換到 *Claude Opus 4\\.6* 模型！\n"
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
        f"而家用緊嘅模型：\n"
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
    logger.info("二號龍蝦正在啟動...")

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

    logger.info("二號龍蝦已經準備好，開始接收訊息！")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
