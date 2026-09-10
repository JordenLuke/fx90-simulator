from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..simulator.reader import Reader
from ..simulator.scenarios import ScenarioLoader


CONTROL_PANEL = """<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>FX90 Simulator</title>
<style>
:root{color-scheme:light}*{box-sizing:border-box}body{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;background:#f3f7fb;color:#1f2937}header{background:#1565c0;color:white;padding:22px 24px;box-shadow:0 2px 6px rgba(0,0,0,.15)}header h1{margin:0 0 4px;font-size:25px}header p{margin:0;opacity:.9}.container{max-width:1100px;margin:24px auto;padding:0 18px 40px}.card{background:white;border:1px solid #d6e2f0;border-radius:9px;padding:20px;margin-bottom:18px;box-shadow:0 2px 6px rgba(30,70,110,.06)}.card h2{color:#1565c0;margin:0 0 16px;font-size:19px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 20px}.field label{display:block;font-weight:600;margin-bottom:5px;font-size:14px}input,select,textarea{width:100%;padding:9px 10px;border:1px solid #b8c7d9;border-radius:5px;background:white;color:#1f2937;font:inherit}input:focus,select:focus,textarea:focus{outline:2px solid #90caf9;border-color:#1565c0}.checkbox{display:flex;align-items:center;gap:8px;height:38px}.checkbox input{width:auto}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}button{border:0;border-radius:5px;padding:10px 17px;background:#1565c0;color:white;font:inherit;font-weight:600;cursor:pointer}button:hover{background:#0d47a1}button.stop{background:#c62828}button.stop:hover{background:#8e0000}button.reset{background:#546e7a}button.reset:hover{background:#37474f}button:disabled{opacity:.55;cursor:not-allowed}.status-banner{display:flex;align-items:center;gap:12px;padding:14px 16px;border-radius:7px;margin-bottom:18px;font-weight:700}.status-banner.running{background:#e8f5e9;color:#1b5e20;border:1px solid #a5d6a7}.status-banner.stopped{background:#eef2f6;color:#455a64;border:1px solid #cfd8dc}.status-dot{width:12px;height:12px;border-radius:50%;background:currentColor}.counters{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}.counter{background:#f7faff;border:1px solid #d6e2f0;border-radius:7px;padding:13px}.counter .value{display:block;font-size:24px;font-weight:700;color:#1565c0}.counter .label{font-size:12px;color:#607d8b;text-transform:uppercase;letter-spacing:.04em}.hint{color:#607d8b;font-size:13px;margin:6px 0 0}#error{color:#b71c1c;margin-top:10px;font-weight:600}pre{margin:0;background:#f5f8fb;border:1px solid #d6e2f0;border-radius:6px;padding:14px;overflow-x:auto;color:#263238;font-size:12px}@media(max-width:900px){.counters{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:500px){.grid,.counters{grid-template-columns:1fr}.container{padding:0 12px 30px}}
</style></head><body>
<header><h1>FX90 Simulator</h1><p>Test the Ultra Tracker RFID interface using the Zebra FXR90 simulator.</p></header>
<div class='container'>
<div class='status-banner stopped' id='status_banner'><span class='status-dot'></span><span id='scan_state'>Stopped</span></div>
<div class='card'><h2>Test Scenario</h2><div class='field'><label for='scenario'>Scenario</label><select id='scenario' onchange='loadScenario()'></select><p class='hint' id='scenario_description'></p></div></div>
<div class='card'><h2>Live Test Status</h2><div class='counters'><div class='counter'><span class='value' id='tags_sent'>0</span><span class='label'>Tags sent</span></div><div class='counter'><span class='value' id='good_tags_sent'>0</span><span class='label'>Runner tags</span></div><div class='counter'><span class='value' id='noise_tags_sent'>0</span><span class='label'>Noise tags</span></div><div class='counter'><span class='value' id='remaining'>0</span><span class='label'>Remaining</span></div><div class='counter'><span class='value' id='custom_noise_remaining'>0</span><span class='label'>Custom noise</span></div><div class='counter'><span class='value' id='clients'>0</span><span class='label'>WebSocket clients</span></div></div></div>
<div class='card'><h2>Simulation Settings</h2><div class='grid'>
<div class='field'><label for='simulation_mode'>Simulation mode</label><select id='simulation_mode'><option value='start-line'>Start Line</option><option value='finish-line'>Finish Line</option></select></div><div class='field'><label for='duration_hours'>Duration (hours)</label><input id='duration_hours' type='number' min='0.01' step='0.1'></div>
<div class='field'><label for='runner_count'>Runner count</label><input id='runner_count' type='number' min='1'></div><div class='field'><label for='tag_order'>Tag order</label><select id='tag_order'><option value='random'>Random</option><option value='sequential'>Sequential</option></select></div>
<div class='field'><label for='bib_start'>Bib start</label><input id='bib_start' type='number' min='1'></div><div class='field'><label for='bib_end'>Bib end</label><input id='bib_end' type='number' min='1'></div>
<div class='field'><label for='noise_percent'>Unknown/noise %</label><input id='noise_percent' type='number' min='0' max='100' step='0.1'></div><div class='field checkbox'><input id='report_each_tag_once' type='checkbox'><label for='report_each_tag_once'>Report each runner tag once</label></div>
<div class='field'><label for='max_burst_size'>Maximum burst size</label><input id='max_burst_size' type='number' min='1'></div><div class='field'><label for='max_burst_seconds'>Maximum burst duration (seconds)</label><input id='max_burst_seconds' type='number' min='0' step='0.01'></div>
<div class='field'><label for='between_bursts_min'>Minimum time between bursts (seconds)</label><input id='between_bursts_min' type='number' min='0' step='0.1'></div><div class='field'><label for='between_bursts_max'>Maximum time between bursts (seconds)</label><input id='between_bursts_max' type='number' min='0' step='0.1'></div>
<div class='field'><label for='tag_delay_ms'>Artificial tag delay (ms)</label><input id='tag_delay_ms' type='number' min='0' step='0.1'></div></div><p class='hint'>Selecting a scenario loads its JSON settings into these fields. You can adjust them before starting the simulator.</p></div>
<div class='card'><h2>Custom Noise</h2><textarea id='noise_tags' rows='6' spellcheck='false' placeholder='["00000000000000000000015A"]'></textarea><p class='hint'>Optional JSON array. Custom noise reads are consumed once before the generated noise pool.</p></div>
<div class='card'><h2>Failure Injection</h2><div class='grid'><div class='field'><label for='disconnect_after_tags'>Disconnect after tags (0 = disabled)</label><input id='disconnect_after_tags' type='number' min='0'></div><div class='field'><label for='disconnect_after_seconds'>Disconnect after seconds (0 = disabled)</label><input id='disconnect_after_seconds' type='number' min='0' step='0.1'></div></div><p class='hint'>Deliberately closes the WebSocket so reconnect and recovery behavior can be tested.</p></div>
<div class='card'><h2>Controls</h2><div class='actions'><button id='save_button' onclick='save()'>Save Settings</button><button id='start_button' onclick='start()'>Start Scan</button><button class='stop' onclick='stop()'>Stop Scan</button><button class='reset' onclick='reset()'>Reset</button></div><div id='error'></div></div>
<div class='card'><h2>Diagnostic Details</h2><pre id='status_json'>Loading...</pre></div></div>
<script>
const ids=['simulation_mode','duration_hours','runner_count','bib_start','bib_end','tag_order','noise_percent','report_each_tag_once','max_burst_size','max_burst_seconds','between_bursts_min','between_bursts_max','disconnect_after_tags','disconnect_after_seconds','tag_delay_ms'];let initialized=false,scenarios=[];
function setForm(c){ids.forEach(id=>{const e=document.getElementById(id);if(e.type==='checkbox')e.checked=!!c[id];else e.value=c[id]??''});document.getElementById('noise_tags').value=c.noise_tags&&c.noise_tags.length?JSON.stringify(c.noise_tags,null,2):''}
function form(){const c={};ids.forEach(id=>{const e=document.getElementById(id);c[id]=e.type==='checkbox'?e.checked:(e.type==='number'?Number(e.value):e.value)});c.scenario_id=document.getElementById('scenario').value;const text=document.getElementById('noise_tags').value.trim();if(text){const parsed=JSON.parse(text);if(!Array.isArray(parsed)||!parsed.every(x=>typeof x==='string'))throw new Error('Custom noise tags must be a JSON array of strings.');c.noise_tags=parsed}else c.noise_tags=null;return c}
function render(s){const running=!!s.scanning;document.getElementById('status_banner').className='status-banner '+(running?'running':'stopped');document.getElementById('scan_state').textContent=running?'Scanning':'Stopped';['tags_sent','good_tags_sent','noise_tags_sent','remaining','custom_noise_remaining','clients'].forEach(id=>document.getElementById(id).textContent=s[id]??0);document.getElementById('status_json').textContent=JSON.stringify(s,null,2);document.getElementById('start_button').disabled=running;document.getElementById('save_button').disabled=running;document.getElementById('scenario').disabled=running;ids.forEach(id=>document.getElementById(id).disabled=running);document.getElementById('noise_tags').disabled=running}
function showError(m){document.getElementById('error').textContent=m||''}
async function request(url,options){const r=await fetch(url,options);let x={};try{x=await r.json()}catch(_){}if(!r.ok)throw new Error(x.detail||x.message||'Request failed');return x}
async function loadScenarios(selected){const list=await request('/test/scenarios');scenarios=list;const select=document.getElementById('scenario');select.innerHTML='';list.forEach(s=>{const o=document.createElement('option');o.value=s.id;o.textContent=s.name;select.appendChild(o)});if(selected&&list.some(s=>s.id===selected))select.value=selected;else if(list.length)select.selectedIndex=0;updateDescription()}
function updateDescription(){const s=scenarios.find(x=>x.id===document.getElementById('scenario').value);document.getElementById('scenario_description').textContent=s?s.description:''}
async function loadScenario(){try{const id=document.getElementById('scenario').value;const s=await request('/test/scenarios/'+encodeURIComponent(id));setForm(s.settings);document.getElementById('scenario').value=s.id;updateDescription();showError('')}catch(e){showError(e.message)}}
async function load(){try{const s=await request('/test/status');if(!initialized){await loadScenarios(s.scenario_id);setForm(s.config);document.getElementById('scenario').value=s.scenario_id;updateDescription();initialized=true}render(s);showError('')}catch(e){showError(e.message)}}
async function save(){try{render(await request('/test/config',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(form())}));showError('')}catch(e){showError(e.message)}}
async function start(){try{render(await request('/test/start',{method:'POST'}));showError('')}catch(e){showError(e.message)}}
async function stop(){try{render(await request('/test/stop',{method:'POST'}));showError('')}catch(e){showError(e.message)}}
async function reset(){try{const s=await request('/test/reset',{method:'POST'});setForm(s.config);document.getElementById('scenario').value=s.scenario_id;updateDescription();render(s);showError('')}catch(e){showError(e.message)}}
load();setInterval(load,1000);
</script></body></html>"""


def create_test_router(reader: Reader, scenarios: ScenarioLoader) -> APIRouter:
    api = APIRouter(prefix="/test")

    def result() -> dict:
        return {**reader.test_status(), "scenario_id": reader.test_config.scenario_id}

    @api.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def panel():
        return CONTROL_PANEL

    @api.get("/scenarios")
    async def list_scenarios():
        try:
            return [{"id": s.id, "name": s.name, "description": s.description} for s in scenarios.list()]
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @api.get("/scenarios/{scenario_id}")
    async def get_scenario(scenario_id: str):
        try:
            scenario = scenarios.get(scenario_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Scenario not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"id": scenario.id, "name": scenario.name, "description": scenario.description, "settings": scenario.settings}

    @api.get("/status")
    async def status():
        return result()

    @api.put("/config")
    async def update_config(values: dict):
        try:
            reader.update_test_config(values)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result()

    @api.post("/start")
    async def start():
        try:
            await reader.start()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result()

    @api.post("/stop")
    async def stop():
        await reader.stop()
        return result()

    @api.post("/reset")
    async def reset():
        await reader.reset()
        return result()

    return api
