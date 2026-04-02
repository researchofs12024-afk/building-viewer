import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("Building Viewer (Kakao + Parcel Highlight)")

html_code = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">

<!-- 🔥 Mixed Content 방지 -->
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">

<!-- 카카오맵 (autoload=false 필수) -->
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=057a4a253017791fe6072d7b089a063a&libraries=services&autoload=false"></script>

</head>

<body>
<div id="map" style="width:100%;height:100vh;"></div>

<script>
kakao.maps.load(function() {

    var mapContainer = document.getElementById('map');
    var mapOption = {
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 2
    };

    var map = new kakao.maps.Map(mapContainer, mapOption);

    var polygons = [];

    // 🔥 지도 클릭 이벤트
    kakao.maps.event.addListener(map, 'click', function(mouseEvent) {

        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();

        // bbox 생성
        var bbox = (lng-0.0003) + "," + (lat-0.0003) + "," + (lng+0.0003) + "," + (lat+0.0003);

        var url = "https://api.vworld.kr/req/wfs?" +
            "key=F12043F0-86DF-3395-9004-27A377FD5FB6" +
            "&service=WFS" +
            "&request=GetFeature" +
            "&typename=lp_pa_cbnd_bonbun" +
            "&output=application/json" +
            "&bbox=" + bbox;

        fetch(url)
        .then(res => res.json())
        .then(data => {

            // 🔥 이전 폴리곤 삭제 (누적 원하면 이 줄 제거)
            polygons.forEach(p => p.setMap(null));
            polygons = [];

            data.features.forEach(feature => {

                var coords = feature.geometry.coordinates;

                // MultiPolygon 대응
                coords.forEach(polygonSet => {
                    polygonSet.forEach(ring => {

                        var path = ring.map(coord => {
                            return new kakao.maps.LatLng(coord[1], coord[0]);
                        });

                        var polygon = new kakao.maps.Polygon({
                            path: path,
                            strokeWeight: 2,
                            strokeColor: '#FF0000',
                            fillColor: '#FF0000',
                            fillOpacity: 0.3
                        });

                        polygon.setMap(map);
                        polygons.push(polygon);

                    });
                });

            });

        });

    });

});
</script>

</body>
</html>
"""

components.html(html_code, height=800)
