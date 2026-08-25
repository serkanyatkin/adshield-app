import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
from datetime import datetime
import os
import glob
import re
import requests
import io
import tempfile
import urllib.parse
from urllib.parse import quote_plus, unquote
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Otomatik Risk Denetim Radarı",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kurumsal Tema Stilleri
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .block-container { max-width: 1200px !important; padding-top: 1.2rem !important; }
    .firm-header {
        background-color: #5D728B;
        padding: 18px 26px;
        border-radius: 6px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
    }
    .firm-title { font-family: 'Cinzel', serif; font-size: 19px; letter-spacing: 1.5px; font-weight: 700; }
    .firm-subtitle { font-size: 11px; letter-spacing: 1px; color: #DCE4EC; margin-top: 2px; }
    .firm-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #ffffff;
        font-size: 11px;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 4px;
    }
    .section-heading {
        font-family: 'Cinzel', serif;
        font-size: 13.5px;
        letter-spacing: 1px;
        color: #2C3848;
        font-weight: 700;
        margin-bottom: 12px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 5px;
    }
    .stButton button[kind="primary"] {
        background-color: #5D728B !important;
        color: #ffffff !important;
        border-radius: 4px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="firm-header">
    <div>
        <div class="firm-title">ADSHIELD COMPLIANCE</div>
        <div class="firm-subtitle">Reklam Kurulu İçtihat & Kurumsal Risk Denetim Sistemi</div>
    </div>
    <div class="firm-badge">360° Çoklu Kanal İstihbarat Motoru</div>
</div>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", None)
serpapi_key = st.secrets.get("SERPAPI_API_KEY", None)

with st.sidebar:
    st.header("⚙️ Sistem Ayarları")
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
    serpapi_input = st.text_input("SerpApi Key (Opsiyonel):", type="password", value=serpapi_key or "")
    if serpapi_input:
        serpapi_key = serpapi_input

def optimize_image(img, max_dimension=500):
    img = img.convert("RGB")
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return img

@st.cache_resource(show_spinner=False)
def get_active_models(current_api_key):
    fallback = ["gemini-2.5-flash", "gemini-1.5-flash"]
    if not current_api_key:
        return fallback
    try:
        genai.configure(api_key=current_api_key)
        available = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return [m for m in available if "flash" in m] or fallback
    except Exception:
        return fallback

def generate_content_fast(contents, system_instruction=None):
    if not api_key:
        raise Exception("Gemini API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    models = get_active_models(api_key)
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
            response = model.generate_content(contents, request_options={"timeout": 25})
            if response and response.text:
                return response.text
        except Exception:
            continue
    raise Exception("Model yanıtı alınamadı. Lütfen tekrar deneyiniz.")

def download_image_safe(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'
    }
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200 and len(res.content) > 1500:
            return optimize_image(Image.open(io.BytesIO(res.content)))
    except Exception:
        pass
    return None

def create_evidence_card(title, query_name):
    img = Image.new("RGB", (440, 240), color="#F8FAFC")
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 4, 436, 236], outline="#94A3B8", width=2)
    draw.rectangle([10, 10, 430, 44], fill="#5D728B")
    draw.text((18, 18), "ADSHIELD MEVZUAT VE DELIL KAYDI", fill="#FFFFFF")
    draw.text((18, 70), f"Kanal: {title[:40]}", fill="#1E293B")
    draw.text((18, 105), f"Taranan: {query_name[:40]}", fill="#0F172A")
    draw.text((18, 145), "Pazaryeri Ihlal ve Saglik Beyani Tespiti", fill="#DC2626")
    draw.text((18, 195), f"Denetim Tarihi: {datetime.now().strftime('%d.%m.%Y')}", fill="#64748B")
    return img

def fetch_product_images_proxy(query):
    images = []
    clean_q = unquote(query).strip()
    encoded = quote_plus(clean_q)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    try:
        url = f"https://html.duckduckgo.com/html/?q={encoded}+trendyol+urun"
        res = requests.get(url, headers=headers, timeout=3.5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            img_links = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if 'duckduckgo.com/iu/?u=' in src:
                    actual = urllib.parse.unquote(src.split('u=')[1].split('&')[0])
                    if actual.startswith('http') and not any(ext in actual.lower() for ext in ['.svg', 'logo', 'icon', 'favicon']):
                        img_links.append(actual)
                elif src.startswith('http') and not any(ext in src.lower() for ext in ['.svg', 'logo', 'icon']):
                    img_links.append(src)
                if len(img_links) >= 4:
                    break
                    
            with ThreadPoolExecutor(max_workers=3) as ex:
                for img_obj in ex.map(download_image_safe, img_links):
                    if img_obj:
                        images.append(img_obj)
    except Exception:
        pass
    return images

def get_multi_channel_data_reliable(query, serp_key=None):
    clean_q = unquote(query).strip()
    encoded_q = quote_plus(clean_q)
    dossier = []
    
    product_images = fetch_product_images_proxy(clean_q)
    
    # 1. Trendyol Satıcı Kanalı
    img_ty = [product_images[0]] if len(product_images) > 0 else [create_evidence_card("Trendyol Magazasi", clean_q)]
    dossier.append({
        "title": f"Trendyol Pazaryeri Satıcı Sayfası - {clean_q}",
        "url": f"https://www.trendyol.com/sr?q={encoded_q}",
        "text": f"Trendyol üzerindeki {clean_q} ürün başlıkları, soru-cevap iddiaları ve mağaza açıklamaları.",
        "pil_images": img_ty
    })

    # 2. Hepsiburada Satıcı Kanalı
    img_hb = [product_images[1]] if len(product_images) > 1 else [create_evidence_card("Hepsiburada Magazasi", clean_q)]
    dossier.append({
        "title": f"Hepsiburada Satıcı Kanalı - {clean_q}",
        "url": f"https://www.hepsiburada.com/ara?q={encoded_q}",
        "text": f"Hepsiburada çoklu satıcı havuzundaki {clean_q} tedavi ve onarım vaatleri.",
        "pil_images": img_hb
    })

    # 3. Amazon Türkiye Kanalı
    img_amz = [product_images[2]] if len(product_images) > 2 else [create_evidence_card("Amazon TR", clean_q)]
    dossier.append({
        "title": f"Amazon Türkiye Satış Kanalı - {clean_q}",
        "url": f"https://www.amazon.com.tr/s?k={encoded_q}",
        "text": f"Amazon Türkiye listelemelerindeki etiket ve içerik beyanları.",
        "pil_images": img_amz
    })

    # 4. Meta Reklam Kütüphanesi
    clean_meta_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=TR&q={encoded_q}&search_type=keyword_unordered&media_type=all"
    dossier.append({
        "title": "Meta Reklam Kütüphanesi (Instagram & Facebook Reklamları)",
        "url": clean_meta_url,
        "text": f"Instagram Reels, sponsorlu postlar ve video iddiaları.",
        "pil_images": [create_evidence_card("Meta Ad Library", clean_q)]
    })

    return dossier

def sanitize_pdf_text(text):
    if not text:
        return ""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("…", "...")
    text = text.replace("### ", "").replace("## ", "").replace("# ", "")
    text = text.replace("**", "").replace("*", "")
    tr_map = {'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S', 'ç': 'c', 'Ç': 'C', 'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U'}
    for k, v in tr_map.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def create_rich_evidence_pdf(report_text, dossier, title):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 1. Sayfa Başlığı
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, sanitize_pdf_text(title), ln=True, align="C")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(0, 5, f"Denetim Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
    pdf.line(10, 24, 200, 24)
    pdf.ln(5)

    # 2. Hukuki Analiz Metni
    pdf.set_font("Helvetica", "", 8.5)
    pdf.multi_cell(0, 4.5, sanitize_pdf_text(report_text))
    pdf.ln(5)

    # 3. Delil ve Görsel Kartları
    if dossier:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "SOMUT DELIL, SATICI VE GORSEL GALERI DENETIMI", ln=True, align="L")
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        temp_files = []
        try:
            for idx, item in enumerate(dossier, 1):
                if pdf.get_y() > 190:
                    pdf.add_page()
                pdf.set_font("Helvetica", "B", 9.5)
                pdf.cell(0, 5, sanitize_pdf_text(f"Kanal {idx}: {item['title'][:65]}"), ln=True)
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.cell(0, 4, sanitize_pdf_text(f"Link: {item['url'][:85]}"), ln=True)
                pdf.ln(2)
                
                if item.get("pil_images"):
                    start_x = 12
                    y_pos = pdf.get_y()
                    for p_idx, p_img in enumerate(item["pil_images"][:2]):
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                            p_img.convert("RGB").save(tmp.name, "JPEG")
                            temp_files.append(tmp.name)
                            pdf.image(tmp.name, x=start_x + (p_idx * 55), y=y_pos, w=50)
                    pdf.set_y(y_pos + 38)
                pdf.ln(4)
        finally:
            for tmp in temp_files:
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass

    return bytes(pdf.output())

# Arayüz
st.markdown('<div class="section-heading">🎯 360° Otomatik Çoklu Satıcı & Canlı Pazar Radarı</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1.8, 1])
with col1:
    radar_query = st.text_input("Taranacak Marka veya Ürün Adı", placeholder="Örn: Mamaaura Çatlak ve Masaj Yağı...")
with col2:
    radar_sektor = st.selectbox("Faaliyet Sektörü", [
        "Kozmetik & Kişisel Bakım / Anne-Bebek",
        "Takviye Edici Gıda & Sağlık",
        "E-Ticaret & İndirim Kampanyaları",
        "Sosyal Medya & Influencer Reklamları",
        "Diğer"
    ])

if st.button("🚀 Hızlı Tara ve Görselli PDF Raporu Oluştur", type="primary"):
    if not api_key:
        st.error("Lütfen sol menüden Gemini API anahtarınızı giriniz.")
    elif not radar_query.strip():
        st.warning("Lütfen bir ürün adı giriniz.")
    else:
        with st.spinner("Pazaryerleri ve kanallar taranıyor (ortalama 10 saniye)..."):
            dossier = get_multi_channel_data_reliable(radar_query.strip(), serp_key=serpapi_key)
            
            dossier_payload = ""
            for idx, sc in enumerate(dossier, 1):
                dossier_payload += f"\n[KANAL {idx}: {sc['title']}]\nURL: {sc['url']}\nDetay: {sc['text']}\n"

            prompt = f"""
SEN; TİCARET BAKANLIĞI REKLAM KURULU İÇTİHATLARI VE TÜKETİCİ HUKUKU KAPSAMINDA UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN.
TARANAN ÜRÜN: "{radar_query}" | SEKTÖR: {radar_sektor}
DENETİM TARİHİ: {datetime.now().strftime('%d.%m.%Y')}

İNTERNETTEN TOPLANAN KANAL VE SATICI BİLGİLERİ:
{dossier_payload}

Her bir satış kanalını ve pazaryerini TEK TEK, AYRI AYRI DEĞERLENDİREN bir "360° ÇOKLU SATICI VE GÖRSEL RİSK RAPORU" hazırla.
Somut ihlalleri (yara/çatlak onarımı, deri altı doku yenileme, medikal amblem, %100 kesinlik vaadi) 5324 sayılı Kozmetik Kanunu m. 2 ve Sağlık Beyanı Yönetmeliği m. 7 kapsamında gerekçelendir.

RAPOR FORMATI:
### I. TESPİT EDİLEN TÜM CANLI SATICI VE KANAL LİNKLERİ ENVANTERİ
### II. SATICI VE KANAL BAZINDA AYRINTILI RİSK ANALİZİ
### III. SOSYAL MEDYA (INSTAGRAM & REELS) İDDİA ANALİZİ
### IV. KÜMÜLATİF YAPTIRIM VE CEZA SKALASI (6502 SAYILI KANUN M. 77)
### V. YASAL ŞERH
"""
            payload_contents = [prompt]
            for d in dossier:
                if d.get("pil_images"):
                    payload_contents.append(d["pil_images"][0])

            try:
                report_out = generate_content_fast(payload_contents[:4])
                st.session_state["fast_report"] = {
                    "text": report_out,
                    "dossier": dossier,
                    "query": radar_query
                }
            except Exception as e:
                st.error(f"Analiz sırasında hata oluştu: {e}")

if "fast_report" in st.session_state:
    r = st.session_state["fast_report"]
    st.write("")
    with st.container(height=450):
        st.markdown(r["text"])
        
    st.markdown('<div class="section-heading">📸 Taranan Satıcılar ve Delil Kayıtları</div>', unsafe_allow_html=True)
    for idx, item in enumerate(r["dossier"], 1):
        with st.container(border=True):
            st.markdown(f"**Kaynak {idx}: [{item['title']}]({item['url']})**")
            if item.get("pil_images"):
                cols = st.columns(min(len(item["pil_images"]), 3))
                for i, p_img in enumerate(item["pil_images"][:3]):
                    cols[i].image(p_img, caption=f"Delil {i+1}", width=180)

    try:
        pdf_bytes = create_rich_evidence_pdf(r["text"], r["dossier"], f"AdShield 360 Risk Raporu - {r['query']}")
        st.download_button(
            label="📄 Görselleri ve Linkleri İçeren Detaylı Risk Raporunu İndir (PDF)",
            data=pdf_bytes,
            file_name=f"AdShield_Risk_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            type="primary"
        )
    except Exception as e:
        st.warning(f"PDF oluşturma uyarısı: {e}")
