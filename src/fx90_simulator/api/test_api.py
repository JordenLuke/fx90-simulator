from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..simulator.reader import Reader


CONTROL_PANEL = """<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>FX90 Simulator Test Control</title>
<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:30px auto;padding:0 16px}fieldset{margin:12px 0;padding:16px}label{display:inline-block;width:230px;margin:5px 0}input,select{width:130px;padding:5px}button{padding:8px 14px;margin:4px}.status{font-family:monospace;background:#f4f4f4;padding:12px;white-space:pre-wrap}.danger{border-color:#c33}</style></head>
<body><h1>FX90 Simulator</h1>
<div class='status' id='status'>Loading...</div>
<fieldset><legend>Race</legend>
<label>Runner count <input id='runner_count' type='number'></label>
<label>Bib start <input id='bib_start' type='number'></label>
<label>Bib end <input id='bib_end' type='number'></label><br>
<label>Tag order <select id='tag_order'><option>random</option><option>sequential</option></select></label>
<label>Noise % <input id='noise_percent' type='number' step='0.1'></label>
<label>Report each tag once <input id='report_each_tag_once' type='checkbox'></label>
</fieldset>
<fieldset><legend>Burst behavior</legend>
<label>Max burst size <input id='max_burst_size' type='number'></label>
<label>Max burst seconds <input id='max_burst_seconds' type='number' step='0.01'></label>
<label>Between bursts min <input id='between_bursts_min' type='number' step='0.1'></label>
<label>Between bursts max <input id='between_bursts_max' type='number' step='0.1'></label>
<label>Tag delay (ms) <input id='tag_delay_ms' type='number' step='0.1'></label>
</fieldset>
<fieldset class='danger'><legend>Failure injection</legend>
<label>Disconnect after tags <input id='disconnect_after_tags' type='number'></label>
<label>Disconnect after seconds <input id='disconnect_after_seconds' type='number' step='0.1'></label>
</fieldset>
<button onclick='save()'>Save settings</button><button onclick='start()'>Start Scan</button><button onclick='stop()'>Stop Scan</button><button onclick='reset()'>Reset</button>
<script>
const ids=['runner_count','bib_start','bib_end','tag_order','noise_percent','report_each_tag_once','max_burst_size','max_burst_seconds','between_bursts_min','between_bursts_max','disconnect_after_tags','disconnect_after_seconds','tag_delay_ms'];
function setForm(c){ids.forEach(id=>{let e=document.getElementById(id);e.type==='checkbox'?e.checked=!!c[id]:e.value=c[id]})}
function form(){let c={};ids.forEach(id=>{let e=document.getElementById(id);c[id]=e.type==='checkbox'?e.checked:(e.type==='number'?Number(e.value):e.value)});return c}
async function load(){let r=await fetch('/test/status');let s=await r.json();setForm(s.config);render(s)}
async function save(){let r=await fetch('/test/config',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(form())});let x=await r.json();if(!r.ok)alert(x.detail||'Unable to save');else render(x)}
async function start(){let r=await fetch('/test/start',{method:'POST'});let x=await r.json();if(!r.ok)alert(x.detail||'Unable to start');render(x)}
async function stop(){let r=await fetch('/test/stop',{method:'POST'});render(await r.json())}
async function reset(){let r=await fetch('/test/reset',{method:'POST'});let x=await r.json();setForm(x.config);render(x)}
function render(s){document.getElementById('status').textContent=JSON.stringify(s,null,2)}
load();setInterval(load,1000);
</script></body></html>"""


def create_test_router(reader: Reader) -> APIRouter:
    api = APIRouter(prefix="/test")

    @api.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def panel():
        return CONTROL_PANEL

    @api.get("/status")
    async def status():
        return reader.test_status()

    @api.put("/config")
    async def update_config(values: dict):
        try:
            reader.update_test_config(values)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return reader.test_status()

    @api.post("/start")
    async def start():
        try:
            await reader.start()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return reader.test_status()

    @api.post("/stop")
    async def stop():
        await reader.stop()
        return reader.test_status()

    @api.post("/reset")
    async def reset():
        await reader.reset()
        return reader.test_status()

    return api
