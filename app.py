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
import tempfile
import urllib.parse
from urllib.parse import urljoin, quote_plus
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Risk Denetim Platformu",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    <div class="firm-badge">Kurumsal Regülasyon & Denetim Motoru</div>
</div>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    with st.sidebar:
        st.header("Sistem Ayarları")
        api_key = st.text_input("Gemini API Key:", type="password")

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
        raise Exception("API anahtarı bulunamadı.")
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
    raise Exception(f"Model yanıtı alınamadı. Detay: {last_err}")

def download_single_img(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200 and len(res.content) > 3000:
            pil_img = Image.open(io.BytesIO(res.content))
            return optimize_image(pil_img)
    except Exception:
        pass
    return None

# Canlı Pazaryeri & Ürün Galeri Kazıma Motoru (Trendyol Gateway + Web Çözücü)
def fetch_real_marketplace_data(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        'Accept-Language': 'tr-TR,tr;q=0.9'
    }
    sellers_dossier = []
    
    try:
        # Trendyol Discovery Gateway API
        ty_api_url = f"https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr?q={quote_plus(query)}&pi=1&culture=tr-TR"
        r = requests.get(ty_api_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            products = data.get("result", {}).get("products", [])
            for p in products[:4]:
                name = p.get("name", "")
                brand = p.get("brand", {}).get("name", "")
                p_url = "https://www.trendyol.com" + p.get("url", "")
                merchant = p.get("merchantName", brand)
                price = p.get("price", {}).get("sellingPrice", "")
                
                # Yüksek çözünürlüklü CDN görselleri
                raw_images = p.get("images", [])
                img_urls = [f"https://cdn.dsmcdn.com{img_path}" if not img_path.startswith("http") else img_path for img_path in raw_images[:3]]
                
                pil_imgs = []
                with ThreadPoolExecutor(max_workers=3) as ex:
                    res_imgs = ex.map(lambda u: download_single_img(u, headers), img_urls)
                    for r_img in res_imgs:
                        if r_img:
                            pil_imgs.append(r_img)
                            
                sellers_dossier.append({
                    "title": f"Trendyol: {brand} - {name} (Satıcı: {merchant})",
                    "url": p_url,
                    "extracted_text": f"Ürün Adı: {name}\nSatıcı Mağaza: {merchant}\nFiyat: {price} TL",
                    "image_urls": img_urls,
                    "pil_images": pil_imgs
                })
    except Exception:
        pass

    # Eğer API'den sonuç dönmezse genel web aramasıyla link ve görsel topla
    if not sellers_dossier:
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query + ' trendyol hepsiburada')}"
            res = requests.get(ddg_url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                for a in soup.find_all('a', class_='result__url')[:3]:
                    href = a.get('href', '')
                    clean_link = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0]) if 'uddg=' in href else href
                    if clean_link.startswith("http"):
                        sellers_dossier.append({
                            "title": f"Pazaryeri Satış Sayfası ({urllib.parse.urlparse(clean_link).netloc})",
                            "url": clean_link,
                            "extracted_text": f"Tespit edilen canlı satış kanalı: {clean_link}",
                            "image_urls": [],
                            "pil_images": []
                        })
        except Exception:
            pass

    return sellers_dossier

@st.cache_data
def load_and_index_kararlar():
    corpus = ""
    txt_dosyalari = glob.glob("kararlar_tek_dosya.txt") + glob.glob("kararlar_havuzu*.txt") + glob.glob("kararlar_parca_*.txt")
    for txt_dosya in txt_dosyalari:
        try:
            with open(txt_dosya, "r", encoding="utf-8", errors="ignore") as f:
                corpus += f.read() + "\n"
        except Exception:
            continue
    karar_bloklari = re.split(r'=== EMSAL KARAR / BÜLTEN:|\n(?=Dosya No\s*:|\d{4}/\d+)', corpus)
    return [k.strip() for k in karar_bloklari if len(k.strip()) > 80]

karar_arsivi = load_and_index_kararlar()

def get_relevant_emsaller(metin, sektor, top_k=3):
    if not karar_arsivi:
        return "Karar arşivi yüklenemedi."
    sektor_keywords = {
        "Kozmetik & Kişisel Bakım / Anne-Bebek": ["kozmetik", "doğal", "bitkisel", "organik", "cilt", "leke", "kırışıklık", "titck", "onaylı", "tedavi", "mucize", "yok eder", "klinik", "sls", "paraben", "içermez"],
        "Takviye Edici Gıda & Sağlık": ["takviye", "gıda", "sağlık beyanı", "tedavi", "hastalık", "kilo", "zayıflama", "bağışıklık", "eklem", "ağrı", "şifa", "onay", "kesin son"],
        "E-Ticaret & İndirim Kampanyaları": ["indirim", "fiyat", "en ucuz", "tavsiye edilen", "stok", "bedava", "en çok satan", "fiyatı düştü", "efsane"],
        "Sosyal Medya & Influencer Reklamları": ["influencer", "işbirliği", "etiket", "örtülü reklam", "sosyal medya", "tanıtım", "link", "ortaklık", "sponsor"]
    }
    anahtarlar = set(sektor_keywords.get(sektor, []))
    if metin:
        anahtarlar.update(re.findall(r'\b\w{3,}\b', metin.lower())[:8])
    skorlu = []
    for karar in karar_arsivi:
        k_lower = karar.lower()
        skor = sum(k_lower.count(k) * 2 for k in anahtarlar)
        if "idari para" in k_lower or "durdurma" in k_lower or "dosya no" in k_lower:
            skor += 4
        if skor > 0:
            skorlu.append((skor, karar[:1200]))
    skorlu.sort(key=lambda x: x[0], reverse=True)
    secilenler = [k[1] for k in skorlu[:top_k]]
    return "\n\n--- [EMSAL KARAR METNİ] ---\n\n".join(secilenler if secilenler else karar_arsivi[:2])

def clean_markdown_text(text):
    if not text:
        return ""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("…", "...")
    text = text.replace("### ", "").replace("## ", "").replace("# ", "")
    text = text.replace("**", "").replace("*", "")
    return text

# Her Satıcı Bloğunun Altına Görselleri Doğrudan Gömen Gelişmiş PDF Rapor Motoru
def create_integrated_visual_pdf(report_text, item_dossier, header_title):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    font_path = "Roboto-Regular.ttf"
    font_yuklendi = False
    if os.path.exists(font_path) and os.path.getsize(font_path) > 10000:
        try:
            pdf.add_font("Roboto", "", font_path)
            font_yuklendi = True
        except Exception:
            font_yuklendi = False

    tr_map = str.maketrans("ğĞüÜşŞçÇ", "gGuUsScC")
    
    # 1. Başlık
    if font_yuklendi:
        pdf.set_font("Roboto", "", 13)
        pdf.cell(0, 7, header_title, ln=True, align="C")
        pdf.set_font("Roboto", "", 8.5)
        pdf.cell(0, 5, f"Denetim Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
    else:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 7, header_title.translate(tr_map), ln=True, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(0, 5, f"Denetim Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        
    pdf.line(10, 24, 200, 24)
    pdf.ln(5)

    # 2. Hukuki Analiz Metni
    clean_txt = clean_markdown_text(report_text)
    if not font_yuklendi:
        clean_txt = clean_txt.replace("İ", "I").replace("ı", "i").translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font("Helvetica", "", 8.5)
    else:
        pdf.set_font("Roboto", "", 9)
        
    pdf.multi_cell(0, 4.6, clean_txt)
    pdf.ln(6)

    # 3. Her Satıcı İçin Doğrudan İlgili Alana Görsellerin Basılması
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
                if pdf.get_y() > 200:
                    pdf.add_page()
                    
                title_str = f"Satıcı / Kanal {idx}: {item['title'][:65]}"
                url_str = f"Link: {item['url'][:85]}"
                
                if not font_yuklendi:
                    title_str = title_str.translate(tr_map)
                    url_str = url_str.translate(tr_map)
                    pdf.set_font("Helvetica", "B", 9)
                else:
                    pdf.set_font("Roboto", "", 9.5)
                    
                pdf.cell(0, 5, title_str, ln=True)
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.cell(0, 4, url_str, ln=True)
                pdf.ln(2)
                
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
                pdf.ln(4)
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
    "🎯 360° Canlı Ürün & Çoklu Satıcı Radarı (Görsel ve Linkli PDF Raporu)"
]

if "hedef_mod" not in st.session_state:
    st.session_state.hedef_mod = MODLAR[2]

if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
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

# MOD 3: 360° CANLI ÇOKLU SATICI & DOĞRUDAN GÖRSEL GÖMÜLÜ RADAR
if mod_secimi == "🎯 360° Canlı Ürün & Çoklu Satıcı Radarı (Görsel ve Linkli PDF Raporu)":
    st.markdown('<div class="section-heading" lang="tr">🎯 360° Çoklu Satıcı, Görsel Galeri & Link Bazlı Risk Radarı</div>', unsafe_allow_html=True)
    st.caption("Ürün veya marka adını girin; sistem Trendyol satıcılarını, kampanya görsellerini ve pazaryeri açıklamalarını canlı olarak çekip görselli PDF raporu oluştursun.")
    
    col_rad1, col_rad2 = st.columns([1.5, 1])
    with col_rad1:
        radar_urun_adi = st.text_input("Taranan Marka ve Ürün Adı", placeholder="Örn: Mamaaura Çatlak ve Masaj Yağı...")
    with col_rad2:
        radar_sektor = st.selectbox("Faaliyet Sektörü", [
            "Kozmetik & Kişisel Bakım / Anne-Bebek",
            "Takviye Edici Gıda & Sağlık",
            "E-Ticaret & İndirim Kampanyaları",
            "Sosyal Medya & Influencer Reklamları",
            "Diğer"
        ])

    if st.button("🚀 Çoklu Satıcıları ve Görselleri Canlı Denetle (Görselli PDF)", type="primary"):
        if not api_key:
            st.error("Lütfen geçerli bir Gemini API anahtarı tanımlayınız.")
        elif not radar_urun_adi.strip():
            st.warning("Lütfen bir ürün adı giriniz.")
        else:
            with st.spinner("1/3 Canlı pazar taraması yapılıyor; Trendyol satıcıları ve yüksek çözünürlüklü ürün fotoğrafları çekiliyor..."):
                scraped_sellers_dossier = fetch_real_marketplace_data(radar_urun_adi.strip())
                all_pil_images = []
                for s in scraped_sellers_dossier:
                    all_pil_images.extend(s.get("pil_images", []))

            with st.spinner("2/3 Çok modlu yapay zeka denetçisi satıcı iddialarını ve görsel delilleri analiz ediyor..."):
                dossier_payload = ""
                for idx, sc in enumerate(scraped_sellers_dossier, 1):
                    dossier_payload += f"\n--- [SATICI / KANAL {idx}: {sc['title']}] ---\n"
                    dossier_payload += f"URL: {sc['url']}\n"
                    dossier_payload += f"Metin / Açıklama:\n{sc['extracted_text']}\n"

                radar_analysis_prompt = f"""
SEN; TİCARET BAKANLIĞI REKLAM KURULU İÇTİHATLARI VE TÜKETİCİ HUKUKU KAPSAMINDA UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN.

TARANAN ÜRÜN / MARKA: "{radar_urun_adi}"
SEKTÖR: {radar_sektor}
DENETİM TARİHİ: {datetime.now().strftime('%d.%m.%Y')}

İNTERNETTEN CANLI OLARAK ÇEKİLEN SATICI VE GÖRSEL DELİL BİLGİLERİ:
{dossier_payload}

GÖREVİN:
Her bir satıcıyı, pazaryeri mağazasını ve ürün galeri görsellerini TEK TEK, AYRI AYRI DEĞERLENDİREN çok kapsamlı bir "360° ÇOKLU SATICI VE GÖRSEL RİSK RAPORU" hazırlamaktır.
Asla varsayımsal veya boş ifadeler kullanma; sektördeki ve görsellerdeki somut ihlalleri (yara izi onarımı, deri altı doku yenileme, medikal amblem, %100 kesinlik vaadi) doğrudan gerekçelendir.

RAPOR FORMATI:

### I. TESPİT EDİLEN TÜM SATICI VE KANAL LİNKLERİ
(İncelenen tüm Trendyol satıcıları ve doğrudan ürün linklerini listele).

### II. SATICI, LİNK VE GÖRSEL BAZINDA AYRINTILI RİSK ANALİZİ

#### [SATICI / KANAL 1]: (Platform Adı - Satıcı Başlığı)
* **İncelenen Satış Linki:** (Doğrudan URL)
* **Kullanılan Sloganlar & İddialar:** (Metindeki tırnak içi somut iddialar)
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
        
        st.markdown(f"**📡 İncelenen Ürün / Dosya:** `{r_info['urun']}` | **Sektör:** `{r_info['sektor']}`")
        
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
                        cols[p_i].image(p_img, caption=f"Görsel {p_i+1}", use_container_width=True)
                else:
                    st.info("Bu satıcı sayfası için görsel bağlantısı bulunamadı.")

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
            st.caption("PDF raporu; tüm satıcı linklerini, ihlal maddelerini ve görsel delil fotoğraflarını içerir.")

# MOD 1 & 2: MANUEL İÇ DENETİM VE PİYASA İNCELEMESİ
else:
    is_danisan = "İç Revizyon" in mod_secimi
    sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

    with sol_kolon:
        with st.container(border=True):
            panel_sol_baslik = "İncelenecek Kampanya Parametreleri" if is_danisan else "İncelenecek Piyasa / Rakip Materyali"
            st.markdown(f'<div class="section-heading" lang="tr">{panel_sol_baslik}</div>', unsafe_allow_html=True)

            sektor = st.selectbox("Faaliyet Sektörü", [
                "Kozmetik & Kişisel Bakım / Anne-Bebek",
                "Takviye Edici Gıda & Sağlık",
                "E-Ticaret & İndirim Kampanyaları",
                "Sosyal Medya & Influencer Reklamları",
                "Diğer"
            ])
            
            mecra = st.selectbox("Yayınlanacak / Yayınlanan Mecra", [
                "İnternet / Sosyal Medya (Instagram, TikTok, Web Sitesi)",
                "Satış Noktası (Eczane/Market Stantları, POS Materyali)",
                "Ulusal Televizyon Kanalı",
                "Yerel Televizyon / Radyo",
                "Açık Hava (Billboard, Broşür vb.)"
            ])
            
            reklam_url = st.text_input("Web Sayfası / Ürün Linki", placeholder="https://www.site.com/urun veya kampanya adresi...")
            reklam_metni = st.text_area("Reklam Metni / Ticari İddialar / Caption", height=120, placeholder="İncelenmesi talep edilen metin veya iddiaları giriniz...")
            yuklenen_gorseller = st.file_uploader("Reklam Görselleri / Taslaklar (Çoklu Yükleme)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            
            buton_etiketi = "Uyum Analizi ve Güvenli Revizyonu Başlat" if is_danisan else "Rakip İhlal Analizini Başlat"
            analiz_butonu = st.button(buton_etiketi, type="primary")

    with sag_kolon:
        with st.container(border=True):
            panel_baslik = "Mevzuat Uyum ve Güvenli Revizyon Raporu" if is_danisan else "Piyasa İhlal Tespiti ve Başvuru Merkezi"
            st.markdown(f'<div class="section-heading" lang="tr">{panel_baslik}</div>', unsafe_allow_html=True)
            
            if analiz_butonu:
                if not api_key:
                    st.error("Lütfen geçerli bir API anahtarı sağlayınız.")
                elif not reklam_metni and not yuklenen_gorseller and not reklam_url:
                    st.warning("Lütfen metin giriniz, link paylaşınız veya görsel yükleyiniz.")
                else:
                    birlestirilmis_metin = f"{reklam_metni}\n\n[Kaynak Link]: {reklam_url}" if reklam_url else reklam_metni
                    ilgili_emsaller = get_relevant_emsaller(birlestirilmis_metin, sektor)
                    
                    prompt = f"""
SEN; TİCARET BAKANLIĞI REKLAM KURULU İÇTİHATLARI VE 6502 SAYILI KANUN KAPSAMINDA UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN.
Sektör: {sektor} | Mecra: {mecra}
İddialar: {birlestirilmis_metin}

Ayrıntılı bir risk ve mevzuat uyum raporu hazırla.
"""
                    icerik_listesi = [prompt]
                    if yuklenen_gorseller:
                        for g in yuklenen_gorseller:
                            icerik_listesi.append(optimize_image(Image.open(g)))

                    with st.spinner("Analiz yapılıyor..."):
                        try:
                            tam_rapor = generate_content_safe(icerik_listesi)
                            st.session_state.rapor_sonucu = tam_rapor
                        except Exception as err:
                            st.error(f"Hata: {err}")

            if st.session_state.rapor_sonucu:
                with st.container(height=450):
                    st.markdown(st.session_state.rapor_sonucu)
            else:
                st.info("Sol panelden parametreleri belirleyip analizi başlattığınızda rapor bu alanda hazır hale gelecektir.")
