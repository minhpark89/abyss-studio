"""Exercise the native HTTP handler and real buttons with an isolated copy of the registry."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,os,shutil,socket,subprocess,time
from urllib.request import build_opener,ProxyHandler
from playwright.sync_api import sync_playwright

factory=Path(__file__).resolve().parents[2]
studio=factory.parent/"abyss-studio"
original=factory/"REPO_REGISTRY.json"
def verify():
    with TemporaryDirectory() as tmp,socket.socket() as allocate:
        file=Path(tmp)/original.name;shutil.copyfile(original,file)
        allocate.bind(("127.0.0.1",0));port=allocate.getsockname()[1];allocate.close()
        base=f"http://127.0.0.1:{port}"
        server=subprocess.Popen(["node","native-server.js"],cwd=studio,env={**os.environ,"NATIVE_STUDIO_PORT":str(port),"ABYSS_REPO_REGISTRY":str(file)},stdout=subprocess.DEVNULL)
        try:
            net=build_opener(ProxyHandler({}))
            for _ in range(60):
                try:
                    with net.open(base+"/api/registry") as res:initial=json.load(res)
                    break
                except OSError:time.sleep(.1)
            else:raise RuntimeError("Test service did not start")
            def persisted(name):
                book=json.loads(file.read_text("utf8"))
                return next(r["status"] for key in ("vendors","studio_catalog","runtime_repos") for r in book[key] if r["name"]==name)
            with sync_playwright() as p:
                b=p.chromium.launch(channel="msedge",headless=True,args=["--no-proxy-server"])
                pg=b.new_page(viewport={"width":1390,"height":900})
                errors=[];pg.on("pageerror",lambda e:errors.append(str(e)))
                pg.goto(base+"/dashboard.html",wait_until="domcontentloaded")
                pg.locator("#repo-rows tr").first.wait_for()
                slots=pg.locator("#pipe-slots article")
                assert slots.count()==6
                sound=slots.filter(has_text="Audio Engine").inner_text()
                assert all(repo in sound for repo in ("spotify/pedalboard","slhck/ffmpeg-normalize","MTG/freesound-python"))
                chosen=next(r for r in initial["repos"] if r["status"]=="TESTING" and any(x["stage"]==r["stage"] and x["status"]=="ACTIVE" for x in initial["repos"]))
                prior=next(r for r in initial["repos"] if r["stage"]==chosen["stage"] and r["status"]=="ACTIVE")
                for label,status in [("Set ACTIVE","ACTIVE"),("Set TESTING","TESTING"),("Archive","ARCHIVED")]:
                    with pg.expect_response(lambda r:r.url.endswith("/api/registry/update")) as done:
                        pg.get_by_role("button",name=label+" · "+chosen["name"],exact=True).click()
                    assert done.value.status==200
                    pg.wait_for_function("([n,s])=>document.querySelector('#pipe-message').textContent.includes(n+' → '+s)",arg=[chosen['name'],status])
                    assert persisted(chosen["name"])==status and persisted(prior["name"])=="ARCHIVED"
                pg.reload(wait_until="domcontentloaded")
                pg.locator("#repo-filters").get_by_role("button",name="ARCHIVED",exact=True).click()
                assert chosen["name"] in pg.locator("#repo-rows").inner_text()
                sb=pg.locator("#trace-rows tr").filter(has_text="SB05")
                sb.get_by_role("button",name="Xem chi tiết lệnh").click()
                assert pg.locator("#trace-dialog").is_visible()
                pg.keyboard.press("Escape")
                sb.get_by_role("link",name="Mở phòng xem").click()
                assert pg.locator("#episode-review").is_visible()
                pg.locator("#return-to-board").click()
                pg.locator("#panel-dashboard").wait_for()
                pg.set_viewport_size({"width":390,"height":844})
                assert pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
                assert not errors,errors
                b.close()
        finally:server.terminate();server.wait(10)
    print("Buttons persisted to disk, previous active archived, modal, review return, mobile and reload passed.")
if __name__=="__main__":verify()

