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
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Risk Denetim Platformu",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Sayfa İçi Akıllı Kaydırma Fonksiyonu
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

# Kurumsal Tema Stilleri
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
        gap: 14px;
        width: 100%;
        margin-bottom: 10px;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: 1;
        background: #FFFFFF;
        border: 1.5px solid #CBD5E1;
        border-radius: 6px;
        padding: 12px 18px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
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

    div[data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar,
    div[data-testid="stChatMessageContainer"]::-webkit-scrollbar {
        width: 6px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-thumb,
    div[data-testid="stChatMessageContainer"]::-webkit-scrollbar-thumb {
        background-color: #cbd5e1;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Üst Header
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

if not api_key:
    with st.sidebar:
        st.header("Sistem Ayarları")
        api_key = st.text_input("Gemini API Key:", type="password")
        serpapi_key = st.text_input("SerpApi Key:", type="password")

def optimize_image(img, max_dimension=800):
    img = img.convert("RGB")
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return img

FAST_MODELS = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"]

def generate_stream_safe(contents, system_instruction=None):
    if not api_key:
        raise Exception("API anahtarı tanımlanmadı.")
    genai.configure(api_key=api_key)
    last_err = None
    for model_name in FAST_MODELS:
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
    last_err = None
    for model_name in FAST_MODELS:
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
        res = requests.get(url, headers=headers, timeout=2.5)
        if res.status_code == 200 and len(res.content) > 3000:
            pil_img = Image.open(io.BytesIO(res.content))
            return optimize_image(pil_img)
    except Exception:
        pass
    return None

def fetch_url_data(url):
    if not url or not url.strip().startswith(("http://", "https://")):
        return "", []
    
    if any(sm in url.lower() for sm in ["instagram.com", "tiktok.com", "facebook.com", "twitter.com", "x.com"]):
        return "[Sosyal medya linki girildi. Güvenlik duvarı nedeniyle görsel ve metin üzerinden incelenecektir.]", []
    
    clean_text = ""
    downloaded_images = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(url.strip(), headers=headers, timeout=3)
        if res.status_code == 200:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(res.text, 'html.parser')
                img_urls = []
                og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if og_img and og_img.get("content"):
                    img_urls.append(urljoin(url, og_img["content"]))
                
                for img_tag in soup.find_all("img"):
                    src = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-original")
                    if src:
                        full_img_url = urljoin(url, src)
                        if not any(ext in full_img_url.lower() for ext in [".svg", "icon", "logo", "pixel", "avatar", "1x1"]):
                            if full_img_url not in img_urls:
                                img_urls.append(full_img_url)
                    if len(img_urls) >= 2:
                        break

                with ThreadPoolExecutor(max_workers=2) as executor:
                    results = executor.map(lambda u: download_single_img(u, headers), img_urls[:2])
                    for r in results:
                        if r is not None:
                            downloaded_images.append(r)

                for s in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                    s.decompose()
                clean_text = ' '.join(soup.get_text(separator=' ').split())[:2500]
            except ImportError:
                clean_text = re.sub(r'<[^>]+>', ' ', res.text)[:2500]
    except Exception as e:
        clean_text = f"[Web içeriği çekilemedi: {e}]"
        
    return clean_text, downloaded_images

# --- HEDEFLİ LİNK VE ÜRÜN DETAY SAYFASI TARAYICISI ---
def tekil_sorgu_at(kategori, sorgu, api_key_val):
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key_val}&engine=google&gl=tr&hl=tr&num=25"
    
    # Alakasız giyim, tekstil ve genel kategori kelimelerini eleyen filtre
    YASAKLI_KELIMELER = [
        "elbise", "giyim", "pantolon", "tulum", "etek", "ayakkabi", "ayakkabı", 
        "bluz", "mont", "ceket", "pijama", "sütyen", "sutyen", "külot", "kulot", 
        "kombin", "tisort", "tişört", "terlik", "çanta", "canta", "aksesuar",
        "gecelik", "tayt", "şort", "sort", "triko", "kazak"
    ]
    
    try:
        response = requests.get(url, timeout=6)
        data = response.json()
        link_havuzu = []
        if "organic_results" in data:
            for result in data["organic_results"]:
                link = result.get("link", "")
                title = result.get("title", "Başlık Belirtilmemiş")
                snippet = result.get("snippet", "")
                
                url_lower = link.lower()
                title_lower = title.lower()
                
                # Arama ve kategori sayfalarını filtrele
                if any(x in url_lower for x in ["/sr?q=", "/ara?q=", "/search?q=", "/kategori/", "/butik/"]):
                    continue
                
                # Alakasız giyim/tekstil sayfalarını filtrele
                if any(y in url_lower or y in title_lower for y in YASAKLI_KELIMELER):
                    continue
                
                link_havuzu.append({
                    "baslik": title,
                    "url": link,
                    "snippet": snippet
                })
        return kategori, link_havuzu
    except Exception:
        return kategori, []

def gelismis_coklu_hedef_taramasi(urun_adi, marka_domain, api_key_val):
    if not api_key_val:
        return {}
    
    marka_kelimesi = urun_adi.split()[0] if urun_adi else "mamaaura"
    
    # Arama motoru seviyesinde negatif filtre
    negatif_filtre = "-elbise -giyim -pantolon -etek -tulum -ayakkabı -bluz -pijama"
    
    queries = {
        "🛒 Trendyol Tekil Ürün Sayfaları": f'site:trendyol.com "{marka_kelimesi}" {negatif_filtre}',
        "🛍️ Hepsiburada & Amazon Tekil Ürünler": f'(site:hepsiburada.com "{marka_kelimesi}" {negatif_filtre}) OR (site:amazon.com.tr "{marka_kelimesi}" {negatif_filtre})',
        "🌐 Marka Resmi Web Sitesi Ürünleri": f'site:{marka_domain} "{marka_kelimesi}"' if marka_domain else f'site:mamaaura.com OR site:tr.mamaaura.com',
        "📱 Instagram Gönderi & Reels İçerikleri": f'site:instagram.com/p/ OR site:instagram.com/reel/ "{marka_kelimesi}"'
    }
    
    kategorize_sonuclar = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(tekil_sorgu_at, kat, q, api_key_val) for kat, q in queries.items()]
        for f in futures:
            kat, sonuclar = f.result()
            gorulenler = set()
            tekil_list = []
            for item in sonuclar:
                if item["url"] not in gorulenler:
                    gorulenler.add(item["url"])
                    tekil_list.append(item)
            kategorize_sonuclar[kat] = tekil_list
            
    return kategorize_sonuclar

@st.cache_data
def load_and_index_kararlar():
    corpus = ""
    txt_dosyalari = (
        glob.glob("kararlar_tek_dosya.txt") +
        glob.glob("kararlar_havuzu*.txt") +
        glob.glob("kararlar_parca_*.txt")
    )
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
        "Kozmetik & Kişisel Bakım / Anne-Bebek": ["kozmetik", "doğal", "bitkisel", "organik", "cilt", "leke", "kırışıklık", "titck", "onaylı", "tedavi", "mucize", "yok eder", "klinik", "sls", "paraben", "içermez", "pişik"],
        "Takviye Edici Gıda & Sağlık": ["takviye", "gıda", "sağlık beyanı", "tedavi", "hastalık", "kilo", "zayıflama", "bağışıklık", "eklem", "ağrı", "şifa", "onay", "kesin son", "iltihap"],
        "E-Ticaret & İndirim Kampanyaları": ["indirim", "fiyat", "en ucuz", "tavsiye edilen", "stok", "bedava", "en çok satan", "fiyatı düştü", "efsane", "tükeniyor"],
        "Sosyal Medya & Influencer Reklamları": ["influencer", "işbirliği", "etiket", "örtülü reklam", "sosyal medya", "tanıtım", "link", "ortaklık", "sponsor", "reklam"]
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

def create_pdf(report_text, baslik_metni):
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

    temiz_metin = clean_markdown_text(report_text)
    if font_yuklendi:
        pdf.set_font("Roboto", "", 12)
        pdf.cell(0, 8, baslik_metni, ln=True, align="C")
        pdf.set_font("Roboto", "", 8.5)
        pdf.cell(0, 5, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        pdf.line(10, 24, 200, 24)
        pdf.ln(5)
        pdf.multi_cell(0, 4.8, temiz_metin)
    else:
        tr_map = str.maketrans("ğĞüÜşŞçÇ", "gGuUsScC")
        baslik_ascii = baslik_metni.replace("İ", "I").replace("ı", "i").translate(tr_map)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, baslik_ascii, ln=True, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(0, 5, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        pdf.line(10, 24, 200, 24)
        pdf.ln(5)
        ascii_metin = temiz_metin.replace("İ", "I").replace("ı", "i").translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4.8, ascii_metin)

    return bytes(pdf.output())

def create_docx(dilekce_text):
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    
    cleaned = dilekce_text.replace("---", "").replace("###", "").replace("##", "").replace("#", "")
    cleaned = re.sub(r'(?i)\bmüstakilen\b\s*', '', cleaned)
    
    lines = cleaned.split("\n")
    in_signature = False
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        raw_line = line_str.replace("**", "").replace("*", "").strip()
        
        if any(h in raw_line.upper() for h in ["T.C. TİCARET BAKANLIĞI", "REKLAM KURULU BAŞKANLIĞINA", "ANKARA"]):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(raw_line)
            r.bold = True
            r.font.name = 'Calibri'
            r.font.size = Pt(11.5)
            continue
            
        if any(sig_start in raw_line for sig_start in ["ŞİKAYET EDEN MÜVEKKİL", "ŞİKAYET EDEN VEKİLİ", "ŞİKAYET EDEN MÜVEKKİL VEKİLİ"]):
            in_signature = True
            
        if in_signature:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(raw_line)
            r.bold = True
            r.font.name = 'Calibri'
            continue

        if any(raw_line.startswith(k) for k in [
            "ŞİKAYET EDEN:", "ŞİKAYET EDEN :", 
            "ADRES:", "ADRES :", 
            "VEKİLİ:", "VEKİLİ / İLETİŞİM:", "VEKİLİ :",
            "ŞİKAYET EDİLEN:", "ŞİKAYET EDİLEN :", 
            "İNCELEME LİNKİ:", "İNCELEME LİNKİ :", 
            "ŞİKAYET KONUSU:", "ŞİKAYET KONUSU :", "KONU:", "KONU :"
        ]):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            
            if ":" in raw_line:
                parts = raw_line.split(":", 1)
                r1 = p.add_run(parts[0].strip() + "\t: ")
                r1.bold = True
                r1.font.name = 'Calibri'
                r2 = p.add_run(parts[1].strip())
                r2.font.name = 'Calibri'
            else:
                r = p.add_run(raw_line)
                r.bold = True
                r.font.name = 'Calibri'
            continue

        if raw_line in ["AÇIKLAMALAR:", "AÇIKLAMALAR", "SONUÇ VE İSTEM:", "SONUÇ VE İSTEM"]:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(raw_line)
            r.bold = True
            r.font.name = 'Calibri'
            continue

        if re.match(r'^\d+\.\s', raw_line):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(raw_line)
            r.bold = True
            r.font.name = 'Calibri'
            continue

        if raw_line.startswith(("- ", "• ")):
            p = doc.add_paragraph(style='List Bullet')
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(raw_line[2:].strip())
            r.font.name = 'Calibri'
            continue

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(raw_line)
        r.font.name = 'Calibri'
                    
    docx_io = io.BytesIO()
    doc.save(docx_io)
    docx_io.seek(0)
    return docx_io.getvalue()

# Session State
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
if "radar_link_sonuclari" not in st.session_state:
    st.session_state.radar_link_sonuclari = None

# Mod Seçimi
st.markdown('<div class="mode-header-title" lang="tr">İnceleme Modunu Seçiniz</div>', unsafe_allow_html=True)

mod_secimi = st.radio(
    "Denetim Modu",
    [
        "Kurumsal Kampanya Taslağı Uyum Denetimi (İç Denetim & Revizyon Modu)",
        "Piyasa ve Rakip Reklam İncelemesi (Haksız Rekabet & Şikayet Modu)",
        "360° Çoklu Satıcı ve Pazar Radarı (Hedefli Ürün Linki Tespiti)"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

is_danisan = "İç Denetim" in mod_secimi
is_radar = "360° Çoklu Satıcı" in mod_secimi

sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

# ==========================================
# MOD 1 & MOD 2: MEVCUT DENETİM VE RAKİP MODLARI
# ==========================================
if not is_radar:
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
                            url_metni, web_gorselleri = fetch_url_data(reklam_url)
                    
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
                    
                    try:
                        pdf_verisi = create_pdf(st.session_state.rapor_sonucu, "AdShield - Reklam Uyum ve Risk Raporu")
                        st.download_button(
                            label="Hukuki Uyum ve Revizyon Raporunu İndir (PDF)",
                            data=pdf_verisi,
                            file_name=f"AdShield_Uyum_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            type="secondary"
                        )
                    except Exception as e:
                        st.warning(f"PDF uyarısı: {e}")
                else:
                    secili_gorunum = st.radio(
                        "Görünüm Seçiniz",
                        ["Haksız Rekabet ve İhlal Raporu", "Reklam Kurulu Şikayet Dilekçesi"],
                        horizontal=True,
                        label_visibility="collapsed",
                        key="rakip_gorunum"
                    )

                    if secili_gorunum == "Haksız Rekabet ve İhlal Raporu":
                        with st.container(height=450):
                            st.markdown(st.session_state.rapor_sonucu)
                        try:
                            pdf_verisi = create_pdf(st.session_state.rapor_sonucu, "AdShield - Rakip Reklam İhlal Raporu")
                            st.download_button(
                                label="Rakip İhlal Raporunu İndir (PDF)",
                                data=pdf_verisi,
                                file_name=f"AdShield_Rakip_Ihlal_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf",
                                type="secondary"
                            )
                        except Exception as e:
                            st.warning(f"PDF uyarısı: {e}")

                    else:
                        st.caption("İncelenen rakip tanıtım hakkında resmi Reklam Kurulu Şikayet Dilekçesi paneli.")
                        
                        with st.expander("⚖️ Dilekçe Taraf Bilgilerini Düzenle", expanded=True):
                            c_taraf1, c_taraf2 = st.columns(2)
                            with c_taraf1:
                                sikayet_eden_unvan = st.text_input("Şikayet Eden (Müvekkil) Unvanı / Vergi No / MERSİS No", value="", placeholder="Örn: ABC İlaç Kozmetik Paz. A.Ş. MERSİS: 0123456789")
                                sikayet_eden_adres = st.text_area("Şikayet Eden Adresi", height=65, placeholder="Cadde, Mahalle, No, İlçe / İl")
                                vekil_bilgisi = st.text_input("Vekil & İletişim Bilgisi", placeholder="Örn: Av. [Ad Soyad] - İletişim: 05XX XXX XX XX")
                            with c_taraf2:
                                sikayet_edilen_unvan = st.text_input("Şikayet Edilen Rakip Unvan / Vergi No / MERSİS No", value="", placeholder="Örn: 1. XYZ Kozmetik A.Ş. VKN: 987654321 / 2. Satıcı Şahıs...")
                                sikayet_edilen_adres = st.text_area("Şikayet Edilen Adresi / Platform Bilgisi", height=65, placeholder="Şirket Adresi veya E-Ticaret Pazaryeri Mağaza Bilgisi")

                        if not st.session_state.dilekce_sonucu:
                            if st.button("Resmi Reklam Kurulu Şikayet Dilekçesini Hazırla (Word)", type="primary"):
                                with st.spinner("Kurumsal Reklam Kurulu şikayet dilekçesi hazırlanıyor..."):
                                    try:
                                        s_eden = sikayet_eden_unvan.strip() if sikayet_eden_unvan.strip() else "[Şikayet Eden Şirket / Müvekkil Unvanı / MERSİS / VKN]"
                                        s_eden_adr = sikayet_eden_adres.strip() if sikayet_eden_adres.strip() else "[Şikayet Eden Şirket Adresi]"
                                        s_vekil = vekil_bilgisi.strip() if vekil_bilgisi.strip() else "Av. [Vekil Adı Soyadı] - İletişim: [Telefon / E-posta]"
                                        s_edilen = sikayet_edilen_unvan.strip() if sikayet_edilen_unvan.strip() else "[Şikayet Edilen Firma Unvanı / Satıcı Bilgisi / VKN]"
                                        s_edilen_adr = sikayet_edilen_adres.strip() if sikayet_edilen_adres.strip() else "[Şikayet Edilen Adres / Platform Bilgisi]"
                                        s_link = reklam_url.strip() if reklam_url.strip() else "[İncelenen Satış Sayfası / Tanıtım URL]"

                                        dilekce_prompt = f"""
Sen tüketici hukuku, haksız rekabet ve Reklam Kurulu regülasyonlarında son derece tecrübeli kıdemli bir Hukuk Müşavirisin.
Aşağıda incelenen rakip tanıtımına ilişkin teknik ihlal raporu ve girilen taraf bilgileri yer almaktadır:

TEKNİK İHLAL RAPORU:
{st.session_state.rapor_sonucu}

TARAF BİLGİLERİ:
ŞİKAYET EDEN: {s_eden}
ADRES: {s_eden_adr}
VEKİLİ / İLETİŞİM: {s_vekil}
ŞİKAYET EDİLEN: {s_edilen}
ADRES: {s_edilen_adr}
İNCELEME LİNKİ: {s_link}

GÖREVİN:
Aşağıdaki kurallara KESİNLİKLE uyarak resmi bir REKLAM KURULU ŞİKAYET DİLEKÇESİ hazırlamaktır.

ÖNEMLİ BİÇİM VE İÇERİK KURALLARI:
1. METİNDE ASLA markdown karakterleri (*, #, ---) KULLANMA. Düz metin olarak çıktı ver.
2. DİLEKÇE GÖVDESİNDE ASLA EMSAL KARARLARA YER VERME (Emsal kararlar bölümünü veya dosya numaralarını dilekçeye yazma).
3. METİNDE ASLA "müstakilen" KELİMESİNİ KULLANMA.
4. "AÇIKLAMALAR" altındaki 1, 2, 3, 4, 5 gibi tüm madde başlıkları TAM VE ANLAMLI BİRER HUKUKİ CÜMLE olsun.
5. Taraf bilgilerinin yanına fazladan "(Sicil No: ...)" gibi ifadeler EKLEME; yukarıda verilen metni aynen kullan.

DİLEKÇE YAPISI:

T.C. TİCARET BAKANLIĞI
REKLAM KURULU BAŞKANLIĞINA
ANKARA

ŞİKAYET EDEN: {s_eden}
ADRES: {s_eden_adr}
VEKİLİ / İLETİŞİM: {s_vekil}
ŞİKAYET EDİLEN: {s_edilen}
ADRES: {s_edilen_adr}
İNCELEME LİNKİ: {s_link}
ŞİKAYET KONUSU: {s_link} adresinde ve ilgili mecralarda satışa sunulan ürünün tanıtımlarında yer alan mevzuata aykırı sağlık beyanları, fizyolojik etki iddiaları, aldatıcı karşılaştırma, geçersiz dipnot, yanıltıcı indirim ve kesinlik vaatleri suretiyle 6502 sayılı Kanun ve Ticari Reklam Yönetmeliği'nin ihlal edilmesi nedeniyle ilgililer hakkında REKLAMLARIN TEDBİREN DURDURULMASI ve İDARİ PARA CEZASI UYGULANMASI talebidir.

AÇIKLAMALAR:
(Giriş paragrafı: Şikayet edilen tarafın tanıtım yaptığı mecra, ürün adı ve genel aldatıcı çerçeve).

1. Somut Olarak Tespit Edilen Mevzuata Aykırı Reklam ve Tanıtım İfadeleri:
(Tanıtımda yer alan tüm tırnak içi yasaklı ifadeleri, sloganları, oranları madde madde sırala).

2. [Kozmetik/Gıda Mevzuatını Aşan ve İlaç Algısı Oluşturan Yasaklı Sağlık Beyanlarına İlişkin Tam Cümle Başlık]:
(5324 sayılı Kanun, Kozmetik Yönetmeliği m. 4 ve Sağlık Beyanı Yönetmeliği m. 7 çerçevesinde gerekçelendir).

3. [Metabolik ve Biyokimyasal Düzeyde Fizyolojik Etki İddialarının Mevzuata Aykırılığına İlişkin Tam Cümle Başlık]:
(TİTCK Kılavuzları ve ilgili düzenlemeler uyarınca biyokimyasal mekanizma iddialarının yasaklığını açıkla).

4. [Hammadde İddiasının Bitmiş Ürüne Teşmili, Karşılaştırmalı Reklam ve Geçersiz Dipnot Kullanımına İlişkin Tam Cümle Başlık]:
(Ticari Reklam Yönetmeliği m. 7/5 ve m. 8 uyarınca ana vaadi çürüten dipnot yasağını ve ispat yükünü izah et).

5. [Kesinlik Bildiren Vaatler, Tüketicinin İstismarı ve Aldatıcı Fiyatlandırma Uygulamalarına İlişkin Tam Cümle Başlık]:
(Kesinlik vaatleri ve yapay stok/süre/indirim manipülasyonlarını gerekçelendir).

SONUÇ VE İSTEM:
Yukarıda arz ve izah edilen nedenlerle; şikayet edilen tarafın 6502 sayılı Kanun ve ilgili mevzuata aykırı tanıtımları hakkında gerekli incelemelerin yapılarak;
1. Anılan hukuka aykırı reklamların 6502 sayılı Kanun'un 63 ve 77. maddeleri gereğince TEDBİREN DURDURULMASINA,
2. Reklam Veren ve ilgililer hakkında 6502 sayılı Kanun'un 77. maddesi uyarınca İDARİ PARA CEZASI UYGULANMASINA karar verilmesini saygıyla talep ederiz.

ŞİKAYET EDEN MÜVEKKİL VEKİLİ
{s_vekil}
"""
                                        st.session_state.dilekce_sonucu = generate_content_safe(dilekce_prompt)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Dilekçe hazırlanırken bir hata oluştu: {e}")

                        if st.session_state.dilekce_sonucu:
                            with st.container(height=400):
                                st.markdown(st.session_state.dilekce_sonucu)
                            
                            col_d1, col_d2 = st.columns([1.5, 1])
                            with col_d1:
                                try:
                                    docx_verisi = create_docx(st.session_state.dilekce_sonucu)
                                    st.download_button(
                                        label="📄 Resmi Şikayet Dilekçesini İndir (Word / .docx)",
                                        data=docx_verisi,
                                        file_name=f"Reklam_Kurulu_Sikayet_Dilekcesi_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        type="primary"
                                    )
                                except Exception as e:
                                    st.warning(f"Word çıktısı oluşturma uyarısı: {e}")
                            with col_d2:
                                if st.button("🔄 Dilekçeyi Yeniden Düzenle"):
                                    st.session_state.dilekce_sonucu = None
                                    st.rerun()
            else:
                st.info("Sol panelden parametreleri belirleyip analizi başlattığınızda rapor bu alanda hazır hale gelecektir.")

# ==========================================
# MOD 3: 360° ÇOKLU SATICI VE PAZAR RADARI (LİNK ODAKLI)
# ==========================================
else:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📡 Hedefli Ürün Linki Avı</div>', unsafe_allow_html=True)
            
            radar_urun = st.text_input("Marka / Ürün Anahtar Kelimesi", value="mamaaura çatlak ve selülit yağı", placeholder="Örn: mamaaura çatlak yağı...")
            radar_domain = st.text_input("Markanın Resmi Domaini (Opsiyonel)", value="mamaaura.com", placeholder="Örn: mamaaura.com")
            
            st.caption("ℹ️ Bu radar; doğrudan tekil ürün satış sayfalarını tarayarak hedef URL havuzunu çıkarır.")
            radar_tara_butonu = st.button("🚀 Tekil Ürün Linklerini Tespit Et", type="primary")

    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📋 Tespit Edilen Tekil Satış Linkleri</div>', unsafe_allow_html=True)

            if radar_tara_butonu:
                trigger_scroll("top")
                if not serpapi_key:
                    st.error("SerpApi API Key bulunamadı. Lütfen Streamlit Secrets ayarlarınızı kontrol ediniz.")
                elif not radar_urun:
                    st.warning("Lütfen taranacak marka veya ürün adını giriniz.")
                else:
                    with st.spinner("Tekil ürün sayfaları ve pazar kanalları taranıyor..."):
                        sonuclar = gelismis_coklu_hedef_taramasi(radar_urun, radar_domain, serpapi_key)
                        st.session_state.radar_link_sonuclari = sonuclar

            if st.session_state.radar_link_sonuclari:
                toplam_link = sum(len(v) for v in st.session_state.radar_link_sonuclari.values())
                st.success(f"🎯 Toplam **{toplam_link}** adet tekil ürün/satış bağlantısı tespit edildi.")
                
                alt_sekmeler = st.tabs(list(st.session_state.radar_link_sonuclari.keys()))
                for i, (kat, links) in enumerate(st.session_state.radar_link_sonuclari.items()):
                    with alt_sekmeler[i]:
                        if len(links) > 0:
                            for idx, item in enumerate(links, 1):
                                st.markdown(f"**{idx}. [{item['baslik']}]({item['url']})**")
                                st.caption(f"🔗 `{item['url']}`")
                                if item['snippet']:
                                    st.caption(f"📝 *İçerik İpuçları:* {item['snippet']}")
                                st.divider()
                        else:
                            st.warning("Bu kategoride doğrudan tekil ürün sayfası bulunamadı.")
            else:
                st.info("Sol panelden taramayı başlattığınızda tespit edilen tüm tekil Trendyol, Hepsiburada, Amazon ve resmi site ürün linkleri burada listelenecektir.")

# ==========================================
# İNTERAKTİF CHATBOT (MEVZUAT ASİSTANI)
# ==========================================
if st.session_state.rapor_sonucu and not is_radar:
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-heading" lang="tr">💬 AdShield Mevzuat Asistanı</div>', unsafe_allow_html=True)
        st.caption("Raporlanan riskler hakkında detay sorabilir veya aşağıdaki hızlı butonları kullanabilirsiniz:")

        c1, c2, c3 = st.columns(3)
        hizli_soru = None
        if c1.button("📌 Revize sloganı Instagram'a uyarla"):
            hizli_soru = "Önerdiğin güvenli reklam metnini Instagram post ve story açıklaması formatına uyarla."
        if c2.button("📝 Zorunlu dipnot metnini hazırla"):
            hizli_soru = "Bu reklamda görselin altına veya ambalaj üstüne eklenmesi gereken zorunlu yasal dipnot metnini yaz."
        if c3.button("🛡️ İspat yükümlülüğü rehberi çıkar"):
            hizli_soru = "Reklam Kurulu denetiminde bu iddialar için hazır bulundurulması gereken teknik/klinik test belgeleri nelerdir?"

        chat_container = st.container(height=340)
        with chat_container:
            if not st.session_state.chat_history:
                st.info("Henüz bir soru sormadınız. Aşağıdan yazabilir veya yukarıdaki butonlara tıklayabilirsiniz.")
            
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        kullanici_sorusu = st.chat_input("Raporla ilgili bir soru yazın...") or hizli_soru

        if kullanici_sorusu:
            st.session_state.chat_history.append({"role": "user", "content": kullanici_sorusu})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(kullanici_sorusu)

                with st.chat_message("assistant"):
                    with st.spinner("Değerlendiriliyor..."):
                        try:
                            chat_instruction = f"""
Sen kurumsal reklam hukuku uzmanısın. Kullanıcının sorularını aşağıdaki rapora göre doğrudan ve profesyonel bir dille yanıtla:
{st.session_state.rapor_sonucu}
"""
                            sohbet_gecmisi_prompt = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in st.session_state.chat_history])
                            cevap_metni = generate_content_safe(sohbet_gecmisi_prompt, system_instruction=chat_instruction)
                            st.markdown(cevap_metni)
                            st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                        except Exception as e:
                            st.error(f"Hata: {e}")
            st.rerun()
