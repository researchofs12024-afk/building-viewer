import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(
    page_title="건축물대장 조회 시스템",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 키 설정
KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

# 질문자님 원래 CSS 디자인 원본
st.markdown("""
<style>
#MainMenu,footer,header,.stDeployButton{display:none!important;}
.block-container{padding:0!important;margin:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none;}
[data-testid="stToolbar"]{display:none;}
.stApp{background:#07090f!important;}
iframe{border:none!important;}
[data-testid="stHorizontalBlock"]{gap:0!important;}
[data-testid="column"]{padding:0!important;}
</style>""", unsafe_allow_html=True)

# ── 주소 추출 함수 ──────────────────────────────────
def coord2addr(lat, lng):
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"x": lng, "y": lat}, timeout=5)
        docs = r.json().get("documents", [])
        if docs:
            return docs[0].get("address", {}).get("address_name", "주소 없음")
        return "주소를 찾을 수 없는 지역"
    except: return "API 오류"

# ── 클릭 처리 로직 ──────────────────────────────────
if "current_addr" not in st.session_state:
    st.session_state.current_addr = "지도를 클릭해 보세요"

qp = st.query_params
if "lat" in qp and "lng" in qp:
    # 지도가 URL로 보낸 좌표를 읽어서 주소 변환
    st.session_state.current_addr = coord2addr(qp["lat"], qp["lng"])

# ── 레이아웃 ─────────────────────────────────────
col_left, col_right = st.columns([10, 17], gap="small")

with col_left:
    st.markdown(f"""
    <div style="padding:20px; color:white;">
        <h3 style="color:#38bdf8;">📍 주소 확인</h3>
        <p style="font-size:1.1rem; background:#161b22; padding:15px; border-radius:10px;">
            {st.session_state.current_addr}
        </p>
        <p style="color:#484f58; font-size:0.7rem;">좌표: {qp.get('lat','-')}, {qp.get('lng','-')}</p>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # ★ 질문자님이 맨 처음 주신 원본 지도 코드 (수정 없음) ★
    map_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
:root{{--ac:#38bdf8;--gr:#10b981;--am:#f59e0b;--t2:#8b949e;--t3:#484f58;
  --bd:rgba(255,255,255,.07);--bd2:rgba(56,189,248,.22);}}
html,body{{height:100%;overflow:hidden;background:#07090f;}}
#map{{width:100%;height:100vh;}}
#lc{{position:absolute;top:12px;left:12px;z-index:400;display:flex;flex-direction:column;gap:4px;}}
.lb{{background:rgba(7,9,15,.88);border:1px solid rgba(56,189,248,.18);color:var(--t2);
  border-radius:7px;font-size:.68rem;font-weight:600;padding:7px 10px;cursor:pointer;
  transition:all .2s;backdrop-filter:blur(12px);display:flex;align-items:center;gap:5px;
  font-family:'Noto Sans KR',-apple-system,sans-serif;border-style:solid;}}
.lb:hover{{background:rgba(56,189,248,.1);border-color:rgba(56,189,248,.4);color:#c9d1d9;}}
.lb.on{{background:rgba(56,189,248,.15);border-color:var(--ac);color:var(--ac);}}
#zc{{position:absolute;top:12px;right:12px;z-index:400;display:flex;flex-direction:column;gap:4px;}}
.sq{{width:32px;height:32px;padding:0;justify-content:center;font-size:.9rem;}}
#cb{{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);z-index:400;
  background:rgba(7,9,15,.88);border:1px solid var(--bd);border-radius:20px;
  padding:4px 12px;font-family:monospace;font-size:.61rem;color:var(--t3);
  backdrop-filter:blur(12px);pointer-events:none;white-space:nowrap;}}
#ch{{position:absolute;bottom:44px;left:50%;transform:translateX(-50%);z-index:400;
  background:rgba(7,9,15,.9);border:1px solid var(--bd2);border-radius:20px;
  padding:5px 13px;font-size:.66rem;color:var(--ac);
  backdrop-filter:blur(12px);pointer-events:none;}}
@keyframes cp{{0%{{transform:translate(-50%,-50%) scale(.5);opacity:1;}}
100%{{transform:translate(-50%,-50%) scale(3);opacity:0;}}}}
.cp{{position:absolute;width:26px;height:26px;border:2px solid var(--ac);border-radius:50%;
  pointer-events:none;animation:cp .6s ease-out forwards;z-index:500;}}
</style>
</head>
<body>
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
<div id="ch">🖱 지도 클릭 → 즉시 조회</div>
<script>
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

  kakao.maps.event.addListener(map, 'click', function(e) {{
    var lat = e.latLng.getLat(), lng = e.latLng.getLng();
    document.getElementById('cb').textContent =
      'LAT '+lat.toFixed(6)+'  ·  LNG '+lng.toFixed(6);
    document.getElementById('ch').style.display='none';
    placeMark(lat, lng);
    map.panTo(e.latLng);

    try {{
      var parentUrl = window.parent.location.href.split('?')[0];
      window.parent.location.href = parentUrl + '?lat=' + lat + '&lng=' + lng;
    }} catch(err) {{
      window.parent.postMessage({{type:'mapClick', lat:lat, lng:lng}}, '*');
    }}
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
  document.getElementById('map').appendChild(p);
  setTimeout(function(){{p.remove();}}, 700);
}}
</script>
</body>
</html>"""
    components.html(map_html, height=780, scrolling=False)
