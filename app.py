import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
import os
import glob
import re
import requests
import io
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import time
import json
import base64
import textwrap

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Risk Denetim Platformu",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- CANLI KUYRUK YÖNETİMİ (TOPLU) -----------------
def eklenti_verilerini_getir():
    try:
        u_url = st.secrets.get("UPSTASH_REDIS_REST_URL")
        u_token = st.secrets.get("UPSTASH_REDIS_REST_TOKEN")
        if not u_url or not u_token: 
            return []
            
        headers = {"Authorization": f"Bearer {u_token}"}
        res = requests.get(f"{u_url}/lrange/adshield_queue/0/-1", headers=headers, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            raw_list = data.get("result", [])
            if raw_list:
                requests.get(f"{u_url}/del/adshield_queue", headers=headers, timeout=3)
                islenmis_liste = []
                for item in raw_list:
                    parsed = json.loads(item)
                    if isinstance(parsed, str): 
                        parsed = json.loads(parsed)
                    islenmis_liste.append(parsed)
                return islenmis_liste
    except Exception as e:
        print(f"Toplu okuma hatası: {e}")
    return []

# ----------------- ÇOKLU ÇIKTI OLUŞTURUCULAR -----------------
def create_docx(vaka_listesi):
    doc = docx.Document()
    for idx, veri in enumerate(vaka_listesi, 1):
        doc.add_heading(f'Vaka Tespit Raporu #{idx}', level=1)
        if veri.get("url"): 
            doc.add_paragraph(f"Kaynak Bağlantı: {veri['url']}")
        if veri.get("gorsel"):
            img_io = io.BytesIO()
            veri["gorsel"].save(img_io, format="PNG")
            img_io.seek(0)
            doc.add_picture(img_io, width=Inches(6.0))
        doc.add_paragraph(veri.get("rapor", "Rapor oluşturulamadı."))
        if idx < len(vaka_listesi): 
            doc.add_page_break()
    docx_io = io.BytesIO()
    doc.save(docx_io)
    return docx_io.getvalue()

def create_pdf(vaka_listesi, baslik_metni="AdShield Denetim Raporu"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for idx, veri in enumerate(vaka_listesi, 1):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"{baslik_metni} - Vaka #{idx}", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        
        if veri.get("url"): 
            guvenli_url = re.sub(r'(\S{70})', r'\1 ', veri['url'])
            pdf.multi_cell(0, 6, f"Kaynak:\n{guvenli_url}")
            pdf.ln(3)
            
        if veri.get("gorsel"):
            temp_img = f"temp_adshield_{int(time.time())}_{idx}.png"
            veri["gorsel"].save(temp_img, format="PNG")
            pdf.image(temp_img, w=170)
            os.remove(temp_img)
            
        pdf.ln(5)
        rapor_metni = veri.get("rapor", "")
        
        for line in rapor_metni.split('\n'):
            guvenli_metin = line.encode('latin-1', 'replace').decode('latin-1')
            guvenli_metin = re.sub(r'(\S{60})', r'\1 ', guvenli_metin)
            pdf.multi_cell(0, 6, guvenli_metin)
                
    return bytes(pdf.output())

# Sayfa İçi Akıllı Kaydırma
def trigger_scroll(position="top"):
    components.html(f"<script>setTimeout(() => window.scrollTo(0, 0), 200);</script>", height=0, width=0)

# Kurumsal Tema Stilleri
st.markdown("""
