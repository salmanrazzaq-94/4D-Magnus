import streamlit as st
import login
from utils.authentication import check_credentials
import home
from streamlit_cookies_controller import CookieController

# Set page config
st.set_page_config(page_title="4D Magnus", page_icon=":star:", layout="wide", initial_sidebar_state="collapsed")

st.set_option('client.showSidebarNavigation', False)

# Initialize cookie manager
cookies = CookieController()


if 'logged_in' in cookies.getAll():
    st.session_state['logged_in'] = cookies.get('logged_in')
else:
    st.session_state['logged_in'] = False

# Debugging: Check if cookies are being set and retrieved
print("Cookies available:", cookies.getAll())

# Main function to control app flow
def main():
    # Ensure 'logged_in' state is present and properly initialized
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    # Check credentials on login
    if st.session_state['logged_in']:
        # Show the sidebar and Home page if logged in
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Home"])

        if page == "Home":
            home.show()

        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            cookies.set('logged_in', False)  # Clear the login cookie
            st.rerun()  # Refresh the page to reflect the change
    else:
        # Show the login page if not logged in
        login.show(cookies)

if __name__ == "__main__":
    main()
