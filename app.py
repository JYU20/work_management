from datetime import date
import streamlit as st
import pandas as pd
import math
import openpyxl

# ページ設定
st.set_page_config(layout="wide", page_title="DXデモアプリ")

# CSS設定：折り返し防止、中央寄せ、表の横スクロール対応
st.markdown("""
<style>
h1 {text-align: center !important;}
p {text-align: left !important;}

/* テーブル全体のスタイル設定 */
table {
    width: auto;
    min-width: 100%;
}

/* ヘッダーとセルの設定 */
table td, table th {
    text-align: center !important;
    white-space: nowrap !important; /* 文字の折り返しを禁止 */
    padding: 10px !important;      /* 見やすくするために余白を調整 */
}

/* スマホ等で表がはみ出た場合に横スクロールを可能にする */
div.stTable {
    overflow-x: auto;
}
</style>""", unsafe_allow_html=True)

# 小数点第2位で切り捨て、かつ文字列として「0.00」形式にする関数
def floor_to_2nd_decimal_str(val):
    if pd.isna(val) or val == "":
        return "0.00"
    truncated = math.floor(float(val) * 100 + 1e-9) / 100.0
    return f"{truncated:.2f}"

# 時間文字列 (HH:MM:SS) を秒数に変換
def hms_to_seconds(hms_str):
    try:
        if pd.isna(hms_str) or hms_str == "":
            return 0
        h, m, s = map(int, str(hms_str).split(':'))
        return h * 3600 + m * 60 + s
    except:
        return 0

# 秒数を時間文字列 (HH:MM:SS) に変換
def seconds_to_hms(seconds):
    if pd.isna(seconds) or seconds <= 0:
        return "00:00:00"
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def main():
    st.title("DXデモアプリ")

    # 1. データの読み込み
    try:
        df = pd.read_excel("デモ用アプリRe.xlsx", sheet_name="Sheet1")
    except Exception as e:
        st.error(f"ファイルが読み込めません: {e}")
        return

    # 前処理
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
        st.warning("条件に一致するデータがありません。")
    else:
        # 4. 製品名別の集計
        summary = filtered_df.groupby('製品名').agg({
            '㎥数': 'first',
            '取数': 'first',
            '主キー': 'count',
            'duration_sec': 'sum'
        }).reset_index()

        summary.columns = ['製品名', '㎥数', '取数', '計測回数', '秒数_合計']
        
        # ㎥数を切り捨て・固定表示
        summary['㎥数'] = summary['㎥数'].apply(floor_to_2nd_decimal_str)
        # 取数を整数・文字列化
        summary['取数'] = summary['取数'].fillna(0).astype(int).astype(str)

        # 5. 最下行（全体統計）の計算
        total_volume_actual_str = floor_to_2nd_decimal_str(filtered_df['㎥数'].sum())
        total_counts = len(filtered_df)
        overall_avg_seconds = filtered_df['duration_sec'].mean()

        total_row = pd.DataFrame({
            '製品名': ['【全体合計/時間のみ平均】'],
            '㎥数': [total_volume_actual_str],
            '取数': ['-'],
            '計測回数': [total_counts],
            '秒数_合計': [overall_avg_seconds]
        })

        final_df = pd.concat([summary, total_row], ignore_index=True)
        final_df['総計測時間'] = final_df['秒数_合計'].apply(seconds_to_hms)

        # 表示用の列整理
        display_table = final_df[['製品名', '㎥数', '取数', '計測回数', '総計測時間']]
        
        # 6. 表示
        st.write("#### 集計表（横スクロール可能・折り返しなし）")
        st.table(display_table)

    with st.expander("操作手順を表示"):
        st.write("手順1～4: (省略)")

if __name__ == "__main__":
    main()