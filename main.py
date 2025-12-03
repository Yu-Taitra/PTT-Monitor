import requests
from bs4 import BeautifulSoup
import os
import json
import time
import random

# 讀取設定
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
user_id = os.environ.get("DISCORD_USER_ID")

# 設定關鍵字
KEYWORDS = ["5700X3D", "5700x3d"]
HISTORY_FILE = "history.json"

def send_discord(msg, link):
    if not webhook_url: return
    
    content = f"<@{user_id}> {msg}" if user_id else msg
    
    data = {
        "content": content,
        "embeds": [{
            "title": "前往 PTT 文章",
            "url": link,
            "color": 16711680
        }]
    }
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Discord 通知發送失敗: {e}")

def get_page_content(url, max_retries=3):
    """
    不死鳥請求功能：
    如果連線失敗，會自動重試 3 次
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "over18=1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    for i in range(max_retries):
        try:
            # 隨機延遲 1~3 秒，模擬人類行為
            time.sleep(random.uniform(1, 3)) 
            
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp
            else:
                print(f"連線狀態碼非 200: {resp.status_code}，重試中 ({i+1}/{max_retries})...")
        
        except Exception as e:
            print(f"連線錯誤: {e}，重試中 ({i+1}/{max_retries})...")
            # 失敗後休息久一點 (5~10秒) 再試
            time.sleep(random.uniform(5, 10))
    
    return None

def main():
    seen = set()
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            seen = set(json.load(f))

    new_seen = seen.copy()
    updated = False

    print("準備檢查 PTT...")
    
    # 使用新的請求函數
    resp = get_page_content("https://www.ptt.cc/bbs/HardwareSale/index.html")
    
    if resp:
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            posts = soup.find_all("div", class_="r-ent")
            
            # 如果抓不到文章列表，可能是被擋了，或是結構改變
            if not posts:
                print("警報：抓取成功但找不到文章列表 (可能遇到 Cloudflare 驗證)")
            
            for div in posts:
                title_div = div.find("div", class_="title")
                if not title_div or not title_div.a: continue
                
                title = title_div.a.text.strip()
                link = "https://www.ptt.cc" + title_div.a["href"]
                
                if ("[賣" in title or "[售" in title) and any(k in title for k in KEYWORDS):
                    if link not in seen:
                        print(f"找到目標: {title}")
                        send_discord(f"🚨 **發現 5700X3D！**\n標題: `{title}`", link)
                        new_seen.add(link)
                        updated = True
            
            if updated:
                with open(HISTORY_FILE, "w") as f:
                    json.dump(list(new_seen), f)
                print("紀錄已更新")
            else:
                print("檢查完畢，無新文章")

        except Exception as e:
            print(f"解析錯誤: {e}")
    else:
        print("三次重試皆失敗，本次放棄，等待下個 15 分鐘。")

if __name__ == "__main__":
    main()
