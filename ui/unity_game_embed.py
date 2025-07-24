import streamlit as st

def show_unity_game():
    st.markdown("## 🎮 Play the Unity Game")
    st.markdown("Below is the Unity game embedded in the app.")
    # Adjust the path if your build is elsewhere    
    st.components.v1.iframe("http://localhost:8502/index.html", height=500, width=800) 
