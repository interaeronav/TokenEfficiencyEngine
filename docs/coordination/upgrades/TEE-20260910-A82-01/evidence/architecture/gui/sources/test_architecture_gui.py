"""Loopback GUI security and real persistence; no owner browser or project used."""

from __future__ import annotations

import http.client
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from tee.architecture.gui import MAX_BODY, ArchitectureGui
from tee.architecture.service import ArchitectureService


@pytest.fixture
def gui(tmp_path):
    grants = {"write": True}
    observed = []

    def authorize(write):
        observed.append(write)
        if write and not grants["write"]:
            raise PermissionError("revoked")

    instance = ArchitectureGui(ArchitectureService(tmp_path), authorize)
    instance.start()
    yield instance, grants, observed
    instance.close()


def request(gui, path, data=None, *, headers=None, authorized=True, method=None):
    endpoint = urlsplit(gui.url)
    token = parse_qs(endpoint.fragment)["token"][0]
    base = f"http://{endpoint.netloc}"
    actual = {"Origin": base}
    if authorized:
        actual["Authorization"] = "Bearer " + token
    payload = None
    if data is not None:
        payload = json.dumps(data).encode()
        actual["Content-Type"] = "application/json"
    actual.update(headers or {})
    connection = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=5)
    connection.request(method or ("POST" if data is not None else "GET"), path, payload, actual)
    response = connection.getresponse()
    raw = response.read()
    result = (
        raw.decode()
        if response.getheader("Content-Type", "").startswith("text/html")
        else json.loads(raw)
    )
    response_headers = dict(response.getheaders())
    connection.close()
    return response.status, result, response_headers


def create(gui):
    status, result, _ = request(gui, "/api/create", {"name": "Fixture", "preset": "compact-house"})
    assert status == 200, result
    return result["model_id"]


def test_static_page_csp_fragment_secret_and_explicit_start(gui):
    instance, _, observed = gui
    endpoint = urlsplit(instance.url)
    assert endpoint.hostname == "127.0.0.1" and not endpoint.query
    token = parse_qs(endpoint.fragment)["token"][0]
    assert len(token) >= 43
    status, page, headers = request(instance, "/", authorized=False)
    assert status == 200 and "archkiln" in page
    assert token not in page and "__NONCE__" not in page
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "unsafe-inline" not in headers["Content-Security-Policy"]
    assert headers["Cache-Control"] == "no-store"
    assert "innerHTML" not in page and "https://" not in page
    assert observed == []
    before = instance.url
    instance.start()
    assert instance.url == before


@pytest.mark.parametrize(
    "path,headers,authorized,expected",
    [
        ("/api/status", {}, False, 401),
        ("/api/status", {"Authorization": "Bearer invalid"}, True, 401),
        ("/api/status", {"Origin": "https://evil.example"}, True, 403),
        ("/api/status", {"Host": "evil.example"}, True, 403),
        ("/api/status?token=not-a-bearer", {}, False, 401),
        ("/api/status?unused=x", {}, True, 400),
        ("/api/status?unused=x&unused=y", {}, True, 400),
        ("/api/../status", {}, True, 404),
        ("/../../.tee/config.toml", {}, True, 404),
        ("/api/%73tatus", {}, True, 404),
        ("http://evil.example/api/status", {}, True, 403),
    ],
)
def test_access_origin_and_endpoint_refusals(gui, path, headers, authorized, expected):
    instance, _, observed = gui
    status, _, _ = request(instance, path, headers=headers, authorized=authorized)
    assert status == expected
    if expected in {401, 403, 404}:
        assert not observed


def test_same_service_edit_undo_revision_and_saved_state(gui):
    instance, _, observed = gui
    model_id = create(instance)
    status, state, _ = request(instance, "/api/state?model_id=" + model_id)
    assert status == 200 and state["revision"] == 1 and "history" not in state
    edit = {
        "model_id": model_id,
        "expected_revision": 1,
        "operations": [{"op": "update", "id": "cabinet", "changes": {"width": 1200}}],
    }
    status, changed, _ = request(instance, "/api/edit", edit)
    assert status == 200 and changed["revision"] == 2
    status, schedule, _ = request(instance, f"/api/schedule?model_id={model_id}&entity_id=cabinet")
    assert status == 200 and schedule["revision"] == 2
    assert next(p for p in schedule["panels"] if p["role"] == "back")["finished_width"] == 1164
    assert request(instance, "/api/edit", edit)[0] == 409  # stale browser
    assert request(instance, "/api/undo", {"model_id": model_id})[0] == 409
    assert request(instance, "/api/undo", {"model_id": model_id, "expected_revision": 2})[0] == 200
    independent = ArchitectureService(instance.service.project)
    assert independent.state(model_id)["entities"]["cabinet"]["width"] == 900
    assert independent.state(model_id)["revision"] == 3
    assert True in observed and False in observed
    status, stock, _ = request(
        instance,
        "/api/query",
        {
            "model_id": model_id,
            "entity_id": "cabinet",
            "detail": "cabinet",
            "stock": {"sheet_width": 1220, "sheet_height": 2440, "kerf": 3},
        },
    )
    assert status == 200 and stock["nesting"]["sheet_count"] >= 1


def test_dynamic_authority_revocation_and_no_implicit_mutation(gui):
    instance, grants, _ = gui
    model_id = create(instance)
    before = instance.service.state(model_id)
    grants["write"] = False
    assert (
        request(
            instance,
            "/api/edit",
            {
                "model_id": model_id,
                "expected_revision": 1,
                "operations": [{"op": "delete", "id": "cabinet"}],
            },
        )[0]
        == 403
    )
    assert request(instance, "/api/export", {"model_id": model_id, "format": "json"})[0] == 403
    assert request(instance, "/api/state?model_id=" + model_id)[0] == 200
    assert instance.service.state(model_id) == before


def test_invalid_geometry_and_escaping_import_do_not_mutate(gui):
    instance, _, _ = gui
    model_id = create(instance)
    before = instance.service.state(model_id)
    assert (
        request(
            instance,
            "/api/edit",
            {
                "model_id": model_id,
                "expected_revision": 1,
                "operations": [{"op": "update", "id": "south", "changes": {"height": 1}}],
            },
        )[0]
        == 400
    )
    assert (
        request(
            instance,
            "/api/import",
            {"model_id": model_id, "path": "../outside.ply", "units": "mm", "tolerance_mm": 10},
        )[0]
        == 400
    )
    assert instance.service.state(model_id) == before


def test_preview_and_json_export_paths(gui):
    instance, _, _ = gui
    model_id = create(instance)
    status, preview, _ = request(instance, "/api/preview?model_id=" + model_id)
    assert status == 200 and preview["units"] == "mm" and preview["meshes"]
    status, exported, _ = request(instance, "/api/export", {"model_id": model_id, "format": "json"})
    assert status == 200
    assert exported["directory"].startswith(str(instance.service.project / "output/archkiln"))
    assert request(instance, exported["directory"])[0] == 404  # no arbitrary file endpoint


def test_request_bounds_content_type_csrf_and_preflight(gui):
    instance, _, _ = gui
    assert (
        request(instance, "/api/create", {"name": "x"}, headers={"Content-Type": "text/plain"})[0]
        == 415
    )
    assert request(instance, "/api/create", {"name": "x"}, headers={"Origin": "null"})[0] == 403
    assert request(instance, "/api/create?extra=1", {"name": "x"})[0] == 400
    assert (
        request(
            instance, "/api/create", {"name": "x"}, headers={"Content-Length": str(MAX_BODY + 1)}
        )[0]
        == 413
    )
    assert request(instance, "/api/create", [1, 2])[0] == 400
    assert request(instance, "/api/create", method="OPTIONS")[0] == 403
    endpoint = urlsplit(instance.url)
    token = parse_qs(endpoint.fragment)["token"][0]
    connection = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=5)
    connection.request(
        "POST",
        "/api/create",
        b'{"name":"x"}',
        {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )
    response = connection.getresponse()
    assert response.status == 403
    response.read()
    connection.close()


@pytest.mark.skipif(
    os.environ.get("TEE_GUI_BROWSER_SMOKE") != "1",
    reason="Opt-in owned headless Chrome; ordinary HTTP tests need no browser.",
)
@pytest.mark.parametrize("race_mode", [False, True], ids=["workflow", "delayed-responses"])
def test_real_headless_browser_workflow(gui, tmp_path, race_mode):
    """Real UI events, canvas and CSP; isolated Chrome profile, never owner tabs."""
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    node = shutil.which("node")
    if not chrome.is_file() or not node:
        pytest.skip("Chrome and Node required for this optional live browser smoke")
    instance, _, _ = gui
    (tmp_path / "wall.xyz").write_text(
        "\n".join(f"{x * 100} 5000 {z * 100}" for x in range(10, 41) for z in range(29))
    )
    profile = tmp_path / "chrome"
    screenshot = Path(os.environ.get("TEE_GUI_EVIDENCE_DIR", str(tmp_path))) / "workbench.png"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        [
            str(chrome),
            "--headless=new",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--remote-debugging-port=0",
            f"--user-data-dir={profile}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    script = r"""
import fs from 'node:fs';
const [port,url,screenshot]=process.argv.slice(1);
const targets=await(await fetch('http://127.0.0.1:'+port+'/json/list')).json();
const target=targets.find(t=>t.type==='page');
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
let seq=0;const pending=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);
 m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}
 else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text)};
function send(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;
pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))})}
async function run(expression){const r=await send('Runtime.evaluate',
{expression,returnByValue:true,awaitPromise:true});
if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
async function until(expression){for(let i=0;i<120;i++){if(await run(expression))return;
await new Promise(r=>setTimeout(r,50))}
throw Error('Timed out: '+expression+'; '+
await run("document.getElementById('status').textContent"))}
await send('Runtime.enable');await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride',
{width:1500,height:1100,deviceScaleFactor:2,mobile:false});
await send('Page.navigate',{url});
await until("document.readyState==='complete'&&document.getElementById('create')!==null");
await run(`$('preset').value='compact-house';
$('modelName').value='Browser fixture';
$('create').click()`);
await until("state?.revision===1&&geometry?.revision===1");
await run("document.querySelector('[data-id=\"cabinet\"]').click()");
await until("document.querySelector('#schedule table')!==null");
await run("document.querySelector('[data-field=\"width\"]').value='1200';$('saveEntity').click()");
await until("state?.revision===2&&geometry?.revision===2");
if(await run("state.entities.cabinet.width")!==1200)throw Error('Edit did not persist');
await run("$('undo').click()");await until("state?.revision===3&&geometry?.revision===3");
if(await run("state.entities.cabinet.width")!==900)throw Error('Undo failed');
await run("$('nest').click()");await until("document.querySelector('#nesting svg')!==null");
if(!await run("$('schedule').textContent.includes('864')"))throw Error('Schedule stayed stale');
await run(`$('country').value='DE';
$('region').value='BE';
$('municipality').value='Berlin';
$('saveLocation').click()`);
await until("state?.revision===4&&geometry?.revision===4");
await run("$('check').click()");await until("$('results').textContent.includes('not_verified')");
await run(`$('sourcePath').value='wall.xyz';
$('sourceUnits').value='mm';
$('tolerance').value='1';
$('import').click()`);
await until("document.querySelector('#candidateList button')!==null");
await run(`document.querySelector('#candidateList button').click();
$('promotionHeight').value='2800';
$('promotionThickness').value='200';
$('promotionOffset').value='100';
$('promote').click()`);
await until("state?.revision===5&&geometry?.revision===5");
await run("$('format').value='json';$('export').click()");
await until("$('status').textContent.startsWith('Export written')");
let raceChecks=[];
__RACE__
const evidence=await run(`({revision:state.revision,
modelId:loadedModelId,
entityCount:Object.keys(state.entities).length,
meshes:geometry.meshes.length,
canvases:[...document.querySelectorAll('canvas')].map(c=>[c.width,c.height]),
coverage:state.project.jurisdiction})`);
if(errors.length)throw Error('Browser errors: '+errors.join(';'));
const shot=await send('Page.captureScreenshot',{format:'png'});
fs.writeFileSync(screenshot,Buffer.from(shot.data,'base64'));
console.log(JSON.stringify({ok:true,...evidence,raceChecks,errors}));ws.close();
"""
    race_script = r"""
const original=await run('model()');
const pair=await run(`(async()=>{
 const a=await api('create',{name:'Race A',preset:'compact-house'},true);
 const b=await api('create',{name:'Race B',preset:'compact-house'},true);
 await models(a.model_id);await select('cabinet');
 return {a:a.model_id,b:b.model_id,aDoc:state.document_id};})()`);
await run(`globalThis.race={rules:[],held:[],posts:[],real:window.fetch.bind(window)};
window.fetch=async function(url,options={}){
 const parsed=new URL(url,location.href);
 const args=options.body?JSON.parse(options.body):Object.fromEntries(parsed.searchParams);
 if(options.method==='POST')race.posts.push({path:parsed.pathname,args});
 const response=await race.real(url,options);
 const index=race.rules.findIndex(r=>r.path===parsed.pathname&&r.id===(args.model_id||null));
 if(index<0)return response;
 race.rules.splice(index,1);
 return await new Promise(resolve=>race.held.push({release:()=>resolve(response)}));};`);
async function hold(path,id){await run(`race.rules.push(${JSON.stringify({path,id})})`)}
async function release(){await run('race.held.shift().release()')}
async function choose(id){await run(`$('models').value=${JSON.stringify(id)};
 $('models').dispatchEvent(new Event('change'))`);
 await until(`ready()&&loadedModelId===${JSON.stringify(id)}`)}
async function ensure(expression,message){if(!await run(expression))throw Error(message)}
// Changing the selector alone cannot combine A's draft/revision with B's ID.
await run(`$('models').value=${JSON.stringify(pair.b)};$('saveEntity').click()`);
await until("!busyActions.has('saveEntity')");
await ensure("race.posts.length===0",'Stale A draft dispatched a mutation to B');
await run(`$('models').value=${JSON.stringify(pair.a)}`);
raceChecks.push('selector_guard');
// An older load cannot overwrite B, even with identical IDs and revision 1.
await hold('/api/state',pair.a);await run("$('refresh').click()");
await until('race.held.length===1');await choose(pair.b);await release();
await until("!busyActions.has('refresh')");
await ensure(`loadedModelId===${JSON.stringify(pair.b)}&&state.revision===1&&draft===null`,
 'Late A state overwrote B');raceChecks.push('stale_state');
// Another client edits A between its state response and preview request.
await choose(pair.a);await hold('/api/state',pair.a);await run("$('refresh').click()");
await until('race.held.length===1');
await run(`race.real('/api/edit',{method:'POST',headers:{Authorization:'Bearer '+token,
 'Content-Type':'application/json'},body:JSON.stringify({model_id:${JSON.stringify(pair.a)},
 expected_revision:1,operations:[{op:'update',id:'cabinet',changes:{width:1100}}]})})`);
await release();await until("!busyActions.has('refresh')");
await ensure("!ready()&&geometry===null&&$('saveEntity').disabled",
 'Mixed state/preview revisions became editable');
await ensure("$('status').textContent.includes('between state and preview')",
 'Missing revision mismatch explanation');raceChecks.push('state_preview_revision');
await choose(pair.a);
// Delay only the preview, then change models.
await hold('/api/preview',pair.a);await run("$('refresh').click()");
await until('race.held.length===1');await choose(pair.b);await release();
await until("!busyActions.has('refresh')");
await ensure(`loadedModelId===${JSON.stringify(pair.b)}&&geometry.revision===1`,
 'Late A preview overwrote B');raceChecks.push('stale_preview');
// Selecting a different entity invalidates a late cabinet schedule.
await choose(pair.a);await hold('/api/schedule',pair.a);
await run("void select('cabinet')");await until('race.held.length===1');
await run("select('south')");await release();
await new Promise(r=>setTimeout(r,80));
await ensure("selected==='south'&&$('schedule').children.length===0",
 'Late cabinet schedule overwrote current entity');raceChecks.push('stale_schedule');
// Retained candidates are scoped to their model and review revision.
const imported=await run(`api('import',{model_id:model(),path:'wall.xyz',units:'mm',
 tolerance_mm:1},true)`);
await run(`$('importId').value=${JSON.stringify(imported.import_id)}`);
await hold('/api/candidates',pair.a);await run("$('loadCandidates').click()");
await until('race.held.length===1');await choose(pair.b);await release();
await until("!busyActions.has('loadCandidates')");
await ensure(`candidate===null&&candidateScope===null&&importId===''&&
 $('candidateList').children.length===0`,'A candidates leaked into B');
raceChecks.push('stale_candidates');
// Check/export results also cannot publish against another selected model.
await choose(pair.a);await hold('/api/check',pair.a);await hold('/api/export',pair.a);
await run("$('format').value='json';$('check').click();$('export').click()");
await until('race.held.length===2');await choose(pair.b);await release();await release();
await until("!busyActions.has('check')&&!busyActions.has('export')");
await ensure(`!$('results').textContent.includes('directory')&&
 !$('results').textContent.includes('regulatory')`,'A check/export result leaked into B');
raceChecks.push('stale_check_export');
// A delayed refresh index cannot restore an earlier explicit selection.
await hold('/api/status',null);await run("$('refresh').click()");
await until('race.held.length===1');await choose(pair.a);await release();
await until("!busyActions.has('refresh')");
await ensure(`loadedModelId===${JSON.stringify(pair.a)}&&state.revision===2`,
 'Late model index changed selection');raceChecks.push('stale_index');
const unchanged=await run(`(async()=>{const r=await race.real(
 '/api/state?model_id='+${JSON.stringify(pair.b)},{headers:{Authorization:'Bearer '+token}});
 return await r.json()})()`);
if(unchanged.revision!==1||unchanged.entities.cabinet.width!==900)
 throw Error('Unintended model B mutation');
await run('window.fetch=race.real');
await run(`models(${JSON.stringify(original)})`);await run("select('cabinet')");
"""
    script = script.replace("__RACE__", race_script if race_mode else "")
    try:
        for _ in range(100):
            port_file = profile / "DevToolsActivePort"
            if port_file.is_file():
                break
            if process.poll() is not None:
                pytest.fail("Owned headless Chrome exited before readiness")
            time.sleep(0.05)
        else:
            pytest.fail("Owned headless Chrome did not become ready")
        port = port_file.read_text().splitlines()[0]
        result = subprocess.run(
            [
                node,
                "--input-type=module",
                "-e",
                script,
                port,
                instance.url,
                str(screenshot),
            ],
            capture_output=True,
            text=True,
            timeout=40,
        )
        assert result.returncode == 0, result.stderr[-3000:]
        evidence = json.loads(result.stdout)
        assert evidence["ok"] and evidence["revision"] == 5
        assert evidence["meshes"] > 20 and evidence["errors"] == []
        assert instance.service.state(evidence["modelId"])["revision"] == 5
        assert len(evidence["raceChecks"]) == (8 if race_mode else 0)
        print("Owned browser evidence:", json.dumps(evidence), "image:", screenshot)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
