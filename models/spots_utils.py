import math
from models.weather import PREFECTURE_COORDS

def calculate_distance(lat1, lon1, lat2, lon2):
    """2点間の距離(km)を計算する (球面三角法)"""
    R = 6371.0 # 地球の半径 km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance

def estimate_bortle_scale(lat, lng):
    """
    緯度経度から大まかなボートルスケール(1-9)を推定する。
    主要都市(都道府県庁所在地)からの距離に基づいた簡易的な計算。
    """
    min_dist = float('inf')
    
    for pref, coords in PREFECTURE_COORDS.items():
        dist = calculate_distance(lat, lng, coords['lat'], coords['lng'])
        if dist < min_dist:
            min_dist = dist
            
    # 都市中心部からの距離に基づく推定マッピング
    if min_dist < 5:
        return 9 # 都市中心部 (中心地極めて明るい)
    elif min_dist < 10:
        return 8 # 都市部
    elif min_dist < 20:
        return 7 # 都市郊外の移行地
    elif min_dist < 35:
        return 6 # 明るい郊外
    elif min_dist < 50:
        return 5 # 郊外
    elif min_dist < 70:
        return 4 # 郊外と地方の移行地
    elif min_dist < 100:
        return 3 # 地方 (田舎)
    else:
        return 2 # 極めて暗い地方
