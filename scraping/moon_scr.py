# -*- coding: utf-8 -*-
import os
import time
from pathlib import Path  # osよりモダンなパス操作
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm  # 進捗バー

def get_moon_data(session, url):
    """スクレイピング部分: sessionを使って効率化"""
    res = session.get(url)
    res.encoding = res.apparent_encoding
    
    # ステータスチェック（404エラーなどの対策）
    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table', {'class': 'result'})
    if not table:
        return None

    trs = table.find_all('tr')
    datas = []
    for tr in trs[1:]:
        tds = tr.find_all('td')
        if len(tds) < 8: continue # データが足りない行を飛ばす
        
        datas.append({
            '月の出': tds[1].text.strip(),
            '月の入': tds[5].text.strip(),
            '月齢': tds[7].text.strip()
        })
    return datas

def save_to_csv(datas, pref_name, month, year):
    """保存部分: 年別の階層を追加"""
    # 年別のフォルダの中に都道府県フォルダを作る構成に変更
    folder = Path(f'csv_folder/{year}/{pref_name}')
    
    # parents=True なので、csv_folder も year も pref_name も一気に作成されます
    folder.mkdir(parents=True, exist_ok=True)
    
    file_path = folder / f'{pref_name}の月の出入り{month}月.csv'
    
    df = pd.DataFrame(datas)
    # ファイル名に year を含める必要がなければ削ってもOK（フォルダで分かれているため）
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

if __name__ == '__main__':
    years = ['2026']
    # リストを手書きせず生成（00〜48, 01〜12）
    pref_numbers = [f"{i:02}" for i in range(49)]
    pref_names = ['札幌(北海道)', '根室(北海道)', '青森(青森県)', '盛岡(岩手県)', '仙台(宮城県)', '秋田(秋田県)', '山形(山形県)', '福島(福島県)', '水戸(茨城県)', '宇都宮(栃木県)', '前橋(群馬県)', 'さいたま(埼玉県)', '千葉(千葉県)', '東京(東京都)', '小笠原[父島](東京都)', '横浜(神奈川県)', '新潟(新潟県)', '富山(富山県)', '金沢(石川県)', '福井(福井県)', '甲府(山梨県)', '長野(長野県)', '岐阜(岐阜県)', '静岡(静岡県)', '名古屋(愛知県)', '津(三重県)', '大津(滋賀県)', '京都(京都府)', '大阪(大阪府)', '神戸(兵庫県)', '奈良(奈良県)', '和歌山(和歌山県)', '鳥取(鳥取県)', '松江(島根県)', '岡山(岡山県)', '広島(広島県)', '山口(山口県)', '徳島(徳島県)', '高松(香川県)', '松山(愛媛県)', '高知(高知県)', '福岡(福岡県)', '佐賀(佐賀県)', '長崎(長崎県)', '熊本(熊本県)', '大分(大分県)', '宮崎(宮崎県)', '鹿児島(鹿児島県)', '那覇(沖縄県)']
    months = [f"{i:02}" for i in range(1, 13)]

    # 1つの接続を使い回すことで高速化
    with requests.Session() as session:
        # tqdmで二重ループを可視化（全体の進捗を見たい場合は total を指定）
        total_tasks = len(years) * len(pref_names) * len(months)
        
        with tqdm(total=total_tasks, desc="全体進捗") as pbar:
            for year in years:
                for m_num, name in zip(pref_numbers, pref_names):
                    for n in months:
                        url = f'https://eco.mtk.nao.ac.jp/koyomi/dni/{year}/m{m_num}{n}.html'
                        
                        try:
                            datas = get_moon_data(session, url)
                            if datas:
                                save_to_csv(datas, name, n, year)
                        except Exception as e:
                            print(f"\nエラー発生: {name} {n}月 - {e}")
                        
                        pbar.update(1) # 進捗を1進める
                        time.sleep(1)  # サーバー負荷を考えて1秒〜（10秒は少し長いかもしれません）