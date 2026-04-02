import streamlit as st
import streamlit.components.v1 as components
import requests
import json

st.set_page_config(layout="wide")
st.title("Kakao Parcel Viewer (CORS 해결 완성형)")

# -----------------------------
# 🔥 Python → VWorld 호출 함수
# -----------------------------
def get_parcel(bbox):
    url = f"https://api.vworld.kr/req/wfs?key=F12043F0-86DF-3395-9004-27A377FD5FB6&service=WFS&request=GetFeature&typename=lp_pa_cbnd_bonbun&output=application/json&bbox={bbox}"
    res = requests.get(url)
    return res.json()

# -----------------------------
# 🔥 Streamlit 세션 저장
# -----------------------------
if "geojson" not in st.session_state:
    st.session_state.geojson = None

# -----------------------------
# 🔥 JS → Python 데이터 받기
# -----------------------------
bbox = st.query_params.get("bbox")

if bbox:
    data = get_parcel(bbox)
    st.session_state.geojson = data

# -----------------------------
# 🔥 지도 HTML
# -----------------------------
geojson_data = json.dumps(st.session_state.geojson) if st.session_state.geojson else "null"

html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">

<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=057a4a253017791fe6072d7b089a063a&autoload=false"></script>
</head>

<body>
<div id="map" style="width:100%;height:100vh;"></div>

<script>
kakao.maps.load(function() {{

    var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 2
    }});

    var polygons = [];

    function drawGeoJSON(data) {{
        if (!data) return;

        polygons.forEach(p => p.setMap(null));
        polygons = [];

        data.features.forEach(feature => {{

            var coords = feature.geometry.coordinates;

            coords.forEach(polygonSet => {{
                polygonSet.forEach(ring => {{

                    var path = ring.map(coord => {{
                        return new kakao.maps.LatLng(coord[1], coord[0]);
                    }});

                    var polygon = new kakao.maps.Polygon({{
                        path: path,
                        strokeWeight: 2,
                        strokeColor: '#FF0000',
                        fillColor: '#FF0000',
                        fillOpacity: 0.3
                    }});

                    polygon.setMap(map);
                    polygons.push(polygon);

                }});
            }});

        }});
    }}

    // 🔥 기존 데이터 있으면 바로 그림
    var geojson = {geojson_data};
    drawGeoJSON(geojson);

    // 🔥 클릭 이벤트 → Streamlit으로 bbox 전달
    kakao.maps.event.addListener(map, 'click', function(mouseEvent) {{

        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();

        var bbox = (lng-0.0003) + "," + (lat-0.0003) + "," + (lng+0.0003) + "," + (lat+0.0003);

        // 🔥 페이지 reload 방식 (Streamlit 호환)
        window.location.search = "?bbox=" + bbox;

    }});

}});
</script>

</body>
</html>
"""

components.html(html_code, height=800)
