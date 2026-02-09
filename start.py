import asyncio
import sys
import os
import subprocess
import time

# استيراد المكونات الأساسية للتحقق من التكامل
from sovereign_foundation import settings, db

class SovereignLauncher:
    """
    [منصة الإطلاق السيادية - نسخة 6.0-FLEX]
    الوظيفة: فحص البيئة، تشغيل المحركات بالتوازي، والترميم الذاتي للمنظومة.
    """
    def __init__(self):
        self.processes = []
        self.banner = """
        \033[1;34m
        SOVEREIGN ELITE PROTOCOL - v6.0-FLEX
        \033[1;32m [ SYSTEM ONLINE ] - HELIUS gRPC/WEBSOCKET STREAMING \033[0m
        \033[1;36m [ INTELLIGENCE ] - FLEXIBLE, PATTERN-BASED ANALYSIS \033[0m
        """

    def check_environment(self):
        """فحص جهوزية القلعة وتكامل الملفات قبل بدء العمليات الحية."""
        print("\033[1;33m🔍 Checking environment integrity...\033[0m")
        
        required_files = [
            ".env", 
            "sovereign_foundation.py", 
            "sovereign_core.py", 
            "intelligence_brain.py", 
            "nexus_interface.py",
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                print(f"\033[1;31m❌ Critical Error: Required file {file} is missing! Cannot start.\033[0m")
                sys.exit(1)
            
        try:
            db._bootstrap() 
            print("✅ Sovereign Memory: Ready for behavioral pattern archival.")
            
            if not settings.HELIUS_RPC_URL or not settings.HELIUS_WS_URL:
                print("⚠️ Warning: Helius RPC/WS URL is missing. Real-time stream will fail.")
                    
        except Exception as e:
            print(f"❌ Failed to sync memory: {e}")
            sys.exit(1)

        print("✅ All engines ready. Flexible framework standing by.")

    async def launch_services(self):
        """إطلاق المنظومة المتكاملة (الواجهة + العقل + المحرك)"""
        print(self.banner)
        
        try:
            print("📡 Opening Nexus Interface (Port 8000)...")
            interface_proc = subprocess.Popen([sys.executable, "nexus_interface.py"])
            self.processes.append(interface_proc)

            await asyncio.sleep(2)

            print(f"🧠 Activating Sovereign Core | Helius Stream Engaged...")
            core_proc = subprocess.Popen([sys.executable, "sovereign_core.py"])
            self.processes.append(core_proc)

            print("\n\033[1;35m--- [ OPERATIONAL REPORT v6.0-FLEX ] ---\033[0m")
            print(f"🔗 Active Pipes: \033[1;32mHELIUS, BIRDEYE, MORALIS\033[0m")
            print(f"🛡️ Behavioral Archive: \033[1;32mActive and Cumulative ✅\033[0m")
            print(f"🖥️ Command URL: \033[1;36mhttp://localhost:8000\033[0m")
            print("\033[1;35m------------------------------------------\033[0m\n")
            
            while True:
                for p in self.processes:
                    if p.poll() is not None:
                        print(f"\033[1;31m⚠️ Pipe interruption! Rebuilding sovereign balance...\033[0m")
                        self.shutdown()
                        time.sleep(2)
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                await asyncio.sleep(5)

        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """إغلاق آمن لجميع العمليات مع تأمين الأرشيف."""
        print("\n\n🛑 Shutting down protocol... Securing behavioral archive...")
        for p in self.processes:
            try:
                p.terminate()
                p.wait(timeout=3)
            except:
                p.kill() 
        print("💤 Shutdown successful. All data saved in sovereign_patterns.db")

if __name__ == "__main__":
    launcher = SovereignLauncher()
    launcher.check_environment()
    try:
        asyncio.run(launcher.launch_services())
    except KeyboardInterrupt:
        pass
