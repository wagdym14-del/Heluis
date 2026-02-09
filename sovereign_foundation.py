
import os
import sqlite3
import time
import jwt
import random
import httpx
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from faker import Faker

# --- [ القسم 1: الإعدادات السيادية المرنة - نسخة 2027 ] ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

fake = Faker()

class HeliusKeyManager:
    def __init__(self):
        self.keys_pool = os.getenv("HELIUS_KEYS_POOL", "").split(',')
        self.current_key_index = 0
        self.active_key = self.keys_pool[self.current_key_index]
        self.user_agent = fake.user_agent()
        self.disabled_keys = {}  # key: expiry_time

    def get_current_key(self):
        return self.active_key

    def get_user_agent(self):
        return self.user_agent

    def rotate_key(self, immediate=False):
        """Rotates the key and User-Agent."""
        self.current_key_index = (self.current_key_index + 1) % len(self.keys_pool)
        self.active_key = self.keys_pool[self.current_key_index]
        self.user_agent = fake.user_agent()
        print(f"🔄 [KEY_ROTATION] Switched to key: ...{self.active_key[-4:]}")
        print(f"🔄 [USER_AGENT] New User-Agent: {self.user_agent}")

        if immediate:
            # Archive the key that caused a 429 error for 1 hour
            self.disabled_keys[self.active_key] = time.time() + 3600
            # Immediately switch to the next available key
            while self.active_key in self.disabled_keys:
                if time.time() > self.disabled_keys[self.active_key]:
                    del self.disabled_keys[self.active_key]
                    break
                self.rotate_key()


    async def scheduled_rotation(self):
        """Rotates the key every 10 minutes."""
        while True:
            await asyncio.sleep(600)  # 10 minutes
            self.rotate_key()

helius_key_manager = HeliusKeyManager()


class SovereignSettings:
    PROJECT_NAME = "Sovereign-Elite-Protocol"
    VERSION = "6.0-FLEX-JITO"

    # --- واجهات برمجة التطبيقات الأساسية (RPC & Data APIs) ---
    HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={helius_key_manager.get_current_key()}"
    HELIUS_WS_URL = os.getenv("HELIUS_WS_URL") # تم التبديل إلى WebSocket/gRPC
    BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
    MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

    # --- حماية MEV (Jito Integration) ---
    JITO_TIPS_URL = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"
    JITO_TIPS_ACCOUNT = os.getenv("JITO_TIPS_ACCOUNT") # حساب لاستلام الإكراميات

    # --- ثوابت مرنة (Flexible Constants) ---
    MAX_SLOTS = int(os.getenv("MAX_SLOTS", 5))
    RADAR_DELAY = float(os.getenv("RADAR_DELAY", 5.0))

    # مسار قاعدة بيانات الأنماط السلوكية
    DB_PATH = BASE_DIR / os.getenv("DB_NAME", "sovereign_patterns.db")

    @classmethod
    def ensure_env(cls):
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

settings = SovereignSettings()
settings.ensure_env()

# --- [ القسم 2: الحماية السيادية (Stealth & MEV Protection) ] ---

def get_sovereign_http_client() -> httpx.AsyncClient:
    """"إنشاء عميل HTTP بـ 'هوية برمجية' ديناميكية (Dynamic Headers) للحماية."""
    headers = {
        "User-Agent": helius_key_manager.get_user_agent(),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    return httpx.AsyncClient(http2=True, headers=headers, timeout=20.0)

# --- [ القسم 3: الذاكرة السلوكية وقاعدة بيانات الأنماط ] ---
class SovereignFoundationDB:
    def __init__(self):
        self.db_path = str(settings.DB_PATH)
        self._bootstrap()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _bootstrap(self):
        """"إنشاء قاعدة بيانات لحفظ 'الحمض النووي للأنماط' (Pattern DNA)."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS manipulation_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mint TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_dna TEXT, -- JSON format
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_mint_pattern ON manipulation_patterns(mint, pattern_type);
            ""”)
            conn.commit()

    def save_pattern_to_archive(self, archive_entry: Dict):
        """"أرشفة نمط التلاعب (كسل/هجوم عنقودي) في قاعدة البيانات."""
        query = """
        INSERT INTO manipulation_patterns (mint, pattern_type, pattern_dna, timestamp) 
        VALUES (?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                conn.execute(query, (
                    archive_entry["mint"],
                    archive_entry["pattern_type"],
                    json.dumps(archive_entry["pattern_dna"]),
                    archive_entry["timestamp"]
                ))
                conn.commit()
        except Exception as e:
            print(f"⚠️ [DB_ERROR] فشل أرشفة نمط التلاعب: {e}")

db = SovereignFoundationDB()
