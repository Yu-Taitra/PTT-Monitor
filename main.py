import requests
from bs4 import BeautifulSoup
import os
import json

# 讀取設定
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
user_id = os.environ.get("DISCORD_USER_ID")

# 設定關鍵字
KEYWORDS = ["5700X3D", "5700x3d"]
HISTORY_FILE = "history.json"

def send_discord(msg, link):
    if not webhook_url: return

    # 這裡判斷要不要 Tag 你
    content = f"<@{user_id}> {msg}" if user_id else msg

    data = {
        "content": content,
        "embeds": [{
            "title": "前往 PTT 文章",
            "url": link,
            "color": 16711680 # 紅色
        }]
    }
    requests.post(webhook_url, json=data)

def main():
    # 讀取歷史紀錄
    seen = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            seen = set(json.load(f))

    new_seen = seen.copy()
    updated = False

    headers = {"User-Agent": "Mozilla/5.0", "Cookie": "over18=1"}
    print("檢查中...")

    try:
        resp = requests.get("https://www.ptt.cc/bbs/HardwareSale/index.html", headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        for div in soup.find_all("div", class_="r-ent"):
            title_div = div.find("div", class_="title")
            if not title_div or not title_div.a: continue

            title = title_div.a.text.strip()
            link = "https://www.ptt.cc" + title_div.a["href"]

            # 篩選條件：要有 [賣] 或 [售]，且包含關鍵字
            if ("[賣" in title or "[售" in title) and any(k in title for k in KEYWORDS):
                if link not in seen:
                    print(f"找到: {title}")
                    send_discord(f"🚨 **發現 5700X3D！**\n標題: `{title}`", link)
                    new_seen.add(link)
                    updated = True

        # 儲存紀錄
        if updated:
            with open(HISTORY_FILE, "w") as f:
                json.dump(list(new_seen), f)
            print("紀錄已更新")
        else:
            print("無新文章")

    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    main()
