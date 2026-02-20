from flask import Blueprint, render_template

spots_bp = Blueprint('spots', __name__)

@spots_bp.route('/spots')
def spots():
    # Mock data for observation spots
    mock_spots = [
        {
            "id": 1,
            "name": "野辺山高原", 
            "lat": 35.946, 
            "lng": 138.474, 
            "note": "星空が非常に綺麗。標高が高く空気が澄んでいる。",
            "bortle": 2,
            "rating": 5
        },
        {
            "id": 2,
            "name": "阿智村", 
            "lat": 35.443, 
            "lng": 137.733, 
            "note": "日本一の星空。星空ナイトツアーで有名。",
            "bortle": 3,
            "rating": 4
        },
        {
            "id": 3,
            "name": "富士山 須走口五合目", 
            "lat": 35.363, 
            "lng": 138.761, 
            "note": "夏は混雑するが、雲海と星空のコラボが狙える。光害も比較的少ない。",
            "bortle": 3,
            "rating": 5
        },
        {
            "id": 4,
            "name": "城ヶ島公園", 
            "lat": 35.132, 
            "lng": 139.620, 
            "note": "都心から近く、南から西にかけての空が開けている。天の川撮影の人気スポット。",
            "bortle": 5,
            "rating": 3
        }
    ]
    return render_template('spots.html', spots=mock_spots)
