import streamlit as st
import streamlit.components.v1 as components

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

# JS에서 클릭 후 동적으로 교체되는 초기 안내 HTML
BLD_INIT_HTML = """
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
          <button class="btn" ON-CLICK="doSearch()">검색</button>
          <button class="btn btng" ON-CLICK="resetAll()">↺</button>
        </div>
        <div id="sres"></div>
      </div>

      <!-- 상태 표시 -->
      <div id="status-bar">
        <span id="status-icon">📌</span>
        <span id="status-txt">지도를 클릭하거나 주소를 검색하세요</span>
      </div>

      <!-- 건물 정보 (JS가 동적으로 교체) -->
      <div id="bld-info">
        {BLD_INIT_HTML}
      </div>

    </div>
  </div>

  <!-- 지도 -->
  <div id="ma">
    <div id="map"></div>
    <div id="lc">
      <button class="lb on" id="b1" ON-CLICK="setT('road')">🗺 일반</button>
      <button class="lb" id="b2" ON-CLICK="setT('sky')">🛰 위성</button>
      <button class="lb" id="b3" ON-CLICK="toggleJ()">📐 지적도</button>
    </div>
    <div id="zc">
      <button class="lb sq" ON-CLICK="map&&map.setLevel(map.getLevel()-1)">＋</button>
      <button class="lb sq" ON-CLICK="map&&map.setLevel(map.getLevel()+1)">－</button>
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

// ── 카카오 REST API ──────────────────────────────────
// ★ coord2address: 주소명 + 지번(본번/부번) 취득
//   → 단, Address 응답에 b_code 없음 (공식문서 확인)
// ★ coord2regioncode: 법정동 코드(b_code 10자리) 취득
//   → region_type=="B" 인 document의 code 필드 사용
// 두 API를 병렬 호출해서 PNU 전체를 조합

async function fetchKakao(url) {{
  var res = await fetch(url, {{ headers: {{ 'Authorization': 'KakaoAK ' + KAKAO_REST }} }});
  return res.json();
}}

async function getPNU(lat, lng) {{
  var baseX = lng, baseY = lat;

  // 두 API 병렬 호출
  var [addrData, regionData] = await Promise.all([
    fetchKakao('https://dapi.kakao.com/v2/local/geo/coord2address.json?x='+baseX+'&y='+baseY),
    fetchKakao('https://dapi.kakao.com/v2/local/geo/coord2regioncode.json?x='+baseX+'&y='+baseY),
  ]);

  // ── coord2address: 주소명 + 본번/부번 ──
  var addrDoc  = (addrData.documents  || [])[0] || {{}};
  var land     = addrDoc.address      || {{}};
  var road     = addrDoc.road_address || {{}};
  var addrName = road.address_name || land.address_name || '';
  var bun      = land.main_address_no || '0';
  var ji       = land.sub_address_no  || '0';

  // ── coord2regioncode: 법정동 코드(10자리) ──
  // region_type이 "B"(법정동)인 항목의 code 사용
  var bCode    = '';
  var regions  = regionData.documents || [];
  for (var i = 0; i < regions.length; i++) {{
    if (regions[i].region_type === 'B') {{
      bCode = regions[i].code || '';   // 예: "1111010100" (10자리)
      break;
    }}
  }}

  var sigungu = bCode.slice(0, 5);   // 앞 5자리: 시군구코드
  var bjdong  = bCode.slice(5, 10);  // 뒤 5자리: 법정동코드

  // 콘솔 로그 (디버깅용)
  console.log('[PNU] 좌표:', lat, lng);
  console.log('[PNU] 주소:', addrName);
  console.log('[PNU] b_code(법정동코드 10자리):', bCode);
  console.log('[PNU] 시군구:', sigungu, '| 법정동:', bjdong, '| 본번:', bun, '| 부번:', ji);

  return {{
    sigungu : sigungu,
    bjdong  : bjdong,
    bun     : bun,
    ji      : ji,
    addr    : addrName,
    bCode   : bCode,
  }};
}}

// ── 건축물대장 API 직접 호출 (JS에서 직접) ──────────
// 공공데이터포털(apis.data.go.kr)은 CORS 허용
// → JS에서 직접 XML 응답을 받아 파싱
var BUILD_KEY = '{BUILDING_API_KEY}';
var BUILD_BASE = 'https://apis.data.go.kr/1613000/BldRgstService_v2';

function buildApiUrl(endpoint, sigungu, bjdong, bun, ji) {{
  var qs = [
    'sigunguCd=' + sigungu,
    'bjdongCd='  + bjdong,
    'platGbCd=0',
    'bun='  + String(bun).padStart(4, '0'),
    'ji='   + String(ji || '0').padStart(4, '0'),
    'startDate=',
    'endDate=',
    'numOfRows=10',
    'pageNo=1',
    'serviceKey=' + BUILD_KEY,
  ].join('&');
  return BUILD_BASE + '/' + endpoint + '?' + qs;
}}

function parseXml(xmlText) {{
  var parser = new DOMParser();
  var doc    = parser.parseFromString(xmlText, 'application/xml');
  var codeEl = doc.querySelector('resultCode');
  if (codeEl && codeEl.textContent !== '00') {{
    var msgEl = doc.querySelector('resultMsg');
    return {{ error: msgEl ? msgEl.textContent : 'API 오류' }};
  }}
  var items = Array.from(doc.querySelectorAll('item'));
  if (!items.length) return {{ items: [] }};
  return {{
    items: items.map(function(item) {{
      var obj = {{}};
      Array.from(item.children).forEach(function(c) {{
        obj[c.tagName] = c.textContent.trim();
      }});
      return obj;
    }})
  }};
}}

async function queryBuilding(pnu) {{
  setStatus('loading', '⏳', '건축물대장 조회 중: ' + pnu.addr);
  document.getElementById('bld-info').innerHTML =
    '<div style="text-align:center;padding:30px;color:var(--t3);">' +
    '<div class="spin" style="width:24px;height:24px;margin:0 auto 10px;border-width:3px;' +
    'border-color:rgba(56,189,248,.15);border-top-color:var(--ac);"></div>' +
    '<div style="font-size:.73rem;">건축물대장 조회 중...</div></div>';

  try {{
    var [basisRes, titleRes] = await Promise.all([
      fetch(buildApiUrl('getBrBasisOulnInfo', pnu.sigungu, pnu.bjdong, pnu.bun, pnu.ji)),
      fetch(buildApiUrl('getBrTitleInfo',     pnu.sigungu, pnu.bjdong, pnu.bun, pnu.ji)),
    ]);

    var [basisText, titleText] = await Promise.all([
      basisRes.text(),
      titleRes.text(),
    ]);

    console.log('[건축물대장 기본개요 응답]', basisText.slice(0, 300));

    var basis = parseXml(basisText);
    var title = parseXml(titleText);

    if (basis.error) {{
      setStatus('err', '❌', '기본개요 오류: ' + basis.error);
      document.getElementById('bld-info').innerHTML =
        '<div class="err-box">⚠️ ' + basis.error + '</div>';
      return;
    }}

    renderBuilding(basis.items || [], title.items || [], pnu.addr);
    setStatus('done', '✅', '조회 완료: ' + pnu.addr);

  }} catch(err) {{
    console.error('[건축물대장] fetch 오류:', err);
    // CORS 오류 시 상세 안내
    setStatus('err', '❌', 'API 오류: ' + err.message);
    document.getElementById('bld-info').innerHTML =
      '<div class="err-box">⚠️ 건축물대장 API 호출 오류<br><br>' +
      '<strong>오류:</strong> ' + err.message + '<br><br>' +
      '수동 PNU 입력 기능을 사용해 주세요.<br>' +
      '시군구: ' + pnu.sigungu + ' | 법정동: ' + pnu.bjdong + '<br>' +
      '본번: ' + pnu.bun + ' | 부번: ' + pnu.ji + '</div>';
  }}
}}

// ── 건축물 정보 렌더링 ──────────────────────────────
function fmtArea(v) {{
  var n = parseFloat(v);
  return isNaN(n) ? (v || '-') : n.toLocaleString('ko', {{minimumFractionDigits:2, maximumFractionDigits:2}}) + ' ㎡';
}}
function fmtDate(v) {{
  if (!v || v.length < 8) return v || '-';
  return v.slice(0,4) + '.' + v.slice(4,6) + '.' + v.slice(6,8);
}}

function renderBuilding(basis, title, addr) {{
  if (!basis.length && !title.length) {{
    document.getElementById('bld-info').innerHTML =
      '<div class="err-box">⚠️ 해당 위치의 건축물 정보가 없습니다.</div>';
    return;
  }}

  var h = '<div class="addr-bar">📍 ' + addr + '</div>';

  basis.forEach(function(x) {{
    h += '<div class="bcard">' +
      '<div class="bhead">' +
        '<div class="bico">🏢</div>' +
        '<div>' +
          '<div class="bnm">' + (x.bldNm || '건물명 미등록') + '</div>' +
          '<div class="badr">' + addr + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="tags">' +
        '<span class="tag tb">' + (x.mainPurpsCdNm || x.mainPurpsCd || '-') + '</span>' +
        '<span class="tag tg">' + (x.strctCdNm || x.strctCd || '-') + '</span>' +
        '<span class="tag ta">지상' + (x.grndFlCnt||'-') + '층/지하' + (x.undgrndFlCnt||'0') + '층</span>' +
      '</div>' +
      '<div class="grid2">' +
        '<div class="cell"><div class="clbl">연면적</div><div class="cval hi">' + fmtArea(x.totArea) + '</div></div>' +
        '<div class="cell"><div class="clbl">건축면적</div><div class="cval">' + fmtArea(x.archArea) + '</div></div>' +
        '<div class="cell"><div class="clbl">대지면적</div><div class="cval">' + fmtArea(x.platArea) + '</div></div>' +
        '<div class="cell"><div class="clbl">건폐율/용적률</div><div class="cval">' + (x.bcRat||'-') + '%/' + (x.vlRat||'-') + '%</div></div>' +
        '<div class="cell"><div class="clbl">허가일</div><div class="cval">' + fmtDate(x.pmsDay) + '</div></div>' +
        '<div class="cell"><div class="clbl">사용승인일</div><div class="cval">' + fmtDate(x.useAprDay) + '</div></div>' +
      '</div>' +
    '</div>';
  }});

  if (title.length) {{
    h += '<div class="sec-title">표제부 상세</div>';
    title.slice(0,3).forEach(function(t) {{
      h += '<div class="bcard" style="border-color:rgba(16,185,129,.2)">' +
        '<div class="bhead">' +
          '<div class="bico" style="background:linear-gradient(135deg,rgba(16,185,129,.15),rgba(56,189,248,.1))">📦</div>' +
          '<div>' +
            '<div class="bnm">' + (t.dongNm||'주동') + '</div>' +
            '<div class="badr">' + (t.mainPurpsCdNm||'-') + '</div>' +
          '</div>' +
        '</div>' +
        '<div class="grid2">' +
          '<div class="cell"><div class="clbl">세대수</div><div class="cval">' + (t.hhldCnt||'-') + ' 세대</div></div>' +
          '<div class="cell"><div class="clbl">가구수</div><div class="cval">' + (t.fmlyCnt||'-') + ' 가구</div></div>' +
          '<div class="cell"><div class="clbl">승강기(일반/비상)</div><div class="cval">' + (t.elvtCnt||'-') + '/' + (t.emgenElevCnt||'-') + '</div></div>' +
          '<div class="cell"><div class="clbl">자주식주차</div><div class="cval">' + (t.indrAutoUtcnt||'-') + ' 대</div></div>' +
        '</div>' +
      '</div>';
    }});
  }}

  document.getElementById('bld-info').innerHTML = h;
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
      // coord2address + coord2regioncode 병렬 호출 → PNU 조합
      var pnu = await getPNU(lat, lng);

      if (!pnu.sigungu || pnu.sigungu.length < 4) {{
        setStatus('err', '❌', '지번 코드를 추출할 수 없습니다. 다른 위치를 클릭해 보세요.');
        return;
      }}

      setStatus('loading', '⏳', '건축물대장 조회 중: ' + pnu.addr);
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
      return '<div class="ri" ON-CLICK="pickResult(' + i + ')">' +
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
    var pnu = await getPNU(lat, lng);
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
