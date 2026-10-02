class ChainTraderDashboard {
    constructor() {
        this.priceChart = null;
        this.autoTradingActive = false;
        this.currentSymbol = 'BTC';
        // Don't call init() in constructor - wait for DOM to be ready
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupPriceChart();
        this.startDataRefresh();
    }

    setupEventListeners() {
        document.getElementById('trainModelBtn').addEventListener('click', () => this.trainModel());
        document.getElementById('predictTradeBtn').addEventListener('click', () => this.predictAndTrade());
        document.getElementById('autoTradeBtn').addEventListener('click', () => this.startAutoTrading());
        document.getElementById('stopTradeBtn').addEventListener('click', () => this.stopAutoTrading());
        document.getElementById('refreshBlockchainBtn').addEventListener('click', () => this.loadBlockchainData());
        document.getElementById('symbolSelect').addEventListener('change', (e) => this.setSymbol(e.target.value));
    }

    async loadInitialData() {
        await this.loadPortfolioData();
        await this.loadBlockchainData();
        await this.loadHistoricalData();
        document.getElementById('symbolSelect').value = this.currentSymbol;
    }

    async loadPortfolioData() {
        try {
            const response = await fetch('/api/portfolio');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            this.currentSymbol = data.current_symbol;
            document.getElementById('balance').textContent = data.balance.toFixed(2);
            document.getElementById('cryptoAmount').textContent = data.crypto_amount.toFixed(6);
            document.getElementById('currentPrice').textContent = data.current_price.toFixed(2);
            document.getElementById('portfolioValue').textContent = data.portfolio_value.toFixed(2);
            document.getElementById('totalTrades').textContent = data.total_trades;

            // Update symbol names
            const symbolSpans = document.getElementsByClassName('symbolName');
            for (let span of symbolSpans) {
                span.textContent = this.currentSymbol.toUpperCase();
            }

            // Update chart title
            document.getElementById('chartTitle').innerHTML = 
                `<i class="fas fa-chart-area me-2"></i>${this.currentSymbol.toUpperCase()} Price Chart (Last 30 Days)`;
        } catch (error) {
            console.error('Error loading portfolio data:', error);
            this.showAlert('danger', 'Failed to load portfolio data');
        }
    }

    async setSymbol(symbol) {
        try {
            const response = await fetch('/api/set_symbol', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbol })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.showAlert('success', data.message);
            await this.loadInitialData();
        } catch (error) {
            console.error('Error setting symbol:', error);
            this.showAlert('danger', 'Failed to switch symbol');
        }
    }

    async trainModel() {
        const btn = document.getElementById('trainModelBtn');
        // Check if Bootstrap is available
        const loadingModal = bootstrap && bootstrap.Modal ? new bootstrap.Modal(document.getElementById('loadingModal')) : null;
        
        try {
            btn.disabled = true;
            if (loadingModal) {
                document.getElementById('loadingText').textContent = 'Training AI Model...';
                loadingModal.show();
            }

            const response = await fetch('/api/train_model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            document.getElementById('aiStatus').innerHTML = 
                '<small class="text-success">Status: Model trained successfully!</small>';
            document.getElementById('modelHash').textContent = data.model_hash;
            
            this.showAlert('success', `Model trained with ${data.data_points} data points!`);
            
        } catch (error) {
            console.error('Training error:', error);
            this.showAlert('danger', `Training failed: ${error.message}`);
            document.getElementById('aiStatus').innerHTML = 
                '<small class="text-danger">Status: Training failed</small>';
        } finally {
            btn.disabled = false;
            if (loadingModal) {
                loadingModal.hide();
            }
        }
    }

    async predictAndTrade() {
        const btn = document.getElementById('predictTradeBtn');
        // Check if Bootstrap is available
        const loadingModal = bootstrap && bootstrap.Modal ? new bootstrap.Modal(document.getElementById('loadingModal')) : null;
        
        try {
            btn.disabled = true;
            if (loadingModal) {
                document.getElementById('loadingText').textContent = 'Making Prediction...';
                loadingModal.show();
            }

            const response = await fetch('/api/predict_and_trade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Update prediction display
            document.getElementById('predCurrentPrice').textContent = data.current_price.toFixed(2);
            document.getElementById('predPrice').textContent = data.predicted_price.toFixed(2);
            
            const signalBadge = document.getElementById('signal');
            signalBadge.textContent = data.signal;
            signalBadge.className = `badge ${this.getSignalColor(data.signal)}`;

            // Show trade result
            if (data.trade_executed && data.trade_details) {
                const trade = data.trade_details;
                this.showAlert('info', 
                    `Trade executed: ${trade.type} ${trade.amount.toFixed(6)} ${this.currentSymbol} at ${trade.price.toFixed(2)}`);
            } else {
                this.showAlert('secondary', `Prediction made: ${data.signal} signal`);
            }

            // Refresh data
            await this.loadPortfolioData();
            await this.loadBlockchainData();
            
        } catch (error) {
            console.error('Prediction error:', error);
            this.showAlert('danger', `Prediction failed: ${error.message}`);
        } finally {
            btn.disabled = false;
            if (loadingModal) {
                loadingModal.hide();
            }
        }
    }

    getSignalColor(signal) {
        switch(signal) {
            case 'BUY': return 'bg-success';
            case 'SELL': return 'bg-danger';
            case 'HOLD': return 'bg-warning';
            default: return 'bg-secondary';
        }
    }

    async startAutoTrading() {
        try {
            const response = await fetch('/api/start_auto_trading', {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.autoTradingActive = true;
            
            document.getElementById('autoTradeBtn').disabled = true;
            document.getElementById('stopTradeBtn').disabled = false;
            
            document.getElementById('aiStatus').innerHTML = 
                '<small class="text-success pulse">Status: Auto trading active...</small>';
                
            this.showAlert('success', 'Auto trading started!');
            
        } catch (error) {
            console.error('Auto trading start error:', error);
            this.showAlert('danger', 'Failed to start auto trading');
        }
    }

    async stopAutoTrading() {
        try {
            const response = await fetch('/api/stop_auto_trading', {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.autoTradingActive = false;
            
            document.getElementById('autoTradeBtn').disabled = false;
            document.getElementById('stopTradeBtn').disabled = true;
            
            document.getElementById('aiStatus').innerHTML = 
                '<small class="text-muted">Status: Auto trading stopped</small>';
                
            this.showAlert('info', 'Auto trading stopped!');
            
        } catch (error) {
            console.error('Auto trading stop error:', error);
            this.showAlert('danger', 'Failed to stop auto trading');
        }
    }

    async loadBlockchainData() {
        try {
            const response = await fetch('/api/blockchain');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const container = document.getElementById('blockchainData');
            
            if (!container) {
                console.error('Blockchain data container not found');
                return;
            }
            
            if (data.chain.length === 0) {
                container.innerHTML = '<p class="text-muted">No blocks in chain yet.</p>';
                return;
            }

            let html = '';
            data.chain.reverse().forEach((block, index) => {
                const hasTransactions = block.transactions && block.transactions.length > 0;
                
                html += `
                    <div class="block-item">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="mb-0">Block #${block.index}</h6>
                            <small>${new Date(block.timestamp).toLocaleString()}</small>
                        </div>
                        <p class="mb-1"><strong>Hash:</strong> <span class="hash-display">${block.hash}</span></p>
                        <p class="mb-2"><strong>Previous Hash:</strong> <span class="hash-display">${block.previous_hash}</span></p>
                        <p class="mb-2"><strong>Nonce:</strong> ${block.nonce}</p>
                        
                        ${hasTransactions ? `
                            <div class="transactions">
                                <strong>Transactions (${block.transactions.length}):</strong>
                                ${block.transactions.map(tx => `
                                    <div class="transaction-item mt-2">
                                        <div class="row">
                                            <div class="col-md-3">
                                                <strong>${tx.type}</strong> ${tx.symbol || 'BTC'}
                                            </div>
                                            <div class="col-md-3">
                                                Amount: ${tx.amount ? tx.amount.toFixed(6) : '0.000000'}
                                            </div>
                                            <div class="col-md-3">
                                                Price: ${tx.price ? tx.price.toFixed(2) : '0.00'}
                                            </div>
                                            <div class="col-md-3">
                                                Value: ${tx.total_value ? tx.total_value.toFixed(2) : '0.00'}
                                            </div>
                                        </div>
                                        <div class="row mt-1">
                                            <div class="col-md-6">
                                                <small>Prediction: ${tx.prediction ? tx.prediction.toFixed(2) : 'N/A'}</small>
                                            </div>
                                            <div class="col-md-6">
                                                <small>Model: ${tx.model_hash || 'N/A'}</small>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p class="mb-0"><em>No transactions in this block</em></p>'}
                    </div>
                `;
            });
            
            container.innerHTML = html;
            
        } catch (error) {
            console.error('Error loading blockchain data:', error);
            const container = document.getElementById('blockchainData');
            if (container) {
                container.innerHTML = '<p class="text-danger">Error loading blockchain data</p>';
            }
        }
    }

    async loadHistoricalData() {
        try {
            const response = await fetch('/api/historical_data');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.updatePriceChart(data);
            
        } catch (error) {
            console.error('Error loading historical data:', error);
        }
    }

    setupPriceChart() {
        const ctx = document.getElementById('priceChart');
        if (!ctx) {
            console.error('Price chart canvas not found');
            return;
        }
        
        this.priceChart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price (USD)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Price: $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    updatePriceChart(data) {
        if (!this.priceChart || !data || data.length === 0) return;

        const labels = data.map(item => item.date);
        const prices = data.map(item => item.price);

        this.priceChart.data.labels = labels;
        this.priceChart.data.datasets[0].label = `${this.currentSymbol.toUpperCase()} Price (USD)`;
        this.priceChart.data.datasets[0].data = prices;
        this.priceChart.update();
    }

    startDataRefresh() {
        // Refresh portfolio and blockchain data every 30 seconds
        setInterval(() => {
            this.loadPortfolioData();
            this.loadBlockchainData();  // Always refresh blockchain
        }, 30000);
    }

    showAlert(type, message) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new ChainTraderDashboard();
    window.dashboard.init();
});