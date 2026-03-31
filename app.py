import streamlit as st
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET
import json

st.set_page_config(page_title="건축물대장 조회 시스템", page_icon="🏢",
                   layout="wide", initial_sidebar_state="collapsed")

KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"
VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

st.markdown("""
<style>
#MainMenu,footer,header,.stDeployButton{display:none!important;}
.block-container{padding:0!important;margin:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none;}
[data-testid="stToolbar"]{display:none;}
.stApp{background:#07090f!important;}
iframe{border:none!important;}
</style>""", unsafe_allow_html=True)

# ── Python API 함수 ──────────────────────────────
def fetch_building(sigungu, bjdong, bun, ji):
    def mk_url(ep):
        qs = "&".join([
            f"sigunguCd={sigungu}", f"bjdongCd={bjdong}", "platGbCd=0",
            f"bun={str(bun).zfill(4)}", f"ji={str(ji).zfill(4) if ji else '0000'}",
            "startDate=", "endDate=", "numOfRows=10", "pageNo=1",
            f"serviceKey={BUILDING_API_KEY}",
        ])
        return f"http://apis.data.go.kr/1613000/BldRgstService_v2/{ep}?{qs}"
    def parse(txt):
        try:
            root = ET.fromstring(txt)
            code = root.find(".//resultCode")
            if code is not None and code.text != "00":
                msg = root.find(".//resultMsg")
                return {"error": msg.text if msg else "API 오류"}
            return {"items": [{c.tag:(c.text or "") for c in i} for i in root.findall(".//item")]}
        except Exception as e:
            return {"error": str(e)}
    try:
        r1 = requests.get(mk_url("getBrBasisOulnInfo"), timeout=10)
        r2 = requests.get(mk_url("getBrTitleInfo"),     timeout=10)
        return {"basis": parse(r1.text), "title": parse(r2.text)}
    except Exception as e:
        return {"error": str(e)}

def coord2addr(lat, lng):
    try:
        r = requests.get("https://dapi.kakao.com/v2/local/geo/coord2address.json",
                         headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
                         params={"x": lng, "y": lat}, timeout=5)
        docs = r.json().get("documents", [])
        return docs[0] if docs else {}
    except: return {}

def addr_search(query):
    try:
        r = requests.get("https://dapi.kakao.com/v2/local/search/address.json",
                         headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
                         params={"query": query, "size": 5}, timeout=5)
        return r.json().get("documents", [])
    except: return []

# ── iframe ↔ Python 통신 ──────────────────────────
def json_resp(data):
    st.markdown(
        f'<pre id="r" style="display:none">{json.dumps(data, ensure_ascii=False)}</pre>',
        unsafe_allow_html=True)
    st.stop()

qp = st.query_params
action = qp.get("action", "")

if action == "click":
    lat, lng = float(qp.get("lat", 0)), float(qp.get("lng", 0))
    doc  = coord2addr(lat, lng)
    land = doc.get("address") or {}
    road = doc.get("road_address") or {}
    addr = road.get("address_name") or land.get("address_name") or ""
    bc   = land.get("b_code", "")
    res  = fetch_building(bc[:5], bc[5:10] if len(bc) >= 10 else "",
                          land.get("main_address_no","0"), land.get("sub_address_no","0"))
    res["addr"] = addr
    json_resp(res)

elif action == "search":
    json_resp(addr_search(qp.get("q", "")))

elif action == "manual":
    res = fetch_building(qp.get("sigungu",""), qp.get("bjdong",""),
                         qp.get("bun","0"), qp.get("ji","0"))
    res["addr"] = qp.get("addr","")
    json_resp(res)

# ── 메인 UI ──────────────────────────────────────
# ★ 핵심: 카카오 공식 문서 방식 그대로 // 상대 프로토콜 사용
#   HTTPS 환경 → 자동으로 HTTPS로 로드 → Mixed Content 없음
#   components.html()은 srcdoc 방식 → 별도 origin → http/https 구분 없이 로드
html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
:root{{
  --bg:#07090f;--bg2:#0d1117;--bg3:#161b22;
  --bd:rgba(255,255,255,.07);--bd2:rgba(56,189,248,.22);
  --t:#c9d1d9;--t2:#8b949e;--t3:#484f58;
  --ac:#38bdf8;--a2:#0ea5e9;--gr:#10b981;--am:#f59e0b;
  --pw:340px;--hh:50px;
}}
html,body{{height:100%;overflow:hidden;background:var(--bg);color:var(--t);
  font-family:'Noto Sans KR',-apple-system,sans-serif;}}
#hdr{{height:var(--hh);background:var(--bg2);border-bottom:1px solid var(--bd);
  display:flex;align-items:center;padding:0 16px;gap:10px;}}
.hl{{width:30px;height:30px;background:linear-gradient(135deg,var(--ac),var(--gr));
  border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;}}
.ht{{font-size:.87rem;font-weight:700;color:#f0f6ff;}}
.hs{{font-size:.58rem;color:var(--t3);font-family:'JetBrains Mono',monospace;}}
.hb{{margin-left:auto;display:flex;align-items:center;gap:5px;
  background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
  color:var(--gr);padding:3px 10px;border-radius:20px;font-size:.63rem;font-weight:600;}}
.hd{{width:6px;height:6px;border-radius:50%;background:var(--gr);animation:blink 2s infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.3;}}}}
#main{{display:flex;height:calc(100vh - var(--hh));overflow:hidden;}}
#panel{{width:var(--pw);min-width:var(--pw);background:var(--bg2);
  border-right:1px solid var(--bd);display:flex;flex-direction:column;overflow:hidden;}}
#ps{{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:10px;}}
#ps::-webkit-scrollbar{{width:3px;}}
#ps::-webkit-scrollbar-thumb{{background:var(--bd2);border-radius:2px;}}
.slbl{{font-size:.59rem;font-weight:700;letter-spacing:.1em;color:var(--ac);
  text-transform:uppercase;margin-bottom:7px;display:flex;align-items:center;gap:5px;}}
.slbl::before{{content:'';width:3px;height:10px;background:var(--ac);border-radius:2px;}}
.sw{{background:var(--bg3);border:1px solid var(--bd);border-radius:10px;padding:11px;}}
.sr{{display:flex;gap:5px;}}
#si{{flex:1;background:var(--bg);border:1px solid var(--bd);border-radius:7px;
  color:var(--t);font-family:inherit;font-size:.8rem;padding:8px 10px;outline:none;
  transition:border-color .2s,box-shadow .2s;}}
#si::placeholder{{color:var(--t3);}}
#si:focus{{border-color:var(--ac);box-shadow:0 0 0 3px rgba(56,189,248,.1);}}
.btn{{background:linear-gradient(135deg,var(--a2),var(--gr));color:#fff;border:none;
  border-radius:7px;font-family:inherit;font-size:.72rem;font-weight:600;padding:8px 11px;
  cursor:pointer;transition:all .2s;white-space:nowrap;}}
.btn:hover{{opacity:.85;transform:translateY(-1px);}}
.btng{{background:var(--bg);border:1px solid var(--bd);color:var(--t2);}}
.btng:hover{{border-color:var(--bd2);color:var(--t);opacity:1;}}
#sres{{margin-top:6px;display:none;flex-direction:column;gap:3px;}}
.ri{{background:var(--bg);border:1px solid var(--bd);border-radius:6px;
  padding:7px 10px;cursor:pointer;font-size:.74rem;color:var(--t2);transition:all .15s;}}
.ri:hover{{border-color:var(--bd2);color:var(--t);background:rgba(56,189,248,.05);}}
.rm{{font-weight:500;color:var(--t);}}
.rs{{font-size:.66rem;color:var(--t3);margin-top:1px;}}
.gbox{{background:var(--bg3);border:1px dashed rgba(56,189,248,.15);
  border-radius:10px;padding:22px 13px;text-align:center;}}
.gi{{font-size:1.8rem;margin-bottom:7px;}}
.gt{{font-size:.8rem;font-weight:600;color:var(--t);margin-bottom:5px;}}
.gd{{font-size:.71rem;color:var(--t3);line-height:1.7;}}
.gd strong{{color:var(--ac);font-weight:500;}}
.leg{{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px;padding-top:11px;border-top:1px solid var(--bd);}}
.li{{display:flex;align-items:center;gap:4px;font-size:.63rem;color:var(--t3);}}
.ld{{width:8px;height:8px;border-radius:2px;}}
.lbox{{background:var(--bg3);border:1px solid var(--bd);border-radius:10px;
  padding:22px;display:flex;flex-direction:column;align-items:center;gap:10px;}}
.spin{{width:24px;height:24px;border:3px solid rgba(56,189,248,.15);
  border-top-color:var(--ac);border-radius:50%;animation:spin .7s linear infinite;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}
.ltx{{font-size:.74rem;color:var(--t2);}}
.bc{{background:var(--bg3);border:1px solid var(--bd);border-radius:10px;padding:12px;transition:border-color .2s;}}
.bc:hover{{border-color:var(--bd2);}}
.bh{{display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;}}
.bic{{width:32px;height:32px;background:linear-gradient(135deg,rgba(56,189,248,.15),rgba(16,185,129,.15));
  border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px;
  flex-shrink:0;border:1px solid rgba(56,189,248,.15);}}
.bn{{font-size:.84rem;font-weight:700;color:#f0f6ff;}}
.ba{{font-size:.68rem;color:var(--t3);margin-top:1px;line-height:1.4;}}
.tags{{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:9px;}}
.tag{{font-size:.61rem;font-weight:600;padding:2px 6px;border-radius:4px;}}
.tb{{background:rgba(56,189,248,.12);color:var(--ac);border:1px solid rgba(56,189,248,.2);}}
.tg{{background:rgba(16,185,129,.12);color:var(--gr);border:1px solid rgba(16,185,129,.2);}}
.ta{{background:rgba(245,158,11,.12);color:var(--am);border:1px solid rgba(245,158,11,.2);}}
.ig{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
.ic{{background:var(--bg);border:1px solid rgba(255,255,255,.04);border-radius:6px;padding:7px 8px;}}
.ic.full{{grid-column:1/-1;}}
.cl{{font-size:.57rem;font-weight:600;color:var(--t3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px;}}
.cv{{font-size:.76rem;font-weight:500;color:var(--t);font-family:'JetBrains Mono',monospace;}}
.cv.hi{{color:var(--ac);}}
.err{{background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);
  border-radius:10px;padding:12px;font-size:.74rem;color:#fca5a5;line-height:1.7;}}
.mw{{background:var(--bg3);border:1px solid var(--bd);border-radius:10px;overflow:hidden;}}
.mt{{width:100%;background:none;border:none;color:var(--t2);font-family:inherit;
  font-size:.71rem;padding:8px 12px;cursor:pointer;text-align:left;display:flex;align-items:center;gap:5px;}}
.mt:hover{{color:var(--t);}}
.mb{{display:none;padding:0 12px 12px;flex-direction:column;gap:7px;}}
.mb.open{{display:flex;}}
.fl{{font-size:.61rem;color:var(--t3);margin-bottom:2px;font-weight:600;}}
.fr{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
input.mn{{width:100%;background:var(--bg);border:1px solid var(--bd);border-radius:5px;
  color:var(--t);font-family:'JetBrains Mono',monospace;font-size:.74rem;padding:6px 8px;outline:none;}}
input.mn:focus{{border-color:var(--ac);}}
input.mn::placeholder{{color:var(--t3);}}
#ma{{flex:1;position:relative;overflow:hidden;}}
#map{{width:100%;height:100%;}}
#lc{{position:absolute;top:12px;left:12px;z-index:400;display:flex;flex-direction:column;gap:4px;}}
.lb{{background:rgba(7,9,15,.88);border:1px solid rgba(56,189,248,.18);color:var(--t2);
  border-radius:7px;font-family:inherit;font-size:.68rem;font-weight:600;padding:7px 10px;
  cursor:pointer;transition:all .2s;backdrop-filter:blur(12px);display:flex;align-items:center;gap:5px;}}
.lb:hover{{background:rgba(56,189,248,.1);border-color:rgba(56,189,248,.4);color:var(--t);}}
.lb.active{{background:rgba(56,189,248,.15);border-color:var(--ac);color:var(--ac);}}
#zc{{position:absolute;top:12px;right:12px;z-index:400;display:flex;flex-direction:column;gap:4px;}}
.lbsq{{width:32px;height:32px;padding:0;justify-content:center;font-size:.9rem;}}
#cb{{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);z-index:400;
  background:rgba(7,9,15,.88);border:1px solid var(--bd);border-radius:20px;
  padding:4px 12px;font-family:'JetBrains Mono',monospace;font-size:.61rem;
  color:var(--t3);backdrop-filter:blur(12px);pointer-events:none;white-space:nowrap;}}
#ch{{position:absolute;bottom:44px;left:50%;transform:translateX(-50%);z-index:400;
  background:rgba(7,9,15,.9);border:1px solid var(--bd2);border-radius:20px;
  padding:5px 13px;font-size:.66rem;color:var(--ac);
  backdrop-filter:blur(12px);pointer-events:none;animation:fiu .5s ease 1s both;}}
@keyframes fiu{{from{{opacity:0;transform:translate(-50%,8px);}}to{{opacity:1;transform:translate(-50%,0);}}}}
@keyframes cp{{0%{{transform:translate(-50%,-50%) scale(.5);opacity:1;}}100%{{transform:translate(-50%,-50%) scale(3);opacity:0;}}}}
.cp{{position:absolute;width:26px;height:26px;border:2px solid var(--ac);border-radius:50%;
  pointer-events:none;animation:cp .6s ease-out forwards;z-index:500;}}
</style>
</head>
<body>
<div id="hdr">
  <div class="hl">🏢</div>
  <div><div class="ht">건축물대장 조회 시스템</div>
    <div class="hs">KAKAO MAPS · VWORLD · BUILDING REGISTRY</div></div>
  <div class="hb"><div class="hd"></div> LIVE</div>
</div>
<div id="main">
  <div id="panel"><div id="ps">
    <div class="sw">
      <div class="slbl">주소 검색</div>
      <div class="sr">
        <input id="si" type="text" placeholder="예: 강남구 테헤란로 152" autocomplete="off">
        <button class="btn" onclick="doSearch()">검색</button>
        <button class="btn btng" onclick="resetAll()">↺</button>
      </div>
      <div id="sres"></div>
    </div>
    <div id="ct">
      <div class="gbox"><div class="gi">🗺️</div>
        <div class="gt">지도를 클릭하세요</div>
        <div class="gd">원하는 위치를 클릭하면<br><strong>건축물대장 정보</strong>가 즉시 표시됩니다.<br><br>주소 검색 후 결과 클릭도 가능합니다.</div>
        <div class="leg">
          <div class="li"><div class="ld" style="background:var(--ac)"></div>일반지도</div>
          <div class="li"><div class="ld" style="background:var(--am)"></div>위성지도</div>
          <div class="li"><div class="ld" style="background:var(--gr)"></div>지적도</div>
        </div>
      </div>
    </div>
    <div class="mw">
      <button class="mt" onclick="toggleM()">⚙️ 수동 PNU 코드 입력 <span id="marr">▾</span></button>
      <div class="mb" id="mb">
        <div><div class="fl">시군구코드 (5자리)</div><input class="mn" id="m1" placeholder="예: 11680" maxlength="5"></div>
        <div><div class="fl">법정동코드 (5자리)</div><input class="mn" id="m2" placeholder="예: 10300" maxlength="5"></div>
        <div class="fr">
          <div><div class="fl">본번</div><input class="mn" id="m3" placeholder="737"></div>
          <div><div class="fl">부번</div><input class="mn" id="m4" placeholder="0"></div>
        </div>
        <button class="btn" style="margin-top:3px" onclick="manualQ()">🏠 건축물대장 조회</button>
      </div>
    </div>
  </div></div>

  <div id="ma">
    <div id="map"></div>
    <div id="lc">
      <button class="lb active" id="b1" onclick="setT('road')">🗺 일반</button>
      <button class="lb" id="b2" onclick="setT('sky')">🛰 위성</button>
      <button class="lb" id="b3" onclick="toggleJ()">📐 지적도</button>
    </div>
    <div id="zc">
      <button class="lb lbsq" onclick="map&&map.setLevel(map.getLevel()-1)">＋</button>
      <button class="lb lbsq" onclick="map&&map.setLevel(map.getLevel()+1)">－</button>
    </div>
    <div id="cb">지도를 클릭하면 건축물대장이 조회됩니다</div>
    <div id="ch">🖱 지도 클릭 → 건축물대장 즉시 조회</div>
  </div>
</div>

<script>
// Streamlit 앱 URL (같은 탭의 parent)
const BASE = window.parent.location.href.split('?')[0];

async function callPy(params) {{
  const res  = await fetch(BASE + '?' + new URLSearchParams(params));
  const text = await res.text();
  const m    = text.match(/<pre id="r"[^>]*>([\s\S]*?)<\/pre>/);
  if (!m) throw new Error('응답 파싱 실패');
  return JSON.parse(m[1]);
}}

// 카카오맵 초기화
var map, geocoder, marker, circle, jijeokOn = false;

kakao.maps.load(function() {{
  map = new kakao.maps.Map(document.getElementById('map'), {{
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level : 4,
  }});
  geocoder = new kakao.maps.services.Geocoder();

  // VWorld 지적도
  kakao.maps.Tileset.add('VW_LP', new kakao.maps.Tileset({{
    width:256, height:256, minZoom:1, maxZoom:21,
    getTileUrl: function(x,y,z) {{
      return 'https://api.vworld.kr/req/wmts/1.0.0/{VWORLD_KEY}/lp/'+z+'/'+y+'/'+x+'.png';
    }},
  }}));

  kakao.maps.event.addListener(map, 'click', async function(e) {{
    var lat = e.latLng.getLat(), lng = e.latLng.getLng();
    document.getElementById('cb').textContent = 'LAT '+lat.toFixed(6)+'  ·  LNG '+lng.toFixed(6);
    document.getElementById('ch').style.display = 'none';
    placeMark(lat, lng);
    map.panTo(e.latLng);
    showL('클릭 위치 조회 중...');
    try {{
      var d = await callPy({{action:'click', lat:lat, lng:lng}});
      render(d.basis&&d.basis.items||[], d.title&&d.title.items||[], d.addr||'');
    }} catch(e) {{ showE('조회 오류: '+e.message); }}
  }});

  kakao.maps.event.addListener(map, 'mousemove', function(e) {{
    if (!marker)
      document.getElementById('cb').textContent =
        'LAT '+e.latLng.getLat().toFixed(6)+'  ·  LNG '+e.latLng.getLng().toFixed(6);
  }});
}});

function setT(t) {{
  if (!map) return;
  map.setMapTypeId(t==='road' ? kakao.maps.MapTypeId.ROADMAP : kakao.maps.MapTypeId.SKYVIEW);
  document.getElementById('b1').classList.toggle('active', t==='road');
  document.getElementById('b2').classList.toggle('active', t==='sky');
}}

function toggleJ() {{
  if (!map) return;
  jijeokOn = !jijeokOn;
  document.getElementById('b3').classList.toggle('active', jijeokOn);
  if (jijeokOn) map.addOverlayMapTypeId(kakao.maps.MapTypeId['VW_LP']);
  else          map.removeOverlayMapTypeId(kakao.maps.MapTypeId['VW_LP']);
}}

function placeMark(lat, lng) {{
  var pos = new kakao.maps.LatLng(lat, lng);
  if (marker) marker.setMap(null);
  if (circle) circle.setMap(null);
  marker = new kakao.maps.Marker({{position:pos, map:map}});
  circle = new kakao.maps.Circle({{
    center:pos, radius:40,
    strokeWeight:2, strokeColor:'#38bdf8', strokeOpacity:.9,
    fillColor:'#38bdf8', fillOpacity:.12,
  }});
  circle.setMap(map);
  var pt = map.getProjection().pointFromCoords(pos);
  var p  = document.createElement('div');
  p.className='cp'; p.style.left=pt.x+'px'; p.style.top=pt.y+'px';
  document.getElementById('ma').appendChild(p);
  setTimeout(function(){{p.remove();}}, 700);
}}

document.getElementById('si').addEventListener('keydown', function(e) {{
  if(e.key==='Enter') doSearch();
}});

async function doSearch() {{
  var q = document.getElementById('si').value.trim();
  if (!q) return;
  try {{ showR(await callPy({{action:'search', q:q}})); }}
  catch(e) {{ showE('검색 오류: '+e.message); }}
}}

function showR(docs) {{
  var b = document.getElementById('sres');
  if (!Array.isArray(docs)||!docs.length) {{
    b.innerHTML='<div class="ri" style="cursor:default;color:var(--t3)">검색 결과 없음</div>';
    b.style.display='flex'; return;
  }}
  b.innerHTML = docs.map(function(d,i) {{
    var road=d.road_address, main=road?road.address_name:d.address_name, sub=road?d.address_name:'';
    return '<div class="ri" onclick="pick('+i+')"><div class="rm">📍 '+main+'</div>'+(sub?'<div class="rs">'+sub+'</div>':'')+'</div>';
  }}).join('');
  b.style.display='flex'; b._d=docs;
}}

async function pick(i) {{
  var doc=document.getElementById('sres')._d[i];
  var lat=parseFloat(doc.y), lng=parseFloat(doc.x);
  document.getElementById('sres').style.display='none';
  document.getElementById('ch').style.display='none';
  if(map){{ map.setCenter(new kakao.maps.LatLng(lat,lng)); map.setLevel(3); }}
  placeMark(lat,lng);
  showL('건축물대장 조회 중...');
  try {{
    var d=await callPy({{action:'click',lat:lat,lng:lng}});
    render(d.basis&&d.basis.items||[], d.title&&d.title.items||[], d.addr||doc.address_name||'');
  }} catch(e) {{ showE('조회 오류: '+e.message); }}
}}

var mOpen=false;
function toggleM(){{
  mOpen=!mOpen;
  document.getElementById('mb').classList.toggle('open',mOpen);
  document.getElementById('marr').textContent=mOpen?'▴':'▾';
}}

async function manualQ(){{
  var sg=document.getElementById('m1').value.trim(), bd=document.getElementById('m2').value.trim();
  var bn=document.getElementById('m3').value.trim(), ji=document.getElementById('m4').value.trim();
  if(!sg||!bd){{alert('시군구코드와 법정동코드를 입력해 주세요.');return;}}
  showL('건축물대장 조회 중...');
  try{{
    var d=await callPy({{action:'manual',sigungu:sg,bjdong:bd,bun:bn||'0',ji:ji||'0'}});
    render(d.basis&&d.basis.items||[], d.title&&d.title.items||[], d.addr||'');
  }}catch(e){{showE('조회 오류: '+e.message);}}
}}

function SC(h){{document.getElementById('ct').innerHTML=h;}}
function showL(msg){{SC('<div class="lbox"><div class="spin"></div><div class="ltx">'+msg+'</div></div>');}}
function showE(msg){{SC('<div class="err">⚠️ '+msg+'</div>');}}
function fa(v){{var n=parseFloat(v);return isNaN(n)?(v||'-'):n.toLocaleString('ko',{{minimumFractionDigits:2,maximumFractionDigits:2}})+' ㎡';}}
function fd(v){{if(!v||v.length<8)return v||'-';return v.slice(0,4)+'.'+v.slice(4,6)+'.'+v.slice(6,8);}}

function render(basis,title,addr){{
  if(!basis.length&&!title.length){{
    SC('<div class="gbox"><div class="gi">⚠️</div><div class="gt">건축물 정보 없음</div><div class="gd">해당 위치 정보를 찾을 수 없습니다.<br>다른 위치를 클릭해 보세요.</div></div>');
    return;
  }}
  var h='';
  basis.forEach(function(x){{
    h+='<div class="bc"><div class="bh"><div class="bic">🏢</div>'
      +'<div><div class="bn">'+(x.bldNm||'건물명 미등록')+'</div><div class="ba">'+addr+'</div></div></div>'
      +'<div class="tags">'
      +'<span class="tag tb">'+(x.mainPurpsCdNm||x.mainPurpsCd||'-')+'</span>'
      +'<span class="tag tg">'+(x.strctCdNm||x.strctCd||'-')+'</span>'
      +'<span class="tag ta">지상 '+(x.grndFlCnt||'-')+'층 / 지하 '+(x.undgrndFlCnt||'0')+'층</span>'
      +'</div><div class="ig">'
      +'<div class="ic"><div class="cl">연면적</div><div class="cv hi">'+fa(x.totArea)+'</div></div>'
      +'<div class="ic"><div class="cl">건축면적</div><div class="cv">'+fa(x.archArea)+'</div></div>'
      +'<div class="ic"><div class="cl">대지면적</div><div class="cv">'+fa(x.platArea)+'</div></div>'
      +'<div class="ic"><div class="cl">건폐율/용적률</div><div class="cv">'+(x.bcRat||'-')+'% / '+(x.vlRat||'-')+'%</div></div>'
      +'<div class="ic"><div class="cl">허가일</div><div class="cv">'+fd(x.pmsDay)+'</div></div>'
      +'<div class="ic"><div class="cl">사용승인일</div><div class="cv">'+fd(x.useAprDay)+'</div></div>'
      +'</div></div>';
  }});
  if(title.length){{
    h+='<div class="slbl" style="margin-top:4px">표제부 상세</div>';
    title.slice(0,3).forEach(function(t){{
      h+='<div class="bc" style="border-color:rgba(16,185,129,.15)">'
        +'<div class="bh"><div class="bic" style="background:linear-gradient(135deg,rgba(16,185,129,.15),rgba(56,189,248,.1))">📦</div>'
        +'<div><div class="bn">'+(t.dongNm||'주동')+'</div><div class="ba">'+(t.mainPurpsCdNm||'-')+'</div></div></div>'
        +'<div class="ig">'
        +'<div class="ic"><div class="cl">세대수</div><div class="cv">'+(t.hhldCnt||'-')+' 세대</div></div>'
        +'<div class="ic"><div class="cl">가구수</div><div class="cv">'+(t.fmlyCnt||'-')+' 가구</div></div>'
        +'<div class="ic"><div class="cl">승강기(일반/비상)</div><div class="cv">'+(t.elvtCnt||'-')+' / '+(t.emgenElevCnt||'-')+'</div></div>'
        +'<div class="ic"><div class="cl">자주식 주차</div><div class="cv">'+(t.indrAutoUtcnt||'-')+' 대</div></div>'
        +(t.totArea?'<div class="ic full"><div class="cl">면적 합계</div><div class="cv hi">'+fa(t.totArea)+'</div></div>':'')
        +'</div></div>';
    }});
  }}
  SC(h);
}}

function resetAll(){{
  if(marker)marker.setMap(null); if(circle)circle.setMap(null); marker=null; circle=null;
  document.getElementById('si').value='';
  document.getElementById('sres').style.display='none';
  document.getElementById('cb').textContent='지도를 클릭하면 건축물대장이 조회됩니다';
  document.getElementById('ch').style.display='block';
  SC('<div class="gbox"><div class="gi">🗺️</div><div class="gt">지도를 클릭하세요</div>'
    +'<div class="gd">원하는 위치를 클릭하면<br><strong>건축물대장 정보</strong>가 즉시 표시됩니다.</div>'
    +'<div class="leg">'
    +'<div class="li"><div class="ld" style="background:var(--ac)"></div>일반지도</div>'
    +'<div class="li"><div class="ld" style="background:var(--am)"></div>위성지도</div>'
    +'<div class="li"><div class="ld" style="background:var(--gr)"></div>지적도</div>'
    +'</div></div>');
}}

document.addEventListener('keydown',function(e){{
  if(e.key==='Escape') document.getElementById('sres').style.display='none';
}});
</script>
</body>
</html>"""

components.html(html, height=820, scrolling=False)
