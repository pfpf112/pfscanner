import requests
import json
import time
from solana.rpc.api import Client
from telebot import TeleBot
import os
from flask import Flask, jsonify

# Configuration from environment variables
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"  # Update if using a private RPC
PUMP_FUN_PROGRAM_ID = "PUMP_FUN_PROGRAM_ID_HERE"  # Replace with actual program ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Securely stored
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Your private Telegram ID

solana_client = Client(SOLANA_RPC_URL)
telegram_bot = TeleBot(TELEGRAM_BOT_TOKEN)

# Flask Web UI
app = Flask(__name__)
detected_tokens = []

def get_recent_transactions():
    try:
        response = solana_client.get_signatures_for_address(PUMP_FUN_PROGRAM_ID, limit=5)
        if "result" in response:
            return [tx["signature"] for tx in response["result"]]
        return []
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return []


def get_transaction_details(signature):
    try:
        response = solana_client.get_transaction(signature, encoding='json')
        if "result" in response:
            return response["result"]
        return None
    except Exception as e:
        print(f"Error fetching transaction details: {e}")
        return None


def extract_token_info(transaction):
    try:
        instructions = transaction["transaction"]["message"]["instructions"]
        for instr in instructions:
            if "programId" in instr and instr["programId"] == PUMP_FUN_PROGRAM_ID:
                return instr  # Modify to extract relevant token details
    except Exception as e:
        print(f"Error extracting token info: {e}")
    return None


def send_to_telegram(token_info):
    try:
        message = f"New Token Launched on Pump.fun!\nDetails: {json.dumps(token_info, indent=2)}"
        telegram_bot.send_message(TELEGRAM_CHAT_ID, message)
        detected_tokens.append(token_info)
        print("Sent to Telegram:", message)
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")


def main():
    processed_tx = set()
    while True:
        transactions = get_recent_transactions()
        for tx in transactions:
            if tx not in processed_tx:
                transaction_details = get_transaction_details(tx)
                if transaction_details:
                    token_info = extract_token_info(transaction_details)
                    if token_info:
                        send_to_telegram(token_info)
                        processed_tx.add(tx)
        time.sleep(30)  # Check every 30 seconds


@app.route("/tokens", methods=["GET"])
def get_detected_tokens():
    return jsonify(detected_tokens)

if __name__ == "__main__":
    from threading import Thread
    Thread(target=main).start()
    app.run(host="0.0.0.0", port=5000)
