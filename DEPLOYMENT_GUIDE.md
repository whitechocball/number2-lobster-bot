# 🦞 二號龍蝦 Telegram Bot 部署指南（Railway 版）

你好！呢份指南會教你點樣一步步將「二號龍蝦」呢個 Telegram Bot 部署到 Railway 雲端平台上面。就算你完全冇編程經驗都唔使驚，跟住下面嘅步驟做就得㗎啦！

---

### 部署前準備

喺開始之前，請你確保已經準備好以下幾樣嘢：

1.  **Telegram 帳戶**：用嚟創建同管理你嘅 Bot。
2.  **GitHub 帳戶**：用嚟存放我哋嘅程式碼。 [註冊 GitHub](https://github.com/signup)
3.  **Railway 帳戶**：用嚟部署同運行我哋嘅 Bot。你可以用 GitHub 帳戶直接登入。 [前往 Railway](https://railway.app)
4.  **OpenRouter 帳戶**：用嚟獲取 AI 模型嘅 API Key。 [註冊 OpenRouter](https://openrouter.ai/signup)

---

### 部署步驟

#### 第 1 步：準備程式碼

我已經將所有需要嘅檔案（`main.py`, `requirements.txt`, `Procfile` 等）都準備好，並會將佢哋壓縮成一個 `.zip` 檔案交俾你。請你先將呢個檔案下載到你嘅電腦，然後解壓縮。

#### 第 2 步：獲取所需嘅鎖匙（API Keys）

我哋需要兩條鎖匙，Bot 先可以正常運作。

##### A. 獲取 Telegram Bot Token

1.  打開 Telegram，搜尋 `BotFather`（佢係 Telegram 官方用嚟管理 Bot 嘅 Bot）。
2.  向 `BotFather` 發送指令 `/newbot`。
3.  跟住佢嘅提示，首先為你嘅 Bot 改個名，你可以入 `二號龍蝦`。
4.  然後，為你嘅 Bot 設定一個獨一無二嘅用戶名（username），呢個名一定要用 `_bot` 結尾，例如 `LobsterNumber2_bot`。
5.  搞掂之後，`BotFather` 就會俾你一串好長嘅 **Token**。呢個就係你嘅 `TELEGRAM_BOT_TOKEN`，請即刻將佢複製起嚟，擺喺一個安全嘅地方，千祈唔好洩漏俾人！

![BotFather Token](https://i.imgur.com/Vz35a2G.png)

##### B. 獲取 OpenRouter API Key

1.  登入你嘅 [OpenRouter](https://openrouter.ai/) 帳戶。
2.  點擊右上角你嘅頭像，然後選擇 `Keys`。
3.  點擊 `Create Key` 按鈕。
4.  為你嘅鎖匙改個名（例如 `LobsterBotKey`），然後點擊 `Create`。
5.  OpenRouter 會產生一條以 `sk-or-` 開頭嘅 **API Key**。呢個就係你嘅 `OPENROUTER_API_KEY`，同樣請即刻複製好，擺喺安全嘅地方。

![OpenRouter Key](https://i.imgur.com/sO8n1h1.png)

#### 第 3 步：將程式碼上傳到 GitHub

1.  登入你嘅 GitHub 帳戶。
2.  點擊右上角嘅 `+` 號，選擇 `New repository`。
3.  為你嘅 repository（程式碼倉庫）改個名，例如 `my-lobster-bot`，然後將佢設定為 `Private`（私人），咁樣其他人就睇唔到你嘅程式碼。
4.  點擊 `Create repository`。
5.  喺新開嘅 repository 頁面，點擊 `uploading an existing file`。
6.  將你喺第 1 步解壓縮嘅所有檔案（`main.py`, `requirements.txt`, `Procfile`, `railway.json`, `runtime.txt`, `.gitignore`）一次過拖曳到上傳區域。
7.  等所有檔案上傳完畢後，點擊 `Commit changes`。

![GitHub Upload](https://i.imgur.com/iXG3y5g.png)

#### 第 4 步：喺 Railway 部署 Bot

1.  前往 [Railway](https://railway.app) 網站，用你嘅 GitHub 帳戶登入。
2.  喺主頁點擊 `New Project`。
3.  選擇 `Deploy from GitHub repo`。
4.  Railway 會要求你授權連接到你嘅 GitHub 帳戶。授權之後，喺列表度揀返你喺第 3 步創建嘅 repository（例如 `my-lobster-bot`）。
5.  Railway 會即刻開始分析同部署你嘅項目。呢個過程可能需要幾分鐘。

#### 第 5 步：設定環境變數

部署開始之後，我哋要將頭先攞到嘅兩條鎖匙加入去。

1.  喺你嘅 Railway 項目頁面，點擊 `Variables` 分頁。
2.  點擊 `New Variable`。
3.  我哋需要加兩個變數：
    *   **第一個變數**：
        *   `Variable Name`：`TELEGRAM_BOT_TOKEN`
        *   `Value`：貼上你喺第 2 步 A 部分攞到嘅 Telegram Bot Token。
    *   **第二個變數**：
        *   `Variable Name`：`OPENROUTER_API_KEY`
        *   `Value`：貼上你喺第 2 步 B 部分攞到嘅 OpenRouter API Key。

4.  加完之後，Railway 會自動重新部署你嘅 Bot。等部署完成（你會見到綠色嘅剔號同 `Active` 狀態）。

![Railway Variables](https://i.imgur.com/pBwZz3f.png)

---

### 第 6 步：大功告成！

恭喜你！你嘅「二號龍蝦」Bot 已經成功部署並且運行緊啦！

而家，你可以返去 Telegram，搜尋你個 Bot 嘅用戶名（例如 `LobsterNumber2_bot`），然後向佢發送 `/start` 指令，睇下佢係咪識得覆你。如果識，就代表一切順利！

### 常見問題

*   **Bot 冇反應？**
    *   返去 Railway 項目嘅 `Deployments` 分頁，睇下有冇任何錯誤日誌（Logs）。
    *   檢查下 `Variables` 裡面嘅兩條鎖匙係咪貼啱咗，有冇多咗空格或者少咗字元。
*   **點樣更新 Bot 嘅程式碼？**
    *   如果我將來提供咗更新版本嘅程式碼，你只需要重複第 3 步，將新嘅檔案上傳到 GitHub 覆蓋舊檔案，Railway 就會自動幫你重新部署。

希望呢份指南幫到你！享受同「二號龍蝦」傾偈嘅樂趣啦！🎉
