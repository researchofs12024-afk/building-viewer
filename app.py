import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

html_code = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=057a4a253017791fe6072d7b089a063a&autoload=false"></script>
</head>

<body>
<div id="map" style="width:100%;height:100vh;"></div>

<script>

var geojson = null;

kakao.maps.load(function() {

    var map = new kakao.maps.Map(document.getElementById('map'), {
        center: new kakao.maps.LatLng(37.5636, 126.9976),
        level: 4
    });

    // 🔥 GeoJSON fetch
    fetch("서울중구.geojson")
    .then(res => res.json())
    .then(data => {
        geojson = data;
        console.log("GeoJSON loaded");
    });

    var selectedPolygon = null;

    function pointInPolygon(point, vs) {
        var x = point[0], y = point[1];
        var inside = false;

        for (var i = 0, j = vs.length - 1; i < vs.length; j = i++) {
            var xi = vs[i][0], yi = vs[i][1];
            var xj = vs[j][0], yj = vs[j][1];

            var intersect = ((yi > y) != (yj > y))
                && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);

            if (intersect) inside = !inside;
        }

        return inside;
    }

    kakao.maps.event.addListener(map, 'click', function(mouseEvent) {

        if (!geojson) {
            alert("데이터 로딩 중...");
            return;
        }

        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();

        if (selectedPolygon) {
            selectedPolygon.setMap(null);
        }

        for (var f of geojson.features) {

            var coords = f.geometry.coordinates;

            for (var polygonSet of coords) {
                for (var ring of polygonSet) {

                    if (pointInPolygon([lng, lat], ring)) {

                        var path = ring.map(coord => 
                            new kakao.maps.LatLng(coord[1], coord[0])
                        );

                        selectedPolygon = new kakao.maps.Polygon({
                            path: path,
                            strokeWeight: 2,
                            strokeColor: '#FF0000',
                            fillColor: '#FF0000',
                            fillOpacity: 0.3
                        });

                        selectedPolygon.setMap(map);
                        return;
                    }
                }
            }

        }

        console.log("필지 없음");

    });

});
</script>

</body>
</html>
"""

components.html(html_code, height=800)
