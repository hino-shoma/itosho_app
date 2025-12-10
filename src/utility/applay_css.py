# cssの適用
import streamlit as st
import base64
from pathlib import Path

def apply_custom_css(css_file, image_path=None):
    """
    CSSファイルを適用し、オプションで背景画像をBase64でエンコードして追加
    """
    with open(css_file, encoding="utf-8") as f:
        css_content = f.read()
    
    # 背景画像がある場合、Base64エンコードして疑似要素で背景レイヤーを作る
    if image_path:
        image_path = Path(image_path)
        if image_path.exists():
            with open(image_path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode()

            # 画像形式を判定
            suffix = image_path.suffix.lower()
            mime_type = "image/png"

            # 疑似要素を使って背景レイヤーを作成（これにより z-index 制御が容易になる）
            # 注意: ::before を下に置き、アプリ内の主要要素を上に表示するために
            # ::before は z-index: 0、コンテンツは z-index: 1 に設定
            background_css = f"""
.stApp {{
    position: relative;
}}
.stApp::before {{
    content: "";
    position: fixed;
    inset: 0;
    background-image: url("data:{mime_type};base64,{encoded_image}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    z-index: 0;
    pointer-events: none;
    opacity: 0.35;
}}
/* アプリ内の直下要素を常に背景より前面に出す */
.stApp > * {{
    position: relative;
    z-index: 1;
}}
/* サイドバーはさらに前面 */
.stSidebar, [data-testid="stSidebar"] {{
    position: relative;
    z-index: 2 !important;
}}
"""
            st.markdown(f'<style>{background_css}</style>', unsafe_allow_html=True)

    # その他のCSSを別の<style>タグで注入（重要！Base64の後に実行）
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

    # サイドバーが隠れるケースに備えて強制的に表示・前面に出すスタイルを注入
    force_css = """
/* 強制サイドバー表示（複数セレクタに対応） */
[data-testid="stSidebar"] {
    display: block !important;
    position: relative !important;
    z-index: 4 !important;

    min-width: 300px !important;
    opacity: 1 !important;
    transform: none !important;
    pointer-events: auto !important;
    background-color: rgba(255,255,255,0.95) !important;
}

/* メイン領域が背景レイヤーより前面に来ることを再保証 */
.stApp > * { z-index: 1 !important; position: relative !important; }
"""
    st.markdown(f'<style>{force_css}</style>', unsafe_allow_html=True)
