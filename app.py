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
import textwrap
import time

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

try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    serpapi_key = st.secrets.get("SERPAPI_API_KEY", None)
except Exception:
    api_key = None
    serpapi_key = None

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

TARGET_MODEL = "gemini-3.6-flash"

def get_working_model(system_instruction=None):
    if not api_key:
        raise Exception("API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=TARGET_MODEL, system_instruction=system_instruction)

def generate_content_safe(contents, system_instruction=None):
    model = get_working_model(system_instruction=system_instruction)
    for attempt in range(2):
        try:
            response = model.generate_content(contents)
            if response and response.text:
                return response.text
            raise Exception("Model boş yanıt döndürdü.")
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Quota" in err_str or "free_tier" in err_str.lower():
                if attempt < 1:
                    time.sleep(15)
                    continue
            raise Exception("🚨 **API KOTASI DOLDU:** Google ücretsiz hesap limitlerine ulaştınız. Lütfen sisteme yeni bir API Key girin veya kotalarınızın sıfırlanması için bekleyin.")

def generate_multi_role_synthesis_stream(contents, system_instruction_base, is_danisan):
    if not api_key:
        raise Exception("API anahtarı bulunamadı.")
    genai.configure(api_key=api_key)
    
    rapor_turu_adi = "Mevzuat Uyum ve Revizyon Raporu" if is_danisan else "Piyasa İhlal ve Şikayet Raporu"
    
    single_master_prompt = f"""
{system_instruction_base}

GÖREVİN: Aşağıdaki materyali tek seferde, eşzamanlı olarak hem KATI BİR MEVZUAT BAŞDENETÇİSİ hem de KIDEMLİ BİR HAKSIZ REKABET AVUKATI şapkalarıyla incelemek ve bana doğrudan KUSURSUZ, HARMANLANMIŞ BİR {rapor_turu_adi} üretmektir.

KESİN KURALLAR:
1. "KİME:", "HAZIRLAYAN:", "KONU:" gibi bürokratik giriş antetlerini ASLA KULLANMA. Doğrudan raporun ana özetine veya ihlal analizine başla.
2. Emsal Kararlar bölümünde sürekli olarak "L'Oreal", "La Roche-Posay" gibi aynı markaları TEKRAR ETME. Çeşitliliği sağla ve gönderdiğim güncel emsalleri kullan.
3. Raporu okuyan kişiyi yormayacak, şık ve ferah bir Markdown düzeni (kalın başlıklar, düzgün listeler) kullan.
"""
    
    payload = [single_master_prompt] + contents
    model = get_working_model()
    
    for attempt in range(2):
        try:
            response = model.generate_content(payload, stream=False)
            
            if response and response.text:
                words = response.text.split(' ')
                for i in range(0, len(words), 6):
                    yield ' '.join(words[i:i+6]) + ' '
                    time.sleep(0.04) 
                return 
            else:
                yield "Analiz başlatılamadı. Model boş yanıt döndürdü."
                return
                
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Quota" in err_str or "free_tier" in err_str.lower():
                if attempt < 1:
                    match = re.search(r'retry in (\d+\.?\d*)s', err_str)
                    wait_time = float(match.group(1)) + 2 if match else 20
                    
                    yield f"\n\n> ⏳ **[Google API Limit Koruması Devrede]** Sistem dakikalık kotaları korumak adına duraklatıldı. Analiz iptal edilmedi, {int(wait_time)} saniye içinde otomatik olarak devam edip ekrana yansıyacaktır...\n\n"
                    time.sleep(wait_time)
                    continue 
                else:
                    yield "\n\n🚨 **API KOTASI TÜKENDİ (429 Hatası):**\nGoogle Free Tier (Ücretsiz Katman) günlük ve dakikalık limitlerinizi tamamen doldurdunuz. Sorun koddan değil, Google'ın hesabınıza uyguladığı engelden kaynaklanmaktadır.\n\n**Çözüm:**\n1. Sol menüdeki ayarlardan farklı bir hesaba ait yepyeni bir Gemini API Key girin.\n2. Veya kotaların sıfırlanması için lütfen daha sonra tekrar deneyin."
                    return
            
            yield f"\nSentezleme sırasında kalıcı bir hata oluştu: {err_str}"
            return

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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
                    src = img_tag.get("src") or img_tag.get("data-src")
                    if src:
                        full_img_url = urljoin(url, src)
                        if not any(ext in full_img_url.lower() for ext in [".svg", "icon", "logo", "pixel"]):
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

def tekil_sorgu_at(kategori, sorgu, api_key_val):
    url = f"https://serpapi.com/search.json?q={urllib.parse.quote(sorgu)}&api_key={api_key_val}&engine=google&gl=tr&hl=tr&num=20"
    try:
        response = requests.get(url, timeout=7)
        data = response.json()
        link_havuzu = []
        raw_items = []
        if "organic_results" in data:
            raw_items.extend(data["organic_results"])
        for result in raw_items:
            link = result.get("link", "")
            title = result.get("title", "Başlık Belirtilmemiş")
            snippet = result.get("snippet", "")
            if not link or not link.startswith("http"):
                continue
            url_lower = link.lower()
            if any(y in url_lower for y in ["/giris", "/hesabim", "/sepetim", "auth", "login"]):
                continue
            link_havuzu.append({"baslik": title, "url": link, "snippet": snippet})
        return kategori, link_havuzu
    except Exception:
        return kategori, []

def gelismis_coklu_hedef_taramasi(urun_adi, marka_domain, api_key_val):
    if not api_key_val or not urun_adi.strip():
        return {}
    temiz_urun = urun_adi.strip()
    queries = {
        "🛒 Trendyol Satış Noktaları": f'{temiz_urun} trendyol satıcı fiyat',
        "🛍️ Hepsiburada Ürün Sayfaları": f'{temiz_urun} hepsiburada',
        "📦 E-Ticaret ve Pazar Yerleri": f'{temiz_urun} satın al sipariş',
        "🌐 Resmi Web Sitesi & Bayiler": f'{temiz_urun} resmi site orjinal',
        "💬 Tüketici Yorumları & Şikayetler": f'{temiz_urun} şikayet var kullanıcı yorumu'
    }
    kategorize_sonuclar = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
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

# --- L'OREAL'İ ENGELLEYEN VE PUANLAYAN EMSAL MOTORU ---
def get_relevant_emsaller(metin, sektor, top_k=3):
    if not karar_arsivi:
        return "Karar arşivi yüklenemedi.", []
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
            
        if "l'oreal" in k_lower or "la roche" in k_lower:
            skor -= 50
            
        if skor > 0:
            skorlu.append((skor, karar[:1200]))
            
    skorlu.sort(key=lambda x: x[0], reverse=True)
    
    secilenler_metin = [k[1] for k in skorlu[:top_k]]
    secilenler_metin = secilenler_metin if secilenler_metin else karar_arsivi[:2]
    
    birlestirilmis_emsal_str = "\n\n--- [EMSAL KARAR METNİ] ---\n\n".join(secilenler_metin)
    return birlestirilmis_emsal_str, secilenler_metin

def create_pdf(report_text, baslik_metni):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    tr_map = str.maketrans("ğĞüÜşŞçÇİı", "gGuUsScCIi")
    
    pdf.set_font("Helvetica", "B", 16)
    baslik_ascii = baslik_metni.translate(tr_map)
    pdf.cell(0, 10, baslik_ascii, ln=True, align="C")
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
    pdf.line(10, 28, 200, 28)
    pdf.ln(8)
    
    pdf.set_text_color(0, 0, 0)

    lines = report_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        
        line_ascii = line.replace("’", "'").replace("“", '"').replace("”", '"').replace('\xa0', ' ').replace('\t', ' ')
        line_ascii = line_ascii.translate(tr_map).encode('latin-1', 'replace').decode('latin-1')

        if line.startswith("###") or line.startswith("I.") or line.startswith("II.") or line.startswith("III.") or line.startswith("IV.") or line.startswith("V."):
            pdf.set_font("Helvetica", "B", 12)
            temiz_satir = line_ascii.replace("###", "").replace("**", "").strip()
            satir_yuksekligi = 7
        elif line.startswith("* **") or line.startswith("- **"):
            pdf.set_font("Helvetica", "B", 11)
            temiz_satir = line_ascii.replace("**", "").replace("* ", "").replace("- ", "").strip()
            satir_yuksekligi = 6
        else:
            pdf.set_font("Helvetica", "", 11)
            temiz_satir = line_ascii.replace("**", "").replace("*", "").strip()
            satir_yuksekligi = 6

        wrapped_lines = textwrap.wrap(temiz_satir, width=85, break_long_words=True, replace_whitespace=False)
        
        for wl in wrapped_lines:
            pdf.cell(0, satir_yuksekligi, wl, ln=True)
            
        if not (line.startswith("* ") or line.startswith("- ")):
            pdf.ln(2)
            
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
            "ŞİKAYET EDEN:", "ŞİKAYET EDEN :", "ADRES:", "ADRES :", 
            "VEKİLİ:", "VEKİLİ / İLETİŞİM:", "VEKİLİ :",
            "ŞİKAYET EDİLEN:", "ŞİKAYET EDİLEN :", "İNCELEME LİNKİ:", 
            "İNCELEME LİNKİ :", "ŞİKAYET KONUSU:", "ŞİKAYET KONUSU :", "KONU:", "KONU :"
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

# Session State Tanımları
if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
if "dilekce_sonucu" not in st.session_state:
    st.session_state.dilekce_sonucu = None
if "kullanilan_emsaller" not in st.session_state:
    st.session_state.kullanilan_emsaller = []
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
                    
                    ilgili_emsaller, emsal_liste = get_relevant_emsaller(birlestirilmis_metin, sektor)
                    st.session_state.kullanilan_emsaller = emsal_liste
                    
                    # --- DERİNLEMESİNE DÜŞÜNME (CHAIN OF THOUGHT) VE SIFIR HALÜSİNASYON TALİMATI ---
                    sistem_metodolojisi = f"""
SEN; TİCARET BAKANLIĞI REKLAM KURULU İÇTİHATLARI VE 6502 SAYILI KANUN KAPSAMINDA UZMAN REKLAM HUKUKU BAŞDENETÇİSİSİN.
Derinlemesine düşünme (Chain of Thought) yeteneğini kullanarak, yüklenen görselleri, metinleri, başlıkları ve ambalaj rozetlerini adım adım analiz et.

KESİN KURAL (SIFIR HALÜSİNASYON):
1. Görsellerdeki ürün isimlerini, sürüm/versiyon numaralarını (örn. 3.0), hacim ve gramaj bilgilerini (örn. 20mg/2mL) bir OCR cihazı hassasiyetiyle oku. 
2. Asla görselde olmayan bir sayıyı, versiyonu veya gramajı uydurma.
3. Görselin kompozisyonunu (örn. modelin kıyafeti, arka plan) hukuki bir delil gibi incele ve bunun tüketici algısına etkisini değerlendir.

=== EMSAL REKLAM KURULU İÇTİHATLARI ===
{ilgili_emsaller}
=======================================

İNCELENEN VERİLER:
Sektör: {sektor} | Mecra: {mecra}
İddialar: {birlestirilmis_metin}
"""
                    if is_danisan:
                        base_prompt = sistem_metodolojisi + f"""
RAPOR FORMATI:
### [RİSK DERECESİ: YÜKSEK / ORTA / DÜŞÜK] - Risk Skoru: [0-100]

### I. MEVZUAT UYUM ANALİZİ VE TESPİT EDİLEN RİSKLİ İDDİALAR
* **[Tespit Edilen İfade/Rozet/Görsel Öğe 1]:** (Mevzuat ihlali ve tüketici algısı)
* **[Tespit Edilen İfade/Rozet/Görsel Öğe 2]:**

### II. REKLAM KURULU EMSAL KARARLARI VE CEZA EŞLEŞMELERİ
* **Emsal Karar 1:** (Dosya No, Karar Tarihi, Ceza Alan İfade, Uygulanan Yaptırım)

### III. ÖNGÖRÜLEN İDARİ PARA CEZASI VE RİSK SKALASI
* **Yayın Mecrası:** {mecra}
* **Ceza & Yaptırım Riski:** 

### IV. GÜVENLİ VE TİCARİ ETKİSİ YÜKSEK REVİZE METİN
* **Önerilen Güvenli İfade & Rozet Alternatifleri:**

### V. YASAL ŞERH
"Bu rapor teknik bir ön risk analizi niteliğinde olup, nihai hukuki mütalaa yerine geçmez."
"""
                    else:
                        base_prompt = sistem_metodolojisi + f"""
RAPOR FORMATI:
### [İHLAL DERECESİ: AĞIR / ORTA / HAFİF] - İhlal Skoru: [0-100]

### I. HAKSIZ REKABET VE MEVZUATA AYKIRILIK TESPİTİ
* **[Hukuka Aykırı İfade/Görsel Algı 1]:** (6502 ve TTK uyarınca haksız ticari uygulama gerekçesi)
* **[Hukuka Aykırı İfade/Görsel Algı 2]:**

### II. REKLAM KURULU EMSAL İÇTİHATLARI
* **Emsal Karar 1:** (Dosya No, İhlal Edilen Kural, Ceza Tutarı)

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
                        with st.spinner("Gelişmiş Yapay Zeka Sentez Motoru (OCR & Analiz) çalışıyor..."):
                            for parca in generate_multi_role_synthesis_stream(icerik_listesi, base_prompt, is_danisan):
                                tam_rapor += parca
                                rapor_alani.markdown(tam_rapor + "▌")
                        rapor_alani.empty()
                        st.session_state.rapor_sonucu = tam_rapor
                        st.session_state.dilekce_sonucu = None
                        st.session_state.chat_history = []
                        st.session_state.rakip_gorunum = "Haksız Rekabet ve İhlal Raporu"
                    except Exception as err:
                        st.error(f"Sistem Hatası: {err}")

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

                    if st.session_state.kullanilan_emsaller:
                        st.write("")
                        st.markdown('<div class="section-heading" lang="tr">📚 Raporda Atıf Yapılan Emsal Kararların Orijinal Metinleri</div>', unsafe_allow_html=True)
                        for idx, karar_metni in enumerate(st.session_state.kullanilan_emsaller):
                            baslik_ipucu = karar_metni[:65].replace('\n', ' ') + "..."
                            with st.expander(f"📄 Emsal Dosya {idx+1} | {baslik_ipucu}"):
                                st.markdown(karar_metni)

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
                        
                        if st.session_state.kullanilan_emsaller:
                            st.write("")
                            st.markdown('<div class="section-heading" lang="tr">📚 Raporda Atıf Yapılan Emsal Kararların Orijinal Metinleri</div>', unsafe_allow_html=True)
                            for idx, karar_metni in enumerate(st.session_state.kullanilan_emsaller):
                                baslik_ipucu = karar_metni[:65].replace('\n', ' ') + "..."
                                with st.expander(f"📄 Emsal Dosya {idx+1} | {baslik_ipucu}"):
                                    st.markdown(karar_metni)

                    else:
                        st.caption("İncelenen rakip tanıtım hakkında resmi Reklam Kurulu Şikayet Dilekçesi paneli.")
                        with st.expander("⚖️ Dilekçe Taraf Bilgilerini Düzenle", expanded=True):
                            c_taraf1, c_taraf2 = st.columns(2)
                            with c_taraf1:
                                sikayet_eden_unvan = st.text_input("Şikayet Eden (Müvekkil) Unvanı / Vergi No / MERSİS No", value="")
                                sikayet_eden_adres = st.text_area("Şikayet Eden Adresi", height=65)
                                vekil_bilgisi = st.text_input("Vekil & İletişim Bilgisi")
                            with c_taraf2:
                                sikayet_edilen_unvan = st.text_input("Şikayet Edilen Rakip Unvan / Vergi No / MERSİS No", value="")
                                sikayet_edilen_adres = st.text_area("Şikayet Edilen Adresi / Platform Bilgisi", height=65)

                        if not st.session_state.dilekce_sonucu:
                            if st.button("Resmi Reklam Kurulu Şikayet Dilekçesini Hazırla (Word)", type="primary"):
                                with st.spinner("Kurumsal Reklam Kurulu şikayet dilekçesi hazırlanıyor..."):
                                    try:
                                        s_eden = sikayet_eden_unvan.strip() if sikayet_eden_unvan.strip() else "[Şikayet Eden Şirket / Müvekkil Unvanı]"
                                        s_eden_adr = sikayet_eden_adres.strip() if sikayet_eden_adres.strip() else "[Şikayet Eden Şirket Adresi]"
                                        s_vekil = vekil_bilgisi.strip() if vekil_bilgisi.strip() else "Av. [Vekil Adı Soyadı] - İletişim"
                                        s_edilen = sikayet_edilen_unvan.strip() if sikayet_edilen_unvan.strip() else "[Şikayet Edilen Firma Unvanı]"
                                        s_edilen_adr = sikayet_edilen_adres.strip() if sikayet_edilen_adres.strip() else "[Şikayet Edilen Adres]"
                                        s_link = reklam_url.strip() if reklam_url.strip() else "[İncelenen URL]"

                                        # --- DİLEKÇE YAZIMINDA GÖRSEL YENİDEN BESLEME VE DERİN DÜŞÜNME TALİMATI ---
                                        dilekce_prompt = f"""
Sen tüketici hukuku, haksız rekabet ve Reklam Kurulu regülasyonlarında tecrübeli, derinlemesine düşünen (chain-of-thought) bir Hukuk Müşavirisin.
Aşağıda incelenen rakip tanıtımına ilişkin teknik ihlal raporu ve girilen taraf bilgileri yer almaktadır. Ayrıca bu sürece ait GÖRSELLER de sana tekrar sunulmuştur.

TEKNİK İHLAL RAPORU:
{st.session_state.rapor_sonucu}

TARAF BİLGİLERİ:
ŞİKAYET EDEN: {s_eden}
ADRES: {s_eden_adr}
VEKİLİ / İLETİŞİM: {s_vekil}
ŞİKAYET EDİLEN: {s_edilen}
ADRES: {s_edilen_adr}
İNCELEME LİNKİ: {s_link}

GÖREVİN: Resmi bir REKLAM KURULU ŞİKAYET DİLEKÇESİ hazırlamaktır.
KESİN KURALLAR VE SIFIR HALÜSİNASYON DİREKTİFİ:
1. Dilekçeyi yazarken ürün adı, model sürümü (örn. 3.0), hacim ve gramaj (örn. 20mg/2mL) gibi bilgileri asla kendin uydurma. Bu bilgileri doğrudan sana sunduğum EKTEKİ GÖRSELLERİN ÜZERİNİ OKUYARAK tespit et.
2. Markdown karakterleri (*, #, ---) kullanma, düz metin ver.
3. Emsal kararlara dilekçe gövdesinde yer verme.
4. "müstakilen" kelimesini asla kullanma.
5. Açıklama altındaki 1, 2, 3, 4, 5 maddeleri tam cümle başlıklar olsun ve her biri güçlü bir avukatın kaleme alacağı şekilde haksız ticari uygulama ve yanıltıcı niteliği somutlaştırsın (özellikle görseldeki spor/açık hava temasının yarattığı algı gibi derin hukuki yorumları mutlaka kullan).

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
ŞİKAYET KONUSU: İlgililer hakkında 6502 sayılı Kanun ve Ticari Reklam Yönetmeliği ihlali nedeniyle tedbiren durdurma ve idari para cezası talebidir.

AÇIKLAMALAR:
(Giriş paragrafı)

1. [Tam Cümle Başlık]:
(Açıklama)

2. [Tam Cümle Başlık]:
(Açıklama)

3. [Tam Cümle Başlık]:
(Açıklama)

4. [Tam Cümle Başlık]:
(Açıklama)

5. [Tam Cümle Başlık]:
(Açıklama)

SONUÇ VE İSTEM:
Yukarıda arz edilen nedenlerle reklamların tedbiren durdurulmasını ve idari para cezası uygulanmasını talep ederiz.

ŞİKAYET EDEN MÜVEKKİL VEKİLİ
{s_vekil}
"""
                                        # Görselleri dilekçe aşamasında yapay zekaya tekrar besliyoruz (halüsinasyonu bitiren adım)
                                        dilekce_icerik = [dilekce_prompt]
                                        if yuklenen_gorseller:
                                            for g in yuklenen_gorseller:
                                                dilekce_icerik.append(optimize_image(Image.open(g)))
                                        if web_gorselleri:
                                            for wg in web_gorselleri:
                                                dilekce_icerik.append(wg)

                                        st.session_state.dilekce_sonucu = generate_content_safe(dilekce_icerik)
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
                                        type="secondary"
                                    )
                                except Exception as e:
                                    st.warning(f"Word çıktısı uyarısı: {e}")
                            with col_d2:
                                if st.button("🔄 Dilekçeyi Yeniden Düzenle"):
                                    st.session_state.dilekce_sonucu = None
                                    st.rerun()
            else:
                st.info("Sol panelden parametreleri belirleyip analizi başlattığınızda rapor bu alanda hazır hale gelecektir.")

else:
    with sol_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📡 Hedefli Ürün & Sosyal Medya Radarı</div>', unsafe_allow_html=True)
            radar_urun = st.text_input("Marka / Ürün Anahtar Kelimesi", value="incia bebek yağı", placeholder="Örn: incia bebek yağı veya mamaaura...")
            radar_domain = st.text_input("Markanın Resmi Domaini (Opsiyonel)", value="incia.com.tr", placeholder="Örn: incia.com.tr")
            st.caption("ℹ️ Bu radar; Trendyol, Hepsiburada, Amazon, resmi site ve Instagram kanallarını tarayarak hedef URL havuzunu oluşturur.")
            radar_tara_butonu = st.button("🚀 Hedef Linkleri ve İçerikleri Tespit Et", type="primary")

    with sag_kolon:
        with st.container(border=True):
            st.markdown('<div class="section-heading" lang="tr">📋 Tespit Edilen Tekil Satış & Sosyal Medya Linkleri</div>', unsafe_allow_html=True)
            if radar_tara_butonu:
                trigger_scroll("top")
                if not serpapi_key:
                    st.error("SerpApi API Key bulunamadı.")
                elif not radar_urun:
                    st.warning("Lütfen marka adı giriniz.")
                else:
                    with st.spinner("Tüm pazaryerleri ve sosyal medya taranıyor..."):
                        sonuclar = gelismis_coklu_hedef_taramasi(radar_urun, radar_domain, serpapi_key)
                        st.session_state.radar_link_sonuclari = sonuclar

            if st.session_state.radar_link_sonuclari:
                toplam_link = sum(len(v) for v in st.session_state.radar_link_sonuclari.values())
                st.success(f"🎯 Toplam **{toplam_link}** adet bağlantı tespit edildi.")
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
                            st.warning("Bu kategoride bağlantı bulunamadı.")
            else:
                st.info("Sol panelden taramayı başlattığınızda tespit edilen bağlantılar burada listelenecektir.")

if st.session_state.rapor_sonucu and not is_radar:
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-heading" lang="tr">💬 AdShield Mevzuat Asistanı</div>', unsafe_allow_html=True)
        st.caption("Raporlanan riskler hakkında soru sorabilir veya hızlı butonları kullanabilirsiniz:")
        c1, c2, c3 = st.columns(3)
        hizli_soru = None
        if c1.button("📌 Revize sloganı Instagram'a uyarla"):
            hizli_soru = "Önerdiğin güvenli reklam metnini Instagram post ve story formatına uyarla."
        if c2.button("📝 Zorunlu dipnot metnini hazırla"):
            hizli_soru = "Bu reklamda ambalaj üstüne eklenmesi gereken zorunlu yasal dipnot metnini yaz."
        if c3.button("🛡️ İspat yükümlülüğü rehberi çıkar"):
            hizli_soru = "Reklam Kurulu denetiminde bu iddialar için hazır bulundurulması gereken test belgeleri nelerdir?"

        chat_container = st.container(height=340)
        with chat_container:
            if not st.session_state.chat_history:
                st.info("Henüz soru sormadınız.")
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
                            chat_instruction = f"Sen kurumsal reklam hukuku uzmanısın. Soruları rapora göre yanıtla:\n{st.session_state.rapor_sonucu}"
                            sohbet_gecmisi = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in st.session_state.chat_history])
                            cevap_metni = generate_content_safe(sohbet_gecmisi, system_instruction=chat_instruction)
                            st.markdown(cevap_metni)
                            st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                        except Exception as e:
                            st.error(f"Hata: {e}")
            st.rerun()
