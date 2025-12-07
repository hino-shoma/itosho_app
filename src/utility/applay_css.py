# cssの適用
import streamlit as st
def apply_custom_css(css_file):
    with open(css_file,encoding="utf-8") as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)