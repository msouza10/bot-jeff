import asyncio
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from src.services.liquipedia_service import LiquipediaService

async def populate():
    service = LiquipediaService()
    
    filepath = 'src/config/gen_cache.txt'
    if not os.path.exists(filepath):
        print(f"File {filepath} not found! Run scripts/generate_cache_list.py first.")
        return

    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    print(f"Found {len(lines)} items to process in {filepath}")
    print("⚠️  Note: Liquipedia API has a strict rate limit (60 req/h).")
    print("⚠️  This script will sleep 5 seconds between requests to be safe(er).")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        
        try:
            type_, name = line.split(':', 1)
        except ValueError:
            print(f"Skipping invalid line: {line}")
            continue
        
        print(f"[{i+1}/{len(lines)}] Processing {type_} '{name}'...")
        
        start_time = time.time()
        result = None
        
        if type_ == 'Team':
            result = await service.get_team(name)
        elif type_ == 'Player':
            result = await service.get_player(name)
            
        if result:
            print(f"   ✅ Success")
        else:
            print(f"   ⚠️  Failed or not found")
            
        # Sleep to respect rate limits
        # If we hit cache, get_team returns fast. If we hit API, we need to wait.
        # Since we don't know if it was a cache hit from here (without parsing logs),
        # we'll just sleep a bit.
        await asyncio.sleep(5) 

if __name__ == "__main__":
    asyncio.run(populate())
