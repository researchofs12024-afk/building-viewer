import streamlit as st
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET
import json

st.set_page_config(
    page_title="건축물대장 조회 시스템",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

# ── 세션 상태 ─────────────────────────────────────
for k, v in {
    "building_data": None,
    "current_addr":  "",
    "pnu": {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── API 함수 ──────────────────────────────────────
def fetch_building(sigungu, bjdong, bun, ji):
    def mk_url(ep):
        qs = "&".join([
            f"sigunguCd={sigungu}",
            f"bjdongCd={bjdong}",
            "platGbCd=0",
            f"bun={str(bun).zfill(4)}",
            f"ji={str(ji or 0).zfill(4)}",
            "startDate=", "endDate=",
            "numOfRows=10", "pageNo=1",
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
            return {"items": [{c.tag: (c.text or "") for c in i}
                               for i in root.findall(".//item")]}
        except Exception as e:
            return {"error": str(e)}

    try:
        r1 = requests.get(mk_url("getBrBasisOulnInfo"), timeout=10)
        r2 = requests.get(mk_url("getBrTitleInfo"),     timeout=10)
        return {"basis": parse(r1.text), "title": parse(r2.text)}
    except Exception as e:
        return {"error": str(e)}

def addr_search(query):
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"query": query, "size": 5}, timeout=5)
        return r.json().get("documents", [])
    except:
        return []

# ══════════════════════════════════════════════════
# query_params 수신
# 지도 JS → Streamlit URL (?action=...) → Python 처리
# ★ allow-top-navigation-by-user-activation 없이도
#   Streamlit이 직접 URL을 바꾸는 게 아니라
#   JS에서 history.replaceState로 같은 origin 내
#   파라미터만 바꾸는 방식 사용
# ══════════════════════════════════════════════════
qp = st.query_params
action = qp.get("action", "")

if action == "query":
    # 지도가 이미 역지오코딩 완료 후 PNU 코드를 넘겨준 경우
    sigungu = qp.get("sigungu", "")
    bjdong  = qp.get("bjdong",  "")
    bun     = qp.get("bun",     "0")
    ji      = qp.get("ji",      "0")
    addr    = qp.get("addr",    "")

    if sigungu and bjdong:
        result = fetch_building(sigungu, bjdong, bun, ji)
        st.session_state.building_data = result
        st.session_state.current_addr  = addr
        st.session_state.pnu = {
            "sigungu": sigungu, "bjdong": bjdong, "bun": bun, "ji": ji
        }
    st.query_params.clear()
    st.rerun()

# ══════════════════════════════════════════════════
# 전체 UI를 하나의 HTML 컴포넌트로
# 카카오맵 + 좌측 패널 모두 HTML 안에 구현
# Python은 건축물대장 API 조회 전용으로만 사용
# ══════════════════════════════════════════════════

# 현재 건물 데이터를 JSON으로 HTML에 주입
bld_json = json.dumps(st.session_state.building_data or {}, ensure_ascii=False)
addr_str  = st.session_state.current_addr.replace('"', '&quot;')

def fa(v):
    try: return f"{float(v):,.2f} ㎡"
    except: return v or "-"

def fd(v):
    if v and len(v) == 8:
        return f"{v[:4]}.{v[4:6]}.{v[6:]}"
    return v or "-"

# 건물 정보 HTML 미리 생성 (Python에서 렌더링)
def render_building_html(bd, addr):
    if not bd:
        return """
<div class="guide-box">
  <div class="gi">🗺️</div>
  <div class="gt">지도를 클릭하세요</div>
  <div class="gd">원하는 위치를 클릭하면<br><strong>건축물대장 정보</strong>가 표시됩니다.</div>
  <div class="legend">
    <span class="leg-item"><span class="leg-dot" style="background:#38bdf8"></span>일반지도</span>
    <span class="leg-item"><span class="leg-dot" style="background:#f59e0b"></span>위성지도</span>
    <span class="leg-item"><span class="leg-dot" style="background:#10b981"></span>지적도</span>
  </div>
</div>"""

    if "error" in bd:
        return f'<div class="err-box">⚠️ {bd["error"]}</div>'

    basis = bd.get("basis", {}).get("items", [])
    title = bd.get("title", {}).get("items", [])

    if not basis and not title:
        return '<div class="err-box">⚠️ 건축물 정보가 없습니다.</div>'

    html = f'<div class="addr-bar">📍 {addr}</div>'

    for item in basis:
        bld_nm  = item.get("bldNm") or "건물명 미등록"
        use_nm  = item.get("mainPurpsCdNm") or item.get("mainPurpsCd") or "-"
        strct   = item.get("strctCdNm") or item.get("strctCd") or "-"
        grnd_fl = item.get("grndFlCnt") or "-"
        undr_fl = item.get("undgrndFlCnt") or "0"
        html += f"""
<div class="bcard">
  <div class="bhead">
    <div class="bico">🏢</div>
    <div>
      <div class="bnm">{bld_nm}</div>
      <div class="badr">{addr}</div>
    </div>
  </div>
  <div class="tags">
    <span class="tag tb">{use_nm}</span>
    <span class="tag tg">{strct}</span>
    <span class="tag ta">지상{grnd_fl}층/지하{undr_fl}층</span>
  </div>
  <div class="grid2">
    <div class="cell"><div class="clbl">연면적</div><div class="cval hi">{fa(item.get("totArea"))}</div></div>
    <div class="cell"><div class="clbl">건축면적</div><div class="cval">{fa(item.get("archArea"))}</div></div>
    <div class="cell"><div class="clbl">대지면적</div><div class="cval">{fa(item.get("platArea"))}</div></div>
    <div class="cell"><div class="clbl">건폐율/용적률</div><div class="cval">{item.get("bcRat") or "-"}%/{item.get("vlRat") or "-"}%</div></div>
    <div class="cell"><div class="clbl">허가일</div><div class="cval">{fd(item.get("pmsDay"))}</div></div>
    <div class="cell"><div class="clbl">사용승인일</div><div class="cval">{fd(item.get("useAprDay"))}</div></div>
  </div>
</div>"""

    if title:
        html += '<div class="sec-title">표제부 상세</div>'
        for t in title[:3]:
            html += f"""
<div class="bcard" style="border-color:rgba(16,185,129,.2)">
  <div class="bhead">
    <div class="bico" style="background:linear-gradient(135deg,rgba(16,185,129,.15),rgba(56,189,248,.1))">📦</div>
    <div>
      <div class="bnm">{t.get("dongNm") or "주동"}</div>
      <div class="badr">{t.get("mainPurpsCdNm") or "-"}</div>
    </div>
  </div>
  <div class="grid2">
    <div class="cell"><div class="clbl">세대수</div><div class="cval">{t.get("hhldCnt") or "-"} 세대</div></div>
    <div class="cell"><div class="clbl">가구수</div><div class="cval">{t.get("fmlyCnt") or "-"} 가구</div></div>
    <div class="cell"><div class="clbl">승강기(일반/비상)</div><div class="cval">{t.get("elvtCnt") or "-"}/{t.get("emgenElevCnt") or "-"}</div></div>
    <div class="cell"><div class="clbl">자주식주차</div><div class="cval">{t.get("indrAutoUtcnt") or "-"} 대</div></div>
  </div>
</div>"""
    return html

bld_html = render_building_html(
    st.session_state.building_data,
    st.session_state.current_addr
)

FULL_HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
:root{{
  --bg:#07090f;--bg2:#0d1117;--bg3:#161b22;
  --bd:rgba(255,255,255,.07);--bd2:rgba(56,189,248,.22);
  --t:#c9d1d9;--t2:#8b949e;--t3:#484f58;
  --ac:#38bdf8;--a2:#0ea5e9;--gr:#10b981;--am:#f59e0b;
  --pw:350px;--hh:50px;
}}
html,body{{height:100%;overflow:hidden;background:var(--bg);color:var(--t);
  font-family:'Noto Sans KR',-apple-system,sans-serif;}}

/* 헤더 */
#hdr{{height:var(--hh);background:var(--bg2);border-bottom:1px solid var(--bd);
  display:flex;align-items:center;padding:0 16px;gap:10px;position:relative;z-index:200;}}
.hlogo{{width:28px;height:28px;background:linear-gradient(135deg,var(--ac),var(--gr));
  border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px;}}
.htit{{font-size:.85rem;font-weight:700;color:#f0f6ff;letter-spacing:-.02em;}}
.hsub{{font-size:.56rem;color:var(--t3);font-family:'JetBrains Mono',monospace;}}
.hbdg{{margin-left:auto;display:flex;align-items:center;gap:5px;
  background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
  color:var(--gr);padding:2px 9px;border-radius:20px;font-size:.6rem;font-weight:600;}}
.hdot{{width:5px;height:5px;border-radius:50%;background:var(--gr);animation:blink 2s infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.3;}}}}

/* 레이아웃 */
#main{{display:flex;height:calc(100vh - var(--hh));overflow:hidden;}}

/* 패널 */
#panel{{width:var(--pw);min-width:var(--pw);background:var(--bg2);
  border-right:1px solid var(--bd);display:flex;flex-direction:column;overflow:hidden;}}
#ps{{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:9px;}}
#ps::-webkit-scrollbar{{width:3px;}}
#ps::-webkit-scrollbar-thumb{{background:var(--bd2);border-radius:2px;}}

.slbl{{font-size:.58rem;font-weight:700;letter-spacing:.1em;color:var(--ac);
  text-transform:uppercase;margin-bottom:6px;display:flex;align-items:center;gap:5px;}}
.slbl::before{{content:'';width:3px;height:10px;background:var(--ac);border-radius:2px;}}

.sw{{background:var(--bg3);border:1px solid var(--bd);border-radius:9px;padding:11px;}}
.srow{{display:flex;gap:5px;}}
#si{{flex:1;background:var(--bg);border:1px solid var(--bd);border-radius:6px;
  color:var(--t);font-family:inherit;font-size:.79rem;padding:7px 10px;outline:none;
  transition:border-color .2s,box-shadow .2s;}}
#si::placeholder{{color:var(--t3);}}
#si:focus{{border-color:var(--ac);box-shadow:0 0 0 3px rgba(56,189,248,.1);}}
.btn{{background:linear-gradient(135deg,var(--a2),var(--gr));color:#fff;border:none;
  border-radius:6px;font-family:inherit;font-size:.72rem;font-weight:600;padding:7px 11px;
  cursor:pointer;transition:all .2s;white-space:nowrap;}}
.btn:hover{{opacity:.85;transform:translateY(-1px);}}
.btng{{background:var(--bg);border:1px solid var(--bd);color:var(--t2);}}
.btng:hover{{border-color:var(--bd2);color:var(--t);opacity:1;}}

#sres{{margin-top:6px;display:none;flex-direction:column;gap:3px;}}
.ri{{background:var(--bg);border:1px solid var(--bd);border-radius:5px;
  padding:7px 10px;cursor:pointer;font-size:.74rem;color:var(--t2);transition:all .15s;}}
.ri:hover{{border-color:var(--bd2);color:var(--t);background:rgba(56,189,248,.05);}}
.ri .rm{{font-weight:500;color:var(--t);}}
.ri .rs{{font-size:.66rem;color:var(--t3);margin-top:1px;}}

/* 상태 배너 */
#status-bar{{background:rgba(56,189,248,.07);border:1px solid rgba(56,189,248,.15);
  border-radius:8px;padding:9px 12px;font-size:.72rem;color:var(--ac);
  display:flex;align-items:center;gap:8px;}}
#status-bar.loading{{color:var(--am);background:rgba(245,158,11,.07);border-color:rgba(245,158,11,.2);}}
#status-bar.done{{color:var(--gr);background:rgba(16,185,129,.07);border-color:rgba(16,185,129,.2);}}
#status-bar.err{{color:#f87171;background:rgba(239,68,68,.07);border-color:rgba(239,68,68,.2);}}
.spin{{width:12px;height:12px;border:2px solid rgba(245,158,11,.2);
  border-top-color:var(--am);border-radius:50%;animation:spin .7s linear infinite;flex-shrink:0;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}

/* 건물 카드 */
.guide-box{{background:var(--bg3);border:1px dashed rgba(56,189,248,.15);
  border-radius:9px;padding:22px 13px;text-align:center;}}
.gi{{font-size:1.7rem;margin-bottom:7px;}}
.gt{{font-size:.78rem;font-weight:600;color:var(--t);margin-bottom:5px;}}
.gd{{font-size:.7rem;color:var(--t3);line-height:1.7;}}
.gd strong{{color:var(--ac);}}
.legend{{display:flex;justify-content:center;gap:10px;margin-top:10px;padding-top:10px;border-top:1px solid var(--bd);}}
.leg-item{{display:flex;align-items:center;gap:4px;font-size:.62rem;color:var(--t3);}}
.leg-dot{{width:7px;height:7px;border-radius:2px;display:inline-block;}}

.addr-bar{{font-size:.7rem;color:var(--t3);padding:6px 10px;
  background:var(--bg3);border-radius:6px;margin-bottom:8px;}}
.bcard{{background:var(--bg3);border:1px solid rgba(56,189,248,.15);border-radius:9px;
  padding:12px;margin-bottom:8px;}}
.bhead{{display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;}}
.bico{{width:30px;height:30px;background:linear-gradient(135deg,rgba(56,189,248,.15),rgba(16,185,129,.15));
  border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;
  flex-shrink:0;border:1px solid rgba(56,189,248,.15);}}
.bnm{{font-size:.82rem;font-weight:700;color:#f0f6ff;}}
.badr{{font-size:.65rem;color:var(--t3);margin-top:1px;}}
.tags{{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:8px;}}
.tag{{font-size:.6rem;font-weight:600;padding:2px 6px;border-radius:4px;}}
.tb{{background:rgba(56,189,248,.12);color:var(--ac);border:1px solid rgba(56,189,248,.2);}}
.tg{{background:rgba(16,185,129,.12);color:var(--gr);border:1px solid rgba(16,185,129,.2);}}
.ta{{background:rgba(245,158,11,.12);color:var(--am);border:1px solid rgba(245,158,11,.2);}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:4px;}}
.cell{{background:var(--bg);border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:7px 8px;}}
.clbl{{font-size:.55rem;font-weight:600;color:var(--t3);text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}}
.cval{{font-size:.72rem;font-weight:500;color:var(--t);font-family:'JetBrains Mono',monospace;}}
.cval.hi{{color:var(--ac);}}
.sec-title{{font-size:.58rem;font-weight:700;color:var(--ac);text-transform:uppercase;
  letter-spacing:.1em;margin:8px 0 5px;display:flex;align-items:center;gap:5px;}}
.sec-title::before{{content:'';width:3px;height:10px;background:var(--ac);border-radius:2px;}}
.err-box{{background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);
  border-radius:9px;padding:12px;font-size:.73rem;color:#fca5a5;line-height:1.7;}}

/* 지도 */
#ma{{flex:1;position:relative;overflow:hidden;}}
#map{{width:100%;height:100%;}}
#lc{{position:absolute;top:12px;left:12px;z-index:400;display:flex;flex-direction:column;gap:4px;}}
.lb{{background:rgba(7,9,15,.9);border:1px solid rgba(56,189,248,.2);color:var(--t2);
  border-radius:7px;font-size:.68rem;font-weight:600;padding:7px 10px;cursor:pointer;
  transition:all .2s;backdrop-filter:blur(12px);display:flex;align-items:center;gap:5px;
  font-family:inherit;border-style:solid;}}
.lb:hover{{background:rgba(56,189,248,.12);border-color:rgba(56,189,248,.5);color:var(--t);}}
.lb.on{{background:rgba(56,189,248,.18);border-color:var(--ac);color:var(--ac);}}
#zc{{position:absolute;top:12px;right:12px;z-index:400;display:flex;flex-direction:column;gap:4px;}}
.sq{{width:32px;height:32px;padding:0;justify-content:center;font-size:.9rem;}}
#cb{{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);z-index:400;
  background:rgba(7,9,15,.9);border:1px solid rgba(255,255,255,.1);border-radius:20px;
  padding:4px 12px;font-family:'JetBrains Mono',monospace;font-size:.61rem;
  color:var(--t3);backdrop-filter:blur(12px);pointer-events:none;white-space:nowrap;}}
@keyframes cp{{
  0%{{transform:translate(-50%,-50%) scale(.5);opacity:1;}}
  100%{{transform:translate(-50%,-50%) scale(3.5);opacity:0;}}}}
.cp{{position:absolute;width:24px;height:24px;border:2px solid var(--ac);border-radius:50%;
  pointer-events:none;animation:cp .6s ease-out forwards;z-index:500;}}
</style>
</head>
<body>

<div id="hdr">
  <div class="hlogo">🏢</div>
  <div>
    <div class="htit">건축물대장 조회 시스템</div>
    <div class="hsub">KAKAO MAPS · VWORLD · BUILDING REGISTRY</div>
  </div>
  <div class="hbdg"><div class="hdot"></div> LIVE</div>
</div>

<div id="main">
  <!-- 패널 -->
  <div id="panel">
    <div id="ps">

      <!-- 검색 -->
      <div class="sw">
        <div class="slbl">주소 검색</div>
        <div class="srow">
          <input id="si" type="text" placeholder="예: 강남구 테헤란로 152" autocomplete="off">
          <button class="btn" onclick="doSearch()">검색</button>
          <button class="btn btng" onclick="resetAll()">↺</button>
        </div>
        <div id="sres"></div>
      </div>

      <!-- 상태 표시 -->
      <div id="status-bar">
        <span id="status-icon">📌</span>
        <span id="status-txt">지도를 클릭하거나 주소를 검색하세요</span>
      </div>

      <!-- 건물 정보 -->
      <div id="bld-info">
        {bld_html}
      </div>

    </div>
  </div>

  <!-- 지도 -->
  <div id="ma">
    <div id="map"></div>
    <div id="lc">
      <button class="lb on" id="b1" onclick="setT('road')">🗺 일반</button>
      <button class="lb" id="b2" onclick="setT('sky')">🛰 위성</button>
      <button class="lb" id="b3" onclick="toggleJ()">📐 지적도</button>
    </div>
    <div id="zc">
      <button class="lb sq" onclick="map&&map.setLevel(map.getLevel()-1)">＋</button>
      <button class="lb sq" onclick="map&&map.setLevel(map.getLevel()+1)">－</button>
    </div>
    <div id="cb">지도를 클릭하면 건축물대장이 조회됩니다</div>
  </div>
</div>

<script>
// ── 상수 ──
var KAKAO_REST = '{KAKAO_REST_KEY}';

// ── 상태 표시 ──
function setStatus(type, icon, msg) {{
  var bar = document.getElementById('status-bar');
  bar.className = 'status-bar ' + type;
  document.getElementById('status-icon').textContent = icon;
  document.getElementById('status-txt').textContent  = msg;
}}

// ── 카카오 REST API: 좌표→주소 (역지오코딩) ──
// Python 서버를 거치지 않고 JS에서 직접 호출
// 카카오 REST API는 HTTPS이므로 Mixed Content 없음
async function coord2addr(lat, lng) {{
  var url = 'https://dapi.kakao.com/v2/local/geo/coord2address.json?x='+lng+'&y='+lat;
  var res  = await fetch(url, {{
    headers: {{ 'Authorization': 'KakaoAK ' + KAKAO_REST }}
  }});
  var data = await res.json();
  var docs = data.documents || [];
  return docs.length ? docs[0] : null;
}}

// ── PNU 코드 추출 ──
// 카카오 coord2address 응답의 b_code(법정동코드 10자리)에서 추출
function extractPNU(doc) {{
  var land = doc.address || {{}};
  var bCode = land.b_code || '';           // 10자리 법정동코드
  // b_code 구조: 시군구코드(5) + 법정동코드(5)
  var sigungu = bCode.slice(0, 5);
  var bjdong  = bCode.slice(5, 10);
  var bun     = land.main_address_no || '0';
  var ji      = land.sub_address_no  || '0';

  var road    = doc.road_address || {{}};
  var addr    = road.address_name || land.address_name || '';

  return {{ sigungu: sigungu, bjdong: bjdong, bun: bun, ji: ji, addr: addr, bCode: bCode }};
}}

// ── Streamlit URL 파라미터로 건축물대장 조회 요청 ──
// history.pushState는 sandbox에서 허용됨 (same-origin 내)
// 단, Streamlit iframe은 about:srcdoc → pushState 불가
// → 대신 Streamlit의 st.query_params를 활용하기 위해
//   현재 Streamlit 앱 URL을 직접 변경
// ★ 해결책: 직접 fetch로 Streamlit 앱에 GET 요청
//   Streamlit이 action=query를 받아서 처리 후 rerun
async function queryBuilding(pnu) {{
  setStatus('loading', '⏳', '건축물대장 조회 중... (' + pnu.addr + ')');
  document.getElementById('bld-info').innerHTML =
    '<div style="text-align:center;padding:30px;color:var(--t3);">' +
    '<div class="spin" style="width:24px;height:24px;margin:0 auto 10px;border-width:3px;' +
    'border-color:rgba(56,189,248,.15);border-top-color:var(--ac);"></div>' +
    '<div style="font-size:.73rem;">건축물대장 조회 중...</div></div>';

  var params = new URLSearchParams({{
    action:  'query',
    sigungu: pnu.sigungu,
    bjdong:  pnu.bjdong,
    bun:     pnu.bun,
    ji:      pnu.ji,
    addr:    pnu.addr,
  }});

  // Streamlit 앱 URL에 파라미터를 붙여서 이동
  // → Streamlit이 query_params를 읽고 처리 후 rerun
  // ★ 핵심: top-level window URL 변경 (iframe 자신이 아닌 parent)
  //   sandbox="allow-top-navigation-by-user-activation" 필요
  //   → Streamlit은 이 권한을 허용함
  try {{
    window.top.location.href = window.top.location.href.split('?')[0] + '?' + params.toString();
  }} catch(e) {{
    // fallback: location.replace
    try {{
      window.location.href = '?' + params.toString();
    }} catch(e2) {{
      setStatus('err', '❌', '페이지 이동 실패. 수동 PNU 입력을 사용해 주세요.');
    }}
  }}
}}

// ── 카카오맵 초기화 ──
var map, marker, circle, jijeokOn = false;

kakao.maps.load(function() {{
  map = new kakao.maps.Map(document.getElementById('map'), {{
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level: 4,
  }});

  kakao.maps.Tileset.add('VW_LP', new kakao.maps.Tileset({{
    width:256, height:256, minZoom:1, maxZoom:21,
    getTileUrl: function(x,y,z) {{
      return 'https://api.vworld.kr/req/wmts/1.0.0/{VWORLD_KEY}/lp/'+z+'/'+y+'/'+x+'.png';
    }},
  }}));

  // ── 지도 클릭 이벤트 ──
  kakao.maps.event.addListener(map, 'click', async function(e) {{
    var lat = e.latLng.getLat(), lng = e.latLng.getLng();

    document.getElementById('cb').textContent =
      'LAT ' + lat.toFixed(6) + '  ·  LNG ' + lng.toFixed(6);

    placeMark(lat, lng);
    map.panTo(e.latLng);
    setStatus('loading', '⏳', '주소 변환 중...');

    try {{
      // STEP 1: 좌표 → 주소 + PNU 코드 (카카오 REST API)
      var doc = await coord2addr(lat, lng);
      if (!doc) {{
        setStatus('err', '❌', '주소를 찾을 수 없습니다.');
        return;
      }}

      var pnu = extractPNU(doc);
      setStatus('loading', '⏳', '주소 확인: ' + pnu.addr);

      // 개발자 확인용 콘솔 출력
      console.log('[건축물대장] 좌표:', lat, lng);
      console.log('[건축물대장] 주소:', pnu.addr);
      console.log('[건축물대장] b_code:', pnu.bCode);
      console.log('[건축물대장] 시군구:', pnu.sigungu, '법정동:', pnu.bjdong, '본번:', pnu.bun, '부번:', pnu.ji);

      if (!pnu.sigungu || pnu.sigungu.length < 4) {{
        setStatus('err', '❌', '지번 코드를 추출할 수 없습니다. 다른 위치를 클릭해 보세요.');
        return;
      }}

      // STEP 2: PNU 코드로 건축물대장 조회 (Streamlit Python 경유)
      await queryBuilding(pnu);

    }} catch(err) {{
      console.error('[건축물대장] 오류:', err);
      setStatus('err', '❌', '오류: ' + err.message);
    }}
  }});

  kakao.maps.event.addListener(map, 'mousemove', function(e) {{
    if (!marker)
      document.getElementById('cb').textContent =
        'LAT ' + e.latLng.getLat().toFixed(6) + '  ·  LNG ' + e.latLng.getLng().toFixed(6);
  }});
}});

function setT(t) {{
  if (!map) return;
  map.setMapTypeId(t==='road' ? kakao.maps.MapTypeId.ROADMAP : kakao.maps.MapTypeId.SKYVIEW);
  document.getElementById('b1').classList.toggle('on', t==='road');
  document.getElementById('b2').classList.toggle('on', t==='sky');
}}

function toggleJ() {{
  if (!map) return;
  jijeokOn = !jijeokOn;
  document.getElementById('b3').classList.toggle('on', jijeokOn);
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
  var p = document.createElement('div');
  p.className='cp'; p.style.left=pt.x+'px'; p.style.top=pt.y+'px';
  document.getElementById('ma').appendChild(p);
  setTimeout(function(){{ p.remove(); }}, 700);
}}

// ── 주소 검색 ──
document.getElementById('si').addEventListener('keydown', function(e) {{
  if (e.key==='Enter') doSearch();
}});

async function doSearch() {{
  var q = document.getElementById('si').value.trim();
  if (!q) return;
  setStatus('loading', '⏳', '주소 검색 중...');

  try {{
    var url = 'https://dapi.kakao.com/v2/local/search/address.json?query=' + encodeURIComponent(q) + '&size=5';
    var res  = await fetch(url, {{headers: {{'Authorization': 'KakaoAK ' + KAKAO_REST}}}});
    var data = await res.json();
    var docs = data.documents || [];

    if (!docs.length) {{
      setStatus('', '📌', '검색 결과가 없습니다.');
      return;
    }}

    var box = document.getElementById('sres');
    box.innerHTML = docs.map(function(d, i) {{
      var road = d.road_address;
      var main = road ? road.address_name : d.address_name;
      var sub  = road ? d.address_name : '';
      return '<div class="ri" onclick="pickResult(' + i + ')">' +
             '<div class="rm">📍 ' + main + '</div>' +
             (sub ? '<div class="rs">' + sub + '</div>' : '') +
             '</div>';
    }}).join('');
    box.style.display = 'flex';
    box._docs = docs;
    setStatus('', '📌', docs.length + '개 결과');

  }} catch(err) {{
    setStatus('err', '❌', '검색 오류: ' + err.message);
  }}
}}

async function pickResult(i) {{
  var doc = document.getElementById('sres')._docs[i];
  var lat = parseFloat(doc.y), lng = parseFloat(doc.x);
  document.getElementById('sres').style.display = 'none';

  if (map) {{ map.setCenter(new kakao.maps.LatLng(lat, lng)); map.setLevel(3); }}
  placeMark(lat, lng);
  setStatus('loading', '⏳', '주소 변환 중...');

  try {{
    var addrDoc = await coord2addr(lat, lng);
    if (!addrDoc) {{ addrDoc = {{ address: doc.address, road_address: doc.road_address }}; }}
    var pnu = extractPNU(addrDoc);
    if (!pnu.addr) pnu.addr = doc.address_name;

    console.log('[검색결과] PNU:', pnu);
    await queryBuilding(pnu);
  }} catch(err) {{
    setStatus('err', '❌', '오류: ' + err.message);
  }}
}}

function resetAll() {{
  if (marker) marker.setMap(null);
  if (circle) circle.setMap(null);
  marker = null; circle = null;
  document.getElementById('si').value = '';
  document.getElementById('sres').style.display = 'none';
  document.getElementById('cb').textContent = '지도를 클릭하면 건축물대장이 조회됩니다';
  setStatus('', '📌', '지도를 클릭하거나 주소를 검색하세요');
  document.getElementById('bld-info').innerHTML = `
    <div class="guide-box">
      <div class="gi">🗺️</div>
      <div class="gt">지도를 클릭하세요</div>
      <div class="gd">원하는 위치를 클릭하면<br><strong>건축물대장 정보</strong>가 표시됩니다.</div>
    </div>`;
}}
</script>
</body>
</html>"""

components.html(FULL_HTML, height=820, scrolling=False)
