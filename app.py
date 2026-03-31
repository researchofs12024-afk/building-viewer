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
[data-testid="stHorizontalBlock"]{gap:0!important;}
[data-testid="column"]{padding:0!important;}
</style>""", unsafe_allow_html=True)

# ── 세션 상태 ────────────────────────────────────
for k, v in {
    "last_lat": None, "last_lng": None,
    "building_data": None, "current_addr": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── API 함수 ─────────────────────────────────────
def fetch_building(sigungu, bjdong, bun, ji):
    def mk_url(ep):
        qs = "&".join([
            f"sigunguCd={sigungu}", f"bjdongCd={bjdong}", "platGbCd=0",
            f"bun={str(bun).zfill(4)}", f"ji={str(ji or 0).zfill(4)}",
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
            return {"items": [{c.tag:(c.text or "") for c in i}
                               for i in root.findall(".//item")]}
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
        r = requests.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"x": lng, "y": lat}, timeout=5)
        docs = r.json().get("documents", [])
        return docs[0] if docs else {}
    except:
        return {}

def addr_search(query):
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"query": query, "size": 5}, timeout=5)
        return r.json().get("documents", [])
    except:
        return []

# ── query_params로 지도 클릭 수신 ────────────────
qp = st.query_params
if "lat" in qp and "lng" in qp:
    try:
        lat_v = float(qp["lat"])
        lng_v = float(qp["lng"])
        if lat_v != st.session_state.last_lat or lng_v != st.session_state.last_lng:
            st.session_state.last_lat = lat_v
            st.session_state.last_lng = lng_v
            addr_doc = coord2addr(lat_v, lng_v)
            land = addr_doc.get("address") or {}
            road = addr_doc.get("road_address") or {}
            display_addr = road.get("address_name") or land.get("address_name") or ""
            bc = land.get("b_code", "")
            st.session_state.current_addr = display_addr
            st.session_state.building_data = fetch_building(
                bc[:5], bc[5:10] if len(bc) >= 10 else "",
                land.get("main_address_no", "0"),
                land.get("sub_address_no", "0")
            )
            st.query_params.clear()
    except:
        pass

# ── 레이아웃 ─────────────────────────────────────
col_left, col_right = st.columns([10, 17], gap="small")

# ══════════════════════════════════════════════════
# 우측: 카카오맵
# ══════════════════════════════════════════════════
with col_right:
    # 지도 클릭 시 parent URL에 ?lat=..&lng=.. 추가 → Streamlit이 읽음
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

  // VWorld 지적도
  kakao.maps.Tileset.add('VW_LP', new kakao.maps.Tileset({{
    width:256, height:256, minZoom:1, maxZoom:21,
    getTileUrl: function(x,y,z) {{
      return 'https://api.vworld.kr/req/wmts/1.0.0/{VWORLD_KEY}/lp/'+z+'/'+y+'/'+x+'.png';
    }},
  }}));

  // 지도 클릭 → parent URL 변경 → Streamlit 인식
  kakao.maps.event.addListener(map, 'click', function(e) {{
    var lat = e.latLng.getLat(), lng = e.latLng.getLng();
    document.getElementById('cb').textContent =
      'LAT '+lat.toFixed(6)+'  ·  LNG '+lng.toFixed(6);
    document.getElementById('ch').style.display='none';
    placeMark(lat, lng);
    map.panTo(e.latLng);

    // ★ 핵심: parent(Streamlit) URL에 파라미터 추가 후 새로고침
    try {{
      var parentUrl = window.parent.location.href.split('?')[0];
      window.parent.location.href = parentUrl + '?lat=' + lat + '&lng=' + lng;
    }} catch(err) {{
      // cross-origin fallback: postMessage
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

# ══════════════════════════════════════════════════
# 좌측: 정보 패널
# ══════════════════════════════════════════════════
with col_left:
    # 헤더
    st.markdown("""
<div style="background:#0d1117;border-bottom:1px solid rgba(255,255,255,.07);
  padding:12px 14px;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:9px;">
    <div style="width:28px;height:28px;background:linear-gradient(135deg,#38bdf8,#10b981);
      border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px;">🏢</div>
    <div>
      <div style="font-size:.82rem;font-weight:700;color:#f0f6ff;">건축물대장 조회</div>
      <div style="font-size:.56rem;color:#484f58;font-family:monospace;">KAKAO MAPS · VWORLD</div>
    </div>
    <div style="margin-left:auto;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);
      color:#10b981;padding:2px 8px;border-radius:20px;font-size:.6rem;font-weight:600;">● LIVE</div>
  </div>
</div>""", unsafe_allow_html=True)

    # 주소 검색
    st.markdown('<p style="font-size:.62rem;font-weight:700;color:#38bdf8;letter-spacing:.1em;text-transform:uppercase;margin-bottom:5px;">🔍 주소 검색</p>', unsafe_allow_html=True)
    query = st.text_input("주소", placeholder="예: 강남구 테헤란로 152",
                          label_visibility="collapsed", key="addr_q")
    if st.button("검색", use_container_width=True, key="search_btn"):
        if query:
            with st.spinner("검색 중..."):
                results = addr_search(query)
            if results:
                for doc in results:
                    road = doc.get("road_address")
                    main = road["address_name"] if road else doc["address_name"]
                    sub  = doc["address_name"] if road else ""
                    btn_label = f"📍 {main}" + (f"\n↳ {sub}" if sub else "")
                    if st.button(btn_label, key=f"r_{doc['address_name']}", use_container_width=True):
                        lat = float(doc["y"]); lng = float(doc["x"])
                        with st.spinner("조회 중..."):
                            addr_doc = coord2addr(lat, lng)
                        land = addr_doc.get("address") or {}
                        road2= addr_doc.get("road_address") or {}
                        display_addr = road2.get("address_name") or land.get("address_name") or main
                        bc = land.get("b_code","")
                        st.session_state.current_addr = display_addr
                        with st.spinner("건축물대장 조회 중..."):
                            st.session_state.building_data = fetch_building(
                                bc[:5], bc[5:10] if len(bc)>=10 else "",
                                land.get("main_address_no","0"),
                                land.get("sub_address_no","0"))
                        st.rerun()
            else:
                st.warning("검색 결과가 없습니다.")

    st.divider()

    # 수동 PNU
    with st.expander("⚙️ 수동 PNU 코드 입력"):
        sg = st.text_input("시군구코드(5자리)", max_chars=5, placeholder="11680", key="psg")
        bd = st.text_input("법정동코드(5자리)", max_chars=5, placeholder="10300", key="pbd")
        c1, c2 = st.columns(2)
        with c1: bn = st.text_input("본번", placeholder="737", key="pbn")
        with c2: ji = st.text_input("부번", placeholder="0",   key="pji")
        if st.button("🏠 건축물대장 조회", use_container_width=True, key="manual_q"):
            if sg and bd:
                with st.spinner("조회 중..."):
                    st.session_state.building_data = fetch_building(sg, bd, bn or "0", ji or "0")
                st.session_state.current_addr = f"시군구:{sg} 법정동:{bd} ({bn}-{ji})"
                st.rerun()
            else:
                st.warning("시군구코드와 법정동코드를 입력해 주세요.")

    st.divider()

    # ── 건축물 정보 표시 ─────────────────────────────
    def fa(v):
        try: return f"{float(v):,.2f} ㎡"
        except: return v or "-"
    def fd(v):
        if v and len(v) == 8:
            return f"{v[:4]}.{v[4:6]}.{v[6:]}"
        return v or "-"

    if st.session_state.building_data is None:
        st.markdown("""
<div style="background:#161b22;border:1px dashed rgba(56,189,248,.15);border-radius:10px;
  padding:24px 14px;text-align:center;margin-top:8px;">
  <div style="font-size:1.8rem;margin-bottom:8px;">🗺️</div>
  <div style="font-size:.8rem;font-weight:600;color:#c9d1d9;margin-bottom:5px;">지도를 클릭하세요</div>
  <div style="font-size:.7rem;color:#484f58;line-height:1.7;">
    지도의 원하는 위치를 클릭하면<br>
    <strong style="color:#38bdf8;">건축물대장 정보</strong>가 표시됩니다.
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;padding-top:12px;
    border-top:1px solid rgba(255,255,255,.07);justify-content:center;">
    <span style="display:flex;align-items:center;gap:3px;font-size:.62rem;color:#484f58;">
      <span style="width:7px;height:7px;background:#38bdf8;border-radius:2px;display:inline-block;"></span>일반지도
    </span>
    <span style="display:flex;align-items:center;gap:3px;font-size:.62rem;color:#484f58;">
      <span style="width:7px;height:7px;background:#f59e0b;border-radius:2px;display:inline-block;"></span>위성지도
    </span>
    <span style="display:flex;align-items:center;gap:3px;font-size:.62rem;color:#484f58;">
      <span style="width:7px;height:7px;background:#10b981;border-radius:2px;display:inline-block;"></span>지적도
    </span>
  </div>
</div>""", unsafe_allow_html=True)

    else:
        bd_data = st.session_state.building_data
        addr    = st.session_state.current_addr

        if "error" in bd_data:
            st.error(f"오류: {bd_data['error']}")
        else:
            basis_items = bd_data.get("basis", {}).get("items", [])
            title_items = bd_data.get("title", {}).get("items", [])

            if not basis_items and not title_items:
                st.warning("해당 위치의 건축물 정보가 없습니다.")
            else:
                if addr:
                    st.caption(f"📍 {addr}")

                for item in basis_items:
                    bld_nm  = item.get("bldNm") or "건물명 미등록"
                    use_nm  = item.get("mainPurpsCdNm") or item.get("mainPurpsCd") or "-"
                    strct   = item.get("strctCdNm") or item.get("strctCd") or "-"
                    grnd_fl = item.get("grndFlCnt") or "-"
                    undr_fl = item.get("undgrndFlCnt") or "0"

                    st.markdown(f"""
<div style="background:#161b22;border:1px solid rgba(56,189,248,.15);border-radius:10px;
  padding:13px;margin-bottom:10px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:9px;">
    <div style="width:30px;height:30px;background:linear-gradient(135deg,rgba(56,189,248,.15),rgba(16,185,129,.15));
      border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:13px;
      border:1px solid rgba(56,189,248,.15);">🏢</div>
    <div>
      <div style="font-size:.82rem;font-weight:700;color:#f0f6ff;">{bld_nm}</div>
      <div style="font-size:.65rem;color:#484f58;">{addr}</div>
    </div>
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:9px;">
    <span style="background:rgba(56,189,248,.12);color:#38bdf8;border:1px solid rgba(56,189,248,.2);
      font-size:.6rem;font-weight:600;padding:2px 6px;border-radius:4px;">{use_nm}</span>
    <span style="background:rgba(16,185,129,.12);color:#10b981;border:1px solid rgba(16,185,129,.2);
      font-size:.6rem;font-weight:600;padding:2px 6px;border-radius:4px;">{strct}</span>
    <span style="background:rgba(245,158,11,.12);color:#f59e0b;border:1px solid rgba(245,158,11,.2);
      font-size:.6rem;font-weight:600;padding:2px 6px;border-radius:4px;">
      지상 {grnd_fl}층/지하 {undr_fl}층</span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:7px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:2px;">연면적</div>
      <div style="font-size:.73rem;color:#38bdf8;font-family:monospace;">{fa(item.get("totArea"))}</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:7px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:2px;">건축면적</div>
      <div style="font-size:.73rem;color:#c9d1d9;font-family:monospace;">{fa(item.get("archArea"))}</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:7px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:2px;">대지면적</div>
      <div style="font-size:.73rem;color:#c9d1d9;font-family:monospace;">{fa(item.get("platArea"))}</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:7px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:2px;">건폐율/용적률</div>
      <div style="font-size:.73rem;color:#c9d1d9;font-family:monospace;">{item.get("bcRat") or "-"}%/{item.get("vlRat") or "-"}%</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:7px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:2px;">허가일</div>
      <div style="font-size:.73rem;color:#c9d1d9;font-family:monospace;">{fd(item.get("pmsDay"))}</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:7px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:2px;">사용승인일</div>
      <div style="font-size:.73rem;color:#c9d1d9;font-family:monospace;">{fd(item.get("useAprDay"))}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

                if title_items:
                    st.markdown('<p style="font-size:.6rem;font-weight:700;color:#38bdf8;letter-spacing:.1em;text-transform:uppercase;margin:6px 0 5px;">표제부 상세</p>', unsafe_allow_html=True)
                    for t in title_items[:3]:
                        st.markdown(f"""
<div style="background:#161b22;border:1px solid rgba(16,185,129,.15);border-radius:10px;padding:11px;margin-bottom:7px;">
  <div style="font-size:.78rem;font-weight:700;color:#f0f6ff;margin-bottom:7px;">
    📦 {t.get("dongNm") or "주동"} — {t.get("mainPurpsCdNm") or "-"}
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:6px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:1px;">세대수</div>
      <div style="font-size:.72rem;color:#c9d1d9;font-family:monospace;">{t.get("hhldCnt") or "-"} 세대</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:6px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:1px;">가구수</div>
      <div style="font-size:.72rem;color:#c9d1d9;font-family:monospace;">{t.get("fmlyCnt") or "-"} 가구</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:6px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:1px;">승강기(일반/비상)</div>
      <div style="font-size:.72rem;color:#c9d1d9;font-family:monospace;">{t.get("elvtCnt") or "-"}/{t.get("emgenElevCnt") or "-"}</div>
    </div>
    <div style="background:#07090f;border:1px solid rgba(255,255,255,.04);border-radius:5px;padding:6px;">
      <div style="font-size:.55rem;font-weight:600;color:#484f58;text-transform:uppercase;margin-bottom:1px;">자주식 주차</div>
      <div style="font-size:.72rem;color:#c9d1d9;font-family:monospace;">{t.get("indrAutoUtcnt") or "-"} 대</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        if st.button("↺ 초기화", use_container_width=True):
            st.session_state.building_data = None
            st.session_state.current_addr = ""
            st.session_state.last_lat = None
            st.session_state.last_lng = None
            st.rerun()
