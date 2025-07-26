# -*- coding: utf-8 -*-

### 全国の月齢・月の出入りのスクレイピング

def moon(url):
    datas = []
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table', {'class', 'result'})
    trs = table.find_all('tr')

    for tr in trs[1:]:
        tds = tr.find_all('td')
        data = {
            '月の出': tds[1].text,
            '月の入': tds[5].text,
            '月齢': tds[7].text
        }
        datas.append(data)
    else:
        print('Success!')
    
    return datas

def save_to_csv(datas, name, n):
    # ファイルを保存するディレクトリのパスを構築
    #folder_path = f'csv_folder/csv_folder_{year}/csv_folder_{name}'
    folder_path = f'csv_folder/csv_folder_{name}'
    
    # ディレクトリが存在しない場合、作成
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # ファイルのパスを構築
    file_path = f'{folder_path}/{name}の月の出入り{n}月.csv'
    
    # データをCSVとして保存
    df = pd.DataFrame(datas)
    df.to_csv(file_path, index=False, encoding='utf-8')
    
    print(f"CSVファイルを保存しました: {file_path}")

if __name__ == '__main__':

    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import time, os

    years = ['2025']
    #years = ['2025', '2026', '2027']
    pref_numbers = ['00', '01', '02', '03', '04', '05', '06', '07', '08']
    #pref_numbers = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48']
    pref_names = ['札幌(北海道)', '根室(北海道)', '青森(青森県)', '盛岡(岩手県)', '仙台(宮城県)', '秋田(秋田県)', '山形(山形県)', '福島(福島県)', '水戸(茨城県)']
    #pref_names = ['札幌(北海道)', '根室(北海道)', '青森(青森県)', '盛岡(岩手県)', '仙台(宮城県)', '秋田(秋田県)', '山形(山形県)', '福島(福島県)', '水戸(茨城県)', '宇都宮(栃木県)', '前橋(群馬県)', 'さいたま(埼玉県)', '千葉(千葉県)', '東京(東京都)', '小笠原[父島](東京都)', '横浜(神奈川県)', '新潟(新潟県)', '富山(富山県)', '金沢(石川県)', '福井(福井県)', '甲府(山梨県)', '長野(長野県)', '岐阜(岐阜県)', '静岡(静岡県)', '名古屋(愛知県)', '津(三重県)', '大津(滋賀県)', '京都(京都府)', '大阪(大阪府)', '神戸(兵庫県)', '奈良(奈良県)', '和歌山(和歌山県)', '鳥取(鳥取県)', '松江(島根県)', '岡山(岡山県)', '広島(広島県)', '山口(山口県)', '徳島(徳島県)', '高松(香川県)', '松山(愛媛県)', '高知(高知県)', '福岡(福岡県)', '佐賀(佐賀県)', '長崎(長崎県)', '熊本(熊本県)', '大分(大分県)', '宮崎(宮崎県)', '鹿児島(鹿児島県)', '那覇(沖縄県)']

    numbers = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    
    for year in years:
        print(f"{year}年のデータです。")
        for m, name in zip(pref_numbers, pref_names):
            print(f"{name}のデータです。")
            for n in numbers:
                url = f'https://eco.mtk.nao.ac.jp/koyomi/dni/{year}/m{m}{n}.html'
                print(f"{n}月のデータです。")
                print(url)

                try:
                    datas = moon(url)
                    save_to_csv(datas, name, n)
                
                except AttributeError:
                    continue
            
                finally:
                    time.sleep(10)
            
        else:
            print('すべてのスクレイピング完了！')
