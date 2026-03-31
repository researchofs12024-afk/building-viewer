import streamlit as st
import streamlit.components.v1 as components
import requests

st.set_page_config(layout="wide")

# API 키 설정 (질문자님 키 유지)
KAKAO_JS_KEY     = "057a4a253017791fe6072d7b089a063a"
KAKAO_REST_KEY   = "c5af33c0d1d6a654362d3fea152cc076"

# ── 1. 좌표를 주소로 바꾸는 함수 ──────────────────────
def coord2addr(lat, lng):
    try:
        url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_KEY}"}
        params = {"x": lng, "y": lat}
        r = requests.get(url, headers=headers, params=params, timeout=5)
        res = r.json()
        if res.get("documents"):
            return res["documents"][0].get("address", {}).get("address_name", "주소 없음")
        return "주소를 찾을 수 없는 위치입니다."
    except Exception as e:
        return f"오류 발생: {e}"

# ── 2. 지도 클릭 신호 감지 (Query Params) ─────────────
# 지도가 window.parent.location.href를 통해 보낸 좌표를 읽습니다.
qp = st.query_params
clicked_lat = qp.get("lat")
clicked_lng = qp.get("lng")

# ── 3. 화면 레이아웃 ──────────────────────────────────
col_left, col_right = st.columns([1, 2])

with col_left:
    st.title("📍 주소 추출 테스트")
    st.write("지도를 클릭하면 아래에 주소가 나타납니다.")
    
    if clicked_lat and clicked_lng:
        st.success(f"클릭한 좌표: {clicked_lat}, {clicked_lng}")
        # 주소 변환 실행
        with st.spinner("주소 변환 중..."):
            address = coord2addr(clicked_lat, clicked_lng)
        st.subheader(f"🏠 주소: {address}")
    else:
        st.info("지도를 클릭해 주세요.")

with col_right:
    # 질문자님의 원래 지도 로직 (수정 없이 그대로 사용)
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
        <style>
            #map {{ width: 100%; height: 600px; }}
            .info-box {{ position:absolute; bottom:10px; left:50%; transform:translateX(-50%); 
                         background:rgba(0,0,0,0.7); color:white; padding:5px 10px; 
                         border-radius:15px; font-size:12px; z-index:10; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="info-box" id="coord-display">지도를 클릭하세요</div>
        <script>
            var container = document.getElementById('map');
            var options = {{ center: new kakao.maps.LatLng(37.5665, 126.9780), level: 3 }};
            var map = new kakao.maps.Map(container, options);
            var marker = new kakao.maps.Marker({{ map: map }});

            kakao.maps.event.addListener(map, 'click', function(e) {{
                var lat = e.latLng.getLat();
                var lng = e.latLng.getLng();
                
                // 하단 텍스트 표시
                document.getElementById('coord-display').textContent = 'LAT: ' + lat.toFixed(6) + ' / LNG: ' + lng.toFixed(6);
                
                // 마커 이동
                marker.setPosition(e.latLng);

                // 핵심: Streamlit 부모 창의 URL을 변경하여 값을 전달
                var parentUrl = window.parent.location.href.split('?')[0];
                window.parent.location.href = parentUrl + '?lat=' + lat + '&lng=' + lng;
            }});
        </script>
    </body>
    </html>
    """
    components.html(map_html, height=650)
