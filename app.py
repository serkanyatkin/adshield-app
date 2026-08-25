import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image, ImageDraw
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
import tempfile
import urllib.parse
from urllib.parse import quote_plus, unquote
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Otomatik Risk Denetim Radarı",
    layout="wide",
    initial_sidebar_state="expanded"
)

def trigger_scroll(position="top"):
    components.html(f"""
    <script>
        setTimeout(() => {{
            try {{
                const p = window.parent;
                const doc = p ? p.document : document;
                const container = doc.querySelector('[data-testid="stAppViewContainer"]') || 
                                  doc.querySelector('section.main') || 
                                  doc.documentElement || 
                                  doc.body;
                if ("{position}" === "bottom") {{
                    if (container) container.scrollTo({{ top: container.scrollHeight + 3000, behavior: 'smooth' }});
                    const el = doc.getElementById('page-bottom-anchor');
                    if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'end' }});
                }} else if ("{position}" === "top") {{
                    if (container) container.scrollTo({{ top: 0, behavior: 'smooth' }});
                    const el = doc.getElementById('page-top-anchor');
                    if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }} catch(e) {{}}
        }}, 200);
    </script>
    """, height=0, width=0)

st.markdown("""
<div id="page-top-anchor"></div>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .block-container {
        max-width: 1200px !important;
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }
    
    .firm-header {
        background-color: #5D728B;
        padding: 18px 26px;
        border-radius: 6px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(93, 114, 139, 0.18);
    }
    .firm-title {
        font-family: 'Cinzel', serif;
        font-size: 19px;
        letter-spacing: 1.5px;
        font-weight: 700;
    }
    .firm-subtitle {
        font-size: 11px;
        letter-spacing: 1px;
        color: #DCE4EC;
        margin-top: 2px;
    }
    .firm-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #ffffff;
        font-size: 11px;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 4px;
    }

    .mode-header-title {
        text-align: center;
        font-family: 'Cinzel', serif;
        font-size: 13.5px;
        letter-spacing: 1.5px;
        color: #2C3848;
        font-weight: 700;
        margin-bottom: 10px;
        text-transform: uppercase;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        justify-content: center;
        gap: 12px;
        width: 100%;
        margin-bottom: 10px;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: 1;
        background: #FFFFFF;
        border: 1.5px solid #CBD5E1;
        border-radius: 6px;
        padding: 12px 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        border-color: #5D728B;
        background: #F8FAFC;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        border-color: #5D728B !important;
        background-color: #F1F5F9 !important;
        box-shadow: 0 0 0 1px #5D728B, 0 3px 8px rgba(93, 114, 139, 0.12) !important;
        font-weight: 600 !important;
        color: #1E293B !important;
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
        border: 1px solid #4D6076 !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #4A5E74 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="firm-header" lang="tr">
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
    st.header("⚙️ Sistem & API Yapılandırması")
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
    serpapi_input = st.text_input("SerpApi Key (Google & Pazaryeri Derin Tarama):", type="password", value=serpapi_key or "")
    if serpapi_input:
        serpapi_key = serpapi_input
    
    st.markdown("---")
    st.caption("ℹ️ **Nasıl Çalışır?**\nSerpApi anahtarı girildiğinde Google Shopping, Trendyol satıcıları ve Meta arşivi bot engeline takılmadan taranır.")

def optimize_image(img, max_dimension=750):
    img = img.convert("RGB")
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return img

@st.cache_resource(show_spinner=False)
def get_active_models(current_api_key):
    fallback = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    if not current_api_key:
        return fallback
    try:
        genai.configure(api_key=current_api_key)
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name.replace("models/", ""))
        if available:
            return [m for m in available if "flash" in m] + [m for m in available if "flash" not in m]
    except Exception:
        pass
    return fallback

def generate_content_safe(contents, system_instruction=None):
    if not api_key:
        raise Exception("Gemini API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    models_to_try = get_active_models(api_key)
    last_err = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            continue
    raise Exception(f"Model yanıtı alınamadı: {last_err}")

# CDN Korumasını Aşan Güvenli Görsel İndirici
def download_single_img(url, default_referer="https://www.trendyol.com/"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': default_referer,
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
    }
    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200 and len(res.content) > 2000:
            pil_img = Image.open(io.BytesIO(res.content))
            return optimize_image(pil_img)
    except Exception:
        pass
    return None

def generate_evidence_card_image(channel_title, query_text):
    img = Image.new("RGB", (480, 260), color="#F8FAFC")
    draw = ImageDraw.Draw(img)
    draw.rectangle([5, 5, 475, 255], outline="#CBD5E1", width=2)
    draw.rectangle([10, 10, 470, 48], fill="#5D728B")
    draw.text((20, 22), "ADSHIELD OTOMATIK DELIL KAYDI", fill="#FFFFFF")
    draw.text((20, 75), f"Mecra: {channel_title[:45]}", fill="#1E293B")
    draw.text((20, 110), f"Urun: {query_text[:45]}", fill="#0F172A")
    draw.text((20, 150), "Pazaryeri Urunu & Ihlal Tespiti", fill="#DC2626")
    draw.text((20, 205), f"Denetim: {datetime.now().strftime('%d.%m.%Y %H:%M')}", fill="#64748B")
    return img

# Çoklu Kanal & Derin Arama Motoru
def execute_deep_multi_channel_search(query, custom_serp_key=None):
    clean_query = unquote(query).strip()
    encoded_q = quote_plus(clean_query)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9'
    }
    scraped_dossier = []
    
    # 1. SERPAPI VARSA (Google Shopping + Çoklu Site)
    if custom_serp_key:
        try:
            shop_url = f"https://serpapi.com/search.json?engine=google_shopping&q={encoded_q}&gl=tr&hl=tr&api_key={custom_serp_key}"
            shop_res = requests.get(shop_url, timeout=8).json()
            if "shopping_results" in shop_res:
                for item in shop_res["shopping_results"][:5]:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    merchant = item.get("source", "Pazaryeri Satıcısı")
                    price = item.get("price", "")
                    thumb = item.get("thumbnail", "")
                    
                    pil_imgs = []
                    if thumb:
                        d_img = download_single_img(thumb, default_referer="https://www.google.com/")
                        if d_img:
                            pil_imgs.append(d_img)
                            
                    scraped_dossier.append({
                        "title": f"Google Alışveriş: {merchant} ({title[:60]})",
                        "url": link,
                        "extracted_text": f"Ürün: {title}\nSatıcı: {merchant}\nFiyat: {price}\nAçıklama: {item.get('snippet', '')}",
                        "pil_images": pil_imgs
                    })
        except Exception:
            pass

    # 2. TRENDYOL DIRECT GATEWAY (Spesifik Ürün Sayfaları ve CDN Resimleri)
    try:
        ty_url = f"https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr?q={encoded_q}&pi=1&culture=tr-TR"
        r = requests.get(ty_url, headers=headers, timeout=6)
        if r.status_code == 200:
            data = r.json()
            products = data.get("result", {}).get("products", [])
            for p in products[:4]:
                name = p.get("name", "")
                brand = p.get("brand", {}).get("name", "")
                p_url = "https://www.trendyol.com" + p.get("url", "")
                merchant = p.get("merchantName", brand)
                price = p.get("price", {}).get("sellingPrice", "")
                
                raw_images = p.get("images", [])
                img_urls = [f"https://cdn.dsmcdn.com{img_path}" if not img_path.startswith("http") else img_path for img_path in raw_images[:3]]
                
                pil_imgs = []
                with ThreadPoolExecutor(max_workers=3) as ex:
                    res_imgs = ex.map(lambda u: download_single_img(u, default_referer="https://www.trendyol.com/"), img_urls)
                    for r_img in res_imgs:
                        if r_img:
                            pil_imgs.append(r_img)
                            
                if not pil_imgs:
                    pil_imgs.append(generate_evidence_card_image(f"Trendyol ({merchant})", clean_query))
                    
                scraped_dossier.append({
                    "title": f"Trendyol: {brand} - {name} (Satıcı: {merchant})",
                    "url": p_url,
                    "extracted_text": f"Ürün: {name}\nSatıcı: {merchant}\nFiyat: {price} TL\nMecra: Trendyol Pazaryeri",
                    "pil_images": pil_imgs
                })
    except Exception:
        pass

    # 3. YEDEK ARAMA (Hepsiburada / Amazon / Sosyal Medya)
    if len(scraped_dossier) < 3:
        sub_queries = [
            f"{clean_query} site:hepsiburada.com",
            f"{clean_query} site:amazon.com.tr"
        ]
        for sq in sub_queries:
            try:
                ddg_url = f"https://html.duckduckgo.com/html/?q={quote_plus(sq)}"
                res = requests.get(ddg_url, headers=headers, timeout=5)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for a in soup.find_all('a', class_='result__url')[:2]:
                        href = a.get('href', '')
                        clean_link = unquote(href.split('uddg=')[1].split('&')[0]) if 'uddg=' in href else href
                        
                        snippet_tag = a.find_parent('div', class_='result__body')
                        snippet = ""
                        title = ""
                        if snippet_tag:
                            s_elem = snippet_tag.find('a', class_='result__snippet')
                            t_elem = snippet_tag.find('a', class_='result__a')
                            snippet = s_elem.text.strip() if s_elem else ""
                            title = t_elem.text.strip() if t_elem else clean_link
                            
                        if clean_link.startswith("http") and not any(ign in clean_link for ign in ["duckduckgo.com", "yandex", "bing"]):
                            if not any(d["url"] == clean_link for d in scraped_dossier):
                                scraped_dossier.append({
                                    "title": title if title else f"Satış Kanalı ({clean_link[:45]})",
                                    "url": clean_link,
                                    "extracted_text": f"Başlık: {title}\nİddialar: {snippet}",
                                    "pil_images": [generate_evidence_card_image(title if title else "Pazaryeri", clean_query)]
                                })
            except Exception:
                pass

    # 4. Meta Reklam Kütüphanesi Temiz Bağlantısı
    clean_meta_url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=TR&q={encoded_q}&search_type=keyword_unordered&media_type=all"
    scraped_dossier.append({
        "title": "Meta Reklam Kütüphanesi (Instagram & Facebook Aktif Video/Görsel Reklamları)",
        "url": clean_meta_url,
        "extracted_text": f"Markaya ait Instagram Reels video reklamları, sponsorlu influencer tanıtımları ve görsel feed reklam arşivi.",
        "pil_images": [generate_evidence_card_image("Meta Ad Library (Instagram)", clean_query)]
    })

    return scraped_dossier

def sanitize_text_for_pdf(text, use_unicode=False):
    if not text:
        return ""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("…", "...")
    text = text.replace("### ", "").replace("## ", "").replace("# ", "")
    text = text.replace("**", "").replace("*", "")
    
    if not use_unicode:
        tr_chars = {
            'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
            'ş': 's', 'Ş': 'S', 'ç': 'c', 'Ç': 'C',
            'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U'
        }
        for k, v in tr_chars.items():
            text = text.replace(k, v)
        text = text.encode('latin-1', 'replace').decode('latin-1')
        
    return text

def get_pdf_font():
    font_path = "Roboto-Regular.ttf"
    if not os.path.exists(font_path) or os.path.getsize(font_path) < 10000:
        try:
            url = "https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto-Regular.ttf"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass
    return os.path.exists(font_path) and os.path.getsize(font_path) > 10000

# Her Satıcı Kartının Altına Görselleri Doğrudan Gömen Gelişmiş PDF Rapor Motoru
def create_integrated_visual_pdf(report_text, item_dossier, header_title):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    font_yuklendi = get_pdf_font()
    if font_yuklendi:
        try:
            pdf.add_font("Roboto", "", "Roboto-Regular.ttf")
        except Exception:
            font_yuklendi = False

    # 1. Başlık Alanı
    if font_yuklendi:
        pdf.set_font("Roboto", "", 13)
        pdf.cell(0, 7, sanitize_text_for_pdf(header_title, use_unicode=True), ln=True, align="C")
        pdf.set_font("Roboto", "", 8.5)
        pdf.cell(0, 5, f"Denetim Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
    else:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 7, sanitize_text_for_pdf(header_title, use_unicode=False), ln=True, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(0, 5, f"Denetim Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        
    pdf.line(10, 24, 200, 24)
    pdf.ln(5)

    # 2. Hukuki Analiz Metni
    clean_txt = sanitize_text_for_pdf(report_text, use_unicode=font_yuklendi)
    if font_yuklendi:
        pdf.set_font("Roboto", "", 9)
    else:
        pdf.set_font("Helvetica", "", 8.5)
        
    pdf.multi_cell(0, 4.6, clean_txt)
    pdf.ln(6)

    # 3. Her Satıcı ve Görsel Kanıt İçin Doğrudan Blok
    if item_dossier:
        pdf.add_page()
        if font_yuklendi:
            pdf.set_font("Roboto", "", 11)
            pdf.cell(0, 7, "SOMUT DELİL, SATICI VE GÖRSEL GALERİ DENETİMİ", ln=True, align="L")
        else:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "SOMUT DELIL, SATICI VE GORSEL GALERI DENETIMI", ln=True, align="L")
            
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        temp_files = []
        try:
            for idx, item in enumerate(item_dossier, 1):
                if pdf.get_y() > 195:
                    pdf.add_page()
                    
                title_str = sanitize_text_for_pdf(f"Kanal / Satıcı {idx}: {item['title'][:70]}", use_unicode=font_yuklendi)
                url_str = sanitize_text_for_pdf(f"Canlı Link: {item['url'][:95]}", use_unicode=font_yuklendi)
                
                if font_yuklendi:
                    pdf.set_font("Roboto", "", 10)
                    pdf.cell(0, 5, title_str, ln=True)
                    pdf.set_font("Roboto", "", 7.5)
                    pdf.cell(0, 4, url_str, ln=True)
                else:
                    pdf.set_font("Helvetica", "B", 9.5)
                    pdf.cell(0, 5, title_str, ln=True)
                    pdf.set_font("Helvetica", "", 7.5)
                    pdf.cell(0, 4, url_str, ln=True)
                pdf.ln(2)
                
                # Görselleri Yan Yana Yerleştir
                if item.get("pil_images"):
                    start_x = 12
                    y_pos = pdf.get_y()
                    img_width = 44
                    for p_idx, p_img in enumerate(item["pil_images"][:3]):
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                            p_img.convert("RGB").save(tmp.name, "JPEG")
                            temp_files.append(tmp.name)
                            pdf.image(tmp.name, x=start_x + (p_idx * 48), y=y_pos, w=img_width)
                    pdf.set_y(y_pos + 48)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    pdf.cell(0, 4, "[Görsel delil kaydı veritabanına eklenmiştir]", ln=True)
                pdf.ln(5)
        finally:
            for tmp_name in temp_files:
                if os.path.exists(tmp_name):
                    try:
                        os.remove(tmp_name)
                    except Exception:
                        pass

    return bytes(pdf.output())

# Session State
MODLAR = [
    "Kurumsal Kampanya Uyum Denetimi (İç Revizyon)",
    "Piyasa ve Rakip Reklam İncelemesi (Şikayet Modu)",
    "🎯 360° Otomatik Çoklu Satıcı & Canlı Pazar Radarı (Seçenek B - API & PDF)"
]

if "hedef_mod" not in st.session_state:
    st.session_state.hedef_mod = MODLAR[2]

if "radar_canli_rapor" not in st.session_state:
    st.session_state.radar_canli_rapor = None

st.markdown('<div class="mode-header-title" lang="tr">İnceleme Modunu Seçiniz</div>', unsafe_allow_html=True)

secili_indeks = MODLAR.index(st.session_state.hedef_mod) if st.session_state.hedef_mod in MODLAR else 2

mod_secimi = st.radio(
    "Denetim Modu",
    MODLAR,
    index=secili_indeks,
    horizontal=True,
    label_visibility="collapsed"
)

st.session_state.hedef_mod = mod_secimi

# MOD 3: TAM OTOMATİK SEÇENEK B RADARI
if mod_secimi == "🎯 360° Otomatik Çoklu Satıcı & Canlı Pazar Radarı (Seçenek B - API & PDF)":
    st.markdown('<div class="section-heading" lang="tr">🎯 360° Otomatik Çoklu Satıcı & Canlı Pazar Radarı</div>', unsafe_allow_html=True)
    st.caption("Sadece ürün adını girin; sistem Google Shopping, Trendyol satıcıları, Hepsiburada, Amazon ve Instagram reklamlarını eş zamanlı tarayarak 10+ kanaldan oluşan görselli PDF raporunu hazırlasın.")
    
    col_rad1, col_rad2 = st.columns([1.8, 1])
    with col_rad1:
        radar_urun_adi = st.text_input("Taranacak Marka veya Ürün Adı", placeholder="Örn: Mamaaura Çatlak ve Masaj Yağı...")
    with col_rad2:
        radar_sektor = st.selectbox("Faaliyet Sektörü", [
            "Kozmetik & Kişisel Bakım / Anne-Bebek",
            "Takviye Edici Gıda & Sağlık",
            "E-Ticaret & İndirim Kampanyaları",
            "Sosyal Medya & Influencer Reklamları",
            "Diğer"
        ])

    if st.button("🚀 Tüm Mecraları Derinlemesine Tara ve Görselli PDF Raporu Oluştur", type="primary"):
        if not api_key:
            st.error("Lütfen sol menüden geçerli bir Gemini API anahtarı giriniz.")
        elif not radar_urun_adi.strip():
            st.warning("Lütfen taranacak bir marka veya ürün adı giriniz.")
        else:
            with st.spinner("1/3 Eş zamanlı arama motorları çalıştırılıyor; Trendyol, Hepsiburada ve Google Alışveriş satıcıları taranıyor..."):
                scraped_sellers_dossier = execute_deep_multi_channel_search(radar_urun_adi.strip(), custom_serp_key=serpapi_key)
                
                all_pil_images = []
                for s in scraped_sellers_dossier:
                    all_pil_images.extend(s.get("pil_images", []))

            with st.spinner(f"2/3 Toplanan {len(scraped_sellers_dossier)} adet canlı kanal ve görsel delil Reklam Kurulu mevzuatına göre analiz ediliyor..."):
                dossier_payload = ""
                for idx, sc in enumerate(scraped_sellers_dossier, 1):
                    dossier_payload += f"\n--- [KANAL / SATICI {idx}: {sc['title']}] ---\n"
                    dossier_payload += f"URL: {sc['url']}\n"
                    dossier_payload += f"Sayfa / Ürün Metni:\n{sc['extracted_text']}\n"

                radar_analysis_prompt = f"""
SEN; TİCARET BAKANLIĞI REKLAM KURULU İÇTİHATLARI VE TÜKETİCİ HUKUKU KAPSAMINDA ÇALIŞAN UZMAN BİR REKLAM HUKUKU BAŞDENETÇİSİSİN.

TARANAN ÜRÜN / MARKA: "{radar_urun_adi}"
SEKTÖR: {radar_sektor}
DENETİM TARİHİ: {datetime.now().strftime('%d.%m.%Y')}

İNTERNETTEN ÇEKİLEN {len(scraped_sellers_dossier)} ADET CANLI KANAL BİLGİSİ:
{dossier_payload}

GÖREVİN:
Her bir satıcıyı, pazaryeri mağazasını ve ürün sayfasını TEK TEK, AYRI AYRI DEĞERLENDİREN kapsamlı bir "360° ÇOKLU SATICI VE GÖRSEL RİSK RAPORU" hazırlamaktır.
Sektördeki ve taranan verilerdeki somut ihlalleri (yara/çatlak onarımı, deri altı doku yenileme, medikal haç amblemi, %100 kesinlik vaadi, sahte indirim) doğrudan kanun maddeleriyle gerekçelendir.

RAPOR FORMATI:

### I. TESPİT EDİLEN TÜM CANLI SATICI VE KANAL LİNKLERİ ENVANTERİ
(Taranan tüm pazaryeri satıcıları, doğrudan ürün sayfaları ve Meta Reklam Kütüphanesi linklerini temiz URL adresleriyle listele).

### II. SATICI, LİNK VE GÖRSEL BAZINDA AYRINTILI RİSK ANALİZİ

#### [SATICI / KANAL 1]: (Platform Adı - Satıcı Başlığı)
* **İncelenen Satış Linki:** (Doğrudan URL)
* **Kullanılan Sloganlar & İddialar:** (Metindeki somut iddialar)
* **Görsel Galeri & Ambalaj Rozeti Analizi:** (Ambalaj üstündeki medikal semboller, Before/After ve '%...' yok eder vaatleri)
* **Mevzuata Aykırılık Tespiti:** (5324 sayılı Kozmetik Kanunu m. 2, Sağlık Beyanı Yönetmeliği m. 7)
* **Satıcı Risk Derecesi:** [YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

#### [SATICI / KANAL 2]: (Platform Adı - Satıcı Başlığı)
* **İncelenen Satış Linki:** (Doğrudan URL)
* **Kullanılan Sloganlar & İddialar:**
* **Görsel Galeri & Ambalaj Rozeti Analizi:**
* **Mevzuata Aykırılık Tespiti:**
* **Satıcı Risk Derecesi:** [YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

### III. SOSYAL MEDYA (INSTAGRAM REELS & VİDEO) İDDİA ANALİZİ
* **Video İçi Sözlü İfadeler:** (Deri altı yağ parçalama, ameliyat izi silme söylemleri)
* **Hassas Kitle İstismarı:** (Lohusa, emziren anne ve estetik kaygı istismarı)

### IV. KÜMÜLATİF YAPTIRIM VE CEZA SKALASI (6502 SAYILI KANUN M. 77)
* **Mecra Bazlı İdari Para Cezası ve Durdurma/Toplatma Riski**

### V. YASAL ŞERH
"Bu rapor AdShield tarafından toplanan canlı delil verileri incelenerek oluşturulmuş teknik bir ön risk analizi olup, nihai hukuki mütalaa yerine geçmez."
"""
                try:
                    payload_list = [radar_analysis_prompt]
                    if all_pil_images:
                        payload_list.extend(all_pil_images[:6])
                        
                    tam_rapor = generate_content_safe(payload_list)
                    st.session_state.radar_canli_rapor = {
                        "urun": radar_urun_adi,
                        "sektor": radar_sektor,
                        "rapor": tam_rapor,
                        "dossier": scraped_sellers_dossier
                    }
                except Exception as e:
                    st.error(f"Radar analizi sırasında hata oluştu: {e}")

    # Rapor ve Satıcı Galeri Kartlarının Gösterimi
    if st.session_state.radar_canli_rapor:
        st.write("")
        r_info = st.session_state.radar_canli_rapor
        
        st.markdown(f"**📡 İncelenen Ürün:** `{r_info['urun']}` | **Sektör:** `{r_info['sektor']}` | **Bulunan Kanal Sayısı:** `{len(r_info['dossier'])}`")
        
        with st.container(height=480):
            st.markdown(r_info['rapor'])
            
        st.markdown('<div class="section-heading" lang="tr">📸 Taranan Satıcılar ve İndirilen Galeri Görselleri</div>', unsafe_allow_html=True)
        
        for idx, item in enumerate(r_info["dossier"], 1):
            with st.container(border=True):
                st.markdown(f"**Kaynak {idx}: [{item['title']}]({item['url']})**")
                st.caption(f"🔗 Doğrudan Link: `{item['url']}`")
                
                if item.get("pil_images"):
                    cols = st.columns(min(len(item["pil_images"]), 4))
                    for p_i, p_img in enumerate(item["pil_images"][:4]):
                        cols[p_i].image(p_img, caption=f"Delil {p_i+1}", use_container_width=True)

        st.write("")
        col_p1, col_p2 = st.columns([1.6, 1])
        with col_p1:
            try:
                pdf_bytes = create_integrated_visual_pdf(
                    r_info['rapor'], 
                    r_info['dossier'], 
                    f"AdShield 360 Coklu Satici Risk Raporu - {r_info['urun']}"
                )
                st.download_button(
                    label="📄 Görselleri ve Linkleri İçeren Detaylı Risk Raporunu İndir (PDF)",
                    data=pdf_bytes,
                    file_name=f"AdShield_Coklu_Satici_Risk_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            except Exception as e:
                st.warning(f"Görselli PDF oluşturma uyarısı: {e}")
        with col_p2:
            st.caption("PDF raporu; taranan tüm canlı satıcı linklerini, iddiaları ve fiziksel delil kartlarını içerir.")

# MOD 1 & 2: MANUEL İÇ DENETİM VE PİYASA İNCELEMESİ
else:
    st.info("Kurumsal Kampanya Uyum veya Piyasa Şikayet modlarını kullanmak için üst menüden seçim yapabilirsiniz.")
