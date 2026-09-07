class ConnectionManager:
 def __init__(self): self.connections=set()
 async def connect(self,ws): await ws.accept(); self.connections.add(ws)
 def disconnect(self,ws): self.connections.discard(ws)
manager=ConnectionManager()
