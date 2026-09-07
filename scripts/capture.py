import asyncio,ssl
from pathlib import Path
import websockets
URL='wss://fxr90c94e1c/ws'; OUTPUT=Path(__file__).resolve().parent.parent/'data'/'fxr90-tag-data.log'
async def capture():
 ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE; OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 with OUTPUT.open('a',encoding='utf-8') as log:
  while True:
   try:
    print(f'Connecting to {URL}...')
    async with websockets.connect(URL,ssl=ctx) as ws:
     print('Connected.'); print(f'Saving messages to {OUTPUT}')
     async for msg in ws:
      if isinstance(msg,bytes): msg=msg.decode('utf-8')
      print(msg); log.write(msg+'\n'); log.flush()
   except Exception as ex: print(f'Connection ended: {type(ex).__name__}: {ex}')
   await asyncio.sleep(2)
if __name__=='__main__':
 try: asyncio.run(capture())
 except KeyboardInterrupt: print('Capture stopped.')
