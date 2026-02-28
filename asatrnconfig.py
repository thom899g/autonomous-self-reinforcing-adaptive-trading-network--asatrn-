"""
ASATrN Configuration Manager
Centralized configuration management with environment variable support and validation.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    # Add more as needed


class TradingMode(Enum):
    """Trading operation modes"""
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


@dataclass
class TradingConfig:
    """Trading-specific configuration"""
    mode: TradingMode = TradingMode.PAPER
    exchange: ExchangeType = ExchangeType.BINANCE
    symbols: list = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    timeframe: str = "1h"
    initial_balance: float = 10000.0
    risk_per_trade: float = 0.02  # 2% risk per trade
    max_open_positions: int = 3


@dataclass
class MLConfig:
    """Machine learning configuration"""
    pattern_window: int = 50  # Window size for pattern detection
    retrain_interval: int = 24  # Hours between retraining
    model_path: str = "./models/"
    feature_columns: list = field(default_factory=lambda: [
        "open", "high", "low", "close", "volume",
        "rsi_14", "macd", "bb_upper", "bb_lower"
    ])


@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    project_id: str = ""
    service_account_path: str = "./firebase-service-account.json"
    collection_prefix: str = "asatrn_"
    enable_realtime: bool = True


class ConfigManager:
    """
    Central configuration manager with environment variable support.
    Validates all configurations and provides defaults.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "./config.json"
        self.trading = TradingConfig()
        self.ml = MLConfig()
        self.firebase = FirebaseConfig()
        self._loaded = False
        self._validate_and_load()
    
    def _validate_and_load(self) -> None:
        """Validate and load configuration from multiple sources"""
        try:
            # 1. Try to load from file
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                self._update_from_dict(file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            
            # 2. Override with environment variables
            self._load_from_env()
            
            # 3. Validate critical configurations
            self._validate_config()
            
            # 4. Ensure model directory exists
            Path(self.ml.model_path).mkdir(parents=True, exist_ok=True)
            
            self._loaded = True
            logger.info("Configuration loaded and validated successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        if 'trading' in config_dict:
            for key, value in config_dict['trading'].items():
                if hasattr(self.trading, key):
                    setattr(self.trading, key, value)
        
        if 'ml' in config_dict:
            for key, value in config_dict['ml'].items():
                if hasattr(self.ml, key):
                    setattr(self.ml, key, value)
        
        if 'firebase' in config_dict:
            for key, value in config_dict['firebase'].items():
                if hasattr(self.firebase, key):
                    setattr(self.firebase, key, value)
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables"""
        env_mappings = {
            'TRADING_MODE': ('trading', 'mode', lambda x: TradingMode[x.upper()]),
            'EXCHANGE': ('trading', 'exchange', lambda x: ExchangeType[x.