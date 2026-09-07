import base64,uvicorn
from fastapi import FastAPI,Header,HTTPException,Request,WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse,Response
from config import *
from reader import Reader
from websocket import manager
app=FastAPI(title='FX90 Simulator'); app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*']); reader=Reader()
def bearer(a):
 if a!=f'Bearer {BEARER_TOKEN}': raise HTTPException(401,'Unauthorized')
@app.get('/cloud/localRestLogin')
async def login(authorization:str|None=Header(default=None)):
 if not authorization or not authorization.startswith('Basic '): raise HTTPException(401,'Basic authentication required')
 try: u,p=base64.b64decode(authorization[6:]).decode().split(':',1)
 except Exception: raise HTTPException(401,'Invalid Basic authentication')
 if u!=USERNAME or p!=PASSWORD: raise HTTPException(401,'Invalid username or password')
 return {'message':BEARER_TOKEN}
@app.get('/cloud/status')
async def status(authorization:str|None=Header(default=None)): bearer(authorization); return reader.status()
@app.get('/cloud/mode')
async def mode(authorization:str|None=Header(default=None)): bearer(authorization); return reader.mode()
@app.put('/cloud/mode')
async def set_mode(request:Request,authorization:str|None=Header(default=None)): bearer(authorization); return Response(status_code=204)
@app.put('/cloud/start')
async def start(request:Request,authorization:str|None=Header(default=None)):
 bearer(authorization)
 if reader.radio_active:return JSONResponse(422,{'message':'start currently ongoing'})
 await reader.start(); return Response(status_code=204)
@app.put('/cloud/stop')
async def stop(authorization:str|None=Header(default=None)): bearer(authorization); await reader.stop(); return Response(status_code=204)
@app.websocket('/ws')
async def ws_endpoint(ws:WebSocket):
 await manager.connect(ws)
 async def sender(msg): await ws.send_text(msg)
 reader.register_sender(sender)
 try:
  while True: await ws.receive()
 except WebSocketDisconnect: pass
 finally: reader.unregister_sender(sender); manager.disconnect(ws)
@app.on_event('startup')
async def startup():
 if AUTO_START: await reader.start()
if __name__=='__main__': uvicorn.run('app:app',host=HOST,port=HTTPS_PORT,ssl_certfile=str(CERT_FILE),ssl_keyfile=str(KEY_FILE))
