import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# 🔥 반드시 JavaScript 키 넣어라 (REST 키 X)
KAKAO_JS_KEY = "여기에_JS키"

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">

<!-- 🔥 반드시 https -->
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}"></script>

<style>
html, body {{
    margin:0;
    padding:0;
    height:100%;
}}
#map {{
    width:100%;
    height:100%;
}}
#info {{
    position:absolute;
    top:10px;
    left:10px;
    z-index:999;
    background:white;
    padding:10px;
    border-radius:8px;
    font-size:14px;
}}
</style>
</head>

<body>

<div id="map"></div>
<div id="info">지도를 클릭하세요</div>

<script>
var mapContainer = document.getElementById('map');

var mapOption = {{
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level: 3
}};

var map = new kakao.maps.Map(mapContainer, mapOption);

var marker;

// 클릭 이벤트
kakao.maps.event.addListener(map, 'click', function(mouseEvent) {{

    var latlng = mouseEvent.latLng;
    var lat = latlng.getLat();
    var lng = latlng.getLng();

    // 마커 표시
    if (marker) {{
        marker.setMap(null);
    }}

    marker = new kakao.maps.Marker({{
        position: latlng
    }});

    marker.setMap(map);

    // 좌표 표시
    document.getElementById('info').innerHTML =
        "위도: " + lat.toFixed(6) + "<br>경도: " + lng.toFixed(6);
}});
</script>

</body>
</html>
"""

components.html(html, height=800)
