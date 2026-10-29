"""Environment check without printing secrets: python check_env.py"""
import os
from dotenv import load_dotenv

load_dotenv()
user_agent = os.getenv('SEC_USER_AGENT', '').strip()
key = os.getenv('API_KEY', '').strip()
print('SEC_USER_AGENT:', user_agent if user_agent and 'Your Full Name' not in user_agent else 'MISSING / PLACEHOLDER')
print('API_KEY:', key[:4] + '…' if key else 'MISSING')
print('MODEL_NAME:', os.getenv('MODEL_NAME', 'gpt-4.1-mini'))
print('Keep .env untracked and private. Do not paste the entire key in chat.')
