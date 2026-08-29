import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import docx
from docx.shared import Inches
import os
import requests
import io
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import time
import json
import base64

st.set_page_config(page_title="AdShield | Kurumsal Denetim", layout="wide", initial_sidebar_state="collapsed")

# ----------------- COKLU KUYRUK YONETIMI -----------------
def eklenti_verilerini_getir():
    try:
        u_url = st.secrets.get("UPSTASH_REDIS_REST_URL")
        u_token = st.secrets.get("UPSTASH_REDIS_REST_TOKEN")
        if not u_url or not u_token: return []
            
        headers = {"Authorization": f"Bearer {u_token}"}
        # Kuyruktaki tüm öğeleri çek (0'dan -1'e kadar)
        res = requests.get(f"{u_url}/lrange/adshield_queue/0/-1", headers=headers, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            raw_list = data.get("result", [])
            if raw_list:
                # Verileri çektikten sonra kuyruğu temizle
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

# ----------------- ÇIKTI OLUŞTURUCULAR -----------------
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
        
        if veri.get("url"): pdf.cell(0, 8, f"Kaynak: {veri['url']}", ln=True)
        if veri.get("gorsel"):
            temp_img = f"temp_adshield_{int(time.time())}_{idx}.png"
            veri["gorsel"].save(temp_img, format="PNG")
            pdf.image(temp_img, w=170)
            os.remove(temp_img)
            
        pdf.ln(5)
        for line in veri.get("rapor", "").split('\n'):
            pdf.multi_cell(0, 6, line.encode('latin-1', 'replace').decode('latin-1'))
    return bytes(pdf.output())

def trigger_scroll(position="top"):
    components.html(f"<script>setTimeout(() => window.scrollTo(0, 0), 200);</script>", height=0, width=0)

# Stiller ve Arayüz Başlangıcı
st.markdown("""<style>.block-container{max-width:1200px!important;}</style>""", unsafe_allow_html=True)

try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
except Exception: api_key = None

def optimize_image(img, max_dimension=2000):
    img = img.convert("RGB")
    if max(img.size) > max_dimension: img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return img

def analiz_et_tekil(gorsel, url, sektor, mecra):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-3.6-flash")
    prompt = f"SEN UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN. Sektör: {sektor} | Mecra: {mecra} | URL: {url}\nLütfen görseli incele, mevzuat uyumunu analiz et ve riskleri listele."
    try:
        res = model.generate_content([prompt, gorsel])
        return res.text
    except Exception as e:
        return f"Hata oluştu: {e}"

if "vaka_havuzu" not in st.session_state: st.session_state.vaka_havuzu = []

st.markdown("### ADSHIELD COMPLIANCE | Kurumsal Denetim Paneli")

# Pazar Radarı ve Toplu İşlem Modülü
with st.container(border=True):
    st.markdown("#### 📥 Yakalanan Reklam Havuzu (Toplu İşlem)")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📥 Eklenti Kuyruğundaki Tüm Görüntüleri Al", use_container_width=True, type="primary"):
            with st.spinner("Kuyruk boşaltılıyor..."):
                gelen_liste = eklenti_verilerini_getir()
                if gelen_liste:
                    for item in gelen_liste:
                        b64_img = item.get('image', '').split(',')[1] if ',' in item.get('image', '') else item.get('image', '')
                        b64_img = b64_img.strip().replace('\n', '').replace('\r', '')
                        b64_img += '=' * ((4 - len(b64_img) % 4) % 4)
                        img = Image.open(io.BytesIO(base64.b64decode(b64_img))).convert("RGB")
                        
                        st.session_state.vaka_havuzu.append({
                            "url": item.get('url', ''),
                            "gorsel": img,
                            "rapor": None
                        })
                    st.success(f"🎯 {len(gelen_liste)} yeni görüntü havuza eklendi!")
                    st.rerun()
                else:
                    st.warning("Kuyrukta yeni veri bulunamadı.")
    with col2:
        if st.button("🧹 Havuzu Temizle", use_container_width=True):
            st.session_state.vaka_havuzu = []
            st.rerun()

    if st.session_state.vaka_havuzu:
        st.write(f"**Mevcut Vaka Sayısı: {len(st.session_state.vaka_havuzu)}**")
        sektor = st.selectbox("Tüm Havuz İçin Sektör", ["Kozmetik & Kişisel Bakım", "Takviye Edici Gıda", "E-Ticaret"])
        mecra = st.selectbox("Tüm Havuz İçin Mecra", ["İnternet", "Televizyon", "Açık Hava"])
        
        if st.button("🚀 Tüm Havuzu Analiz Et (Batch Processing)"):
            progress_text = "Vakalar analiz ediliyor..."
            my_bar = st.progress(0, text=progress_text)
            
            for i, vaka in enumerate(st.session_state.vaka_havuzu):
                vaka["rapor"] = analiz_et_tekil(vaka["gorsel"], vaka["url"], sektor, mecra)
                my_bar.progress((i + 1) / len(st.session_state.vaka_havuzu), text=f"İşleniyor: {i+1}/{len(st.session_state.vaka_havuzu)}")
            st.success("Tüm analizler tamamlandı!")

        st.markdown("---")
        # Sonuçları listeleme
        for idx, vaka in enumerate(st.session_state.vaka_havuzu, 1):
            with st.expander(f"Vaka #{idx} - {vaka['url'][:60]}..."):
                st.image(vaka["gorsel"], width=300)
                if vaka["rapor"]:
                    st.markdown(vaka["rapor"])
                else:
                    st.info("Henüz analiz edilmedi.")
                    
        # Dışa Aktarım Butonları
        if any(v.get("rapor") for v in st.session_state.vaka_havuzu):
            col_pdf, col_word = st.columns(2)
            with col_pdf:
                pdf_bytes = create_pdf(st.session_state.vaka_havuzu)
                st.download_button("⬇️ Tümünü PDF Olarak İndir", data=pdf_bytes, file_name="adshield_toplu_rapor.pdf", mime="application/pdf", use_container_width=True)
            with col_word:
                word_bytes = create_docx(st.session_state.vaka_havuzu)
                st.download_button("⬇️ Tümünü Word Olarak İndir", data=word_bytes, file_name="adshield_toplu_rapor.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
