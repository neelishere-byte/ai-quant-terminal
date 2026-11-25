
# AI QUANT TERMINAL
# Historical Market Data Collector v1.0
# Free development / Research only

import os
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

OUTPUT_DIR = "historical_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initial global market symbols
MARKETS = {
    "INDIA_STOCKS": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS",
        "INFY.NS", "ICICIBANK.NS", "SBIN.NS"
    ],
    "US_STOCKS": [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"
    ],
    "FOREX": [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"
    ],
    "CRYPTO": [
        "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"
    ],
    "METALS": [
        "GC=F", "SI=F", "HG=F"
    ],
    "ENERGY": [
        "CL=F", "BZ=F", "NG=F"
    ],
    "INDICES": [
        "^NSEI", "^BSESN", "^GSPC", "^IXIC", "^DJI"
    ]
}

def validate_data(df):
    if df.empty:
        return False, "No data returned"

    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        return False, f"Missing columns: {missing}"

    if df["Close"].isna().all():
        return False, "All closing prices are missing"

    if (df["High"].dropna() < df["Low"].dropna()).any():
        return False, "Invalid High/Low values"

    return True, "Data validation passed"

def collect_symbol(symbol, market):
    print(f"\nDownloading: {symbol} [{market}]")

    try:
        df = yf.download(
            symbol,
            period="10y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )

        # Handle possible MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty:
            print("FAILED: No data available")
            return None

        df = df.reset_index()
        df.columns = [str(c) for c in df.columns]

        ok, message = validate_data(df.set_index("Date"))

        if not ok:
            print("FAILED:", message)
            return None

        filename = f"{symbol.replace('^','').replace('=','_').replace('-','_')}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)

        df.to_csv(filepath, index=False)

        result = {
            "symbol": symbol,
            "market": market,
            "rows": len(df),
            "first_date": str(df["Date"].min()),
            "last_date": str(df["Date"].max()),
            "file": filepath,
            "status": "SUCCESS"
        }

        print("SUCCESS:", result["rows"], "rows saved")
        return result

    except Exception as e:
        print("ERROR:", str(e))
        return None

def main():
    results = []

    for market, symbols in MARKETS.items():
        print("\n==========", market, "==========")

        for symbol in symbols:
            result = collect_symbol(symbol, market)

            if result:
                results.append(result)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance via yfinance",
        "period": "10y requested; actual available history may vary",
        "interval": "1d",
        "successful_downloads": len(results),
        "results": results
    }

    with open(
        os.path.join(OUTPUT_DIR, "collection_report.json"),
        "w"
    ) as f:
        json.dump(report, f, indent=2)

    print("\n========== FINAL REPORT ==========")
    print("Successful symbols:", len(results))
    print("Saved in:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
