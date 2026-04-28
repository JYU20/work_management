from datetime import date
import streamlit as st
import pandas as pd
import openpyxl

# ページ設定
st.set_page_config(layout="wide", page_title="DXデモアプリ")

# タイトルやスタイルの設定
st.markdown("""
<style>
h1 {text-align: center !important;}
p {text-align: left !important;}
.summary-box {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin-top: 20px;
}
</style>""", unsafe_allow_html=True)

# 時間文字列 (HH:MM:SS) を秒数に変換する関数
def hms_to_seconds(hms_str):
    try:
        if pd.isna(hms_str) or hms_str == "":
            return 0
        h, m, s = map(int, str(hms_str).split(':'))
        return h * 3600 + m * 60 + s
    except:
        return 0

# 秒数を時間文字列 (HH:MM:SS) に変換する関数
def seconds_to_hms(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def main():
    st.title("DXデモアプリ")

    # 1. データの読み込み
    try:
        # Excelファイルの読み込み
        df = pd.read_excel("デモ用アプリRe.xlsx", sheet_name="Sheet1")
    except Exception as e:
        st.error(f"ファイルが見つからないか、読み込めません。設定を確認してください: {e}")
        return

    # データの前処理
    df['日付'] = pd.to_datetime(df['日付']).dt.date
    # 総計測時間を計算用の秒数に変換
    df['duration_sec'] = df['総計測時間'].apply(hms_to_seconds)

    # 2. サイドバーの設定
    factory_dropdown = df["工場名"].unique()
    selected_factory = st.sidebar.selectbox("工場名を選択してください", factory_dropdown)
    
    start_date = st.sidebar.date_input("計測開始日を選択してください", value=df['日付'].min())
    end_date = st.sidebar.date_input("計測終了日を選択してください", value=df['日付'].max())
    
    st.sidebar.markdown(f"データ表示期間:<br>{start_date} ～ {end_date}", unsafe_allow_html=True)

    # 3. データのフィルタリング
    mask = (
        (df['工場名'] == selected_factory) &
        (df['日付'] >= start_date) &
        (df['日付'] <= end_date) &
        (df['製品名'].notna()) # 製品名があるデータ（主に打設計測）に絞る
    )
    filtered_df = df.loc[mask].copy()

    # 情報表示
    st.markdown(f"### 選択された工場: {selected_factory}")
    st.markdown(f"選択された期間: {start_date} ～ {end_date}")

    if filtered_df.empty:
        st.warning("選択された条件に該当するデータがありません。")
    else:
        # 4. 製品名別の集計
        # ㎥数、取数は製品ごとの値（平均/代表値）、計測回数は件数、時間は合計と平均を算出
        summary_df = filtered_df.groupby('製品名').agg({
            '㎥数': 'first',
            '取数': 'first',
            '主キー': 'count',
            'duration_sec': ['mean', 'sum']
        })

        # カラム名の整理
        summary_df.columns = ['㎥数', '取数', '計測回数', '平均計測時間(秒)', '合計計測時間(秒)']
        summary_df = summary_df.reset_index()

        # 秒数を HH:MM:SS 形式に変換
        summary_df['平均計測時間'] = summary_df['平均計測時間(秒)'].apply(seconds_to_hms)
        summary_df['合計計測時間'] = summary_df['合計計測時間(秒)'].apply(seconds_to_hms)

        # 表示用のテーブルを整理（ユーザー指定の並び）
        display_df = summary_df[['製品名', '㎥数', '取数', '計測回数', '平均計測時間', '合計計測時間']]
        
        st.write("#### 製品別集計表")
        st.table(display_df)

        # 5. 合計値の算出と表示
        # ㎥数の合計（各行の㎥数を全て足し合わせる：生産総量）
        total_volume = filtered_df['㎥数'].sum()
        # 計測回数の合計
        total_counts = len(filtered_df)
        # 総計測時間の合計
        total_time_sec = filtered_df['duration_sec'].sum()
        total_time_hms = seconds_to_hms(total_time_sec)

        st.markdown("---")
        st.markdown("#### 全体合計")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("㎥数 合計", f"{total_volume:.2f} ㎥")
        with col2:
            st.metric("計測回数 合計", f"{total_counts} 回")
        with col3:
            st.metric("総計測時間 合計", total_time_hms)

    # アプリの説明
    with st.expander("操作手順を表示"):
        st.write("手順1: DXデモアプリ上で打設機の稼働・非稼働時間を計測する")
        st.write("手順2: 計測終了後【デモ用アプリ】を.xlsxとしてDLし、【DXデモアプリ】秒単位ずれフォルダにいれる")
        st.write("手順3: 【実行.bat】をダブルクリックし、計測終了と次の計測時間の重なりをなくす")
        st.write("(注↑) Excelファイル名 = デモ用アプリRe.xlsx / Excelシート名 = Sheet1 なのを確認する")
        st.write("手順4: Github上のフォルダにあるデモ用アプリRe.xlsxに差分を追加する")

if __name__ == "__main__":
    main()