import sys
from playwright.sync_api import sync_playwright
base=sys.argv[1].rstrip('/')
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",args=["--no-sandbox"])
    def shot(url,path,w,h,mobile=False,full=False):
        ctx=b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mobile else 1,is_mobile=mobile,has_touch=mobile)
        pg=ctx.new_page(); pg.goto(url,wait_until="networkidle"); pg.wait_for_timeout(1200)
        sw=pg.evaluate("document.documentElement.scrollWidth"); print(path,"viewport",w,"scrollWidth",sw)
        pg.screenshot(path=path,full_page=full); ctx.close()
    shot(base+"/v2/","shots/v2-index.png",1440,1800)
    shot(base+"/v2/","shots/v2-index-mobile.png",390,1600,mobile=True)
    shot(base+"/v2/projects/eutelsat-financial-analysis/index.html","shots/v2-detail.png",1440,2200)
    shot(base+"/v2/projects/european-government-departments-and-agencies/index.html","/tmp/v2-detail-mobile.png",390,2400,mobile=True)
    b.close()
