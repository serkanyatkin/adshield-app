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
        if not u_url or not u_token: return []
            
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
                    if isinstance(parsed, str): parsed = json.loads(parsed)
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
        if veri.get("url"): doc.add_paragraph(f"Kaynak Bağlantı: {veri['url']}")
        if veri.get("gorsel"):
            img_io = io.BytesIO()
            veri["gorsel"].save(img_io, format="PNG")
            img_io.seek(0)
            doc.add_picture(img_io, width=Inches(6.0))
        doc.add_paragraph(veri.get("rapor", "Rapor oluşturulamadı."))
        if idx < len(vaka_listesi): doc.add_page_break()
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
            # URL çok uzunsa zorla böl
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
            # KESİN ÇÖZÜM: 60 karakterden uzun boşluksuz herhangi bir kelime/çizgi varsa araya boşluk ekler
            guvenli_metin = re.sub(r'(\S{60})', r'\1 ', guvenli_metin)
            pdf.multi_cell(0, 6, guvenli_metin)
                
    return bytes(pdf.output())

# Sayfa İçi Akıllı Kaydırma
def trigger_scroll(position="top"):
    components.html(f"<script>setTimeout(() => window.scrollTo(0, 0), 200);</script>", height=0, width=0)

# Kurumsal Tema Stilleri
st.markdown("""
<div id="page-top-anchor"></div>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .block-container { max-width: 1200px !important; padding-top: 1.2rem !important; margin: 0 auto !important; }
    .firm-header { background-color: #5D728B; padding: 18px 26px; border-radius: 6px; color: #ffffff; display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; box-shadow: 0 4px 14px rgba(93, 114, 139, 0.18); }
    .firm-title { font-family: 'Cinzel', serif; font-size: 19px; letter-spacing: 1.5px; font-weight: 700; }
    .firm-subtitle { font-size: 11px; letter-spacing: 1px; color: #DCE4EC; margin-top: 2px; }
    .firm-badge { background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.3); color: #ffffff; font-size: 11px; font-weight: 600; padding: 5px 12px; border-radius: 4px; }
    .mode-header-title { text-align: center; font-family: 'Cinzel', serif; font-size: 13.5px; letter-spacing: 1.5px; color: #2C3848; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; }
    div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; justify-content: center; gap: 14px; width: 100%; margin-bottom: 10px; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label { flex: 1; background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 12px 18px; cursor: pointer; text-align: center; display: flex; align-items: center; justify-content: center; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { border-color: #5D728B; background: #F8FAFC; }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) { border-color: #5D728B !important; background-color: #F1F5F9 !important; box-shadow: 0 0 0 1px #5D728B, 0 3px 8px rgba(93, 114, 139, 0.12) !important; font-weight: 600 !important; color: #1E293B !important; }
    .section-heading { font-family: 'Cinzel', serif; font-size: 13.5px; letter-spacing: 1px; color: #2C3848; font-weight: 700; margin-bottom: 12px; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="firm-header" lang="tr">
    <div>
        <div class="firm-title">ADSHIELD COMPLIANCE</div>
        <div class="firm-subtitle">Reklam Kurulu İçtihat & Kurumsal Risk Denetim Sistemi</div>
    </div>
    <div class="firm-badge">Kurumsal Regülasyon & Denetim Motoru</div>
</div>
""", unsafe_allow_html=True)

try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    serpapi_key = st.secrets.get("SERPAPI_API_KEY", None)
except Exception:
    api_key = None
    serpapi_key = None

with st.sidebar:
    st.header("Sistem Ayarları")
    api_key = st.text_input("Gemini API Key:", value=api_key or "", type="password")
    serpapi_key = st.text_input("SerpApi Key:", value=serpapi_key or "", type="password")

def optimize_image(img, max_dimension=2000):
    img = img.convert("RGB")
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return img

TARGET_MODEL = "gemini-3.6-flash"

def get_working_model(system_instruction=None):
    if not api_key: raise Exception("API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=TARGET_MODEL, system_instruction=system_instruction)

def generate_multi_role_synthesis_stream(contents, system_instruction_base, is_danisan):
    if not api_key: raise Exception("API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    rapor_turu_adi = "Mevzuat Uyum ve Revizyon Raporu" if is_danisan else "Piyasa İhlal ve Şikayet Raporu"
    single_master_prompt = f"""{system_instruction_base}
GÖREVİN: Aşağıdaki materyali tek seferde, eşzamanlı olarak hem KATI BİR MEVZUAT BAŞDENETÇİSİ hem de KIDEMLİ BİR HAKSIZ REKABET AVUKATI şapkalarıyla incelemek ve bana doğrudan KUSURSUZ, HARMANLANMIŞ BİR {rapor_turu_adi} üretmektir.
KESİN KURALLAR:
1. "KİME:", "HAZIRLAYAN:", "KONU:" gibi bürokratik giriş antetlerini ASLA KULLANMA. 
2. Emsal Kararlarda "L'Oreal", "La Roche-Posay" tekrarlarından kaçın.
3. Raporu şık bir Markdown düzeninde oluştur.
4. Görsel üzerinde ambalaj, mg, enjektör gibi "tıbbi cihaz" işaretleri varsa asla kozmetik muamelesi yapma."""
    payload = [single_master_prompt] + contents
    model = get_working_model()
    for attempt in range(2):
        try:
            response = model.generate_content(payload, stream=False, generation_config=genai.types.GenerationConfig(temperature=0.0))
            if response and response.text:
                words = response.text.split(' ')
                for i in range(0, len(words), 6):
                    yield ' '.join(words[i:i+6]) + ' '
                    time.sleep(0.04) 
                return 
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt < 1:
                yield "\n\n> ⏳ Sistem duraklatıldı, 15 saniye içinde devam edecek...\n\n"
                time.sleep(15); continue 
            yield f"\nSentezleme hatası: {err_str}"; return

def analiz_et_tekil(gorsel, url, sektor, mecra):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=TARGET_MODEL)
    prompt = f"SEN UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN. Sektör: {sektor} | Mecra: {mecra} | URL: {url}\nLütfen görseli incele, mevzuat uyumunu analiz et ve riskleri listele. Antet kullanma."
    try:
        res = model.generate_content([prompt, gorsel])
        return res.text
    except Exception as e:
        return f"Hata oluştu: {e}"

def tekil_sorgu_at(kategori, sorgu, api_key_val):
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key_val}&engine=google&gl=tr&hl=tr&num=20"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        if "error" in data: return kategori, [{"baslik": "⚠️ API HATASI", "url": "#", "snippet": data['error']}]
        link_havuzu = []
