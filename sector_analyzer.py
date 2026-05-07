import yfinance as yf
import pandas as pd
import requests
import os

# --- 設定 ---
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

# 東証セクター別ETF（代表的な17業種）
SECTORS = {
    "1617.T": "食品",
    "1618.T": "エネルギー",
    "1619.T": "建設・資材",
    "1620.T": "素材・化学",
    "1621.T": "医薬品",
    "1622.T": "自動車・輸送",
    "1623.T": "鉄鋼・非鉄",
    "1624.T": "機械",
    "1625.T": "電機・精密",
    "1626.T": "情報・通信",
    "1627.T": "電力・ガス",
    "1628.T": "運輸・物流",
    "1629.T": "商社・卸売",
    "1630.T": "小売",
    "1631.T": "銀行",
    "1632.T": "金融（除く銀行）",
    "1633.T": "不動産"
}

def send_discord(message):
    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
    else:
        print("Webhook URLが設定されていません。")

def analyze_sectors():
    results = []
    print("📊 セクター分析を開始...")

    for ticker, name in SECTORS.items():
        try:
            # 過去1ヶ月分のデータを取得
            df = yf.download(ticker, period="1mo", progress=False)
            if len(df) < 10: continue

            # ✅ 新コード（MultiIndex・通常形式どちらでも動作）
            close = df['Close']
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]  # MultiIndexの場合、最初のカラム（=そのticker）を取り出す

            current_price = float(close.iloc[-1])
            price_5d_ago  = float(close.iloc[-5])
            price_20d_ago = float(close.iloc[0])

            # 騰落率の計算
            perf_5d = ((current_price / price_5d_ago) - 1) * 100
            perf_20d = ((current_price / price_20d_ago) - 1) * 100

            results.append({
                "name": name,
                "perf_5d": float(perf_5d),
                "perf_20d": float(perf_20d)
            })
        except Exception as e:
            print(f"Error {ticker}: {e}")
            continue

    if not results:
        print("分析対象のデータが得られませんでした。")
        return

    # 1週間のパフォーマンス順にソート
    results = sorted(results, key=lambda x: x['perf_5d'], reverse=True)

    # メッセージ作成
    msg = "[302_sector_analyzer] 📅 **週刊【セクター別資金流向レポート】** 📈📉\n"
    msg += "直近1週間の業種別騰落率ランキング\n"
    msg += "----------------------------------\n"
    
    msg += "🔥 **買われているセクター (TOP 5)**\n"
    for i, r in enumerate(results[:5]):
        msg += f"{i+1}. {r['name']}: +{r['perf_5d']:.2f}% (月間: {r['perf_20d']:.1f}%)\n"

    msg += "\n❄️ **売られているセクター (BOTTOM 5)**\n"
    for r in results[-5:]:
        msg += f"・{r['name']}: {r['perf_5d']:.2f}% (月間: {r['perf_20d']:.1f}%)\n"

    msg += "----------------------------------\n"
    msg += "💡 資金が入っているセクターの銘柄は、リバウンドも早い傾向があります。"

    send_discord(msg)
    print("✅ 分析レポートを送信しました。")

if __name__ == "__main__":
    analyze_sectors()
