import asyncio
import json
import websockets
import sys
from typing import List, Dict

from sovereign_foundation import settings, db
from intelligence_brain import brain

class SovereignCore:
    """
    [المحرك السيادي المركزي - نسخة النخبة 6.0-FLEX]
    التحول الكامل إلى الرصد عبر WebSocket/gRPC لسرعة فائقة.
    """
    def __init__(self):
        self.manual_slots = []
        self.active_slots = []
        self.last_status = "IDLE"
        self.helius_ws_url = settings.HELIUS_WS_URL # تحديث من PUMP_PORTAL_WS

    def add_manual_token(self, mint: str):
        """إضافة عملة يدوياً للمراقبة المستمرة."""
        if mint not in self.manual_slots:
            self.manual_slots.append(mint)
            if mint not in self.active_slots:
                self.active_slots.append(mint)
            print(f"📥 [CORE] تم حجز مقعد يدوي: {mint}")

    async def _listen_to_helius_stream(self):
        """
        العمود الفقري للرصد: الاستماع المباشر لـ Helius gRPC/WebSocket.
        هنا يتم تطبيق 'محرك التسارع' لاتخاذ القرارات الأولية.
        """
        ws_url = self.helius_ws_url
        if ws_url and ws_url.startswith('https://'):
            ws_url = 'wss://' + ws_url[len('https://'):]

        while True:
            try:
                async with websockets.connect(ws_url) as ws:
                    print("📡 [CORE] متصل بـ Helius Stream. في انتظار البيانات...")
                    # الاشتراك في تدفق البيانات العام أو المحدد
                    subscribe_msg = {"method": "subscribeTokenTrade", "keys": self.active_slots if self.active_slots else ["*"]}
                    await ws.send(json.dumps(subscribe_msg))

                    async for message in ws:
                        token_data = json.loads(message)
                        mint = token_data.get('mint')

                        # 1. محرك التسارع (Velocity Engine)
                        # يحلل نسبة نمو السيولة مقابل سرعة توزيع العملات
                        is_wash_trade, reason = await brain.analyze_velocity(token_data)
                        if is_wash_trade:
                            print(f"🕵️ [VELOCITY ENGINE] تم كشف Wash Trading للعملة {mint} | السبب: {reason}")
                            await brain.archive_manipulation_pattern(mint, "VELOCITY_WASH", {"reason": reason})
                            continue # تجاهل العملة المشبوهة

                        # 2. التحليل الجنائي للمصدر (Cluster Intelligence)
                        is_cluster_attack, cluster_reason = await brain.analyze_funding_source(mint)
                        if is_cluster_attack:
                            print(f"🚨 [CLUSTER INTEL] هجوم عنقودي محتمل على {mint} | السبب: {cluster_reason}")
                            await brain.archive_manipulation_pattern(mint, "CLUSTER_ATTACK", {"reason": cluster_reason})
                            continue

                        # إذا نجحت العملة في اجتياز الاختبارات، قد يتم إضافتها للمقاعد النشطة
                        self.manage_new_candidate(mint)

            except Exception as e:
                print(f"⚠️ [HELIUS_STREAM] انقطع الاتصال: {e}. إعادة المحاولة خلال 5 ثواني...")
                await asyncio.sleep(5)

    def manage_new_candidate(self, mint: str):
        """إدارة إضافة المرشحين الجدد إلى المقاعد النشطة."""
        if len(self.active_slots) < settings.MAX_SLOTS and mint not in self.active_slots:
            self.active_slots.append(mint)
            print(f"✅ [CORE] مرشح جديد تمت إضافته: {mint}")

    async def process_active_slots(self) -> List[str]:
        """معالجة المقاعد النشطة لتقييم الطرد."""
        eviction_list = []
        for mint in self.active_slots:
            if mint in self.manual_slots:
                continue

            # استدعاء Birdeye/Moralis كطبقة تأكيد (Confirmation Layer)
            confirmation_data = await brain.get_confirmation_data(mint)

            if brain.evaluate_eviction(mint, confirmation_data):
                eviction_list.append(mint)
        return eviction_list

    def manage_evictions(self, eviction_list: List[str]):
        """إزالة المقاعد التي تم طردها."""
        for mint in eviction_list:
            if mint in self.active_slots:
                self.active_slots.remove(mint)
                db.save_analysis(mint, "TKN", "EVICTED_PERFORMANCE", 0.99, 0.0, True)
                print(f"🚪 [CORE] تم طرد {mint} بناءً على ضعف الأداء.")
        # إعادة تعيين الاشتراك في الـ WebSocket إذا تغيرت القائمة
        # سيتم إعادة الاتصال تلقائياً في الحلقة الرئيسية لـ _listen_to_helius_stream

    async def run_forever(self):
        """تشغيل المحرك السيادي بشكل مستمر."""
        print(f"🚀 المحرك السيادي المرن نشط | القوانين: {settings.MAX_SLOTS} مقاعد ديناميكية")
        asyncio.create_task(self._listen_to_helius_stream())

        while True:
            try:
                eviction_list = await self.process_active_slots()
                if eviction_list:
                    self.manage_evictions(eviction_list)

            except Exception as e:
                print(f"⚠️ [CORE_LOG] خطأ في دورة العمل الرئيسية: {e}")

            await asyncio.sleep(settings.RADAR_DELAY)

core = SovereignCore()

if __name__ == "__main__":
    try:
        asyncio.run(core.run_forever())
    except KeyboardInterrupt:
        sys.exit(0)
