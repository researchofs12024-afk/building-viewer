import streamlit as st
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET
import json

# ══════════════════════════════════════════════
# 페이지 설정
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="건축물대장 조회 시스템",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════
# API 키
# ══════════════════════════════════════════════
KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"
VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

# ══════════════════════════════════════════════
# Streamlit 기본 UI 숨기기
# ══════════════════════════════════════════════
st.markdown("""
<style>
#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 건축물대장 API 함수 (Python 서버에서 직접 호출 → CORS 없음)
# ══════════════════════════════════════════════

def build_url(endpoint: str, sigungu: str, bjdong: str, bun: str, ji: str) -> str:
    base = f"http://apis.data.go.kr/1613000/BldRgstService_v2/{endpoint}"
    qs = "&".join([
        f"sigunguCd={sigungu}",
        f"bjdongCd={bjdong}",
        "platGbCd=0",
        f"bun={bun.zfill(4)}",
        f"ji={ji.zfill(4) if ji else '0000'}",
        "startDate=", "endDate=",
        "numOfRows=10", "pageNo=1",
        f"serviceKey={BUILDING_API_KEY}",
    ])
    return f"{base}?{qs}"

def parse_xml(xml_text: str) -> dict:
    try:
        root = ET.fromstring(xml_text)
        code = root.find(".//resultCode")
        if code is not None and code.text != "00":
            msg = root.find(".//resultMsg")
            return {"error": msg.text if msg is not None else "API 오류"}
        items = root.findall(".//item")
        if not items:
            return {"items": []}
        return {"items": [{c.tag: (c.text or "") for c in item} for item in items]}
    except Exception as e:
        return {"error": f"파싱 오류: {e}"}

def fetch_building(sigungu: str, bjdong: str, bun: str, ji: str) -> dict:
    try:
        r1 = requests.get(build_url("getBrBasisOulnInfo", sigungu, bjdong, bun, ji), timeout=10)
        r2 = requests.get(build_url("getBrTitleInfo",     sigungu, bjdong, bun, ji), timeout=10)
        return {
            "basis": parse_xml(r1.text),
            "title": parse_xml(r2.text),
        }
    except Exception as e:
        return {"error": str(e)}

def kakao_coord2addr(lat: float, lng: float) -> dict:
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"x": lng, "y": lat, "input_coord": "WGS84"},
            timeout=5,
        )
        docs = r.json().get("documents", [])
        return docs[0] if docs else {}
    except:
        return {}

def kakao_addr_search(query: str) -> list:
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"query": query, "size": 5},
            timeout=5,
        )
        return r.json().get("documents", [])
    except:
        return []

# ══════════════════════════════════════════════
# 쿼리 파라미터로 지도↔Python 통신
# ══════════════════════════════════════════════
qp = st.query_params

action = qp.get("action", "")

# ── 지도 클릭 → 좌표 전달 → Python이 처리 후 JSON 반환 ──
if action == "click":
    lat = float(qp.get("lat", 0))
    lng = float(qp.get("lng", 0))

    # 역지오코딩
    addr_doc = kakao_coord2addr(lat, lng)
    land = addr_doc.get("address") or {}
    road = addr_doc.get("road_address") or {}

    display_addr = road.get("address_name") or land.get("address_name") or ""
    b_code   = land.get("b_code", "")
    sigungu  = b_code[:5]
    bjdong   = b_code[5:10] if len(b_code) >= 10 else ""
    bun      = land.get("main_address_no", "0")
    ji       = land.get("sub_address_no", "0")

    # 건축물대장 조회
    result = fetch_building(sigungu, bjdong, bun, ji)
    result["addr"] = display_addr
    result["lat"]  = lat
    result["lng"]  = lng

    # JSON을 HTML로 감싸서 반환 (iframe이 읽음)
    st.markdown(
        f'<pre id="api-result" style="display:none">{json.dumps(result, ensure_ascii=False)}</pre>',
        unsafe_allow_html=True
    )
    st.stop()

# ── 주소 검색 요청 ──
elif action == "search":
    query = qp.get("q", "")
    docs  = kakao_addr_search(query)
    st.markdown(
        f'<pre id="api-result" style="display:none">{json.dumps(docs, ensure_ascii=False)}</pre>',
        unsafe_allow_html=True
    )
    st.stop()

# ── 수동 PNU 조회 ──
elif action == "manual":
    sigungu = qp.get("sigungu", "")
    bjdong  = qp.get("bjdong", "")
    bun     = qp.get("bun", "0")
    ji      = qp.get("ji", "0")
    addr    = qp.get("addr", f"{sigungu}-{bjdong} ({bun}-{ji})")
    result  = fetch_building(sigungu, bjdong, bun, ji)
    result["addr"] = addr
    st.markdown(
        f'<pre id="api-result" style="display:none">{json.dumps(result, ensure_ascii=False)}</pre>',
        unsafe_allow_html=True
    )
    st.stop()

# ══════════════════════════════════════════════
# 메인 UI — 전체 화면을 하나의 HTML 컴포넌트로
# (지도 + 패널 통합, 새로고침 없음)
# ══════════════════════════════════════════════

# Streamlit 앱의 실제 URL을 JS에 전달
APP_ORIGIN = ""   # 같은 origin이므로 비워도 됨

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
:root{{
  --bg:#07090f;--bg2:#0d1117;--bg3:#161b22;
  --border:rgba(255,255,255,.07);--border2:rgba(56,189,248,.22);
  --text:#c9d1d9;--text2:#8b949e;--text3:#484f58;
  --accent:#38bdf8;--a2:#0ea5e9;--green:#10b981;--amber:#f59e0b;
  --pw:360px;--hh:52px;
}}
html,body{{height:100%;overflow:hidden;background:var(--bg);color:var(--text);
  font-family:'Noto Sans KR',-apple-system,sans-serif;}}

/* ── HEADER ── */
#hdr{{
  height:var(--hh);background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 18px;gap:10px;position:relative;z-index:200;
}}
.hlogo{{width:32px;height:32px;background:linear-gradient(135deg,var(--accent),var(--green));
  border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;}}
.htitle{{font-size:.9rem;font-weight:700;color:#f0f6ff;letter-spacing:-.02em;}}
.hsub{{font-size:.6rem;color:var(--text3);font-family:'JetBrains Mono',monospace;}}
.hbadge{{margin-left:auto;display:flex;align-items:center;gap:5px;
  background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
  color:var(--green);padding:3px 10px;border-radius:20px;font-size:.65rem;font-weight:600;}}
.hdot{{width:6px;height:6px;border-radius:50%;background:var(--green);animation:blink 2s infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.3;}}}}

/* ── LAYOUT ── */
#main{{display:flex;height:calc(100vh - var(--hh));overflow:hidden;}}

/* ── PANEL ── */
#panel{{
  width:var(--pw);min-width:var(--pw);background:var(--bg2);
  border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;
}}
#pscroll{{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;}}
#pscroll::-webkit-scrollbar{{width:3px;}}
#pscroll::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:2px;}}

.slabel{{font-size:.6rem;font-weight:700;letter-spacing:.12em;color:var(--accent);
  text-transform:uppercase;margin-bottom:8px;display:flex;align-items:center;gap:5px;}}
.slabel::before{{content:'';width:3px;height:11px;background:var(--accent);border-radius:2px;}}

.swrap{{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:12px;}}
.srow{{display:flex;gap:5px;}}
#sinput{{
  flex:1;background:var(--bg);border:1px solid var(--border);border-radius:7px;
  color:var(--text);font-family:inherit;font-size:.82rem;padding:8px 11px;outline:none;
  transition:border-color .2s,box-shadow .2s;
}}
#sinput::placeholder{{color:var(--text3);}}
#sinput:focus{{border-color:var(--accent);box-shadow:0 0 0 3px rgba(56,189,248,.1);}}

.btn{{background:linear-gradient(135deg,var(--a2),var(--green));color:#fff;border:none;
  border-radius:7px;font-family:inherit;font-size:.75rem;font-weight:600;padding:8px 12px;
  cursor:pointer;transition:all .2s;white-space:nowrap;}}
.btn:hover{{opacity:.85;transform:translateY(-1px);}}
.btn-g{{background:var(--bg);border:1px solid var(--border);color:var(--text2);}}
.btn-g:hover{{border-color:var(--border2);color:var(--text);opacity:1;}}

#sresults{{margin-top:7px;display:none;flex-direction:column;gap:3px;}}
.ritem{{background:var(--bg);border:1px solid var(--border);border-radius:6px;
  padding:8px 11px;cursor:pointer;font-size:.76rem;color:var(--text2);transition:all .15s;}}
.ritem:hover{{border-color:var(--border2);color:var(--text);background:rgba(56,189,248,.05);}}
.rm{{font-weight:500;color:var(--text);}}
.rs{{font-size:.68rem;color:var(--text3);margin-top:1px;}}

/* ── 가이드 ── */
.gbox{{background:var(--bg3);border:1px dashed rgba(56,189,248,.15);
  border-radius:10px;padding:24px 14px;text-align:center;}}
.gicon{{font-size:2rem;margin-bottom:8px;}}
.gtitle{{font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:5px;}}
.gdesc{{font-size:.73rem;color:var(--text3);line-height:1.7;}}
.gdesc strong{{color:var(--accent);font-weight:500;}}
.legend{{display:flex;flex-wrap:wrap;gap:9px;margin-top:12px;padding-top:12px;border-top:1px solid var(--border);}}
.li{{display:flex;align-items:center;gap:4px;font-size:.66rem;color:var(--text3);}}
.ld{{width:8px;height:8px;border-radius:2px;}}

/* ── 로딩 ── */
.lbox{{background:var(--bg3);border:1px solid var(--border);border-radius:10px;
  padding:24px;display:flex;flex-direction:column;align-items:center;gap:10px;}}
.spin{{width:26px;height:26px;border:3px solid rgba(56,189,248,.15);
  border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}
.ltxt{{font-size:.76rem;color:var(--text2);}}

/* ── 건물 카드 ── */
.bcard{{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:13px;transition:border-color .2s;}}
.bcard:hover{{border-color:var(--border2);}}
.bhdr{{display:flex;align-items:flex-start;gap:9px;margin-bottom:9px;}}
.bico{{width:34px;height:34px;background:linear-gradient(135deg,rgba(56,189,248,.15),rgba(16,185,129,.15));
  border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:15px;
  flex-shrink:0;border:1px solid rgba(56,189,248,.15);}}
.bnm{{font-size:.87rem;font-weight:700;color:#f0f6ff;}}
.badr{{font-size:.7rem;color:var(--text3);margin-top:1px;line-height:1.4;}}
.tags{{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:10px;}}
.tag{{font-size:.63rem;font-weight:600;padding:2px 7px;border-radius:4px;}}
.tb{{background:rgba(56,189,248,.12);color:var(--accent);border:1px solid rgba(56,189,248,.2);}}
.tg{{background:rgba(16,185,129,.12);color:var(--green);border:1px solid rgba(16,185,129,.2);}}
.ta{{background:rgba(245,158,11,.12);color:var(--amber);border:1px solid rgba(245,158,11,.2);}}
.igrid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
.icell{{background:var(--bg);border:1px solid rgba(255,255,255,.04);border-radius:6px;padding:8px 9px;}}
.icell.full{{grid-column:1/-1;}}
.clabel{{font-size:.58rem;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.07em;margin-bottom:2px;}}
.cval{{font-size:.78rem;font-weight:500;color:var(--text);font-family:'JetBrains Mono',monospace;}}
.cval.hi{{color:var(--accent);}}
.errbox{{background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);
  border-radius:10px;padding:13px;font-size:.76rem;color:#fca5a5;line-height:1.7;}}

/* ── 수동 입력 ── */
.mwrap{{background:var(--bg3);border:1px solid var(--border);border-radius:10px;overflow:hidden;}}
.mtoggle{{width:100%;background:none;border:none;color:var(--text2);font-family:inherit;
  font-size:.73rem;padding:9px 13px;cursor:pointer;text-align:left;display:flex;align-items:center;gap:5px;}}
.mtoggle:hover{{color:var(--text);}}
.mbody{{display:none;padding:0 13px 13px;flex-direction:column;gap:7px;}}
.mbody.open{{display:flex;}}
.flabel{{font-size:.63rem;color:var(--text3);margin-bottom:2px;font-weight:600;}}
.frow{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
input.mini{{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:5px;
  color:var(--text);font-family:'JetBrains Mono',monospace;font-size:.76rem;padding:6px 9px;outline:none;}}
input.mini:focus{{border-color:var(--accent);}}
input.mini::placeholder{{color:var(--text3);}}

/* ── MAP ── */
#map-area{{flex:1;position:relative;overflow:hidden;}}
#map{{width:100%;height:100%;}}
.mctrl{{position:absolute;z-index:50;display:flex;flex-direction:column;gap:4px;}}
.mctrl.tl{{top:12px;left:12px;}}
.mctrl.tr{{top:12px;right:12px;}}
.mbtn{{background:rgba(7,9,15,.88);border:1px solid rgba(56,189,248,.18);color:var(--text2);
  border-radius:7px;font-family:inherit;font-size:.7rem;font-weight:600;padding:7px 11px;
  cursor:pointer;transition:all .2s;backdrop-filter:blur(12px);display:flex;align-items:center;gap:5px;}}
.mbtn:hover{{background:rgba(56,189,248,.1);border-color:rgba(56,189,248,.4);color:var(--text);}}
.mbtn.active{{background:rgba(56,189,248,.15);border-color:var(--accent);color:var(--accent);}}
.mbtn-sq{{width:32px;height:32px;padding:0;justify-content:center;font-size:.95rem;}}
#cbar{{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);z-index:50;
  background:rgba(7,9,15,.88);border:1px solid var(--border);border-radius:20px;
  padding:4px 13px;font-family:'JetBrains Mono',monospace;font-size:.63rem;
  color:var(--text3);backdrop-filter:blur(12px);pointer-events:none;}}
#chint{{position:absolute;bottom:46px;left:50%;transform:translateX(-50%);z-index:50;
  background:rgba(7,9,15,.9);border:1px solid var(--border2);border-radius:20px;
  padding:5px 14px;font-size:.68rem;color:var(--accent);
  backdrop-filter:blur(12px);pointer-events:none;
  animation:fiu .5s ease 1s both;}}
@keyframes fiu{{from{{opacity:0;transform:translate(-50%,8px);}}to{{opacity:1;transform:translate(-50%,0);}}}}
@keyframes cpulse{{0%{{transform:translate(-50%,-50%) scale(.5);opacity:1;}}100%{{transform:translate(-50%,-50%) scale(3);opacity:0;}}}}
.cpulse{{position:absolute;width:28px;height:28px;border:2px solid var(--accent);border-radius:50%;
  pointer-events:none;animation:cpulse .6s ease-out forwards;z-index:60;}}

/* 반응형 */
@media(max-width:700px){{
  :root{{--pw:100vw;}}
  #main{{flex-direction:column-reverse;}}
  #panel{{width:100%;min-width:unset;height:55vh;border-right:none;border-top:1px solid var(--border);}}
  #map-area{{flex:1;}}
}}
</style>
</head>
<body>

<div id="hdr">
  <div class="hlogo">🏢</div>
  <div>
    <div class="htitle">건축물대장 조회 시스템</div>
    <div class="hsub">BUILDING REGISTRY · KAKAO MAPS · VWORLD</div>
  </div>
  <div class="hbadge"><div class="hdot"></div> LIVE</div>
</div>

<div id="main">
  <div id="panel">
    <div id="pscroll">

      <div class="swrap">
        <div class="slabel">주소 검색</div>
        <div class="srow">
          <input id="sinput" type="text" placeholder="예: 강남구 테헤란로 152" autocomplete="off">
          <button class="btn" ON-CLICK="doSearch()">검색</button>
          <button class="btn btn-g" ON-CLICK="resetAll()">↺</button>
        </div>
        <div id="sresults"></div>
      </div>

      <div id="content">
        <div class="gbox">
          <div class="gicon">🗺️</div>
          <div class="gtitle">지도를 클릭하세요</div>
          <div class="gdesc">
            원하는 위치를 클릭하면<br>
            <strong>건축물대장 정보</strong>가 즉시 표시됩니다.<br><br>
            주소 검색 후 결과 클릭도 가능합니다.
          </div>
          <div class="legend">
            <div class="li"><div class="ld" style="background:var(--accent)"></div>일반지도</div>
            <div class="li"><div class="ld" style="background:var(--amber)"></div>위성지도</div>
            <div class="li"><div class="ld" style="background:var(--green)"></div>지적도 오버레이</div>
          </div>
        </div>
      </div>

      <div class="mwrap">
        <button class="mtoggle" ON-CLICK="toggleManual()">⚙️ 수동 PNU 코드 입력 <span id="marrow">▾</span></button>
        <div class="mbody" id="mbody">
          <div><div class="flabel">시군구코드 (5자리)</div><input class="mini" id="m-sg" placeholder="예: 11680" maxlength="5"></div>
          <div><div class="flabel">법정동코드 (5자리)</div><input class="mini" id="m-bd" placeholder="예: 10300" maxlength="5"></div>
          <div class="frow">
            <div><div class="flabel">본번</div><input class="mini" id="m-bn" placeholder="737"></div>
            <div><div class="flabel">부번</div><input class="mini" id="m-ji" placeholder="0"></div>
          </div>
          <button class="btn" style="margin-top:3px" ON-CLICK="manualQuery()">🏠 건축물대장 조회</button>
        </div>
      </div>

    </div>
  </div>

  <div id="map-area">
    <div id="map"></div>
    <div class="mctrl tl">
      <button class="mbtn active" id="btn-road" ON-CLICK="setMapType('road')">🗺 일반</button>
      <button class="mbtn" id="btn-sky" ON-CLICK="setMapType('sky')">🛰 위성</button>
      <button class="mbtn" id="btn-jijeok" ON-CLICK="toggleJijeok()">📐 지적도</button>
    </div>
    <div class="mctrl tr">
      <button class="mbtn mbtn-sq" ON-CLICK="map.setLevel(map.getLevel()-1)">＋</button>
      <button class="mbtn mbtn-sq" ON-CLICK="map.setLevel(map.getLevel()+1)">－</button>
    </div>
    <div id="cbar">지도를 클릭하면 건축물대장이 조회됩니다</div>
    <div id="chint">🖱 지도 클릭 → 건축물대장 즉시 조회</div>
  </div>
</div>

<script>
/* ══════════════════════════════════════════════
   핵심 원리:
   iframe(이 HTML) 안에서 지도 클릭 발생
   → fetch()로 같은 Streamlit 앱의 ?action=click&lat=...&lng=... 호출
   → Python이 API 처리 후 JSON 반환
   → 결과를 이 패널에 직접 렌더링 (새로고침 없음!)
══════════════════════════════════════════════ */

const BASE_URL = window.location.href.split('?')[0];

// Streamlit 내부 API 호출 함수
async function callPython(params) {{
  const url = BASE_URL + '?' + new URLSearchParams(params).toString();
  const res  = await fetch(url);
  const html = await res.text();
  // Python이 반환한 HTML에서 JSON 추출
  const m = html.match(/<pre id="api-result"[^>]*>([\s\S]*?)<\/pre>/);
  if (!m) throw new Error('응답 파싱 실패');
  return JSON.parse(m[1]);
}}

/* ── 카카오맵 초기화 ── */
const map = new kakao.maps.Map(document.getElementById('map'), {{
  center: new kakao.maps.LatLng(37.5665, 126.9780),
  level : 4,
}});
const geocoder = new kakao.maps.services.Geocoder();
let marker = null, circle = null, jijeokOn = false;

function setMapType(t) {{
  map.setMapTypeId(t === 'road' ? kakao.maps.MapTypeId.ROADMAP : kakao.maps.MapTypeId.SKYVIEW);
  document.getElementById('btn-road').classList.toggle('active', t === 'road');
  document.getElementById('btn-sky').classList.toggle('active', t === 'sky');
}}

function toggleJijeok() {{
  jijeokOn = !jijeokOn;
  document.getElementById('btn-jijeok').classList.toggle('active', jijeokOn);
  if (jijeokOn) {{
    kakao.maps.Tileset.add('VW_LP', new kakao.maps.Tileset({{
      width:256, height:256, minZoom:1, maxZoom:21,
      getTileUrl:(x,y,z) => `https://api.vworld.kr/req/wmts/1.0.0/{VWORLD_KEY}/lp/${{z}}/${{y}}/${{x}}.png`,
    }}));
    map.addOverlayMapTypeId(kakao.maps.MapTypeId['VW_LP']);
  }} else {{
    map.removeOverlayMapTypeId(kakao.maps.MapTypeId['VW_LP']);
  }}
}}

function placeMarker(lat, lng) {{
  const pos = new kakao.maps.LatLng(lat, lng);
  if (marker) marker.setMap(null);
  if (circle) circle.setMap(null);
  marker = new kakao.maps.Marker({{ position:pos, map }});
  circle = new kakao.maps.Circle({{
    center:pos, radius:40,
    strokeWeight:2, strokeColor:'#38bdf8', strokeOpacity:.9,
    fillColor:'#38bdf8', fillOpacity:.12,
  }});
  circle.setMap(map);
  // 클릭 펄스 이펙트
  const pt = map.getProjection().pointFromCoords(pos);
  const p  = document.createElement('div');
  p.className='cpulse'; p.style.left=pt.x+'px'; p.style.top=pt.y+'px';
  document.getElementById('map-area').appendChild(p);
  setTimeout(()=>p.remove(), 700);
}}

/* ── 지도 클릭 ── */
kakao.maps.event.addListener(map, 'click', async function(e) {{
  const lat = e.latLng.getLat(), lng = e.latLng.getLng();
  document.getElementById('cbar').textContent = `LAT ${{lat.toFixed(6)}}  ·  LNG ${{lng.toFixed(6)}}`;
  document.getElementById('chint').style.display = 'none';
  placeMarker(lat, lng);
  map.panTo(e.latLng);
  showLoading('클릭 위치 조회 중...');

  try {{
    const data = await callPython({{ action:'click', lat, lng }});
    renderBuilding(data.basis?.items||[], data.title?.items||[], data.addr||'');
  }} catch(err) {{
    showError('조회 오류: ' + err.message);
  }}
}});

kakao.maps.event.addListener(map, 'mousemove', function(e) {{
  if (!marker)
    document.getElementById('cbar').textContent =
      `LAT ${{e.latLng.getLat().toFixed(6)}}  ·  LNG ${{e.latLng.getLng().toFixed(6)}}`;
}});

/* ── 주소 검색 ── */
document.getElementById('sinput').addEventListener('keydown', e => {{ if(e.key==='Enter') doSearch(); }});

async function doSearch() {{
  const q = document.getElementById('sinput').value.trim();
  if (!q) return;
  try {{
    const docs = await callPython({{ action:'search', q }});
    renderSearchResults(docs);
  }} catch(err) {{
    showError('검색 오류: ' + err.message);
  }}
}}

function renderSearchResults(docs) {{
  const box = document.getElementById('sresults');
  if (!Array.isArray(docs) || !docs.length) {{
    box.innerHTML='<div class="ritem" style="cursor:default;color:var(--text3)">검색 결과 없음</div>';
    box.style.display='flex'; return;
  }}
  box.innerHTML = docs.map((d,i) => {{
    const road = d.road_address;
    const main = road ? road.address_name : d.address_name;
    const sub  = road ? d.address_name : '';
    return `<div class="ritem" ON-CLICK="selectResult(${{i}})">
      <div class="rm">📍 ${{main}}</div>
      ${{sub ? `<div class="rs">${{sub}}</div>` : ''}}
    </div>`;
  }}).join('');
  box.style.display='flex';
  box._docs = docs;
}}

async function selectResult(i) {{
  const doc  = document.getElementById('sresults')._docs[i];
  const x = parseFloat(doc.x), y = parseFloat(doc.y);
  document.getElementById('sresults').style.display = 'none';
  document.getElementById('chint').style.display = 'none';
  map.setCenter(new kakao.maps.LatLng(y, x));
  map.setLevel(3);
  placeMarker(y, x);
  showLoading('건축물대장 조회 중...');

  try {{
    const data = await callPython({{ action:'click', lat:y, lng:x }});
    renderBuilding(data.basis?.items||[], data.title?.items||[], data.addr||doc.address_name||'');
  }} catch(err) {{
    showError('조회 오류: ' + err.message);
  }}
}}

/* ── 수동 입력 ── */
let manOpen = false;
function toggleManual() {{
  manOpen = !manOpen;
  document.getElementById('mbody').classList.toggle('open', manOpen);
  document.getElementById('marrow').textContent = manOpen ? '▴' : '▾';
}}

async function manualQuery() {{
  const sg = document.getElementById('m-sg').value.trim();
  const bd = document.getElementById('m-bd').value.trim();
  const bn = document.getElementById('m-bn').value.trim();
  const ji = document.getElementById('m-ji').value.trim();
  if (!sg || !bd) {{ alert('시군구코드와 법정동코드를 입력해 주세요.'); return; }}
  showLoading('건축물대장 조회 중...');
  try {{
    const data = await callPython({{ action:'manual', sigungu:sg, bjdong:bd, bun:bn||'0', ji:ji||'0' }});
    renderBuilding(data.basis?.items||[], data.title?.items||[], data.addr||'');
  }} catch(err) {{
    showError('조회 오류: ' + err.message);
  }}
}}

/* ── 렌더링 ── */
function setContent(html) {{ document.getElementById('content').innerHTML = html; }}

function showLoading(msg) {{
  setContent(`<div class="lbox"><div class="spin"></div><div class="ltxt">${{msg}}</div></div>`);
}}

function showError(msg) {{
  setContent(`<div class="errbox">⚠️ ${{msg}}</div>`);
}}

function fmt(v, unit='㎡') {{
  const n = parseFloat(v);
  return isNaN(n) ? (v||'-') : n.toLocaleString('ko',{{minimumFractionDigits:2,maximumFractionDigits:2}})+' '+unit;
}}
function fmtDate(v) {{
  if(!v||v.length<8) return v||'-';
  return `${{v.slice(0,4)}}.${{v.slice(4,6)}}.${{v.slice(6,8)}}`;
}}

function renderBuilding(basis, title, addr) {{
  if (!basis.length && !title.length) {{
    setContent(`<div class="gbox"><div class="gicon">⚠️</div>
      <div class="gtitle">건축물 정보 없음</div>
      <div class="gdesc">해당 위치의 건축물대장 정보를<br>찾을 수 없습니다.<br>다른 위치를 클릭해 보세요.</div>
    </div>`);
    return;
  }}
  let html = '';
  basis.forEach(item => {{
    html += `<div class="bcard">
      <div class="bhdr">
        <div class="bico">🏢</div>
        <div><div class="bnm">${{item.bldNm||'건물명 미등록'}}</div><div class="badr">${{addr}}</div></div>
      </div>
      <div class="tags">
        <span class="tag tb">${{item.mainPurpsCdNm||item.mainPurpsCd||'-'}}</span>
        <span class="tag tg">${{item.strctCdNm||item.strctCd||'-'}}</span>
        <span class="tag ta">지상 ${{item.grndFlCnt||'-'}}층 / 지하 ${{item.undgrndFlCnt||'0'}}층</span>
      </div>
      <div class="igrid">
        <div class="icell"><div class="clabel">연면적</div><div class="cval hi">${{fmt(item.totArea)}}</div></div>
        <div class="icell"><div class="clabel">건축면적</div><div class="cval">${{fmt(item.archArea)}}</div></div>
        <div class="icell"><div class="clabel">대지면적</div><div class="cval">${{fmt(item.platArea)}}</div></div>
        <div class="icell"><div class="clabel">건폐율/용적률</div><div class="cval">${{item.bcRat||'-'}}% / ${{item.vlRat||'-'}}%</div></div>
        <div class="icell"><div class="clabel">허가일</div><div class="cval">${{fmtDate(item.pmsDay)}}</div></div>
        <div class="icell"><div class="clabel">사용승인일</div><div class="cval">${{fmtDate(item.useAprDay)}}</div></div>
      </div>
    </div>`;
  }});
  if (title.length) {{
    html += `<div class="slabel" style="margin-top:4px">표제부 상세</div>`;
    title.slice(0,3).forEach(t => {{
      html += `<div class="bcard" style="border-color:rgba(16,185,129,.15)">
        <div class="bhdr">
          <div class="bico" style="background:linear-gradient(135deg,rgba(16,185,129,.15),rgba(56,189,248,.1))">📦</div>
          <div><div class="bnm">${{t.dongNm||'주동'}}</div><div class="badr">${{t.mainPurpsCdNm||t.mainPurpsCd||'-'}}</div></div>
        </div>
        <div class="igrid">
          <div class="icell"><div class="clabel">세대수</div><div class="cval">${{t.hhldCnt||'-'}} 세대</div></div>
          <div class="icell"><div class="clabel">가구수</div><div class="cval">${{t.fmlyCnt||'-'}} 가구</div></div>
          <div class="icell"><div class="clabel">승강기 (일반/비상)</div><div class="cval">${{t.elvtCnt||'-'}} / ${{t.emgenElevCnt||'-'}}</div></div>
          <div class="icell"><div class="clabel">자주식 주차</div><div class="cval">${{t.indrAutoUtcnt||'-'}} 대</div></div>
          ${{t.totArea?`<div class="icell full"><div class="clabel">면적 합계</div><div class="cval hi">${{fmt(t.totArea)}}</div></div>`:''}}
        </div>
      </div>`;
    }});
  }}
  setContent(html);
}}

/* ── 초기화 ── */
function resetAll() {{
  if(marker) marker.setMap(null);
  if(circle) circle.setMap(null);
  marker=null; circle=null;
  document.getElementById('sinput').value='';
  document.getElementById('sresults').style.display='none';
  document.getElementById('cbar').textContent='지도를 클릭하면 건축물대장이 조회됩니다';
  document.getElementById('chint').style.display='block';
  setContent(`<div class="gbox">
    <div class="gicon">🗺️</div>
    <div class="gtitle">지도를 클릭하세요</div>
    <div class="gdesc">원하는 위치를 클릭하면<br><strong>건축물대장 정보</strong>가 즉시 표시됩니다.</div>
    <div class="legend">
      <div class="li"><div class="ld" style="background:var(--accent)"></div>일반지도</div>
      <div class="li"><div class="ld" style="background:var(--amber)"></div>위성지도</div>
      <div class="li"><div class="ld" style="background:var(--green)"></div>지적도 오버레이</div>
    </div>
  </div>`);
}}

document.addEventListener('keydown', e => {{
  if(e.key==='Escape') document.getElementById('sresults').style.display='none';
}});
</script>
</body>
</html>"""

# 전체 화면을 HTML 컴포넌트로 렌더링
components.html(html, height=800, scrolling=False)
