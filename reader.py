import asyncio,json,random
from datetime import datetime
from config import *
class Reader:
 def __init__(self):
  self.radio_active=False; self.event_num=0; self._task=None; self._senders=set(); self._tags=self._load_tags(); self._noise_tags=[f'E200341201{n:08X}' for n in range(1,NOISE_POOL_SIZE+1)]
 def _load_tags(self):
  if TAGS_FILE.exists():
   d=json.loads(TAGS_FILE.read_text()); tags=d.get('tags',[]) if isinstance(d,dict) else d
  else: tags=[]
  tags=[str(x) for x in tags]
  return (tags if len(tags)>=RUNNER_COUNT else [f'{n:024X}' for n in range(1,RUNNER_COUNT+1)])[:RUNNER_COUNT]
 def register_sender(self,s): self._senders.add(s)
 def unregister_sender(self,s): self._senders.discard(s)
 def status(self):
  return {'antennas':{str(i):'connected' for i in range(1,7)},'ble':{'beaconCounts':{'altBeacon':0,'eddystone':0,'generic':0,'iBeacon':0,'total':0},'scanStartTime':'','scanState':'scanning' if self.radio_active else 'stopped'},'cpu':{'system':0,'user':1},'flash':{k:{'free':0,'total':0,'used':0} for k in ['platform','readerConfig','readerData','rootFileSystem']},'impinjGen2X':{'feature':'none','isActive':False},'interfaceConnectionStatus':{'data':[{'connectionError':'','connectionStatus':'connected' if self._senders else 'disconnected','description':'WEBSOCKET_TEST','interface':'WEBSOCKET_TEST'}]},'ntp':{'offset':0,'reach':-1},'powerNegotiation':'POE+','powerSource':'PWR_BRICK','radioActivity':'active' if self.radio_active else 'inactive','radioConnection':'connected','ram':{'free':70,'total':100,'used':30},'systemTime':datetime.now().strftime('%m/%d/%Y %H:%M'),'temperature':31,'uptime':'0D0H0M0S'}
 def mode(self): return {'delayBetweenAntennaCycles':{'duration':0,'type':'DISABLED'},'environment':'AUTO_DETECT','transmitPower':[27,27,27,27,27,27],'type':'CUSTOM'}
 async def start(self):
  if self.radio_active:return
  self.radio_active=True; self._task=asyncio.create_task(self._generate_race())
 async def stop(self):
  self.radio_active=False
  if self._task and not self._task.done():
   self._task.cancel()
   try: await self._task
   except asyncio.CancelledError: pass
  self._task=None
 async def _generate_race(self):
  remaining=list(self._tags); random.shuffle(remaining)
  while self.radio_active:
   if REPORT_EACH_TAG_ONCE and not remaining: await asyncio.sleep(1); continue
   count=min(random.randint(1,MAX_BURST_SIZE),len(remaining) if REPORT_EACH_TAG_ONCE else MAX_BURST_SIZE)
   for _ in range(count):
    noise=random.random()<NOISE_PERCENT/100; epc=random.choice(self._noise_tags) if noise else (remaining.pop() if REPORT_EACH_TAG_ONCE else random.choice(self._tags))
    self.event_num+=1; event={'data':{'eventNum':self.event_num,'format':'epc','idHex':epc},'timestamp':datetime.now().astimezone().isoformat(timespec='milliseconds'),'type':'CUSTOM'}
    await self._broadcast(json.dumps(event,separators=(',',':')))
    if count>1: await asyncio.sleep(random.uniform(MAX_BURST_SECONDS/count*.25,MAX_BURST_SECONDS/count*1.5))
   await asyncio.sleep(random.uniform(BETWEEN_BURSTS_MIN,BETWEEN_BURSTS_MAX))
 async def _broadcast(self,msg):
  for s in list(self._senders):
   try: await s(msg)
   except Exception: self.unregister_sender(s)
