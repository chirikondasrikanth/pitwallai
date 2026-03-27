"""
download_assets.py - Downloads 4 images per F1 circuit
Run from: C:/Users/srika/Downloads/f1_platform_v2/f1_platform
"""

import os, urllib.request

os.makedirs("dashboard/assets/circuits", exist_ok=True)

CIRCUIT_IMAGES = {
    "japanese":  ["https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=1920&q=90","https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=1920&q=90","https://images.unsplash.com/photo-1480796927426-f609979314bd?w=1920&q=90","https://images.unsplash.com/photo-1490806843957-31f4c9a91c65?w=1920&q=90"],
    "australian":["https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920&q=90","https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=90","https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?w=1920&q=90","https://images.unsplash.com/photo-1572825739459-0ed3bffe8e2a?w=1920&q=90"],
    "chinese":   ["https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=1920&q=90","https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=1920&q=90","https://images.unsplash.com/photo-1537523836300-9f6e2291abb0?w=1920&q=90","https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=1920&q=90"],
    "bahrain":   ["https://images.unsplash.com/photo-1466442929976-97f336a657be?w=1920&q=90","https://images.unsplash.com/photo-1451337516015-6b6e9a44a8a3?w=1920&q=90","https://images.unsplash.com/photo-1512632578888-169bbbc64f33?w=1920&q=90","https://images.unsplash.com/photo-1548199569-6b2c9bb8b07b?w=1920&q=90"],
    "monaco":    ["https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=1920&q=90","https://images.unsplash.com/photo-1514890547357-a9ee288728e0?w=1920&q=90","https://images.unsplash.com/photo-1592853625601-e72c4b22bff1?w=1920&q=90","https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1920&q=90"],
    "british":   ["https://images.unsplash.com/photo-1500829243541-74b677fecc30?w=1920&q=90","https://images.unsplash.com/photo-1486299267070-83823f5448dd?w=1920&q=90","https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=1920&q=90","https://images.unsplash.com/photo-1520986606214-8b456906c813?w=1920&q=90"],
    "italian":   ["https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=1920&q=90","https://images.unsplash.com/photo-1515542622106-078bda21f01f?w=1920&q=90","https://images.unsplash.com/photo-1534445867742-43195f401b6c?w=1920&q=90","https://images.unsplash.com/photo-1506377872008-6645d9d29ef7?w=1920&q=90"],
    "singapore": ["https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1920&q=90","https://images.unsplash.com/photo-1508964942454-1a56651d54ac?w=1920&q=90","https://images.unsplash.com/photo-1501952476817-d7ae22e8ee4e?w=1920&q=90","https://images.unsplash.com/photo-1565967511849-76a60a516170?w=1920&q=90"],
    "lasvegas":  ["https://images.unsplash.com/photo-1581351721010-8cf859cb14a4?w=1920&q=90","https://images.unsplash.com/photo-1605833556294-ea5c7a74f57d?w=1920&q=90","https://images.unsplash.com/photo-1568515387631-8b650bbcdb90?w=1920&q=90","https://images.unsplash.com/photo-1531347468851-0d81a2c79b40?w=1920&q=90"],
    "abudhabi":  ["https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1920&q=90","https://images.unsplash.com/photo-1548245563-8a557e4e8d16?w=1920&q=90","https://images.unsplash.com/photo-1580674684081-7617fbf3d745?w=1920&q=90","https://images.unsplash.com/photo-1582672060674-bc2bd808a8b5?w=1920&q=90"],
    "miami":     ["https://images.unsplash.com/photo-1514214246283-d427a95c5d2f?w=1920&q=90","https://images.unsplash.com/photo-1533106418989-88406c7cc8ca?w=1920&q=90","https://images.unsplash.com/photo-1506966953602-c20cc11f75e3?w=1920&q=90","https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=1920&q=90"],
    "belgian":   ["https://images.unsplash.com/photo-1476067897447-d28b660ec3a4?w=1920&q=90","https://images.unsplash.com/photo-1491557345352-5929e343eb89?w=1920&q=90","https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=1920&q=90","https://images.unsplash.com/photo-1582553032777-56d2cb5c9d26?w=1920&q=90"],
    "saudi":     ["https://images.unsplash.com/photo-1586861256632-a2baa6af0a25?w=1920&q=90","https://images.unsplash.com/photo-1578895101408-1a36b834405b?w=1920&q=90","https://images.unsplash.com/photo-1591604466107-ec97de577aff?w=1920&q=90","https://images.unsplash.com/photo-1547981609-4b6bfe67ca0b?w=1920&q=90"],
    "canadian":  ["https://images.unsplash.com/photo-1534430480872-3498386e7856?w=1920&q=90","https://images.unsplash.com/photo-1517935706615-2717063c2225?w=1920&q=90","https://images.unsplash.com/photo-1507992781348-310259076fe0?w=1920&q=90","https://images.unsplash.com/photo-1519832979-6fa011b87667?w=1920&q=90"],
    "austrian":  ["https://images.unsplash.com/photo-1527576539890-dfa815648363?w=1920&q=90","https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=90","https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=1920&q=90","https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920&q=90"],
}

print("\n" + "="*55)
print("  Downloading 4 Circuit Images Per GP")
print("="*55)

headers = {"User-Agent": "Mozilla/5.0"}
total = 0

for circuit, urls in CIRCUIT_IMAGES.items():
    print(f"\n  📸 {circuit.upper()}")
    for i, url in enumerate(urls, 1):
        path = f"dashboard/assets/circuits/{circuit}_{i}.jpg"
        if os.path.exists(path):
            print(f"     ✅ Already exists: {circuit}_{i}.jpg")
            total += 1
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            print(f"     ✅ {circuit}_{i}.jpg ({len(data)//1024} KB)")
            total += 1
        except Exception as e:
            print(f"     ❌ {circuit}_{i}: {e}")

print(f"\n{'='*55}")
print(f"  ✅ Downloaded {total} images")
print(f"  📁 Saved to: dashboard/assets/circuits/")
print(f"{'='*55}")