import json
import os
import urllib.request
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
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode("utf-8"))
    if data.get("returnValue") == "success":
        return data
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
    for r in [latest_round, latest_round - 1]:
        print(f"  Fetching round {r}...")
        data = fetch_lotto_data(r)
        if data:
            print(f"  OK: {data['drwtNo1']},{data['drwtNo2']},{data['drwtNo3']},{data['drwtNo4']},{data['drwtNo5']},{data['drwtNo6']}+{data['bnusNo']}")
            break
    if not data:
        print("Failed to fetch data")
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
