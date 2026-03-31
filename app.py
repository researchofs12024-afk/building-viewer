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

KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"
BUILDING_API_KEY = "9619e124e16b9e57bad6cfefdc82f6c87749176260b4caff32eda964aad5de1b"
VWORLD_KEY       = "F12043F0-86DF-3395-9004-27A377FD5FB6"

# CSS 디자인 유지
st.markdown("""
<style>
#MainMenu,footer,header,.stDeployButton{display:none!important;}
.block-container{padding:0!important;margin:0!important;max-width:100%!important;}
.stApp{background:#07090f!important;}
iframe{border:none!important;}
</style>""", unsafe_allow_html=True)

# ── API 함수 ─────────────────────────────────────
def coord2addr(lat, lng):
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"x": lng, "y": lat}, timeout=5)
        docs = r.json().get("documents", [])
        return docs[0] if docs else {}
    except: return {}

# ── 지도 클릭 수신 로직 ───────────────────────────
# URL 파라미터 읽기
qp = st.query_params
if "lat" in qp and "lng" in qp:
    lat_v = qp["lat"]
    lng_v = qp["lng"]
    addr_doc = coord2addr(lat_v, lng_v)
    land = addr_doc.get("address") or {}
    st.session_state.current_addr = land.get("address_name", f"좌표: {lat_v}, {lng_v}")
else:
    if "current_addr" not in st.session_state:
        st.session_state.current_addr = "지도를 클릭하세요"

# ── 레이아웃 ─────────────────────────────────────
col_left, col_right = st.columns([10, 17])

with col_left:
    st.markdown(f"""
    <div style="padding:20px; color:white;">
        <h3>📍 주소 정보</h3>
        <div style="background:#161b22; padding:15px; border-radius:10px; border:1px solid #38bdf833;">
            {st.session_state.current_addr}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # 지도 로직 수정 포인트:
    # 1. 스크립트 호출 시 https 명시
    # 2. window.parent.location.href 차단 우회 (target='_top' 사용)
    map_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<!-- HTTPS 명시 및 스크립트 로드 방식 최적화 -->
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services&autoload=false"></script>
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
.lb.on{{background:rgba(56,189,248,.15);border-color:var(--ac);color:var(--ac);}}
#cb{{position:absolute;bottom:12px;left:50%;transform:translateX(-50%);z-index:400;
  background:rgba(7,9,15,.88);border:1px solid var(--bd);border-radius:20px;
  padding:4px 12px;font-family:monospace;font-size:.61rem;color:var(--t3);
  backdrop-filter:blur(12px);pointer-events:none;white-space:nowrap;}}
</style>
</head>
<body>
<div id="map"></div>
<div id="lc">
  <button class="lb on" id="b1" onclick="setT('road')">🗺 일반</button>
  <button class="lb" id="b2" onclick="setT('sky')">🛰 위성</button>
</div>
<div id="cb">지도를 클릭하면 주소를 가져옵니다</div>
<script>
var map, marker;

// kakao.maps.load를 사용하여 라이브러리가 완전히 로드된 후 실행
kakao.maps.load(function() {{
  var container = document.getElementById('map');
  var options = {{
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level: 4
  }};
  map = new kakao.maps.Map(container, options);
  marker = new kakao.maps.Marker({{ map: map }});

  kakao.maps.event.addListener(map, 'click', function(e) {{
    var lat = e.latLng.getLat();
    var lng = e.latLng.getLng();
    marker.setPosition(e.latLng);
    
    // Streamlit Cloud의 Sandbox 보안 정책 때문에 window.parent.location 직접 수정은 차단됨
    // 우회 방법: <a> 태그를 생성하여 _top으로 클릭 이벤트 발생
    var parentUrl = window.location.ancestorOrigins && window.location.ancestorOrigins[0] 
                    ? window.location.ancestorOrigins[0] 
                    : window.parent.location.origin;
    
    // 현재 URL의 쿼리스트링을 제거한 순수 경로 추출
    var baseUrl = window.parent.location.href.split('?')[0];
    var targetUrl = baseUrl + '?lat=' + lat + '&lng=' + lng;

    var link = document.createElement('a');
    link.href = targetUrl;
    link.target = '_top'; // 부모 창 전체를 리다이렉트
    link.click();
  }});
}});

function setT(t) {{
  map.setMapTypeId(t==='road' ? kakao.maps.MapTypeId.ROADMAP : kakao.maps.MapTypeId.SKYVIEW);
  document.getElementById('b1').classList.toggle('on', t==='road');
  document.getElementById('b2').classList.toggle('on', t==='sky');
}}
</script>
</body>
</html>"""
    components.html(map_html, height=780, scrolling=False)
