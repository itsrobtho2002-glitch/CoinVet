import os
import requests
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()
GOPLUS_API_KEY = os.getenv("GOPLUS_API_KEY")
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

# Supported chains
CHAIN_IDS = {
    "1": "Ethereum",
    "56": "BSC",
    "137": "Polygon",
    "42161": "Arbitrum",
    "8453": "Base",
    "10": "Optimism"
}

def detect_chain(ca):
    """Auto-detect chain by querying GoPlus on all supported chains"""
    for chain_id in CHAIN_IDS.keys():
        url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={ca}"
        r = requests.get(url, headers={"API-KEY": GOPLUS_API_KEY})
        if r.status_code == 200 and r.json().get("result"):
            data = r.json()["result"].get(ca.lower())
            if data:
                return chain_id
    return None

def get_goplus_data(chain_id, ca):
    """Fetch token security info from GoPlus API"""
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={ca}"
    r = requests.get(url, headers={"API-KEY": GOPLUS_API_KEY})
    if r.status_code != 200:
        return None
    data = r.json().get("result", {}).get(ca.lower())
    return data

def get_holders_data(chain_id, ca):
    """Fetch holder distribution from Moralis API (if available)"""
    if not MORALIS_API_KEY:
        return None
    moralis_chain = {
        "1": "eth",
        "56": "bsc",
        "137": "polygon",
        "42161": "arbitrum",
        "8453": "base",
        "10": "optimism"
    }.get(chain_id)
    if not moralis_chain:
        return None

    url = f"https://deep-index.moralis.io/api/v2/token/{ca}/holders?chain={moralis_chain}&limit=10"
    r = requests.get(url, headers={"X-API-Key": MORALIS_API_KEY})
    if r.status_code != 200:
        return None
    return r.json().get("result", [])

def classify_buy_zone(data):
    """Classify Buy-Zone based on liquidity, taxes, and honeypot status"""
    if not data:
        return "UNKNOWN", "No data available"

    liquidity = float(data.get("liquidity_usd", 0))
    buy_tax = float(data.get("buy_tax", 0))
    sell_tax = float(data.get("sell_tax", 0))
    honeypot = data.get("is_honeypot", "0") == "1"

    if honeypot:
        return "RED", "Honeypot detected — DO NOT BUY"

    if liquidity < 5000 or buy_tax > 10 or sell_tax > 10:
        return "RED", "Low liquidity or high taxes"

    if 5000 <= liquidity <= 20000 and buy_tax <= 5 and sell_tax <= 5:
        return "YELLOW", "Medium liquidity, moderate taxes"

    if liquidity > 20000 and buy_tax <= 5 and sell_tax <= 5:
        return "GREEN", "High liquidity, low taxes"

    return "YELLOW", "Check details manually"

def analyze_contract(ca):
    """Main analysis function"""
    chain_id = detect_chain(ca)
    if not chain_id:
        return f"❌ Could not detect chain for CA: {ca}"

    chain_name = CHAIN_IDS[chain_id]
    goplus_data = get_goplus_data(chain_id, ca)
    holders_data = get_holders_data(chain_id, ca)
    zone, reason = classify_buy_zone(goplus_data)

    output = []
    output.append(["Contract Address", ca])
    output.append(["Chain", chain_name])
    output.append(["Buy-Zone", f"{zone} — {reason}"])
    if goplus_data:
        output.append(["Liquidity (USD)", goplus_data.get("liquidity_usd", "N/A")])
        output.append(["Buy Tax (%)", goplus_data.get("buy_tax", "N/A")])
        output.append(["Sell Tax (%)", goplus_data.get("sell_tax", "N/A")])
        output.append(["Honeypot", goplus_data.get("is_honeypot", "N/A")])
        output.append(["Owner Renounced", goplus_data.get("owner_renounced", "N/A")])
    if holders_data:
        top_holder = holders_data[0]
        output.append(["Top Holder %", top_holder.get("percentage", "N/A")])

    print(tabulate(output, headers=["Metric", "Value"], tablefmt="pretty"))
    return {"chain_id": chain_id, "chain_name": chain_name, "goplus": goplus_data, "holders": holders_data, "buy_zone": (zone, reason)}

if __name__ == "__main__":
    ca_input = input("Enter Contract Address: ").strip()
    analyze_contract(ca_input)
