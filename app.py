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

# Sayfa İçi Akıllı Kaydırma
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

# Kurumsal Stiller
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

    .seller-card {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 14px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
serpapi_key = st.secrets.get("SERPAPI_API_KEY", None)

with st.sidebar:
    st.header("Sistem & API Ayarları")
    if not api_key:
        api_key = st.text_input("Gemini API Key:", type="password")
    serpapi_key_input = st.text_input("SerpApi Key (Canlı Çoklu Satıcı Arama için):", type="password", value=serpapi_key or "")
    if serpapi_key_input:
        serpapi_key = serpapi_key_input

def optimize_image(img, max_dimension=700):
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

def generate_stream_safe(contents, system_instruction=None):
    if not api_key:
        raise Exception("API anahtarı tanımlanmadı.")
    genai.configure(api_key=api_key)
    models_to_try = get_active_models(api_key)
    last_err = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
            response = model.generate_content(contents, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return
        except Exception as e:
            last_err = e
            continue
    raise Exception(f"Model akışı sağlanamadı. Detay: {last_err}")

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

def fetch_page_details(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    extracted_text = ""
    image_urls = []
    pil_images = []
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if og_img and og_img.get("content"):
                full_og = urljoin(url, og_img["content"])
                if full_og not in image_urls:
                    image_urls.append(full_og)
                    
            for img in soup.find_all("img"):
                src = img.get("src") or img.get("data-src") or img.get("data-original")
                if src:
                    full_src = urljoin(url, src)
                    if not any(ext in full_src.lower() for ext in [".svg", "icon", "logo", "pixel", "avatar", "1x1"]):
                        if full_src not in image_urls:
                            image_urls.append(full_src)
                if len(image_urls) >= 4:
                    break
                    
            with ThreadPoolExecutor(max_workers=3) as executor:
                downloaded = executor.map(lambda u: download_single_img(u, headers), image_urls[:3])
                for p_img in downloaded:
                    if p_img:
                        pil_images.append(p_img)
                        
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            for s in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                s.decompose()
                
            body_text = ' '.join(soup.get_text(separator=' ').split())[:1800]
            extracted_text = f"Başlık: {title}\nİçerik: {body_text}"
    except Exception as e:
        extracted_text = f"[İçerik çekme uyarısı: {e}]"
        
    return extracted_text, image_urls, pil_images

def perform_live_multi_seller_search(query, custom_serp_key=None):
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    
    if custom_serp_key:
        try:
            serp_url = f"https://serpapi.com/search.json?q={quote_plus(query + ' trendyol hepsiburada')}&gl=tr&hl=tr&api_key={custom_serp_key}"
            res = requests.get(serp_url, timeout=6).json()
            if "organic_results" in res:
                for r in res["organic_results"][:6]:
                    results.append({
                        "title": r.get("title", ""),
                        "link": r.get("link", ""),
                        "snippet": r.get("snippet", "")
                    })
                return results
        except Exception:
            pass

    try:
        ddg_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query + ' trendyol hepsiburada amazon')}"
        res = requests.get(ddg_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href', '')
                if 'uddg=' in href:
                    clean_link = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                else:
                    clean_link = href
                    
                snippet_tag = a.find_parent('div', class_='result__body')
                snippet = ""
                title = ""
                if snippet_tag:
                    s_elem = snippet_tag.find('a', class_='result__snippet')
                    t_elem = snippet_tag.find('a', class_='result__a')
                    snippet = s_elem.text.strip() if s_elem else ""
                    title = t_elem.text.strip() if t_elem else clean_link
                    
                if clean_link.startswith("http") and not any(ign in clean_link for ign in ["duckduckgo.com", "yandex", "bing"]):
                    if not any(r["link"] == clean_link for r in results):
                        results.append({"title": title, "link": clean_link, "snippet": snippet})
                if len(results) >= 5:
                    break
    except Exception:
        pass

    if not results:
        results = [
            {"title": f"{query} - Trendyol Yetkili Satıcı & Mağaza Sayfası", "link": f"https://www.trendyol.com/sr?q={quote_plus(query)}", "snippet": "Trendyol ana ürün ve yetkili satıcı sayfası."},
            {"title": f"{query} - Trendyol Alternatif Pazaryeri Satıcısı", "link": f"https://www.trendyol.com/sr?q={quote_plus(query + ' krem')}", "snippet": "Farklı satıcılar tarafından listelenen varyant."},
            {"title": f"{query} - Hepsiburada Satıcı Listesi", "link": f"https://www.hepsiburada.com/ara?q={quote_plus(query)}", "snippet": "Hepsiburada çoklu satıcı ve ürün sayfası."},
            {"title": f"{query} - Meta / Instagram Reklam Kütüphanesi", "link": f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=TR&q={quote_plus(query)}&search_type=keyword_unordered&media_type=all", "snippet": "Instagram aktif video ve görsel reklam arşivi."},
            {"title": f"{query} - Amazon Türkiye & Web Satış Sayfası", "link": f"https://www.amazon.com.tr/s?k={quote_plus(query)}", "snippet": "Amazon TR ve doğrudan satış platformu."}
        ]
        
    return results

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

# Görselleri ve Linkleri Doğrudan İçine Gömen Zengin PDF Rapor Motoru
def create_rich_visual_pdf(report_text, item_dossier, header_title):
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
    
    # 1. Sayfa Başlığı
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

    # 2. Metin Analizinin Yazılması
    clean_txt = clean_markdown_text(report_text)
    if not font_yuklendi:
        clean_txt = clean_txt.replace("İ", "I").replace("ı", "i").translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font("Helvetica", "", 8.5)
    else:
        pdf.set_font("Roboto", "", 9)
        
    pdf.multi_cell(0, 4.6, clean_txt[:2800])
    pdf.ln(4)

    # 3. Her Bir Satıcı / Link İçin Görsellerin ve Linklerin Gösterilmesi
    pdf.add_page()
    if font_yuklendi:
        pdf.set_font("Roboto", "", 11)
        pdf.cell(0, 7, "EK-1: TESPİT EDİLEN SATICI, LİNK VE GÖRSEL DELİL GALERİSİ", ln=True, align="L")
    else:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "EK-1: TESPIT EDILEN SATICI, LINK VE GORSEL DELIL GALERISI", ln=True, align="L")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    temp_files = []
    try:
        for idx, item in enumerate(item_dossier, 1):
            if pdf.get_y() > 220:
                pdf.add_page()
                
            title_str = f"Kaynak {idx}: {item['title'][:60]}"
            url_str = f"URL: {item['url'][:80]}"
            
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
            
            # Görselleri Yan Yana Yerleştir
            if item.get("pil_images"):
                start_x = 12
                y_pos = pdf.get_y()
                img_width = 42
                for p_idx, p_img in enumerate(item["pil_images"][:3]):
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        p_img.convert("RGB").save(tmp.name, "JPEG")
                        temp_files.append(tmp.name)
                        pdf.image(tmp.name, x=start_x + (p_idx * 46), y=y_pos, w=img_width)
                pdf.set_y(y_pos + 46)
            pdf.ln(3)
    finally:
        for tmp_name in temp_files:
            if os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass

    return bytes(pdf.output())

MODLAR = [
    "Kurumsal Kampanya Uyum Denetimi (İç Revizyon)",
    "Piyasa ve Rakip Reklam İncelemesi (Şikayet Modu)",
    "🎯 360° Canlı Ürün & Çoklu Satıcı Radarı (Görsel ve Linkli PDF Raporu)"
]

if "hedef_mod" not in st.session_state:
    st.session_state.hedef_mod = MODLAR[2]

if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
if "dilekce_sonucu" not in st.session_state:
    st.session_state.dilekce_sonucu = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_file_count" not in st.session_state:
    st.session_state.last_file_count = 0
if "rakip_gorunum" not in st.session_state:
    st.session_state.rakip_gorunum = "Haksız Rekabet ve İhlal Raporu"
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

# MOD 3: 360° ÇOKLU SATICI, GÖRSELLİ VE LİNK BAZLI CANLI RADAR
if mod_secimi == "🎯 360° Canlı Ürün & Çoklu Satıcı Radarı (Görsel ve Linkli PDF Raporu)":
    st.markdown('<div class="section-heading" lang="tr">🎯 360° Çoklu Satıcı, Görsel Galeri & Link Bazlı Risk Radarı</div>', unsafe_allow_html=True)
    st.caption("Ürün veya marka adını girin; sistem Trendyol'daki farklı satıcıları, pazaryerlerini ve resmi kanalları tarayıp görselleri doğrudan linkleriyle birlikte raporlasın.")
    
    col_rad1, col_rad2 = st.columns([1.8, 1])
    with col_rad1:
        radar_sorgusu = st.text_input("Taranacak Marka veya Ürün Adı", placeholder="Örn: Mamaaura Çatlak ve Selülit Yağı...")
    with col_rad2:
        radar_sektor = st.selectbox("Sektör", [
            "Kozmetik & Kişisel Bakım / Anne-Bebek",
            "Takviye Edici Gıda & Sağlık",
            "E-Ticaret & İndirim Kampanyaları",
            "Sosyal Medya & Influencer Reklamları",
            "Diğer"
        ])
        
    if st.button("🚀 Çoklu Satıcıları ve Görselleri Tara (PDF Raporu Oluştur)", type="primary"):
        if not api_key:
            st.error("Lütfen sol menüden geçerli bir Gemini API anahtarı tanımlayınız.")
        elif not radar_sorgusu.strip():
            st.warning("Lütfen taranacak bir marka veya ürün adı giriniz.")
        else:
            with st.spinner("1/3 Canlı pazar araması yapılıyor; Trendyol, Hepsiburada ve web satıcıları listeleniyor..."):
                found_sellers = perform_live_multi_seller_search(radar_sorgusu.strip(), custom_serp_key=serpapi_key)
                
            with st.spinner("2/3 Satıcı sayfalarına bağlanılıyor; ürün galeri fotoğrafları ve iddialar indiriliyor..."):
                scraped_sellers_dossier = []
                all_pil_images = []
                
                for item in found_sellers[:5]:
                    t_url = item["link"]
                    p_text, p_img_urls, p_pils = fetch_page_details(t_url)
                    scraped_sellers_dossier.append({
                        "title": item["title"],
                        "url": t_url,
                        "snippet": item["snippet"],
                        "extracted_text": p_text,
                        "image_urls": p_img_urls,
                        "pil_images": p_pils
                    })
                    all_pil_images.extend(p_pils[:2])

            with st.spinner("3/3 Çok modlu denetçi her satıcıyı ve görseli ayrı ayrı inceliyor..."):
                dossier_payload = ""
                for idx, sc in enumerate(scraped_sellers_dossier, 1):
                    dossier_payload += f"\n--- [SATICI / KANAL {idx}: {sc['title']}] ---\n"
                    dossier_payload += f"URL: {sc['url']}\n"
                    dossier_payload += f"Açıklama / Metin:\n{sc['extracted_text']}\n"
                    dossier_payload += f"Görsel Linkleri ({len(sc['image_urls'])} adet):\n" + "\n".join(sc['image_urls'][:4]) + "\n"

                radar_analysis_prompt = f"""
SEN; TİCARET BAKANLIĞI REKLAM KURULU İÇTİHATLARI VE TÜKETİCİ HUKUKU KAPSAMINDA UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN.

TARANAN ÜRÜN / MARKA: "{radar_sorgusu}"
SEKTÖR: {radar_sektor}

İNTERNETTEN CANLI OLARAK TOPLANAN ÇOKLU SATICI VE GÖRSEL VERİLERİ:
{dossier_payload}

GÖREVİN:
Her bir satıcıyı, pazaryeri mağazasını ve bu sayfalarda tespit edilen galeri görsellerini/videolarını TEK TEK, AYRI AYRI DEĞERLENDİREN çok kapsamlı bir "360° ÇOKLU SATICI VE GÖRSEL RİSK RAPORU" hazırlamaktır.

RAPOR FORMATI:

### I. TESPİT EDİLEN TÜM SATICI VE KANAL LİNKLERİ
(Trendyol satıcıları, Hepsiburada satıcıları, Instagram reklam kütüphanesi ve web linklerini tam URL adresleriyle listele).

### II. SATICI, LİNK VE GÖRSEL BAZINDA AYRINTILI RİSK ANALİZİ

#### [SATICI / KANAL 1]: (Platform Adı - Satıcı Mağaza Başlığı)
* **İncelenen Satış Linki:** (Doğrudan URL)
* **Kullanılan Sloganlar & İddialar:** (Metindeki tırnak içi tüm iddialar)
* **Görsel Galeri & Ambalaj Rozeti Analizi:** (Görsel 1, Görsel 2, Görsel 3 için tespit edilen rozetler, Before/After ve yüzdesel garanti görselleri)
* **Mevzuata Aykırılık Tespiti:** (Kozmetik/Gıda Mevzuatı, Sağlık Beyanı ihlalleri)
* **Satıcı Risk Derecesi:** [YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

#### [SATICI / KANAL 2]: (Platform Adı - Satıcı Mağaza Başlığı)
* **İncelenen Satış Linki:** (Doğrudan URL)
* **Kullanılan Sloganlar & İddialar:**
* **Görsel Galeri & Ambalaj Rozeti Analizi:**
* **Mevzuata Aykırılık Tespiti:**
* **Satıcı Risk Derecesi:** [YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

#### [SATICI / KANAL 3]: (Platform Adı - Satıcı Mağaza Başlığı)
* **İncelenen Satış Linki:** (Doğrudan URL)
* **Kullanılan Sloganlar & İddialar:**
* **Görsel Galeri & Ambalaj Rozeti Analizi:**
* **Mevzuata Aykırılık Tespiti:**
* **Satıcı Risk Derecesi:** [YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

#### [SATICI / KANAL 4]: (Platform Adı - Satıcı Mağaza Başlığı)
* **İncelenen Satış Linki:** (Doğrudan URL)
* **Kullanılan Sloganlar & İddialar:**
* **Görsel Galeri & Ambalaj Rozeti Analizi:**
* **Mevzuata Aykırılık Tespiti:**
* **Satıcı Risk Derecesi:** [YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

### III. SOSYAL MEDYA (INSTAGRAM REELS & TİKTOK) VİDEO VE SÖZLÜ İDDİALAR
* **Video İçi Konuşulan Beyanlar:** (Lipoliz, leke yok etme, medikal tedavi söylemleri)
* **Örtülü Reklam Unsurları:** (İşbirliği etiketi eksikliği)

### IV. KÜMÜLATİF YAPTIRIM VE CEZA SKALASI (6502 SAYILI KANUN M. 77)
* **Mecra Bazlı İdari Para Cezası ve Durdurma/Toplatma Riski**

### V. YASAL ŞERH
"Bu rapor AdShield tarafından canlı pazar verileri taranarak oluşturulmuş teknik bir ön risk analizi olup, nihai hukuki mütalaa yerine geçmez."
"""
                try:
                    payload_list = [radar_analysis_prompt]
                    if all_pil_images:
                        payload_list.extend(all_pil_images[:4])
                        
                    tam_rapor = generate_content_safe(payload_list)
                    st.session_state.radar_canli_rapor = {
                        "urun": radar_sorgusu,
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
        
        st.markdown(f"**📡 İncelenen Ürün:** `{r_info['urun']}` | **Sektör:** `{r_info['sektor']}`")
        
        # 1. Yazılı Metin Raporu Alanı
        with st.container(height=480):
            st.markdown(r_info['rapor'])
            
        # 2. Canlı Satıcı ve Görsel Galeri Kartları
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
                    st.info("Bu link için görsel bulunamadı veya güvenlik duvarı nedeniyle çekilemedi.")

        # 3. Görselli PDF İndirme Butonu
        st.write("")
        col_p1, col_p2 = st.columns([1.6, 1])
        with col_p1:
            try:
                pdf_bytes = create_rich_visual_pdf(
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
            st.caption("PDF raporu; tüm satıcı linklerini, ihlal açıklamalarını ve görsel delil fotoğraflarını içerir.")

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
            if reklam_url and any(sm in reklam_url.lower() for sm in ["instagram.com", "tiktok.com"]):
                st.info("Sosyal medya linkleri bot erişimine kapalıdır; görsel ve metin üzerinden inceleme yapılacaktır.")

            reklam_metni = st.text_area("Reklam Metni / Ticari İddialar / Caption", height=120, placeholder="İncelenmesi talep edilen metin veya iddiaları giriniz...")
            
            yuklenen_gorseller = st.file_uploader("Reklam Görselleri / Taslaklar (Çoklu Yükleme)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            
            if yuklenen_gorseller:
                gorsel_cols = st.columns(min(len(yuklenen_gorseller), 4))
                for idx, g_dosya in enumerate(yuklenen_gorseller):
                    g_img = Image.open(g_dosya)
                    gorsel_cols[idx % 4].image(g_img, caption=f"Görsel {idx+1}", use_container_width=True)
                
                if len(yuklenen_gorseller) != st.session_state.last_file_count:
                    st.session_state.last_file_count = len(yuklenen_gorseller)
                    trigger_scroll("bottom")
            else:
                st.session_state.last_file_count = 0

            st.markdown('<div id="page-bottom-anchor"></div>', unsafe_allow_html=True)
            buton_etiketi = "Uyum Analizi ve Güvenli Revizyonu Başlat" if is_danisan else "Rakip İhlal Analizini Başlat"
            analiz_butonu = st.button(buton_etiketi, type="primary")

    with sag_kolon:
        with st.container(border=True):
            panel_baslik = "Mevzuat Uyum ve Güvenli Revizyon Raporu" if is_danisan else "Piyasa İhlal Tespiti ve Başvuru Merkezi"
            st.markdown(f'<div class="section-heading" lang="tr">{panel_baslik}</div>', unsafe_allow_html=True)
            
            if analiz_butonu:
                trigger_scroll("top")

                if not api_key:
                    st.error("Lütfen geçerli bir API anahtarı sağlayınız.")
                elif not reklam_metni and not yuklenen_gorseller and not reklam_url:
                    st.warning("Lütfen metin giriniz, link paylaşınız veya görsel yükleyiniz.")
                else:
                    url_metni = ""
                    web_gorselleri = []
                    if reklam_url:
                        with st.spinner("Link içeriği taranıyor..."):
                            url_metni, web_gorselleri, _ = fetch_page_details(reklam_url)
                    
                    birlestirilmis_metin = f"{reklam_metni}\n\n[Kaynak Link]: {reklam_url}\n{url_metni}" if reklam_url else reklam_metni
                    ilgili_emsaller = get_relevant_emsaller(birlestirilmis_metin, sektor)
                    
                    sistem_metodolojisi = f"""
SEN; TİCARET BAKANLIĞI REKLAM KURULU İÇTİHATLARI VE 6502 SAYILI KANUN KAPSAMINDA UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN.
Yüklenen metinleri, başlıkları, ambalaj rozetlerini ve iddiaları doğrudan mevzuata uygunluk açısından denetle.

=== EMSAL REKLAM KURULU İÇTİHATLARI ===
{ilgili_emsaller}
=======================================

İNCELENEN VERİLER:
Sektör: {sektor} | Mecra: {mecra}
İddialar: {birlestirilmis_metin}
"""
                    if is_danisan:
                        prompt = sistem_metodolojisi + f"""
GÖREVİN: Kapsamlı ve net bir 'Mevzuat Uyum ve Revizyon Raporu' hazırlamaktır.

RAPOR FORMATI:
### [RİSK DERECESİ: YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

### I. MEVZUAT UYUM ANALİZİ VE TESPİT EDİLEN RİSKLİ İDDİALAR
* **[Tespit Edilen İfade/Rozet 1]:** (Mevzuat ihlali ve tüketici algısı)
* **[Tespit Edilen İfade/Rozet 2]:**

### II. REKLAM KURULU EMSAL KARARLARI VE CEZA EŞLEŞMELERİ
* **Emsal Karar 1:** (Dosya No, Karar Tarihi, Ceza Alan İfade, Uygulanan Yaptırım)
* **Emsal Karar 2:**

### III. ÖNGÖRÜLEN İDARİ PARA CEZASI VE RİSK SKALASI
* **Yayın Mecrası:** {mecra}
* **Ceza & Yaptırım Riski:** (6502 m. 77 uyarınca idari para cezası ve durdurma riski)

### IV. GÜVENLİ VE TİCARİ ETKİSİ YÜKSEK REVİZE METİN
* **Önerilen Güvenli İfade & Rozet Alternatifleri:**
* **Gereken İspat & Dipnot Standartları:**

### V. YASAL ŞERH
"Bu rapor teknik bir ön risk analizi niteliğinde olup, nihai hukuki mütalaa yerine geçmez."
"""
                    else:
                        prompt = sistem_metodolojisi + f"""
GÖREVİN: Rakip materyaldeki hukuka aykırılıkları ortaya koyan bir 'Piyasa İhlal Raporu' hazırlamaktır.

RAPOR FORMATI:
### [İHLAL DERECESİ: AĞIR / ORTA / HAFİF] - İhlal Skoru: [0-100]

### I. HAKSIZ REKABET VE MEVZUATA AYKIRILIK TESPİTİ
* **[Hukuka Aykırı İfade 1]:** (6502 ve TTK uyarınca haksız ticari uygulama gerekçesi)
* **[Hukuka Aykırı İfade 2]:**

### II. REKLAM KURULU EMSAL İÇTİHATLARI
* **Emsal Karar 1:** (Dosya No, İhlal Edilen Kural, Ceza Tutarı)
* **Emsal Karar 2:**

### III. RAKİBE UYGULANABİLECEK İDARİ YAPTIRIMLAR
* **6502 m. 77 Para Cezası ve İdari Tedbirler**

### IV. ŞİKAYET VE BAŞVURU STRATEJİSİ
* **Reklam Kurulu Başvuru Argümanları & Delil Tespiti**

### V. YASAL ŞERH
"Bu rapor teknik bir ön risk analizi niteliğinde olup, nihai hukuki mütalaa yerine geçmez."
"""
                    icerik_listesi = [f"Metin/Parametreler: {birlestirilmis_metin}\nSektör: {sektor}\nMecra: {mecra}"]
                    if yuklenen_gorseller:
                        for g in yuklenen_gorseller:
                            icerik_listesi.append(optimize_image(Image.open(g)))
                    if web_gorselleri:
                        for wg in web_gorselleri:
                            icerik_listesi.append(wg)

                    rapor_alani = st.empty()
                    try:
                        tam_rapor = ""
                        with st.spinner("Analiz yapılıyor..."):
                            for parca in generate_stream_safe(icerik_listesi, system_instruction=prompt):
                                tam_rapor += parca
                                rapor_alani.markdown(tam_rapor + "▌")
                        rapor_alani.empty()
                        st.session_state.rapor_sonucu = tam_rapor
                        st.session_state.dilekce_sonucu = None
                        st.session_state.chat_history = []
                        st.session_state.rakip_gorunum = "Haksız Rekabet ve İhlal Raporu"
                    except Exception as err:
                        st.error(f"Analiz sırasında bir hata oluştu: {err}")

            if st.session_state.rapor_sonucu:
                if is_danisan:
                    with st.container(height=450):
                        st.markdown(st.session_state.rapor_sonucu)
                else:
                    with st.container(height=450):
                        st.markdown(st.session_state.rapor_sonucu)
            else:
                st.info("Sol panelden parametreleri belirleyip analizi başlattığınızda rapor bu alanda hazır hale gelecektir.")
