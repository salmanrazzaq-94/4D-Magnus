import streamlit as st
from utils.authentication import check_credentials
from pages import home, login

# Set page config
st.set_page_config(page_title="Multipage Streamlit App", page_icon=":star:", layout="centered", initial_sidebar_state="auto")

# Main function to control app flow
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Home", "Another Page"])
        
        if page == "Home":
            home.show()
        
        if st.sidebar.button("Logout"):
            st.session_state["logged_in"] = False
    else:
        login.show()

if __name__ == "__main__":
    main()