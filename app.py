import streamlit as st

st.set_page_config(layout="wide")
st.markdown("""
<style>h1, p{
text-align: center;}
</style>""",unsafe_allow_html=True
)

def main():
    st.title("【DXデモアプリ】")
    st.write("手順1: 【DXデモアプリ上で打設機の稼働・非稼働時間を計測する】")
    st.write("手順2: 計測終了後【デモ用アプリ】を.xlsxとしてダウンロードし、【DXデモアプリ】秒単位ずれフォルダにいれる")
    st.write("手順3: 【実行.batをダブルクリックし、計測終了と次の計測時間の重なりをなくす】")
    steps = ["実行.batをダブルクリックし、計測終了と次の計測開始時間の重なりをなくす"]

if __name__ == "__main__":
    main()
    