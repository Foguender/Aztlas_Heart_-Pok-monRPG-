import os
import sqlite3
import panda as pd
import streamlit as st
import random

st.set_page_config(page_title="Pokédex Aztlas", page_icon="   ", layout="wide")

st. markdown(
  """
  <style>
  @keyframe fundoAnimado {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  .stApp {
  background: linear-gradient(-45deg, #a0e0ff, #cceeff, #80d4ff, #e6f7ff);
  background-size: 400% 400%;
  animation: fundoAnimado 15s ease infinite;
  }

  .main .block-container {
  border: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 12 px;
  padding: 2rem;
  background-color: rgba(255, 255, 255, 0.9);
  }
  </style>
  """,
  unsafe_allow_html=True,
)
  }
