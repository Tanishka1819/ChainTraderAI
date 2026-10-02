import hashlib
import json
import time
from datetime import datetime

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        """Mine block with proof-of-work"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

class TradingBlockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.pending_transactions = []
        self.mining_reward = 0.1
        
    def create_genesis_block(self):
        """Create the first block in the chain"""
        return Block(0, [], time.time(), "0")
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def add_transaction(self, transaction):
        """Add a new transaction to pending transactions"""
        self.pending_transactions.append(transaction)
    
    def mine_pending_transactions(self):
        """Mine a new block with pending transactions"""
        block = Block(
            len(self.chain),
            self.pending_transactions,
            time.time(),
            self.get_latest_block().hash
        )
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
    
    def create_transaction(self, trade_type, symbol, amount, price, prediction, model_hash):
        """Create a trading transaction"""
        transaction = {
            "id": hashlib.sha256(f"{time.time()}{trade_type}{symbol}".encode()).hexdigest()[:16],
            "timestamp": datetime.now().isoformat(),
            "type": trade_type,
            "symbol": symbol,
            "amount": amount,
            "price": price,
            "prediction": prediction,
            "model_hash": model_hash,
            "total_value": amount * price
        }
        return transaction
    
    def get_chain_data(self):
        """Get blockchain data for display"""
        chain_data = []
        for block in self.chain:
            chain_data.append({
                "index": block.index,
                "hash": block.hash,
                "previous_hash": block.previous_hash,
                "timestamp": datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                "transactions": block.transactions,
                "nonce": block.nonce
            })
        return chain_data
    
    def is_chain_valid(self):
        """Validate the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        return True