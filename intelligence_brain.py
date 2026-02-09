
import numpy as np
import httpx
import time
from typing import Dict, Any, List, Tuple

from sovereign_foundation import db, settings, helius_key_manager

class SovereignIntelligence:
    """
    [المختبر السيادي - نسخة الوعي السلوكي 8.0]
    نظام يقرأ 'نوايا' صناع السوق من خلال أنماط أفعالهم، ويؤرشف هذه الأنماط
    للتعرف عليهم مستقبلاً.
    """

    def __init__(self):
        # We need to re-initialize the URL with the latest key after a potential rotation
        self.helius_client = httpx.AsyncClient(
            baseURL=f"https://mainnet.helius-rpc.com/?api-key={helius_key_manager.get_current_key()}",
            http2=True,
            headers={"Accept": "application/json", "User-Agent": helius_key_manager.get_user_agent()}
        )

    async def _get_recent_transactions(self, mint: str, limit: int = 100) -> List[Dict[str, Any]]:
        """جلب أحدث المعاملات لعملة معينة باستخدام Helius API."""
        try:
            # Refresh client to ensure it uses the current key
            self.helius_client.base_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key_manager.get_current_key()}"
            
            response = await self.helius_client.post(
                url="",
                json={
                    "jsonrpc": "2.0",
                    "id": "sovereign-nexus",
                    "method": "getSignaturesForAsset",
                    "params": {"assetId": mint, "limit": limit},
                },
                timeout=30.0
            )
            if response.status_code == 429:
                print("🚨 [HELIUS_RATE_LIMIT] Reached Helius rate limit. Rotating key immediately.")
                helius_key_manager.rotate_key(immediate=True)
                # Retry with the new key
                self.helius_client.base_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key_manager.get_current_key()}"
                response = await self.helius_client.post(
                    url="",
                    json={
                        "jsonrpc": "2.0",
                        "id": "sovereign-nexus-retry",
                        "method": "getSignaturesForAsset",
                        "params": {"assetId": mint, "limit": limit},
                    },
                    timeout=30.0
                )

            response.raise_for_status()
            signatures_data = response.json().get('result', [])
            if not signatures_data:
                return []
            
            signatures = [item['signature'] for item in signatures_data]
            
            # Fetch full transaction details
            tx_details_resp = await self.helius_client.post(
                url="",
                json={
                    "jsonrpc": "2.0",
                    "id": "sovereign-nexus-txs",
                    "method": "getTransactions",
                    "params": {"signatures": signatures},
                }
            )
            tx_details_resp.raise_for_status()
            return tx_details_resp.json().get('result', [])
        except httpx.HTTPStatusError as e:
            print(f"⚠️ [HELIUS_ERROR] خطأ في جلب المعاملات لـ {mint}: {e.response.status_code} {e.response.text}")
        except Exception as e:
            print(f"⚠️ [INTELLIGENCE_ERROR] خطأ غير متوقع في _get_recent_transactions: {e}")
        return []


    async def analyze_temporal_synchronization(self, transactions: List[Dict[str, Any]]) -> Tuple[float, str, Dict]:
        """
        محرك تحليل التزامن الزمني لكشف العمليات المتطابقة زمنياً من محافظ مختلفة.
        """
        if len(transactions) < 5:
            return 0.0, "", {}

        # فرز المعاملات حسب الطابع الزمني
        transactions.sort(key=lambda tx: tx['blockTime'])
        
        timestamps = np.array([tx['blockTime'] for tx in transactions])
        wallets = [tx['transaction']['message']['accountKeys'][0] for tx in transactions]

        # حساب الفروقات الزمنية بين المعاملات المتتالية (بالثواني)
        time_deltas = np.diff(timestamps)
        
        # تحويل عتبة الميكرو-ثانية إلى ثواني للمقارنة
        threshold_seconds = settings.SYNC_TIME_THRESHOLD / 1_000_000.0

        # البحث عن مجموعات من المعاملات المتزامنة
        sync_clusters = np.where(time_deltas <= threshold_seconds)[0]

        if len(sync_clusters) > 3:  # إذا وجدنا أكثر من 3 عمليات متزامنة
            implicated_indices = np.unique(np.concatenate([sync_clusters, sync_clusters + 1]))
            implicated_wallets = {wallets[i] for i in implicated_indices}
            
            # يجب أن تكون المحافظ فريدة لكشف التلاعب
            if len(implicated_wallets) > 3:
                confidence = min(1.0, (len(implicated_wallets) / 10.0)) # A simple confidence score
                reason = f"رصد تلاعب تزامني: {len(implicated_wallets)} محافظ نفذت عمليات ضمن فارق زمني قدره {threshold_seconds} ثانية."
                footprint = {
                    "temporal_footprint": {
                        "wallets": list(implicated_wallets),
                        "sync_delta_us": settings.SYNC_TIME_THRESHOLD
                    }
                }
                return confidence, reason, footprint
                
        return 0.0, "", {}

    async def analyze_pool_resilience(self, transactions: List[Dict[str, Any]]) -> Tuple[float, str, Dict]:
        """
        محرك تحليل مرونة الحوض: يحلل 'جودة التعافي' بعد عمليات البيع الكبيرة.
        """
        if not transactions:
            return 0.0, "", {}

        sells = []
        buys = []

        for tx in transactions:
            # تحليل بسيط يعتمد على تغير رصيد SOL
            pre_sol = next((bal['uiTokenAmount']['uiAmount'] for bal in tx.get('meta', {}).get('preTokenBalances', []) if bal['mint'] == "So11111111111111111111111111111111111111112"), 0)
            post_sol = next((bal['uiTokenAmount']['uiAmount'] for bal in tx.get('meta', {}).get('postTokenBalances', []) if bal['mint'] == "So11111111111111111111111111111111111111112"), 0)
            
            sol_change = post_sol - pre_sol
            
            # هذا تبسيط، المنطق الحقيقي يحتاج تتبع العملة نفسها
            if sol_change > 0:
                sells.append(sol_change) # زيادة SOL تعني بيع العملة
            elif sol_change < 0:
                buys.append(abs(sol_change)) # نقصان SOL يعني شراء العملة

        total_sell_volume = sum(sells)
        total_buy_volume = sum(buys)

        if total_sell_volume > 0:
            resilience_ratio = total_buy_volume / total_sell_volume
            
            if resilience_ratio < settings.RESILIENCE_FACTOR:
                confidence = 1.0 - (resilience_ratio / settings.RESILIENCE_FACTOR)
                reason = f"موت الزخم: مرونة الحوض ضعيفة ({resilience_ratio:.2f}). نسبة التعافي أقل من العتبة ({settings.RESILIENCE_FACTOR})."
                footprint = {"flow_distribution": {"inflow_ratio": resilience_ratio, "outflow_volume": total_sell_volume}}
                return confidence, reason, footprint
            else:
                # هذا ليس حكماً، بل ملاحظة إيجابية
                return -1.0, f"فرصة محتملة: مرونة الحوض قوية ({resilience_ratio:.2f}).", {}

        return 0.0, "", {}


    async def get_sovereign_verdict(self, mint: str, token_data: Dict) -> Tuple[str, str, float]:
        """
        [القاضي السيادي - نسخة الوعي السلوكي]
        يصدر الحكم النهائي بناءً على تقاطع الأنماط السلوكية.
        """
        
        recent_transactions = await self._get_recent_transactions(mint)
        
        # 1. تحليل التزامن الزمني
        sync_confidence, sync_reason, sync_footprint = await self.analyze_temporal_synchronization(recent_transactions)
        
        if sync_confidence >= settings.DECISION_CONFIDENCE_THRESHOLD:
            await self.archive_behavior_footprint(mint, "SYNCHRONIZED_MANIPULATION", sync_confidence, sync_footprint)
            return 'EVACUATE', f"إخلاء: {sync_reason}", sync_confidence

        # 2. تحليل مرونة الحوض
        resilience_confidence, resilience_reason, resilience_footprint = await self.analyze_pool_resilience(recent_transactions)

        # إذا كانت النتيجة سلبية، فهي فرصة
        if resilience_confidence == -1.0:
            return 'OPPORTUNITY', resilience_reason, 0.0

        if resilience_confidence > 0.7: # عتبة عالية لموت الزخم
             await self.archive_behavior_footprint(mint, "DEAD_MOMENTUM", resilience_confidence, resilience_footprint)
             return 'EVACUATE', f"إخلاء: {resilience_reason}", resilience_confidence
        
        # 3. تحليل تشتت الإمداد (منطق سابق، يمكن تحسينه لاحقاً)
        # supply_confidence, supply_reason, supply_footprint = await self.analyze_holder_clustering(mint)
        # if supply_confidence > settings.DECISION_CONFIDENCE_THRESHOLD:
        #    await self.archive_behavior_footprint(mint, "HOLDER_CLUSTERING", supply_confidence, supply_footprint)
        #    return 'EVACUATE', f"إخلاء: {supply_reason}", supply_confidence

        # في حالة عدم وجود تهديد مباشر، استمر في المراقبة
        final_reason = f"مراقبة: ثقة التزامن ({sync_confidence:.2f}), ثقة المرونة ({resilience_confidence:.2f})."
        return 'MONITOR', final_reason, max(sync_confidence, resilience_confidence)

    async def archive_behavior_footprint(self, mint: str, pattern_type: str, confidence: float, footprint: Dict):
        """
        أرشفة البصمة السلوكية الكاملة للتعلم المستقبلي.
        """
        archive_entry = {
            "mint": mint,
            "pattern_type": pattern_type,
            "behavioral_footprint": footprint,
            "confidence_score": confidence,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        db.save_behavior_footprint(archive_entry)


brain = SovereignIntelligence()
