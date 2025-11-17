import streamlit as st

@st.cache_data()
def logos():
    with st.container(horizontal=True, vertical_alignment="bottom"):
        with st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="bottom"):
            st.image(image="images/RIF_60.png")
            st.image(image="images/fir_60.png")
        with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="bottom"):
            st.image(image="images/IGF_60.png")
            st.image(image="images/BMWE_100.png")

def footer():
    st.markdown("---")

    logos()

    # Links
    with st.container(horizontal=True, horizontal_alignment="center"):
        st.link_button("Impressum", "https://www.rif-ev.de/impressum")
        st.link_button("Datenschutz", "https://www.rif-ev.de/datenschutz")
