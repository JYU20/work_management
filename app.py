import streamlit as st
import pandas as pd
from datetime import date
import math
import openpyxl

# 1. ページ設定
st.set_page_config(layout="wide", page_title="DXデモアプリ")

# 2. CSS設定（デザイン調整：中央寄せ・折り返し防止・スクロール対応）
st.markdown("""
<style>
h1 {text-align: center !important;}
p {text-align: left !important;}

/* テーブル全体のスタイル設定 */
table {
    width: auto;
    min-width: 100%;
}

/* ヘッダーとセルの設定：中央寄せ + 折り返し防止 */
table td, table th {
    text-align: center !important;
    white-space: nowrap !important; /* スマホ等での改行を禁止 */
    padding: 10px !important;
}

/* スマホ等で表が横に長い場合にスクロール可能にする */
div.stTable {
    overflow-x: auto;
}
</style>""", unsafe_allow_html=True)

# --- ユーティリティ関数 ---

def floor_to_2nd_decimal_str(val):
    """小数点第2位で切り捨て、かつ文字列として'0.00'形式に固定する"""
    if pd.isna(val) or val == "":
        return "0.00"
    try:
        # 浮動小数点の演算誤差を防ぐため極小値を足して切り捨て
        truncated = math.floor(float(val) * 100 + 1e-9) / 100.0
        return f"{truncated:.2f}"
    except:
        return "0.00"

def hms_to_seconds(hms_str):
    """時間文字列 (HH:MM:SS) を秒数(整数)に変換"""
    try:
        if pd.isna(hms_str) or hms_str == "":
            return 0
        h, m, s = map(int, str(hms_str).split(':'))
        return h * 3600 + m * 60 + s
    except:
        return 0

def seconds_to_hms(seconds):
    """秒数を時間文字列 (HH:MM:SS) に変換"""
    if pd.isna(seconds) or seconds <= 0:
        return "00:00:00"
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

# --- メイン処理 ---

def main():
    st.title("DXデモアプリ")

    # 1. データの読み込み
    try:
        df = pd.read_excel("デモ用アプリRe.xlsx", sheet_name="Sheet1")
    except Exception as e:
        st.error(f"Excelファイル『デモ用アプリRe.xlsx』の読み込みに失敗しました: {e}")
        return

    # 前処理：日付型への変換と秒数の算出
    df['日付'] = pd.to_datetime(df['日付']).dt.date
    df['duration_sec'] = df['総計測時間'].apply(hms_to_seconds)

    # 2. サイドバー設定
    factory_dropdown = df["工場名"].unique()
    selected_factory = st.sidebar.selectbox("工場名を選択してください", factory_dropdown)
    
    start_date = st.sidebar.date_input("計測開始日", value=df['日付'].min())
    end_date = st.sidebar.date_input("計測終了日", value=df['日付'].max())

    # 3. データのフィルタリング
    mask = (
        (df['工場名'] == selected_factory) &
        (df['日付'] >= start_date) &
        (df['日付'] <= end_date) &
        (df['製品名'].notna())
    )
    filtered_df = df.loc[mask].copy()

    st.markdown(f"### 工場: {selected_factory}")

    if filtered_df.empty:
        st.warning("選択された期間・工場に該当するデータがありません。")
    else:
        # 4. 製品名別の集計
        summary = filtered_df.groupby('製品名').agg({
            '㎥数': 'first',      # 製品ごとの単位㎥数
            '取数': 'first',      # 製品ごとの取数
            '主キー': 'count',    # 計測回数
            'duration_sec': 'sum' # 製品ごとの合計計測時間
        }).reset_index()

        summary.columns = ['製品名', '㎥数', '取数', '計測回数', '秒数_合計']
        
        # 5. 最下行（全体統計）の計算
        # ㎥数：全計測データの合計（切り捨て）
        total_volume_str = floor_to_2nd_decimal_str(filtered_df['㎥数'].sum())
        
        # 計測回数：全件数の合計
        total_counts = len(filtered_df)
        
        # 【修正箇所】総計測時間の「合計」を算出
        # summaryに格納されている各製品の合計時間をさらに合算します
        total_seconds_sum = summary['秒数_合計'].sum()

        # 合計行のデータフレーム作成
        total_row = pd.DataFrame({
            '製品名': ['【全体合計】'],
            '㎥数': [total_volume_str],
            '取数': ['-'],
            '計測回数': [total_counts],
            '秒数_合計': [total_seconds_sum]
        })

        # 6. 表示用にデータを成形
        summary['㎥数'] = summary['㎥数'].apply(floor_to_2nd_decimal_str)
        summary['取数'] = summary['取数'].fillna(0).astype(int).astype(str)

        # 結合
        final_df = pd.concat([summary, total_row], ignore_index=True)

        # 秒数を HH:MM:SS に変換
        final_df['総計測時間'] = final_df['秒数_合計'].apply(seconds_to_hms)

        # 不要なカラムを除外して表示
        display_table = final_df[['製品名', '㎥数', '取数', '計測回数', '総計測時間']]
        
        st.write(f"#### 集計結果（{start_date} ～ {end_date}）")
        st.table(display_table)

    # 7. 操作手順
    st.markdown("---")
    with st.expander("操作手順を表示"):
        st.write("手順1～4: (中略)")

if __name__ == "__main__":
    main()