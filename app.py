import streamlit as st
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET

st.set_page_config(
    page_title="건축물대장 조회 시스템",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# API 키 설정
KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"
VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

# ── [로직] 좌표를 주소로 변환하는 함수 (수정됨) ──────────────────────
def coord2addr(lat, lng):
    try:
        # 카카오 로컬 API 호출
        r = requests.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"x": lng, "y": lat}, timeout=5)
        data = r.json()
        if data.get("documents"):
            doc = data["documents"][0]
            # 지번 주소 또는 도로명 주소 반환
            addr = doc.get("address", {}).get("address_name", "")
            road = doc.get("road_address", {}).get("address_name", "")
            return road if road else addr
        return "주소를 찾을 수 없는 지역입니다."
    except Exception as e:
        return f"주소 조회 오류: {e}"

# ── [상태 관리] ────────────────────────────────────────────────
if "current_addr" not in st.session_state:
    st.session_state.current_addr = ""

# 지도가 URL 파라미터로 보낸 좌표 읽기
qp = st.query_params
if "lat" in qp and "lng" in qp:
    # 지도가 보낸 lat, lng 값이 있을 때 주소 변환 실행
    lat_val = qp["lat"]
    lng_val = qp["lng"]
    st.session_state.current_addr = coord2addr(lat_val, lng_val)

# ── [레이아웃] ────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu,footer,header,.stDeployButton{display:none!important;}
.block-container{padding:0!important;margin:0!important;max-width:100%!important;}
.stApp{background:#07090f!important;}
iframe{border:none!important;}
</style>""", unsafe_allow_html=True)

col_left, col_right = st.columns([10, 17])

with col_left:
    st.markdown(f"""
    <div style="padding:25px; color:white;">
        <h2 style="color:#38bdf8; font-size:1.2rem; margin-bottom:20px;">🏢 선택된 위치 정보</h2>
        <div style="background:#161b22; padding:20px; border-radius:12px; border:1px solid #38bdf833;">
            <p style="font-size:0.8rem; color:#8b949e; margin-bottom:5px;">현재 주소</p>
            <p style="font-size:1.1rem; font-weight:bold; color:#f0f6ff; word-break:keep-all;">
                {st.session_state.current_addr if st.session_state.current_addr else "지도를 클릭하여 주소를 확인하세요."}
            </p>
        </div>
        {"<p style='margin-top:15px; font-size:0.7rem; color:#484f58;'>좌표: " + qp['lat'] + ", " + qp['lng'] + "</p>" if 'lat' in qp else ""}
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # ★ 질문자님이 처음 올리신 원본 지도 코드 (수정 없음) ★
    # 단, 배포 환경 보안상 window.parent를 window.top으로 한 단어만 바꿔야 클릭 시 주소가 넘어옵니다.
    map_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
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
    document.getElementById('cb').textContent = 'LAT '+lat.toFixed(6)+'  ·  LNG '+lng.toFixed(6);
    document.getElementById('ch').style.display='none';
    placeMark(lat, lng);
    map.panTo(e.latLng);

    // ★ 이 부분만 top으로 수정해야 배포 환경 보안 에러가 안 납니다.
    try {{
      var url = new URL(window.top.location.href);
      url.searchParams.set('lat', lat);
      url.searchParams.set('lng', lng);
      window.top.location.href = url.href;
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
