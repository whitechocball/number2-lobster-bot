'''
二號龍蝦 — Telegram AI 聊天機械人 v3
透過 OpenRouter API 接入 GLM-5 / Claude Opus 4.6
功能：SQLite 自動記憶、對話總結、記憶管理指令、ElevenLabs TTS
新增功能：Perplexity 搜索、網頁瀏覽摘要、Google Docs 管理
v3 新增：/research 深度研究（小紅書 + IMA 抓取 + AI 分析報告）
'''

import os
import logging
import sqlite3
import json
import io
import re
import asyncio
import aiohttp
from collections import defaultdict
from datetime import datetime

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from elevenlabs.client import ElevenLabs

# ─── 日誌設定 ───────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── 環境變數 ───────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")  # 用 getenv 避免 Key 不存在時出錯
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")  # Google Docs 用

# v3 新增：Browser Service 設定
BROWSER_SERVICE_URL = os.getenv("BROWSER_SERVICE_URL", "http://104.196.252.197:8080")
BROWSER_API_KEY = os.getenv("BROWSER_API_KEY", "")
XHS_COOKIES = os.getenv("XHS_COOKIES", "")  # 小紅書 Cookie

# ─── ElevenLabs 客戶端初始化 ────────────────────────────────
eleven_client = None
if ELEVENLABS_API_KEY:
    try:
        eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        logger.info("ElevenLabs 客戶端已初始化")
    except Exception as e:
        logger.error("初始化 ElevenLabs 客戶端失敗: %s", e)

# ─── Google Docs 客戶端初始化 ───────────────────────────────
google_docs_service = None
google_drive_service = None
if GOOGLE_SERVICE_ACCOUNT_KEY:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_KEY)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=[
                "https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        google_docs_service = build("docs", "v1", credentials=credentials)
        google_drive_service = build("drive", "v3", credentials=credentials)
        logger.info("Google Docs / Drive 客戶端已初始化")
    except Exception as e:
        logger.error("初始化 Google Docs 客戶端失敗: %s", e)

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
PROJECT_MEMORY = '''以下係用戶正在進行嘅項目記憶，當用戶提及項目名稱時，你要知道佢講緊咩：

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
用戶一個人做，冇編程經驗，盡量少平台。'''

# ─── 對話上下文長度限制 ──────────────────────────────────────
MAX_HISTORY_MESSAGES = 40

# ─── SQLite 數據庫設定 ────────────────────────────────────────
DB_FILE = "memory.db"

# ─── 每個用戶嘅狀態 ─────────────────────────────────────────
user_histories: dict[int, list[dict]] = defaultdict(list)
user_models: dict[int, str] = defaultdict(lambda: DEFAULT_MODEL)
user_memory_loaded: dict[int, bool] = defaultdict(bool)

# ─── Google Docs 預設分享 Email ─────────────────────────────
DEFAULT_SHARE_EMAIL = os.getenv("GOOGLE_DOCS_SHARE_EMAIL", "")


# ═══════════════════════════════════════════════════════════
#  SQLite 數據庫操作
# ═══════════════════════════════════════════════════════════
def init_database() -> None:
    """初始化 SQLite 數據庫，建立記憶表。"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS ai_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                summary TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        conn.commit()
        conn.close()
        logger.info("SQLite 數據庫已初始化")
    except Exception as e:
        logger.error("初始化數據庫失敗：%s", e)


def save_memory(project_name: str, summary: str, category: str) -> bool:
    """將記憶存入 SQLite 數據庫。"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO ai_memory (project_name, summary, category)
            VALUES (?, ?, ?)
            ''',
            (project_name, summary, category),
        )
        conn.commit()
        conn.close()
        logger.info("記憶已保存：%s - %s (%s)", project_name, summary[:30], category)
        return True
    except Exception as e:
        logger.error("保存記憶失敗：%s", e)
        return False


def get_recent_memories(limit: int = 20) -> list[dict]:
    """從 SQLite 讀取最近嘅記憶。"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, project_name, summary, category, created_at
            FROM ai_memory
            ORDER BY created_at DESC
            LIMIT ?
            ''',
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()

        memories = []
        for row in rows:
            memories.append(
                {
                    "id": row[0],
                    "project_name": row[1],
                    "summary": row[2],
                    "category": row[3],
                    "created_at": row[4],
                }
            )
        return memories
    except Exception as e:
        logger.error("讀取記憶失敗：%s", e)
        return []


def clear_all_memories() -> bool:
    """清除所有記憶。"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ai_memory")
        conn.commit()
        conn.close()
        logger.info("所有記憶已清除")
        return True
    except Exception as e:
        logger.error("清除記憶失敗：%s", e)
        return False


def format_memories_for_prompt(memories: list[dict]) -> str:
    """將記憶格式化成可加入 system prompt 嘅文本。"""
    if not memories:
        return ""

    formatted = "\n\n=== 最近嘅 AI 記憶（自動總結）===\n"
    for mem in reversed(memories):  # 反轉以顯示時間順序
        # Safely access created_at and format it
        created_at = mem.get("created_at")
        if isinstance(created_at, str):
            date_str = created_at.split(" ")[0]
        elif isinstance(created_at, datetime):
            date_str = created_at.strftime('%Y-%m-%d')
        else:
            date_str = "N/A"
        formatted += f"• [{date_str}] {mem.get('project_name', 'N/A')} ({mem.get('category', 'N/A')}): {mem.get('summary', 'N/A')}\n"

    return formatted


# ═══════════════════════════════════════════════════════════
#  AI 對話總結功能
# ═══════════════════════════════════════════════════════════
def summarize_conversation(user_id: int) -> tuple[str, str, str]:
    '''
    用 AI 自動總結當前對話，返回 (summary, project_name, category)。
    如果無法總結，返回 ("", "", "")。
    '''
    if not user_histories[user_id]:
        return "", "", ""

    # 取最後 10 條訊息作為總結對象
    recent_messages = user_histories[user_id][-10:]

    # 構建總結提示
    conversation_text = "\n".join(
        [f"{msg['role'].upper()}: {msg['content'][:200]}" for msg in recent_messages]
    )

    summarize_prompt = f'''你係一個對話總結助手。分析以下對話，提取關鍵信息。

對話內容：
{conversation_text}

請按照以下格式返回 JSON（唔好包含任何其他文本）：
{{
    "summary": "30-50 字嘅總結，只記錄決策、變更、新需求、下一步行動。如果係閒聊或重複內容，返回空字符串",
    "project": "涉及嘅項目名稱（Tryme、NIS、RDDR、EDYD 之一），如果無相關項目返回空字符串",
    "category": "記憶類別（decision、change、requirement、action），如果無法分類返回空字符串"
}}'''

    try:
        payload = {
            "model": MODELS["glm"]["id"],
            "messages": [{"role": "user", "content": summarize_prompt}],
            "temperature": 0.3,
            "max_tokens": 300,
        }

        resp = requests.post(
            OPENROUTER_URL,
            headers=OPENROUTER_HEADERS,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        response_text = data["choices"][0]["message"]["content"]

        # 嘗試解析 JSON
        try:
            result = json.loads(response_text)
            summary = result.get("summary", "").strip()
            project = result.get("project", "").strip()
            category = result.get("category", "").strip()

            # 只有當有有效嘅摘要同類別時，先返回
            if summary and category:
                return summary, project or "General", category
            else:
                return "", "", ""

        except json.JSONDecodeError:
            logger.warning("AI 返回嘅唔係有效 JSON：%s", response_text[:100])
            return "", "", ""

    except Exception as e:
        logger.error("對話總結失敗：%s", e)
        return "", "", ""


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
    system_content = SYSTEM_PROMPT
    if user_memory_loaded[user_id]:
        system_content += "\n\n" + PROJECT_MEMORY

        # 加入 SQLite 記憶
        recent_memories = get_recent_memories(20)
        memories_text = format_memories_for_prompt(recent_memories)
        if memories_text:
            system_content += memories_text

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

        # 每 10 條訊息自動總結一次
        if len(user_histories[user_id]) % 20 == 0:  # 每 10 次對話 (user+assistant)
            summary, project_name, category = summarize_conversation(user_id)
            if summary and project_name and category:
                save_memory(project_name, summary, category)

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
#  功能 1：Perplexity 搜索（透過 OpenRouter）
# ═══════════════════════════════════════════════════════════
def perplexity_search(query: str) -> str:
    """用 Perplexity (sonar) 透過 OpenRouter 進行實時網絡搜索。"""
    payload = {
        "model": "perplexity/sonar",
        "messages": [
            {
                "role": "system",
                "content": "你係一個搜索助手。用廣東話回覆搜索結果摘要，簡潔實用。",
            },
            {
                "role": "user",
                "content": query,
            },
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers=OPENROUTER_HEADERS,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "搜索超時咗，請遲啲再試下啦！"
    except requests.exceptions.HTTPError as e:
        logger.error("Perplexity search HTTP error: %s — %s", e, resp.text)
        return f"搜索 API 出錯咗：{resp.status_code}。"
    except Exception as e:
        logger.error("Perplexity search error: %s", e)
        return f"搜索時出咗啲問題：{e}"


# ═══════════════════════════════════════════════════════════
#  功能 2：網頁瀏覽摘要
# ═══════════════════════════════════════════════════════════
def fetch_and_summarize_url(url: str) -> str:
    """抓取網頁內容並用 AI 做摘要。"""
    from bs4 import BeautifulSoup

    # 第一步：抓取網頁
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding  # 自動偵測編碼
    except requests.exceptions.Timeout:
        return "抓取網頁超時咗，請確認個 URL 係咪正確。"
    except requests.exceptions.ConnectionError:
        return "連接唔到呢個網頁，請確認個 URL 係咪正確。"
    except requests.exceptions.HTTPError as e:
        return f"網頁返回錯誤：{e.response.status_code}"
    except Exception as e:
        return f"抓取網頁時出錯：{e}"

    # 第二步：解析 HTML，提取主要文字
    try:
        soup = BeautifulSoup(resp.text, "lxml")

        # 移除 script、style、nav、footer 等無用元素
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
            tag.decompose()

        # 提取標題
        title = soup.title.string.strip() if soup.title and soup.title.string else "無標題"

        # 提取主要文字內容
        text = soup.get_text(separator="\n", strip=True)

        # 清理多餘空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        if not clean_text:
            return "呢個網頁冇搵到可讀嘅文字內容。"

        # 截取前 3000 字
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "\n\n...（內容太長，只取前 3000 字）"

    except Exception as e:
        return f"解析網頁內容時出錯：{e}"

    # 第三步：用 AI 做摘要
    try:
        payload = {
            "model": MODELS["glm"]["id"],
            "messages": [
                {
                    "role": "system",
                    "content": "你係一個網頁摘要助手。用廣東話將以下網頁內容做一個簡潔嘅摘要，保留重點信息。",
                },
                {
                    "role": "user",
                    "content": f"網頁標題：{title}\n\n網頁內容：\n{clean_text}\n\n請用廣東話做一個摘要。",
                },
            ],
            "temperature": 0.5,
            "max_tokens": 1500,
        }

        ai_resp = requests.post(
            OPENROUTER_URL,
            headers=OPENROUTER_HEADERS,
            json=payload,
            timeout=60,
        )
        ai_resp.raise_for_status()
        data = ai_resp.json()
        summary = data["choices"][0]["message"]["content"]
        return f"📄 *{title}*\n\n{summary}"
    except Exception as e:
        logger.error("Browse summarize error: %s", e)
        return f"AI 摘要時出錯：{e}\n\n原文前 500 字：\n{clean_text[:500]}"


# ═══════════════════════════════════════════════════════════
#  功能 3：Google Docs 管理
# ═══════════════════════════════════════════════════════════
def create_google_doc(title: str, content: str) -> dict:
    """建立一個新嘅 Google Doc 並寫入內容。返回 {'url': ..., 'id': ...} 或 {'error': ...}。"""
    if not google_docs_service or not google_drive_service:
        return {"error": "Google Docs 功能未啟用，請先設定 GOOGLE_SERVICE_ACCOUNT_KEY 環境變數。"}

    try:
        # 建立文檔
        doc = google_docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")

        # 寫入內容
        if content:
            insert_requests = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": content,
                    }
                }
            ]
            google_docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": insert_requests}
            ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        # 分享俾用戶（如果有預設 email）
        if DEFAULT_SHARE_EMAIL:
            try:
                google_drive_service.permissions().create(
                    fileId=doc_id,
                    body={
                        "type": "user",
                        "role": "writer",
                        "emailAddress": DEFAULT_SHARE_EMAIL,
                    },
                    sendNotificationEmail=False,
                ).execute()
            except Exception as e:
                logger.warning("分享文檔失敗（但文檔已建立）：%s", e)

        # 設定為任何人都可以用連結查看
        try:
            google_drive_service.permissions().create(
                fileId=doc_id,
                body={
                    "type": "anyone",
                    "role": "reader",
                },
            ).execute()
        except Exception as e:
            logger.warning("設定公開連結失敗：%s", e)

        return {"url": doc_url, "id": doc_id}

    except Exception as e:
        logger.error("建立 Google Doc 失敗：%s", e)
        return {"error": f"建立文檔失敗：{e}"}


def list_google_docs(limit: int = 10) -> list[dict] | str:
    """列出 Service Account 擁有嘅最近 Google Docs。"""
    if not google_drive_service:
        return "Google Docs 功能未啟用，請先設定 GOOGLE_SERVICE_ACCOUNT_KEY 環境變數。"

    try:
        results = (
            google_drive_service.files()
            .list(
                q="mimeType='application/vnd.google-apps.document'",
                pageSize=limit,
                orderBy="modifiedTime desc",
                fields="files(id, name, modifiedTime, webViewLink)",
            )
            .execute()
        )
        files = results.get("files", [])
        return files
    except Exception as e:
        logger.error("列出 Google Docs 失敗：%s", e)
        return f"列出文檔失敗：{e}"


# ═══════════════════════════════════════════════════════════
#  功能 4：深度研究（v3 新增）
# ═══════════════════════════════════════════════════════════
async def call_browser_service(endpoint: str, payload: dict, timeout: int = 180) -> dict:
    """調用 Browser Service API。"""
    url = f"{BROWSER_SERVICE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {BROWSER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status == 401:
                    return {"error": "Browser Service API Key 認證失敗"}
                if resp.status == 503:
                    return {"error": "Browser Service 瀏覽器未就緒"}
                if resp.status != 200:
                    text = await resp.text()
                    return {"error": f"Browser Service 返回錯誤 {resp.status}: {text[:200]}"}
                return await resp.json()
    except asyncio.TimeoutError:
        return {"error": f"Browser Service 請求超時（{timeout}秒）"}
    except aiohttp.ClientConnectorError:
        return {"error": f"無法連接 Browser Service ({BROWSER_SERVICE_URL})，請確認服務是否運行中"}
    except Exception as e:
        return {"error": f"調用 Browser Service 時出錯：{e}"}


def format_xhs_results(data: dict) -> str:
    """將小紅書抓取結果格式化成文字。"""
    if data.get("error"):
        return f"小紅書搜索失敗：{data['error']}"

    posts = data.get("posts", [])
    if not posts:
        return "小紅書搜索冇搵到任何帖子。"

    lines = [f"小紅書搜索結果（關鍵詞：{data.get('keyword', '')}，共 {len(posts)} 個帖子）：\n"]

    for i, post in enumerate(posts, 1):
        if post.get("error"):
            lines.append(f"--- 帖子 {i}（抓取失敗：{post['error'][:50]}）---\n")
            continue

        lines.append(f"--- 帖子 {i} ---")
        if post.get("title"):
            lines.append(f"標題：{post['title']}")
        if post.get("content"):
            # 截取前 500 字
            content = post["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"內容：{content}")
        if post.get("likes"):
            lines.append(f"點贊：{post['likes']}")
        if post.get("collects"):
            lines.append(f"收藏：{post['collects']}")
        if post.get("comments"):
            lines.append(f"評論：{post['comments']}")
        if post.get("url"):
            lines.append(f"連結：{post['url']}")
        lines.append("")

    return "\n".join(lines)


def format_ima_results(data: dict) -> str:
    """將 IMA 抓取結果格式化成文字。"""
    if data.get("error"):
        return f"IMA 搜索失敗：{data['error']}"

    results = data.get("results", [])
    raw_text = data.get("raw_text", "")

    if not results and not raw_text:
        return "IMA 搜索冇搵到任何結果。"

    lines = [f"IMA 搜索結果（關鍵詞：{data.get('keyword', '')}）：\n"]

    if results:
        for i, item in enumerate(results, 1):
            text = item.get("text", "")
            if text:
                # 截取前 800 字
                if len(text) > 800:
                    text = text[:800] + "..."
                lines.append(f"結果 {i}：{text}\n")
    elif raw_text:
        if len(raw_text) > 3000:
            raw_text = raw_text[:3000] + "..."
        lines.append(raw_text)

    return "\n".join(lines)


async def generate_research_report(keyword: str, xhs_text: str, ima_text: str) -> str:
    """用 AI 生成深度研究報告。"""
    prompt = f'''你係一個專業嘅市場研究分析師。我而家俾你兩個來源嘅搜索結果，請你用廣東話寫一份深度研究報告。

搜索關鍵詞：{keyword}

=== 來源 1：小紅書（社交媒體平台）===
{xhs_text[:6000]}

=== 來源 2：IMA（騰訊 AI 搜索）===
{ima_text[:4000]}

請按照以下格式寫報告：

📊 深度研究報告：{keyword}

一、主要發現
（總結兩個來源嘅核心信息，3-5 個要點）

二、小紅書熱門觀點
（總結小紅書用戶嘅主要觀點同討論方向）

三、IMA 搜索結果摘要
（總結 IMA 搜索到嘅關鍵信息）

四、值得注意嘅帖子
（列出 2-3 個最有價值嘅帖子，附連結）

五、綜合分析同總結
（結合兩個來源，給出你嘅分析同建議）

注意：
- 用廣東話寫
- 保持客觀，唔好加入主觀判斷
- 如果某個來源冇結果，就跳過嗰個部分
- 報告長度控制喺 2000 字以內'''

    try:
        payload = {
            "model": MODELS["glm"]["id"],
            "messages": [
                {
                    "role": "system",
                    "content": "你係一個專業嘅市場研究分析師，擅長用廣東話撰寫研究報告。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.5,
            "max_tokens": 4000,
        }

        resp = requests.post(
            OPENROUTER_URL,
            headers=OPENROUTER_HEADERS,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        return "AI 生成報告超時咗，但以下係原始數據：\n\n" + xhs_text[:2000] + "\n\n" + ima_text[:2000]
    except Exception as e:
        logger.error("生成研究報告失敗：%s", e)
        return f"AI 生成報告失敗：{e}\n\n原始數據：\n{xhs_text[:1000]}\n\n{ima_text[:1000]}"


# ═══════════════════════════════════════════════════════════
#  Telegram 指令處理
# ═══════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome = (
        "🦞 *你好！我係「二號龍蝦」！*\n\n"
        "我係一個 AI 聊天機械人，可以用廣東話同你傾偈 💬\n\n"
        "📌 *基本指令：*\n"
        "• /glm — 切換到 GLM\\-5 模型（預設）\n"
        "• /opus — 切換到 Claude Opus 4\\.6（處理困難任務）\n"
        "• /model — 查看而家用緊邊個模型\n"
        "• /clear — 清除對話歷史，重新開始\n\n"
        "🗣️ *語音功能：*\n"
        "• /speak `文字` — 將文字轉成語音\n\n"
        "🧠 *記憶功能：*\n"
        "• /memory — 載入項目記憶（討論項目前用）\n"
        "• /forget — 卸載項目記憶（加快回覆速度）\n"
        "• /save — 手動總結當前對話並存入記憶\n"
        "• /recall — 顯示最近 10 條記憶總結\n"
        "• /delmemory — 清除所有記憶\n\n"
        "🔍 *搜索同瀏覽：*\n"
        "• /search `關鍵字` — 實時網絡搜索\n"
        "• /browse `URL` — 抓取網頁內容並做摘要\n\n"
        "🔬 *深度研究：*\n"
        "• /research `關鍵字` — 深度研究（小紅書 \\+ IMA 抓取 \\+ AI 分析）\n\n"
        "📝 *Google Docs：*\n"
        "• /doc `標題 \\| 內容` — 建立新 Google 文檔\n"
        "• /doclist — 列出最近嘅文檔\n\n"
        "• /help — 顯示呢個幫助訊息\n\n"
        "直接打字同我傾偈就得啦！🎉"
    )
    await update.message.reply_text(welcome, parse_mode="MarkdownV2")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_speak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """將文字轉換為語音。"""
    if not eleven_client:
        await update.message.reply_text("TTS 功能未啟用，請先設定 ELEVENLABS_API_KEY。")
        return

    text_to_speak = " ".join(context.args)
    if not text_to_speak:
        await update.message.reply_text("請喺 /speak 後面加上你想轉換成語音嘅文字。")
        return

    await update.message.chat.send_action("record_voice")

    try:
        # 使用 ElevenLabs API 生成語音
        audio_iterator = eleven_client.text_to_speech.convert(
            text=text_to_speak,
            voice_id="SjTlcCqd03iRQAnUDRx4",  # 用戶克隆嘅廣東話聲音（新版）
            model_id="eleven_multilingual_v2",
        )

        # 將語音以 BytesIO 形式發送
        audio_bytes = io.BytesIO()
        for chunk in audio_iterator:
            audio_bytes.write(chunk)
        audio_bytes.seek(0)

        if audio_bytes.getbuffer().nbytes > 0:
            await update.message.reply_voice(voice=audio_bytes)
        else:
            await update.message.reply_text("生成語音失敗，請稍後再試。")

    except Exception as e:
        logger.error("ElevenLabs API 錯誤: %s", e)
        await update.message.reply_text(f"生成語音時發生錯誤：{e}")


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
    """載入項目記憶同 SQLite 記憶。"""
    user_id = update.effective_user.id
    user_memory_loaded[user_id] = True

    # 讀取最近嘅記憶數量
    recent_memories = get_recent_memories(20)
    memory_count = len(recent_memories)

    await update.message.reply_text(
        f"🧠 項目記憶已載入！而家你可以用項目名稱（Tryme、NIS、RDDR、EDYD）同我討論。\n"
        f"已加載 {memory_count} 條自動記憶到對話上下文。\n"
        f"傾完之後用 /forget 卸載記憶，回覆速度會快返。"
    )


async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """卸載項目記憶。"""
    user_id = update.effective_user.id
    user_memory_loaded[user_id] = False
    await update.message.reply_text(
        "💨 項目記憶已卸載！回覆速度會快返。\n"
        "需要討論項目嘅時候，再用 /memory 載入就得。"
    )


async def cmd_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """手動觸發對話總結並存入記憶。"""
    user_id = update.effective_user.id

    if not user_histories[user_id]:
        await update.message.reply_text("冇對話可以總結啦！先同我傾偈先。")
        return

    await update.message.chat.send_action("typing")

    # 調用 AI 總結
    summary, project_name, category = summarize_conversation(user_id)

    if not summary:
        await update.message.reply_text(
            "呢個對話冇特別嘅內容值得記憶（可能係閒聊或重複內容）。"
        )
        return

    # 如果冇偵測到項目名稱，用預設值
    if not project_name:
        project_name = "General"

    # 存入數據庫
    success = save_memory(project_name, summary, category)

    if success:
        await update.message.reply_text(
            f"✅ 記憶已保存！\n"
            f"項目：{project_name}\n"
            f"類別：{category}\n"
            f"摘要：{summary}"
        )
    else:
        await update.message.reply_text("❌ 記憶保存失敗，請檢查數據庫連接。")


async def cmd_recall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """顯示最近 10 條記憶總結（唔載入到 system prompt）。"""
    recent_memories = get_recent_memories(10)

    if not recent_memories:
        await update.message.reply_text("冇記憶記錄。")
        return

    # 格式化顯示
    message = "📚 *最近嘅記憶總結（最新 10 條）：*\n\n"
    for mem in recent_memories:
        created_at = mem.get("created_at")
        if isinstance(created_at, str):
            date_str = created_at.split(" ")[0]
        elif isinstance(created_at, datetime):
            date_str = created_at.strftime('%Y-%m-%d')
        else:
            date_str = "N/A"
        message += (
            f"• [{date_str}] {mem.get('project_name', 'N/A')} "
            f"({mem.get('category', 'N/A')})\n"
            f"  {mem.get('summary', 'N/A')}\n\n"
        )

    if len(message) <= 4096:
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    else:
        # 分段發送
        for i in range(0, len(message), 4096):
            chunk = message[i : i + 4096]
            await update.message.reply_text(chunk, parse_mode="MarkdownV2")


async def cmd_delmemory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """清除所有記憶。"""
    success = clear_all_memories()

    if success:
        await update.message.reply_text("🗑️ 所有記憶已清除！")
    else:
        await update.message.reply_text("❌ 清除記憶失敗，請檢查數據庫連接。")


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


# ─── 新功能指令：搜索 ──────────────────────────────────────
async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """用 Perplexity 進行實時網絡搜索。"""
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text(
            "請喺 /search 後面加上你想搜索嘅關鍵字。\n"
            "例如：/search 香港天氣"
        )
        return

    await update.message.chat.send_action("typing")
    logger.info("用戶 %s 搜索：%s", update.effective_user.id, query)

    result = perplexity_search(query)

    # Telegram 訊息長度限制 4096
    if len(result) <= 4096:
        await update.message.reply_text(f"🔍 搜索結果：{query}\n\n{result}")
    else:
        # 分段發送
        header = f"🔍 搜索結果：{query}\n\n"
        first_chunk = header + result[:4096 - len(header)]
        await update.message.reply_text(first_chunk)
        remaining = result[4096 - len(header):]
        for i in range(0, len(remaining), 4096):
            chunk = remaining[i : i + 4096]
            await update.message.reply_text(chunk)


# ─── 新功能指令：瀏覽器 ────────────────────────────────────
async def cmd_browse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """抓取網頁內容並用 AI 做摘要。"""
    url = " ".join(context.args).strip()
    if not url:
        await update.message.reply_text(
            "請喺 /browse 後面加上你想瀏覽嘅網址。\n"
            "例如：/browse https://example.com"
        )
        return

    # 簡單驗證 URL 格式
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    await update.message.chat.send_action("typing")
    logger.info("用戶 %s 瀏覽：%s", update.effective_user.id, url)

    result = fetch_and_summarize_url(url)

    if len(result) <= 4096:
        await update.message.reply_text(result)
    else:
        for i in range(0, len(result), 4096):
            chunk = result[i : i + 4096]
            await update.message.reply_text(chunk)


# ─── 新功能指令：Google Docs ────────────────────────────────
async def cmd_doc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """建立新嘅 Google Doc。格式：/doc 標題 | 內容"""
    if not GOOGLE_SERVICE_ACCOUNT_KEY:
        await update.message.reply_text(
            "📝 Google Docs 功能未啟用。\n"
            "請先設定 GOOGLE_SERVICE_ACCOUNT_KEY 環境變數。"
        )
        return

    if not google_docs_service:
        await update.message.reply_text(
            "📝 Google Docs 初始化失敗，請檢查 GOOGLE_SERVICE_ACCOUNT_KEY 格式係咪正確。"
        )
        return

    raw_text = " ".join(context.args)
    if not raw_text:
        await update.message.reply_text(
            "請喺 /doc 後面加上標題同內容。\n"
            "格式：/doc 標題 | 內容\n"
            "例如：/doc 會議記錄 | 今日討論咗以下事項..."
        )
        return

    # 用 | 分隔標題同內容
    if "|" in raw_text:
        parts = raw_text.split("|", 1)
        title = parts[0].strip()
        content = parts[1].strip()
    else:
        # 如果冇 |，第一行做標題，其餘做內容
        lines = raw_text.strip().split("\n", 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

    if not title:
        await update.message.reply_text("標題唔可以係空嘅，請再試下。")
        return

    await update.message.chat.send_action("typing")
    logger.info("用戶 %s 建立 Google Doc：%s", update.effective_user.id, title)

    result = create_google_doc(title, content)

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
    else:
        share_info = ""
        if DEFAULT_SHARE_EMAIL:
            share_info = f"\n已分享俾：{DEFAULT_SHARE_EMAIL}"

        await update.message.reply_text(
            f"✅ Google 文檔已建立！\n\n"
            f"📄 標題：{title}\n"
            f"🔗 連結：{result['url']}"
            f"{share_info}"
        )


async def cmd_doclist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """列出最近嘅 Google Docs。"""
    if not GOOGLE_SERVICE_ACCOUNT_KEY:
        await update.message.reply_text(
            "📝 Google Docs 功能未啟用。\n"
            "請先設定 GOOGLE_SERVICE_ACCOUNT_KEY 環境變數。"
        )
        return

    if not google_drive_service:
        await update.message.reply_text(
            "📝 Google Docs 初始化失敗，請檢查 GOOGLE_SERVICE_ACCOUNT_KEY 格式係咪正確。"
        )
        return

    await update.message.chat.send_action("typing")

    result = list_google_docs(10)

    if isinstance(result, str):
        # 返回錯誤訊息
        await update.message.reply_text(f"❌ {result}")
        return

    if not result:
        await update.message.reply_text("📝 暫時冇任何 Google 文檔。")
        return

    message = "📚 最近嘅 Google 文檔：\n\n"
    for i, doc in enumerate(result, 1):
        name = doc.get("name", "無標題")
        modified = doc.get("modifiedTime", "N/A")
        # 格式化日期
        if modified != "N/A":
            try:
                dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                modified = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        link = doc.get("webViewLink", "")
        message += f"{i}. {name}\n   📅 {modified}\n   🔗 {link}\n\n"

    if len(message) <= 4096:
        await update.message.reply_text(message)
    else:
        for i in range(0, len(message), 4096):
            chunk = message[i : i + 4096]
            await update.message.reply_text(chunk)


# ─── v3 新增：深度研究指令 ─────────────────────────────────
async def cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """深度研究功能：同時搜索小紅書 + IMA，再用 AI 生成研究報告。"""
    keyword = " ".join(context.args)
    if not keyword:
        await update.message.reply_text(
            "請喺 /research 後面加上你想研究嘅關鍵字。\n"
            "例如：/research 香港物理治療\n\n"
            "呢個功能會同時搜索小紅書同 IMA，然後用 AI 生成一份深度研究報告。"
        )
        return

    # 檢查 Browser Service 設定
    if not BROWSER_API_KEY:
        await update.message.reply_text(
            "⚠️ 深度研究功能未啟用。\n"
            "請先設定 BROWSER_API_KEY 環境變數。"
        )
        return

    user_id = update.effective_user.id
    logger.info("用戶 %s 發起深度研究：%s", user_id, keyword)

    # 第一步：通知用戶
    await update.message.reply_text(
        f"🔬 收到！我而家去幫你研究「{keyword}」，請等等...\n\n"
        f"⏳ 大約需要 1-2 分鐘，我會同時搜索：\n"
        f"  • 小紅書（社交媒體觀點）\n"
        f"  • IMA（騰訊 AI 搜索）\n\n"
        f"搜索完成後會用 AI 生成一份綜合研究報告。"
    )

    await update.message.chat.send_action("typing")

    # 第二步：同時發請求去兩個 endpoint
    xhs_payload = {
        "keyword": keyword,
        "max_posts": 10,
        "cookies": XHS_COOKIES,
    }
    ima_payload = {
        "keyword": keyword,
    }

    # 用 asyncio.gather 同時發兩個請求
    xhs_task = call_browser_service("/research/xiaohongshu", xhs_payload, timeout=180)
    ima_task = call_browser_service("/research/ima", ima_payload, timeout=60)

    try:
        xhs_result, ima_result = await asyncio.gather(xhs_task, ima_task)
    except Exception as e:
        logger.error("深度研究請求失敗：%s", e)
        await update.message.reply_text(f"❌ 深度研究請求失敗：{e}")
        return

    # 第三步：格式化結果
    xhs_text = format_xhs_results(xhs_result)
    ima_text = format_ima_results(ima_result)

    # 發送中間狀態
    xhs_count = xhs_result.get("total_scraped", 0) if isinstance(xhs_result, dict) else 0
    ima_count = len(ima_result.get("results", [])) if isinstance(ima_result, dict) else 0

    await update.message.reply_text(
        f"📡 數據收集完成！\n"
        f"  • 小紅書：成功抓取 {xhs_count} 個帖子\n"
        f"  • IMA：搵到 {ima_count} 個結果\n\n"
        f"🤖 正在用 AI 生成研究報告..."
    )

    await update.message.chat.send_action("typing")

    # 第四步：用 AI 生成研究報告
    report = await generate_research_report(keyword, xhs_text, ima_text)

    # 第五步：發送報告（處理 Telegram 4096 字符限制）
    if len(report) <= 4096:
        await update.message.reply_text(report)
    else:
        # 分段發送
        chunks = []
        current_chunk = ""
        for line in report.split("\n"):
            if len(current_chunk) + len(line) + 1 > 4000:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += "\n" + line if current_chunk else line
        if current_chunk:
            chunks.append(current_chunk)

        for i, chunk in enumerate(chunks):
            if i == 0:
                await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(f"（續 {i + 1}/{len(chunks)}）\n\n{chunk}")

    logger.info("用戶 %s 嘅深度研究完成：%s", user_id, keyword)


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
        "已載入" if user_memory_loaded[user_id] else "未載入",
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
    logger.info("二號龍蝦 v3 正在啟動...")

    # 初始化數據庫
    init_database()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 指令處理器 — 基本
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("glm", cmd_glm))
    app.add_handler(CommandHandler("opus", cmd_opus))
    app.add_handler(CommandHandler("speak", cmd_speak))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("forget", cmd_forget))
    app.add_handler(CommandHandler("save", cmd_save))
    app.add_handler(CommandHandler("recall", cmd_recall))
    app.add_handler(CommandHandler("delmemory", cmd_delmemory))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("model", cmd_model))

    # 指令處理器 — 新功能
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("browse", cmd_browse))
    app.add_handler(CommandHandler("doc", cmd_doc))
    app.add_handler(CommandHandler("doclist", cmd_doclist))

    # v3 新增：深度研究
    app.add_handler(CommandHandler("research", cmd_research))

    # 文字訊息處理器
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 錯誤處理器
    app.add_error_handler(error_handler)

    logger.info("二號龍蝦 v3 已經準備好，開始接收訊息！")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
