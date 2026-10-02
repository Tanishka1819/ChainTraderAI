from flask import Flask, render_template, jsonify, request
import json
import os
import numpy as np
import time
import threading
from models.blockchain import TradingBlockchain
from models.ai_trader import AITrader
from data.data_fetcher import CryptoDataFetcher

app = Flask(__name__)

# -------------------------------------------------------
# INITIALIZE SYSTEM COMPONENTS
# -------------------------------------------------------
blockchain = TradingBlockchain()
data_fetcher = CryptoDataFetcher()
SYMBOLS = list(data_fetcher.symbols.keys())
ai_traders = {symbol: AITrader() for symbol in SYMBOLS}

portfolio = {
    'balance': 100000.0,  # Starting balance
    'holdings': {symbol: 0.0 for symbol in SYMBOLS},
    'total_trades': 0,
    'profit_loss': 0.0
}

# Seed initial holdings
portfolio['holdings'].update({
    'BTC': 0.01, 'ETH': 1.0, 'SOL': 10.0, 'BNB': 1.0, 'XRP': 300.0,
    'DOGE': 3000.0, 'ADA': 1000.0, 'AVAX': 30.0, 'LINK': 40.0, 'DOT': 200.0, 'LTC': 8.0
})
print(f"Initial Portfolio Loaded. Balance=${portfolio['balance']:.2f}")

trading_active = False
current_symbol = 'BTC'


# -------------------------------------------------------
# DASHBOARD ROUTE
# -------------------------------------------------------
@app.route('/')
def dashboard():
    return render_template('dashboard.html')


# -------------------------------------------------------
# PORTFOLIO DATA
# -------------------------------------------------------
@app.route('/api/portfolio')
def get_portfolio():
    current_price = data_fetcher.get_current_price(current_symbol)
    crypto_amount = portfolio['holdings'][current_symbol]
    portfolio_value = portfolio['balance'] + sum(
        portfolio['holdings'][s] * data_fetcher.get_current_price(s) for s in SYMBOLS
    )

    return jsonify({
        'balance': portfolio['balance'],
        'crypto_amount': crypto_amount,
        'current_price': current_price,
        'portfolio_value': portfolio_value,
        'total_trades': portfolio['total_trades'],
        'profit_loss': portfolio['profit_loss'],
        'current_symbol': current_symbol
    })


# -------------------------------------------------------
# SYMBOL SWITCH
# -------------------------------------------------------
@app.route('/api/set_symbol', methods=['POST'])
def set_symbol():
    data = request.json
    symbol = data.get('symbol')
    global current_symbol
    if symbol in SYMBOLS:
        current_symbol = symbol
        return jsonify({'message': f'Switched to {symbol}'})
    else:
        return jsonify({'error': 'Invalid symbol'}), 400


# -------------------------------------------------------
# MANUAL TRADING
# -------------------------------------------------------
@app.route('/api/manual_trade', methods=['POST'])
def manual_trade():
    try:
        data = request.json
        action = data.get('action')
        amount_usd = float(data.get('amount', 0))

        if action not in ['BUY', 'SELL', 'HOLD']:
            return jsonify({'error': 'Invalid trade action'}), 400
        if amount_usd <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400

        current_price = data_fetcher.get_current_price(current_symbol)

        if action == 'BUY':
            if portfolio['balance'] < amount_usd:
                return jsonify({'error': 'Insufficient balance'}), 400

            amount_crypto = amount_usd / current_price
            portfolio['balance'] -= amount_usd
            portfolio['holdings'][current_symbol] += amount_crypto
            portfolio['total_trades'] += 1

            transaction = blockchain.create_transaction(
                'BUY', current_symbol, amount_crypto, current_price,
                current_price, 'MANUAL'
            )
            blockchain.add_transaction(transaction)
            blockchain.mine_pending_transactions()

            result = {'message': f'Manual BUY of ${amount_usd:.2f} executed'}

        elif action == 'SELL':
            max_sellable_usd = portfolio['holdings'][current_symbol] * current_price
            if amount_usd > max_sellable_usd:
                return jsonify({'error': 'Not enough crypto to sell'}), 400

            amount_crypto = amount_usd / current_price
            portfolio['balance'] += amount_usd
            portfolio['holdings'][current_symbol] -= amount_crypto
            portfolio['total_trades'] += 1

            transaction = blockchain.create_transaction(
                'SELL', current_symbol, amount_crypto, current_price,
                current_price, 'MANUAL'
            )
            blockchain.add_transaction(transaction)
            blockchain.mine_pending_transactions()

            result = {'message': f'Manual SELL of ${amount_usd:.2f} executed'}

        else:
            result = {'message': 'Manual HOLD - no action taken'}

        portfolio_value = portfolio['balance'] + sum(
            portfolio['holdings'][s] * data_fetcher.get_current_price(s) for s in SYMBOLS
        )

        return jsonify({
            **result,
            'balance': portfolio['balance'],
            'holdings': portfolio['holdings'][current_symbol],
            'portfolio_value': portfolio_value
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# TRAIN MODEL
# -------------------------------------------------------
@app.route('/api/train_model', methods=['POST'])
def train_model():
    try:
        print(f"🧠 Training AI model for {current_symbol}...")
        historical_data = data_fetcher.fetch_historical_data(current_symbol, '1y')

        if historical_data is None or len(historical_data) < 100:
            return jsonify({'error': 'Insufficient data for training'}), 400

        ai_traders[current_symbol].train(historical_data, epochs=20, batch_size=16)
        return jsonify({
            'message': f'Model trained successfully for {current_symbol}',
            'model_hash': ai_traders[current_symbol].model_hash
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# AI PREDICT & TRADE
# -------------------------------------------------------
@app.route('/api/predict_and_trade', methods=['POST'])
def predict_and_trade():
    try:
        trader = ai_traders[current_symbol]
        if not trader.is_trained:
            return jsonify({'error': 'Model must be trained first'}), 400

        data = data_fetcher.fetch_historical_data(current_symbol, '3mo')
        recent_prices = data['Close'].values
        if len(recent_prices) < trader.sequence_length:
            return jsonify({'error': 'Insufficient data'}), 400

        current_price = data_fetcher.get_current_price(current_symbol)
        predicted_price = trader.predict_next_price(recent_prices)
        signal = trader.generate_trading_signal(current_price, predicted_price)

        trade_executed = False
        trade_type = None

        if signal == 'BUY' and portfolio['balance'] > current_price:
            amount_usd = portfolio['balance'] * 0.1
            amount_crypto = amount_usd / current_price
            portfolio['balance'] -= amount_usd
            portfolio['holdings'][current_symbol] += amount_crypto
            portfolio['total_trades'] += 1
            blockchain.add_transaction(blockchain.create_transaction('BUY', current_symbol, amount_crypto, current_price, predicted_price, trader.model_hash))
            blockchain.mine_pending_transactions()
            trade_executed = True
            trade_type = 'BUY'

        elif signal == 'SELL' and portfolio['holdings'][current_symbol] > 0:
            amount_crypto = portfolio['holdings'][current_symbol] * 0.1
            amount_usd = amount_crypto * current_price
            portfolio['balance'] += amount_usd
            portfolio['holdings'][current_symbol] -= amount_crypto
            portfolio['total_trades'] += 1
            blockchain.add_transaction(blockchain.create_transaction('SELL', current_symbol, amount_crypto, current_price, predicted_price, trader.model_hash))
            blockchain.mine_pending_transactions()
            trade_executed = True
            trade_type = 'SELL'

        portfolio_value = portfolio['balance'] + sum(
            portfolio['holdings'][s] * data_fetcher.get_current_price(s) for s in SYMBOLS
        )

        return jsonify({
            'symbol': current_symbol,
            'current_price': current_price,
            'predicted_price': predicted_price,
            'signal': signal,
            'trade_executed': trade_executed,
            'trade_type': trade_type,
            'portfolio_value': portfolio_value
        })

    except Exception as e:
        print(f"Predict error: {e}")
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# AUTO TRADING LOOP
# -------------------------------------------------------
def auto_trading_loop():
    global trading_active
    while trading_active:
        try:
            app.test_client().post('/api/predict_and_trade')
            time.sleep(60)
        except Exception as e:
            print(f"Auto trading error: {e}")
            time.sleep(30)


@app.route('/api/start_auto_trading', methods=['POST'])
def start_auto_trading():
    global trading_active
    if not trading_active:
        trading_active = True
        threading.Thread(target=auto_trading_loop, daemon=True).start()
        return jsonify({'message': 'Auto trading started'})
    return jsonify({'message': 'Already running'})


@app.route('/api/stop_auto_trading', methods=['POST'])
def stop_auto_trading():
    global trading_active
    trading_active = False
    return jsonify({'message': 'Auto trading stopped'})


# -------------------------------------------------------
# BLOCKCHAIN VIEW
# -------------------------------------------------------
@app.route('/api/blockchain')
def get_blockchain():
    return jsonify({
        'chain': blockchain.get_chain_data(),
        'pending_transactions': blockchain.pending_transactions,
        'is_valid': blockchain.is_chain_valid()
    })


# -------------------------------------------------------
# HISTORICAL PRICE DATA (used by the dashboard price chart)
# -------------------------------------------------------
@app.route('/api/historical_data')
def get_historical_data():
    try:
        df = data_fetcher.fetch_historical_data(current_symbol, '1mo')
        if df is None or df.empty:
            return jsonify([])
        return jsonify([
            {'date': row['Date'].strftime('%Y-%m-%d'), 'price': float(row['Close'])}
            for _, row in df.tail(30).iterrows()
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# DEBUG STATUS
# -------------------------------------------------------
@app.route('/api/debug_status')
def debug_status():
    return jsonify({
        'trading_active': trading_active,
        'model_trained': ai_traders[current_symbol].is_trained,
        'current_symbol': current_symbol,
        'portfolio': portfolio,
        'blockchain_blocks': len(blockchain.chain)
    })


# -------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------
if __name__ == '__main__':
    # Debug mode and public binding are OFF by default (the Flask debugger allows
    # remote code execution if exposed). Opt in locally with:
    #   FLASK_DEBUG=1 python app.py
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting ChainTraderAI on http://{host}:{port}")
    app.run(debug=debug, host=host, port=port)
