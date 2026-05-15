# app.py
# Streamlit wrapper for your original HTML workbook.
# This keeps the HTML/CSS/JavaScript design exactly as it was.
#
# Folder structure:
#   German/
#   ├── app.py
#   ├── index.html
#   └── requirements.txt
#
# requirements.txt:
#   streamlit
#
# Run locally:
#   streamlit run app.py

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="German A1 Sentence Builder",
    page_icon="🇩🇪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove Streamlit's default spacing so the embedded HTML feels like a real website.
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
            max-width: 100%;
        }
        header[data-testid="stHeader"] {
            display: none;
        }
        footer {
            display: none;
        }
        #MainMenu {
            visibility: hidden;
        }
        iframe {
            display: block;
            width: 100%;
            border: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

html_path = Path(__file__).parent / "index.html"

if not html_path.exists():
    st.error(
        "Missing index.html. Add your original HTML file beside app.py and name it index.html."
    )
    st.code(
        """
German/
├── app.py
├── index.html
└── requirements.txt
        """.strip()
    )
    st.stop()

html = html_path.read_text(encoding="utf-8")

# Height is intentionally large because the original HTML page handles its own layout.
# scrolling=True keeps the page usable on all screen sizes.
components.html(html, height=9000, scrolling=True)
