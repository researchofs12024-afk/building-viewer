import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

html_code = """
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
kakao.maps.load(function() {

    var map = new kakao.maps.Map(document.getElementById('map'), {
        center: new kakao.maps.LatLng(37.5665, 126.9780),
        level: 2
    });

    var polygons = [];

    // 🔥 JSONP 콜백 함수
    window.vworldCallback = function(data) {

        polygons.forEach(p => p.setMap(null));
        polygons = [];

        if (!data || !data.features) return;

        data.features.forEach(feature => {

            var coords = feature.geometry.coordinates;

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
    };

    kakao.maps.event.addListener(map, 'click', function(mouseEvent) {

        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();

        var bbox = (lng-0.0003) + "," + (lat-0.0003) + "," + (lng+0.0003) + "," + (lat+0.0003);

        // 🔥 기존 script 제거
        var oldScript = document.getElementById("vworldScript");
        if (oldScript) oldScript.remove();

        // 🔥 JSONP 요청
        var script = document.createElement("script");
        script.id = "vworldScript";
        script.src = "https://api.vworld.kr/req/wfs?" +
            "key=F12043F0-86DF-3395-9004-27A377FD5FB6" +
            "&service=WFS" +
            "&request=GetFeature" +
            "&typename=lp_pa_cbnd_bonbun" +
            "&output=application/json" +
            "&bbox=" + bbox +
            "&callback=vworldCallback";

        document.body.appendChild(script);

    });

});
</script>

</body>
</html>
"""

components.html(html_code, height=800)
