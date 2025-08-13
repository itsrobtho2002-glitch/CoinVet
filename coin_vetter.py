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
        hdrs = {"API-KEY": GOPLUS_API_KEY} if GOPLUS_API_KEY else {}
        r = requests.get(url, headers=hdrs, timeout=30)
        if r.status_code == 200:
            body = r.json()
            result = body.get("result")
            found = None
            if isinstance(result, dict):
                found = result.get(ca.lower())
            elif isinstance(result, list) and result:
                found = result[0]
            if found:
                return chain_id
    return None

def get_goplus_data(chain_id, ca):
    """Fetch token security info from GoPlus API"""
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={ca}"
    hdrs = {"API-KEY": GOPLUS_API_KEY} if GOPLUS_API_KEY else {}
    r = requests.get(url, headers=hdrs, timeout=30)
    if r.status_code != 200:
        return None
    result = r.json().get("result")
    if isinstance(result, dict):
        return result.get(ca.lower())
    if isinstance(result, list) and result:
        return result[0]
    return None

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
    r = requests.get(url, headers={"X-API-Key": MORALIS_API_KEY}, timeout=30)
    if r.status_code != 200:
        return None
    return r.json().get("result") or r.json().get("items") or []

def classify_buy_zone_from_goplus(gp):
    """Very simple liquidity/tax/honeypot check for buy-zone color."""
    if not gp:
        return "YELLOW", "No GoPlus data (check chain/CA)"
    try:
        liquidity = float(gp.get("liquidity_usd", 0) or 0)
    except Exception:
        liquidity = 0.0
    try:
        buy_tax = float(gp.get("buy_tax", 0) or 0)
        sell_tax = float(gp.get("sell_tax", 0) or 0)
    except Exception:
        buy_tax = sell_tax = 0.0

    honeypot = str(gp.get("is_honeypot", "0")).lower() in ("1","true","yes")

    if honeypot:
        return "RED", "Honeypot risk — do not buy"

    if liquidity < 5000 or buy_tax > 10 or sell_tax > 10:
        return "RED", "Low liquidity or high taxes"

    if 5000 <= liquidity <= 20000 and buy_tax <= 5 and sell_tax <= 5:
        return "YELLOW", "Medium liquidity, moderate taxes"

    if liquidity > 20000 and buy_tax <= 5 and sell_tax <= 5:
        return "GREEN", "Higher liquidity, low taxes"

    return "YELLOW", "Mixed signals — review details"

def analyze_contract(ca):
    """Main analysis function used by CLI and app."""
    chain_id = detect_chain(ca)
    if not chain_id:
        return f"❌ Could not detect chain for CA: {ca}"

    chain_name = CHAIN_IDS[chain_id]
    goplus_data = get_goplus_data(chain_id, ca)
    holders_data = get_holders_data(chain_id, ca)
    zone, reason = classify_buy_zone_from_goplus(goplus_data)

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
        pct = top_holder.get("percentage") or top_holder.get("percent") or "N/A"
        output.append(["Top Holder %", pct])

    print(tabulate(output, headers=["Metric", "Value"], tablefmt="pretty"))
    return {"chain_id": chain_id, "chain_name": chain_name, "goplus": goplus_data, "holders": holders_data, "buy_zone": (zone, reason)}

if __name__ == "__main__":
    ca_input = input("Enter Contract Address: ").strip()
    analyze_contract(ca_input)
