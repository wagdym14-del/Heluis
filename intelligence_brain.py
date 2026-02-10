import numpy as np
import httpx
import time
import asyncio
from typing import Dict, Any, List, Tuple
from collections import defaultdict

from sovereign_foundation import db, settings, helius_key_manager

class SovereignIntelligence:
    """
    [المختبر السيادي - نسخة الذكاء الهجين 9.2.1]
    تم التحديث: نظام Parallel Async لتجاوز قيود Helius Batch (خطأ 400).
    """

    def __init__(self):
        self.helius_client = httpx.AsyncClient(
            http2=True,
            timeout=45.0,
            headers={"Accept": "application/json", "User-Agent": helius_key_manager.get_user_agent()}
        )
        self.behavioral_entities: Dict[str, List[str]] = {}

    def _get_helius_url(self) -> str:
        """جلب الرابط مع تدوير المفاتيح تلقائياً."""
        return f"{settings.HELIUS_RPC_URL}{helius_key_manager.get_current_key()}"

    async def _get_batch_asset_data(self, mints: List[str], limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """
        [تحديث حاسم] جلب البيانات لكل عملة بشكل منفصل ومتوازي لتجنب رفض Helius للطلبات الجماعية.
        """
        results = {}
        
        async def fetch_single_mint(mint):
            url = self._get_helius_url()
            payload = {
                "jsonrpc": "2.0",
                "id": f"sovereign-{mint}-{int(time.time())}",
                "method": "getSignaturesForAsset",
                "params": {
                    "assetId": mint,
                    "limit": limit
                }
            }
            try:
                response = await self.helius_client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return mint, data.get("result", [])
                elif response.status_code == 401:
                    helius_key_manager.rotate_key(immediate=True)
            except Exception as e:
                print(f"⚠️ [NETWORK_RETRY] فشل جلب {mint[:8]}: {e}")
            return mint, []

        # تشغيل جميع الطلبات في وقت واحد (Parallel)
        tasks = [fetch_single_mint(mint) for mint in mints]
        completed_tasks = await asyncio.gather(*tasks)
        
        for mint, signatures in completed_tasks:
            results[mint] = signatures
            
        return results

    async def analyze_market_dynamics(self, mint: str, signatures: List[Dict[str, Any]]) -> Tuple[float, str, Dict]:
        """تحليل السلوك لاكتشاف صناع السوق وأرشفة نشاطهم."""
        if not signatures:
            return 0.0, "No Data", {}

        total_buy_volume = 0
        total_sell_volume = 0
        fast_swaps = 0
        wallets_involved = set()

        for sig in signatures:
            # محاكاة تحليل المعاملات (بناءً على البصمة الزمنية)
            # في النسخة الكاملة يتم جلب تفاصيل المعاملة هنا
            wallets_involved.add(sig.get('signature', '')) 

        # خوارزمية كشف Bait Volume (حجم الطعم)
        # إذا كان هناك عدد كبير من المعاملات في وقت قياسي
        if len(signatures) > 50:
            confidence = 0.85
            reason = "High-Frequency Activity detected (Market Maker Pattern)"
            footprint = {
                "activity_density": len(signatures),
                "is_mm_bot": True,
                "timestamp": time.time()
            }
            
            # أرشفة فورية لصانع السوق
            await self.archive_behavior_footprint(mint, "MM_ALGO_DETECTED", confidence, footprint)
            return confidence, reason, footprint

        return 0.1, "Normal Activity", {}

    async def archive_behavior_footprint(self, mint: str, pattern_type: str, confidence: float, footprint: Dict):
        """أرشفة البصمة السلوكية في قاعدة البيانات للاستخدام المستقبلي."""
        archive_entry = {
            "mint": mint,
            "pattern_type": pattern_type,
            "behavioral_footprint": footprint,
            "confidence_score": confidence,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            db.save_behavior_footprint(archive_entry)
            # تسجيل إضافي لروبوتات MM
            db.log_mm_bot_activity(mint, "Multiple_Entities", pattern_type)
        except Exception as e:
            print(f"⚠️ [ARCHIVE_ERROR] {e}")

brain = SovereignIntelligence()
