"""
SEA-TO Configuration
Global settings untuk seluruh sistem
"""

import os

# GitHub Configuration
GITHUB_REPO = "elingfathurrodo-efr/AI-HEDGE-CORE"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/"

# Trading Configuration
SYMBOL = "XAUUSD"
TIMEFRAME = "M5"  # 5-minute scalping
MAX_SPREAD = 50  # points

# Evolution Configuration
POPULATION_SIZE = 100
ELITE_RATIO = 0.1
MUTATION_RATE = 0.1
GENERATION_INTERVAL_HOURS = 4

# Security Configuration
MAX_TRAUMA_SCORE = 10
ROLLBACK_ON_FAILURE = True
BACKUP_RETENTION = 10  # Keep last 10 backups

# MT5 Configuration
MT5_CHECK_INTERVAL = 10  # seconds
GHOST_SL_ENABLED = True
DYNAMIC_TRAILING = True

# Future I/O (Robot preparation)
ENABLE_CAMERA = False  # Placeholder untuk masa depan
ENABLE_MIC = False     # Placeholder untuk masa depan
ENABLE_TOUCH = False   # Placeholder untuk masa depan

def get_pat_token():
    """Get PAT dari environment variable"""
    return os.getenv('PAT_TOKEN', '')

