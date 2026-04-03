import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(layout="wide")

# -------------------------------
# 1️⃣ 로컬 GeoJSON 불러오기
# -------------------------------
with open("서울중구.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# JSON 문자열로 변환
geojson_str = json.dumps(geojson_data)

# -------------------------------
# 2️⃣ HTML + Kakao Maps
# -------------------------------
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
var geojson = {geojson_str};

kakao.maps.load(function() {{

    var map = new kakao.maps.Map(document.getElementById('map'), {{
        center: new kakao.maps.LatLng(37.5636, 126.9976),
        level: 4
    }});

    var selectedPolygon = null;

    function pointInPolygon(point, vs) {{
        var x = point[0], y = point[1];
        var inside = false;

        for (var i = 0, j = vs.length - 1; i < vs.length; j = i++) {{
            var xi = vs[i][0], yi = vs[i][1];
            var xj = vs[j][0], yj = vs[j][1];

            var intersect = ((yi > y) != (yj > y))
                && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);

            if (intersect) inside = !inside;
        }}

        return inside;
    }}

    kakao.maps.event.addListener(map, 'click', function(mouseEvent) {{

        var lat = mouseEvent.latLng.getLat();
        var lng = mouseEvent.latLng.getLng();

        if (selectedPolygon) {{
            selectedPolygon.setMap(null);
        }}

        for (var f of geojson.features) {{

            var coords = f.geometry.coordinates;

            for (var polygonSet of coords) {{
                for (var ring of polygonSet) {{

                    if (pointInPolygon([lng, lat], ring)) {{

                        var path = ring.map(coord => 
                            new kakao.maps.LatLng(coord[1], coord[0])
                        );

                        selectedPolygon = new kakao.maps.Polygon({{
                            path: path,
                            strokeWeight: 2,
                            strokeColor: '#FF0000',
                            fillColor: '#FF0000',
                            fillOpacity: 0.3
                        }});

                        selectedPolygon.setMap(map);
                        return;
                    }}
                }}
            }}

        }}

        console.log("필지 없음");

    }});

}});
</script>
</body>
</html>
"""

# -------------------------------
# 3️⃣ Streamlit에서 렌더링
# -------------------------------
components.html(html_code, height=800)
