
#!/usr/bin/env python3
"""
Keep alive service for production deployment
"""
import time
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class KeepAlive:
    def __init__(self):
        self.running = True
        self.last_ping = datetime.now()
    
    def ping(self):
        """Update last ping time"""
        self.last_ping = datetime.now()
        logger.info(f"Service ping at {self.last_ping}")
    
    def monitor(self):
        """Monitor service health"""
        while self.running:
            try:
                now = datetime.now()
                time_diff = (now - self.last_ping).total_seconds()
                
                if time_diff > 300:  # 5 minutes without ping
                    logger.warning(f"No ping for {time_diff} seconds")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(60)
    
    def start_monitor(self):
        """Start monitoring in background thread"""
        monitor_thread = threading.Thread(target=self.monitor, daemon=True)
        monitor_thread.start()
        logger.info("Keep alive monitor started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Keep alive monitor stopped")

# Global instance
keep_alive = KeepAlive()
