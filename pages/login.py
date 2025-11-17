import streamlit as st


from functions.menu import default_menu
from functions.session_state import check_mode
from functions.page import footer

st.set_page_config(page_title="Admin Login", layout="wide")

check_mode()
default_menu()

# State management -----------------------------------------------------------

state = st.session_state


def init_state(key, value):
    if key not in state:
        state[key] = value


# generic callback to set state
def _set_state_cb(**kwargs):
    for state_key, widget_key in kwargs.items():
        val = state.get(widget_key, None)
        if val is not None or val == "":
            setattr(state, state_key, state[widget_key])


def _set_login_cb(username, password):
    state.login_successful = login(username, password)


def _reset_login_cb():
    state.login_successful = False
    state.username = ""
    state.password = ""
    state.mode = "fragebogen"


init_state('login_successful', False)
init_state('username', '')
init_state('password', '')


# -----------------------------------------------------------------------------

# Function to check login credentials
def login(username, password):
    # secrets.toml
    credentials = st.secrets["credentials"]
    # Prüfen, ob Username existiert und Passwort stimmt
    return username in credentials and password == credentials[username]

# If login is successful
if state.login_successful:
    st.subheader("Admin Login")
    st.write("Login erfolgreich")
    st.button("Logout", on_click=_reset_login_cb)
    if state.mode == "fragebogen":
        state.mode = "analyse"
        st.switch_page("pages/analyse.py")


else:
    st.subheader("Admin Login")
    # Display login form
    st.text_input(
        "Benutzername:", value=state.username, key='username_input',
        on_change=_set_state_cb, kwargs={'username': 'username_input'}
    )
    st.text_input(
        "Passwort:", type="password", value=state.password, key='password_input',
        on_change=_set_state_cb, kwargs={'password': 'password_input'}
    )

    # Check login credentials
    if not state.login_successful and st.button("Login", on_click=_set_login_cb,
                                                args=(state.username, state.password)):
        st.warning("Falscher Benutzername oder Passwort")
footer()