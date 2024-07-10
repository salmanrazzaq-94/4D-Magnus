import streamlit as st

def footer():
    footer_html = """
    <style>
    .footer {
        position: sticky;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #333;
        color: white;
        text-align: center;
        padding: 10px;
        box-shadow: 0 -1px 5px rgba(0, 0, 0, 0.1);
        z-index: 100;
    }
    body {
        margin-bottom: 50px; /* Ensure there's space for the footer */
    }
    </style>
    <div class="footer">
        Made with ❤️ by Salman
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

