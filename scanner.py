"""Batch job: refreshes docs/stocks.json (one summary row per NSE stock).
Usage: python scanner.py [--rebuild] [--max-minutes 300]
Resumable: progress is saved after every chunk; re-running continues where it stopped.
"""
import argparse, io, json, os, time, datetime as dt
import pandas as pd, requests, yfinance as yf

OUT = os.path.join("docs", "stocks.json")
NSE_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
store = {"stocks": {}, "nodata": {}, "updated": None, "complete": False}
d_ = lambda ts: ts.strftime("%Y-%m-%d")

def save():
    os.makedirs("docs", exist_ok=True)
    with open(OUT + ".tmp", "w") as f: json.dump(store, f, separators=(",", ":"))
    os.replace(OUT + ".tmp", OUT)

def universe():
    for attempt in range(3):
        try:
            r = requests.get(NSE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            r.raise_for_status(); open("EQUITY_L.csv", "w", encoding="utf-8").write(r.text); break
        except Exception:
            time.sleep(3)
    if not os.path.exists("EQUITY_L.csv"):
        raise SystemExit("Could not get EQUITY_L.csv from NSE; commit a copy to the repo root as a fallback.")
    df = pd.read_csv("EQUITY_L.csv"); df.columns = [c.strip() for c in df.columns]
    df = df[df["SERIES"].str.strip().isin(["EQ", "BE", "BZ", "SM", "ST"])]
    return dict(zip(df["SYMBOL"].str.strip(), df["NAME OF COMPANY"].str.strip()))

def fetch(symbols, period):
    for attempt in range(3):
        try:
            raw = yf.download([s + ".NS" for s in symbols], period=period, interval="1d", group_by="ticker",
                              auto_adjust=False, threads=True, progress=False)
            break
        except Exception:
            time.sleep(10 * (attempt + 1)); raw = None
    out = {}
    if raw is None or len(raw) == 0: return out
    for s in symbols:
        try:
            df = raw[s + ".NS"][["Open", "High", "Low", "Close"]].dropna()
            df = df[(df.Open > 0) & (df.High > 0) & (df.Close > 0)]
            if len(df): out[s] = df
        except Exception: pass
    return out

def summarize(df, name):
    return dict(name=name, first_date=d_(df.index[0]), listing=float(df.Open.iloc[0]),
                max_close=float(df.Close.max()), ath=float(df.High.max()), ath_date=d_(df.High.idxmax()),
                last=float(df.Close.iloc[-1]), last_date=d_(df.index[-1]))

def merge(old, df):
    same = df[[d_(i) == old["last_date"] for i in df.index]]
    if len(same) and abs(same.Close.iloc[0] / old["last"] - 1) > 0.01: return None  # split/bonus suspected
    old["max_close"] = max(old["max_close"], float(df.Close.max()))
    if df.High.max() > old["ath"]: old["ath"] = float(df.High.max()); old["ath_date"] = d_(df.High.idxmax())
    old["last"] = float(df.Close.iloc[-1]); old["last_date"] = d_(df.index[-1])
    return old

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--max-minutes", type=float, default=300); a = ap.parse_args()
    t0 = time.time(); over = lambda: (time.time() - t0) / 60 > a.max_minutes
    if os.path.exists(OUT) and not a.rebuild: store.update(json.load(open(OUT)))
    uni = universe(); st = store["stocks"]
    for s in [s for s in st if s not in uni]: del st[s]
    redo, existing = [], [s for s in uni if s in st]
    if existing:
        latest = max(st[s]["last_date"] for s in existing)
        gap = (dt.date.today() - dt.date.fromisoformat(latest)).days
        period = "5d" if gap <= 4 else "1mo" if gap <= 25 else "3mo" if gap <= 80 else "1y" if gap <= 350 else None
        if period is None: redo = existing
        else:
            print("updating", len(existing), "stocks, period", period, flush=True)
            for i in range(0, len(existing), 200):
                for s, df in fetch(existing[i:i+200], period).items():
                    if merge(st[s], df) is None: redo.append(s)
            save()
    now = time.time()
    store["nodata"] = {s: t for s, t in store["nodata"].items() if now - t < 7 * 86400}
    todo = redo + [s for s in uni if s not in st and s not in store["nodata"]]
    print("full history needed for", len(todo), flush=True)
    for i in range(0, len(todo), 50):
        if over(): print("time budget reached; partial save"); break
        chunk = todo[i:i+50]; got = fetch(chunk, "max")
        for s in chunk:
            if s in got: st[s] = summarize(got[s], uni[s])
            else: store["nodata"][s] = now
        save(); print(i + len(chunk), "/", len(todo), flush=True); time.sleep(1)
    for s in st: st[s]["name"] = uni.get(s, st[s].get("name", ""))
    store["complete"] = not any(s not in st and s not in store["nodata"] for s in uni)
    store["updated"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    save(); print("done:", len(st), "stocks")

if __name__ == "__main__": main()
