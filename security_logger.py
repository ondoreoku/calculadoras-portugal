import logging
import os
from datetime import datetime

logger = logging.getLogger('security')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = f"logs/security_{datetime.now().strftime('%Y-%m-%d')}.log"
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def log_security_event(event_type, ip, details=""):
    logger.info(f"{event_type} | IP: {ip} | {details}")

def log_brute_force_attempt(ip, endpoint):
    logger.warning(f"⚠️ BRUTE FORCE DETECTED | IP: {ip} | Endpoint: {endpoint}")

def log_invalid_input(ip, endpoint, input_data):
    logger.warning(f"⚠️ INVALID INPUT | IP: {ip} | Endpoint: {endpoint} | Data: {input_data[:100]}")
