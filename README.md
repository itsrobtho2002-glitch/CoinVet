# Coin Vetter (Auto Chain Detect + Buy-Zone)

Paste a token contract address and this tool will:
- Auto-detect the blockchain (ETH/BSC/Polygon/Arbitrum/Base/Optimism) using GoPlus lookups
- Pull security/taxes (GoPlus)
- (Optional) Top holders (Moralis)
- Classify a simple Buy-Zone (GREEN/YELLOW/RED) based on liquidity/taxes/honeypot
- Render an easy web UI

## Quick Start (local)

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.sample .env          # then edit .env with your keys
python app.py
```

Open the printed URL and paste a contract address.

## Replit

- Import this repo to a Python Repl
- Add `GOPLUS_API_KEY` (+ optional `MORALIS_API_KEY`) in **Secrets**
- Run:
  ```
  pip install -r requirements.txt
  python app.py
  ```

## Security

Never commit real API keys to a public repo. Keep them in `.env` (not tracked because of `.gitignore`) or in Replit Secrets.
