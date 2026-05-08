import json
import os
import urllib.request
import ssl
import firebase_admin
from firebase_admin import credentials, db

def get_latest_round():
    from datetime import datetime, timezone, timedelta
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    base_date = datetime(2026, 5, 2, 20, 35, 0, tzinfo=kst)
    base_round = 1222
    diff_days = (now - base_date).days
    extra_rounds = diff_days // 7
    return base_round + extra_rounds

def fetch_lotto_data(round_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_no}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.dhlottery.co.kr/gameResult.do?method=byWin"
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as res:
            raw = res.read().decode("utf-8")
            print(f"  Response length: {len(raw)}, starts with: {raw[:50]}")
            if raw.strip().startswith("{"):
                data = json.loads(raw)
                if data.get("returnValue") == "success":
                    return data
            else:
                print(f"  Not JSON response")
    except Exception as e:
        print(f"  Error fetching round {round_no}: {e}")
    return None

def main():
    service_account = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
    cred = credentials.Certificate(service_account)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://lotto-lab-495701-default-rtdb.firebaseio.com"
    })
    latest_round = get_latest_round()
    print(f"Latest round estimate: {latest_round}")
    data = None
    for r in [latest_round, latest_round - 1, latest_round - 2]:
        print(f"  Trying round {r}...")
        data = fetch_lotto_data(r)
        if data:
            print(f"  Found: {data['drwtNo1']},{data['drwtNo2']},{data['drwtNo3']},{data['drwtNo4']},{data['drwtNo5']},{data['drwtNo6']}+{data['bnusNo']}")
            break
    if not data:
        print("Failed to fetch any round data")
        return
    ref = db.reference("latestDraw")
    ref.set({
        "drwNo": data["drwNo"],
        "drwtNo1": data["drwtNo1"],
        "drwtNo2": data["drwtNo2"],
        "drwtNo3": data["drwtNo3"],
        "drwtNo4": data["drwtNo4"],
        "drwtNo5": data["drwtNo5"],
        "drwtNo6": data["drwtNo6"],
        "bnusNo": data["bnusNo"],
        "drwNoDate": data.get("drwNoDate", ""),
        "firstWinamnt": data.get("firstWinamnt", 0),
        "firstPrzwnerCo": data.get("firstPrzwnerCo", 0),
        "totSellamnt": data.get("totSellamnt", 0),
        "updatedAt": int(__import__("time").time() * 1000)
    })
    print(f"Firebase updated: round {data['drwNo']}")

if __name__ == "__main__":
    main()
