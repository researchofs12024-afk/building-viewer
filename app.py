import streamlit as st
import streamlit.components.v1 as components
import requests
import xml.etree.ElementTree as ET
import json

st.set_page_config(page_title="건축물대장 조회 시스템", layout="wide")

KAKAO_JS_KEY     = "여기에_JS키"
KAKAO_REST_KEY   = "여기에_REST키"
BUILDING_API_KEY = "여기에_건축물API키"

# ---------------- API ----------------
def fetch_building(sigungu, bjdong, bun, ji):
    def mk_url(ep):
        qs = "&".join([
            f"sigunguCd={sigungu}",
            f"bjdongCd={bjdong}",
            "platGbCd=0",
            f"bun={str(bun).zfill(4)}",
            f"ji={str(ji).zfill(4)}",
            f"serviceKey={BUILDING_API_KEY}",
        ])
        return f"http://apis.data.go.kr/1613000/BldRgstService_v2/{ep}?{qs}"

    def parse(txt):
        try:
            root = ET.fromstring(txt)
            return {
                "items": [
                    {c.tag: (c.text or "") for c in i}
                    for i in root.findall(".//item")
                ]
            }
        except:
            return {"items": []}

    try:
        r1 = requests.get(mk_url("getBrBasisOulnInfo"))
        r2 = requests.get(mk_url("getBrTitleInfo"))
        return {"basis": parse(r1.text), "title": parse(r2.text)}
    except:
        return {"basis": {"items": []}, "title": {"items": []}}


def coord2addr(lat, lng):
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"x": lng, "y": lat},
        )
        data = r.json()
        docs = data.get("documents", [])
        return docs[0] if docs else {}
    except:
        return {}


def addr_search(q):
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            params={"query": q},
        )
        return r.json().get("documents", [])
    except:
        return []


# ---------------- JSON 응답 ----------------
def json_resp(data):
    st.write(json.dumps(data, ensure_ascii=False))
    st.stop()


# ---------------- Router ----------------
qp = st.query_params
action = qp.get("action", "")

if action == "click":
    lat = float(qp.get("lat", 0))
    lng = float(qp.get("lng", 0))

    doc = coord2addr(lat, lng)
    land = doc.get("address") or {}
    road = doc.get("road_address") or {}

    addr = road.get("address_name") or land.get("address_name") or ""
    bc   = land.get("b_code", "")

    if len(bc) < 10:
        json_resp({"error": "b_code 없음", "addr": addr})

    res = fetch_building(
        bc[:5],
        bc[5:10],
        land.get("main_address_no", "0"),
        land.get("sub_address_no", "0"),
    )

    res["addr"] = addr
    json_resp(res)

elif action == "search":
    json_resp(addr_search(qp.get("q", "")))

# ---------------- HTML ----------------
html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
<style>
html,body,#map{{height:100%;margin:0}}
</style>
</head>
<body>
<div id="map"></div>

<script>
const BASE = window.parent.location.href.split('?')[0];

async function callPy(params) {{
  const res = await fetch(BASE + '?' + new URLSearchParams(params));
  const text = await res.text();
  return JSON.parse(text);
}}

var map = new kakao.maps.Map(document.getElementById('map'), {{
  center: new kakao.maps.LatLng(37.5665,126.9780),
  level:3
}});

var marker;

kakao.maps.event.addListener(map, 'click', async function(e) {{
  var lat = e.latLng.getLat();
  var lng = e.latLng.getLng();

  if(marker) marker.setMap(null);
  marker = new kakao.maps.Marker({{position:e.latLng,map:map}});

  try {{
    const res = await callPy({{action:'click', lat:lat, lng:lng}});
    alert(JSON.stringify(res, null, 2));
  }} catch(e) {{
    alert("에러: " + e.message);
  }}
}});
</script>
</body>
</html>
"""

components.html(html, height=700)
