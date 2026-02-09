import numpy as np
import httpx
from typing import Dict, Any, List, Tuple

from sovereign_foundation import db, settings

class SovereignIntelligence:
    """
    [المختبر السيادي - نسخة الذكاء العنقودي 2027]
    تحليل سلوكي مرن، كشف التلاعب المتقدم، وأرشفة الحمض النووي للأنماط.
    """

    def __init__(self):
        self.birdeye_client = httpx.AsyncClient(baseURL="https://public-api.birdeye.so", headers={"X-API-KEY": settings.BIRDEYE_API_KEY})
        self.moralis_client = httpx.AsyncClient(baseURL="https://solana-gateway.moralis.io", headers={"X-API-KEY": settings.MORALIS_API_KEY})

    async def analyze_velocity(self, token_data: Dict) -> Tuple[bool, str]:
        """
        محرك التسارع (Velocity Engine): يحلل نسبة نمو السيولة مقابل سرعة توزيع العملات.
        يكشف عن "MM Wash Trading" عندما ينمو الحجم بشكل كبير دون زيادة مقابلة في عدد المحافظ الحقيقية.
        """
        liquidity_growth = token_data.get('liquidity_growth_ratio', 0.0)
        holder_velocity = token_data.get('holder_velocity', 0.0)

        # منطق مرن: إذا كان نمو السيولة مرتفعًا جدًا ولكن سرعة اكتساب الحاملين بطيئة، فهذا غسيل أموال.
        if liquidity_growth > 2.5 and holder_velocity < 0.1:
            return True, "Explosive volume with stagnant holder growth."

        # يمكن إضافة المزيد من القواعد المرنة هنا

        return False, ""

    async def analyze_funding_source(self, mint: str) -> Tuple[bool, str]:
        """
        التحليل الجنائي للمصدر (Cluster Intelligence): يتتبع مصدر تمويل المحافظ الكبرى.
        إذا تم تمويلها من محفظة أم واحدة أو عبر 'Disper'، يتم تصنيفها كـ 'Cluster Attack'.
        """
        try:
            # 1. جلب أكبر حاملي الأسهم من Birdeye
            holders_resp = await self.birdeye_client.get(f"/defi/token_holders?address={mint}")
            if holders_resp.status_code != 200:
                return False, "Could not fetch holders."

            top_holders = holders_resp.json().get('data', {}).get('holders', [])[:10] # تحليل أفضل 10

            # 2. التحليل الجنائي لمصدر تمويل كل حامل كبير
            funding_sources = []
            for holder in top_holders:
                address = holder.get('address')
                # استخدام Moralis لتتبع تاريخ المعاملات
                tx_history_resp = await self.moralis_client.get(f"/account/mainnet/{address}/spl/transfers")
                if tx_history_resp.status_code == 200:
                    transactions = tx_history_resp.json().get('result', [])
                    # البحث عن أول معاملة (مصدر التمويل)
                    if transactions:
                        funding_sources.append(transactions[-1].get('from'))

            # 3. كشف هجوم العنقود
            if len(funding_sources) > 3:
                unique_sources = set(funding_sources)
                # إذا كان أكثر من 50% من كبار الملاك ممولين من مصدر واحد، فهذا هجوم عنقودي
                if len(unique_sources) <= len(funding_sources) * 0.5:
                    return True, f"Cluster attack detected. {len(funding_sources)} top holders funded by {len(unique_sources)} sources."

        except Exception as e:
            return False, f"Error during funding analysis: {e}"

        return False, ""

    async def archive_manipulation_pattern(self, mint: str, pattern_type: str, details: Dict):
        """
        الوعي بالأرشفة: يحفظ 'نمط التلاعب' (Pattern DNA) في market_makers_archive.json.
        """
        archive_entry = {
            "mint": mint,
            "pattern_type": pattern_type,
            "pattern_dna": details, # حفظ التفاصيل الكاملة للنمط
            "timestamp": np.datetime64('now')
        }
        db.save_pattern_to_archive(archive_entry)
        print(f"💾 [ARCHIVE] تم أرشفة نمط تلاعب جديد: {pattern_type} للعملة {mint}")

    async def get_confirmation_data(self, mint: str) -> Dict:
        """
        استخدام Birdeye/Moralis كطبقات تأكيد (Confirmation Layers) للتحقق من البيانات.
        """
        try:
            # جلب بيانات الأسعار والسيولة من Birdeye للتأكيد
            token_overview_resp = await self.birdeye_client.get(f"/defi/overview?address={mint}")
            if token_overview_resp.status_code == 200:
                return token_overview_resp.json().get('data', {})
        except Exception as e:
            print(f"⚠️ [CONFIRMATION] فشل الحصول على بيانات التأكيد من Birdeye: {e}")

        return {}

    def evaluate_eviction(self, mint: str, confirmation_data: Dict) -> bool:
        """
        [قاضي المقاعد] يقرر ما إذا كان يجب طرد العملة بناءً على بيانات التأكيد.
        منطق الطرد يعتمد على قواعد مرنة بدلاً من الأرقام الثابتة.
        """
        # مثال: إذا انخفضت السيولة بأكثر من 20% خلال الساعة الماضية، قم بالطرد
        liquidity_change_1h = confirmation_data.get('liquidityChange1h', 0)
        if liquidity_change_1h < -20:
            print(f"🚪 [EVICTION] طرد {mint} بسبب انخفاض السيولة بنسبة {liquidity_change_1h}%.")
            return True

        # يمكن إضافة المزيد من قواعد الطرد المرنة هنا

        return False

brain = SovereignIntelligence()
