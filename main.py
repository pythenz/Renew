from keep_alive import keep_alive
from core import run_bot
import time

if __name__ == "__main__":
    print("Starting keep_alive server...")
    keep_alive()
    time.sleep(3)
    print("Starting Renew bot...")
    run_bot()
