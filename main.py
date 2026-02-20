
Agents
喺 Railway 入面搵 Variables 嘅方法：
打開你嘅 Railway 項目頁面
你會見到你部署咗嘅 service（通常係一個紫色或者彩色嘅方塊），撳入去
入到 service 之後，上面會有幾個 tab，例如「Deployments」、「Settings」、「Variables」、「Logs」等等
撳「Variables」呢個 tab
然後撳「+ New Variable」或者「RAW Editor」
分別加入：
Key 填 TELEGRAM_BOT_TOKEN，Value 填你嘅 Bot Token
Key 填 OPENROUTER_API_KEY，Value 填你嘅 OpenRouter API Key
加完之後 Railway 會自動重新部署。等佢部署完，再去 Telegram 發 /start 測試。
如果你喺 tab 入面搵唔到「Variables」，可能你仲喺項目嘅總覽頁面，記住要先撳入個 service 方塊入去先會見到。
pasted_content.txt
文本 · 5.06 KB
add two varibable 到 raliway後，出現failure log. 
等龍蝦睇下你嘅 error log。
問題好簡單：Railway 搵唔到你設定嘅環境變數。最大可能係你加 Variable 嘅時候，個 Key 名稱有少少唔啱，例如前後有空格，或者大細楷唔同。
你去 Railway 嘅 Variables 頁面檢查以下幾點：
確認 Key 名稱係 TELEGRAM_BOT_TOKEN（全部大楷，冇空格，冇引號）
確認 Value 係你喺 BotFather 攞到嘅 Token（冇空格，冇引號）
同樣確認 OPENROUTER_API_KEY 嘅 Key 同 Value 都冇多餘嘅空格
如果唔確定，建議你將兩個 Variable 刪除，重新加過一次。加完之後，Railway 會自動重新部署。
另外，你亦可以試下喺 Variables 頁面撳「RAW Editor」，直接貼入以下格式（將 xxx 換成你嘅真實值）：
TELEGRAM_BOT_TOKEN=xxx
OPENROUTER_API_KEY=xxx
貼完撳 Save，等佢重新部署就得。
我現在已經可以成功跟2號龍蝦傾偈 . 我按照你嘅方法去部署的.  現在2號龍蝦，我應該用什麼方法可以令消耗的Token. 盡量比較少.  甚至是控制每一個月上限不會超過有限的金額
恭喜！二號龍蝦成功上線！
慳 Token 同控制成本，你可以做以下幾樣嘢：
第一，喺 OpenRouter 設定消費上限：
去 openrouter.ai → Settings → Limits，你可以設定每月嘅消費上限（例如 $10 美金）。到咗上限就會自動停止，唔會超支。
第二，減少每次對話嘅 Token 消耗：
而家二號龍蝦保留 20 輪對話歷史，每次提問都會將之前嘅對話一齊送去 AI，所以越傾越耐就越貴。你可以養成習慣，傾完一個話題就發 /clear 清除歷史，重新開始。
第三，盡量用 GLM 模型：
GLM 比 Claude Opus 4.5 平好多倍。日常提問用 GLM 就夠，只有真正複雜嘅任務先切換去 /opus。
第四，提問盡量簡短精準：
長篇大論嘅提問會消耗更多 Token。問題越精準，回覆越短，成本越低。
最重要係第一點，去 OpenRouter 設定月費上限，咁就一定唔會超預算。你而家就可以去設定。
你給我的程式碼，是否已經設定為. 盡量用 GLM 模型
係，程式碼已經預設用 GLM 模型。
你每次開始對話，二號龍蝦自動用 GLM。只有當你主動發 /opus 指令，先會切換去 Claude Opus 4.5。切換之後如果想返去 GLM，發 /glm 就得。
所以你唔特別做任何嘢，日常使用已經係用最平嘅 GLM 模型。
GLM4, 大概$5美金的話，能夠用多長時間
GLM-4 喺 OpenRouter 上面嘅價錢大約係：
輸入：$0.001 / 1K tokens
輸出：$0.001 / 1K tokens
即係每 1000 個 token 大約 $0.001 美金。
$5 美金大約可以用 500 萬個 token。
一般嚟講，一次普通嘅對話（你問一個問題 + AI 回覆）大約消耗 500-1500 個 token。如果以平均每次 1000 個 token 計算：
$5 美金大約可以做 5000 次對話。
如果你每日用 20-30 次，$5 美金大約可以用 5-8 個月。
當然，如果你保留多輪對話歷史，每次消耗嘅 token 會越嚟越多。所以記住傾完一個話題就 /clear，可以慳好多。
不過以上係估算，實際要睇你每次對話嘅長度。你可以喺 OpenRouter 嘅 Dashboard 睇到實時嘅消耗情況。
幫我開始用Telegram跟2號龍蝦溝通，但一開始已經看到以下問題  出咗啲意外狀況，請遲啲再試下。
呢個錯誤通常係 OpenRouter API 嗰邊出問題。最常見嘅原因有幾個：
OpenRouter 帳號未充值 — 你去 openrouter.ai → Settings → Credits 確認下你有冇餘額。如果係 $0，就要先充值先用到。
API Key 有問題 — 去 OpenRouter → Settings → Keys，確認你嘅 API Key 係 active 狀態，冇被 revoke。
模型名稱唔啱 — GLM-4 喺 OpenRouter 上面嘅模型 ID 可能同程式碼入面寫嘅唔一樣。你去 openrouter.ai/models 搜尋 "GLM"，睇下佢嘅完整模型 ID 係咩，話俾龍蝦知，龍蝦幫你改程式碼。
你先檢查第一同第二點，最快排除問題。如果兩個都冇問題，就話俾龍蝦知，龍蝦幫你查第三點。
名稱叫，GLM 5
明白，你想用 GLM-5 但程式碼入面寫嘅係 GLM-4，所以要改模型 ID。
你去 openrouter.ai/models 搜尋「GLM」，搵到 GLM-5 嗰個，撳入去睇佢嘅完整模型 ID（通常係類似 zhipu/glm-5 或者 thudm/glm-5 嘅格式）。
攞到之後話俾龍蝦知，龍蝦即刻幫你出一份更新咗嘅程式碼。
或者你直接截圖俾龍蝦睇 OpenRouter 上面 GLM-5 嘅頁面都得。
z-ai/glm-5
好，你需要改 main.py 入面嘅模型 ID。
去你嘅 GitHub repo，打開 main.py，搵到類似呢行：
"zhipu/glm-4" 或者 "thudm/glm-4"
將佢改成：
"z-ai/glm-5"
可能出現喺兩個地方（一個係預設模型設定，一個係 /glm 指令嘅切換），兩個都要改。
改完之後喺 GitHub 撳 Commit，Railway 會自動重新部署。部署完再去 Telegram 試下發訊息俾二號龍蝦。
如果你唔識喺 GitHub 改檔案，你可以直接喺 GitHub 嘅網頁上面撳入 main.py → 撳右上角嘅鉛筆圖示（Edit）→ 用 Ctrl+F 搜尋 "glm-4" → 全部改成 "glm-5" → 改完撳 Commit changes。
兩個模型的ID我給你一下, anthropic/claude-opus-4.6 和z-ai/glm-5 ,  main.py 你整段程式重新打一次出來，然後我蓋過本來的版本
好，龍蝦即刻幫你出更新版嘅 main.py，大約 2 分鐘。
更新咗嘅 main.py 附喺下面，已經改好兩個模型 ID：
GLM：z-ai/glm-5
Opus：anthropic/claude-opus-4.6
你去 GitHub 嘅 repo 入面，撳入 main.py → 撳右上角鉛筆圖示（Edit）→ 全選刪除舊內容 → 將附件入面嘅新 main.py 內容全部貼上去 → 撳 Commit changes。
Railway 會自動重新部署，部署完去 Telegram 發 /start 測試就得。
main.py
代码 · 10.72 KB
查看此任务中的所有文件


FirefliesGmailGoogle Calendar
+3

main.py
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
    "X-Title": "二號龍蝦 Telegram Bot",
}

# ─── 模型定義 ───────────────────────────────────────────────
MODELS = {
    "glm": {
        "id": "z-ai/glm-5",
        "name": "GLM-5（智譜）",
    },
    "opus": {
        "id": "anthropic/claude-opus-4.6",
        "name": "Claude Opus 4.6",
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
        "✅ 已經切換到 *GLM\\-5（智譜）* 模型！\n呢個係預設模型，適合日常對話。",
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
Agents - Manus
