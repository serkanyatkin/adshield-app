import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
from datetime import datetime
import os
import glob
import re
import requests
import io
from urllib.parse import urljoin

st.set_page_config(
    page_title="AdShield | Reklam Mevzuatı & Risk Denetim Platformu",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kurumsal, Ortalanmış ve Alan Seçimli CSS Tasarımı
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Sayfayı Ortala */
    .block-container {
        max-width: 1180px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        margin: 0 auto !important;
    }
    
    /* Üst Header */
    .firm-header {
        background-color: #5D728B;
        padding: 22px 30px;
        border-radius: 6px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(93, 114, 139, 0.18);
    }
    .firm-title {
        font-family: 'Cinzel', serif;
        font-size: 20px;
        letter-spacing: 1.5px;
        font-weight: 700;
    }
    .firm-subtitle {
        font-size: 11.5px;
        letter-spacing: 1px;
        color: #DCE4EC;
        margin-top: 3px;
    }
    .firm-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #ffffff;
        font-size: 11px;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 4px;
        letter-spacing: 0.8px;
    }

    /* Ortalanmış Mod Başlığı */
    .mode-header-title {
        text-align: center;
        font-family: 'Cinzel', serif;
        font-size: 14.5px;
        letter-spacing: 1.5px;
        color: #2C3848;
        font-weight: 700;
        margin-bottom: 14px;
        text-transform: uppercase;
    }

    /* Yuvarlak Butonları Gizle ve Kart Segment Haline Getir */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        justify-content: center;
        gap: 16px;
        width: 100%;
        margin-bottom: 12px;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: 1;
        background: #FFFFFF;
        border: 1.5px solid #CBD5E1;
        border-radius: 6px;
        padding: 16px 20px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }

    /* Yuvarlak radyo simgesini gizle */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        border-color: #5D728B;
        background: #F8FAFC;
    }

    /* Seçili kart stili */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        border-color: #5D728B !important;
        background-color: #F1F5F9 !important;
        box-shadow: 0 0 0 1px #5D728B, 0 4px 10px rgba(93, 114, 139, 0.12) !important;
        font-weight: 600 !important;
        color: #1E293B !important;
    }

    .section-heading {
        font-family: 'Cinzel', serif;
        font-size: 14px;
        letter-spacing: 1px;
        color: #2C3848;
        font-weight: 700;
        margin-bottom: 14px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
    }

    .stButton button[kind="primary"] {
        background-color: #5D728B !important;
        color: #ffffff !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        letter-spacing: 0.5px !important;
        border-radius: 4px !important;
        border: 1px solid #4D6076 !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #4A5E74 !important;
        box-shadow: 0 4px 12px rgba(74, 94, 116, 0.25) !important;
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
if not api_key:
    with st.sidebar:
        st.header("Sistem Ayarları")
        api_key = st.text_input("Gemini API Key:", type="password")

def generate_content_safe(contents, system_instruction=None):
    if not api_key:
        raise Exception("API anahtarı bulunamadı.")
    
    genai.configure(api_key=api_key)
    
    aktif_modeller = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                aktif_modeller.append(m.name)
    except Exception:
        aktif_modeller = ["models/gemini-1.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro"]

    oncelikli = [m for m in aktif_modeller if "flash" in m] + [m for m in aktif_modeller if "flash" not in m]
    
    last_err = None
    for model_name in oncelikli:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
            response = model.generate_content(contents)
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            continue
            
    raise Exception(f"Aktif modellerle bağlantı kurulamadı. Hata: {last_err}")

def fetch_url_data(url):
    if not url or not url.strip().startswith(("http://", "https://")):
        return "", []
    
    if any(sm in url.lower() for sm in ["instagram.com", "tiktok.com", "facebook.com", "twitter.com", "x.com"]):
        return "[Sosyal medya linki girildi. Güvenlik duvarı nedeniyle doğrudan taranamamaktadır; görsel ve metin üzerinden incelenecektir.]", []
    
    clean_text = ""
    downloaded_images = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(url.strip(), headers=headers, timeout=10)
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
                    if len(img_urls) >= 4:
                        break

                for i_url in img_urls[:3]:
                    try:
                        img_res = requests.get(i_url, headers=headers, timeout=6)
                        if img_res.status_code == 200 and len(img_res.content) > 4000:
                            pil_img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                            downloaded_images.append(pil_img)
                    except Exception:
                        continue

                for s in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                    s.decompose()
                raw_text = soup.get_text(separator=' ')
                clean_text = ' '.join(raw_text.split())[:4500]

            except ImportError:
                clean_text = re.sub(r'<[^>]+>', ' ', res.text)[:4500]

    except Exception as e:
        clean_text = f"[Web içeriği çekilemedi: {e}]"
        
    return clean_text, downloaded_images

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

def get_relevant_emsaller(metin, sektor, top_k=8):
    if not karar_arsivi:
        return "Karar arşivi yüklenemedi."
    
    sektor_keywords = {
        "Kozmetik & Kişisel Bakım / Anne-Bebek": ["kozmetik", "doğal", "bitkisel", "organik", "cilt", "leke", "kırışıklık", "titck", "onaylı", "tedavi", "mucize", "yok eder", "klinik"],
        "Takviye Edici Gıda & Sağlık": ["takviye", "gıda", "sağlık beyanı", "tedavi", "hastalık", "kilo", "zayıflama", "bağışıklık", "eklem", "ağrı", "şifa", "onay", "kesin son", "iltihap"],
        "E-Ticaret & İndirim Kampanyaları": ["indirim", "fiyat", "en ucuz", "tavsiye edilen", "stok", "bedava", "en çok satan", "fiyatı düştü", "efsane", "tükeniyor"],
        "Sosyal Medya & Influencer Reklamları": ["influencer", "işbirliği", "etiket", "örtülü reklam", "sosyal medya", "tanıtım", "link", "ortaklık", "sponsor", "reklam"]
    }
    
    anahtarlar = set(sektor_keywords.get(sektor, []))
    if metin:
        kelimeler = re.findall(r'\b\w{3,}\b', metin.lower())
        anahtarlar.update(kelimeler[:12])

    skorlu = []
    for karar in karar_arsivi:
        k_lower = karar.lower()
        skor = sum(k_lower.count(k) * 2 for k in anahtarlar)
        if "idari para" in k_lower or "durdurma" in k_lower or "dosya no" in k_lower:
            skor += 5
        if '"' in karar or '“' in karar:
            skor += 3
        if skor > 0:
            skorlu.append((skor, karar[:3800]))

    skorlu.sort(key=lambda x: x[0], reverse=True)
    secilenler = [k[1] for k in skorlu[:top_k]]
    return "\n\n--- [EMSAL KARAR METNİ] ---\n\n".join(secilenler if secilenler else karar_arsivi[:4])

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
    
    if not os.path.exists(font_path) or os.path.getsize(font_path) < 10000:
        try:
            url = "https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.66/fonts/Roboto/Roboto-Regular.ttf"
            res = requests.get(url, timeout=10)
            if res.status_code == 200 and len(res.content) > 10000:
                with open(font_path, "wb") as f:
                    f.write(res.content)
        except Exception:
            pass

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
        pdf.set_font("Roboto", "", 8.5)
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
        pdf.set_font("Helvetica", "", 8.5)
        ascii_metin = temiz_metin.replace("İ", "I").replace("ı", "i").translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4.8, ascii_metin)

    return bytes(pdf.output())

# Session State
if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
if "dilekce_sonucu" not in st.session_state:
    st.session_state.dilekce_sonucu = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Ortalanmış Başlık ve Alan İşaretli Seçim Kartları
st.markdown('<div class="mode-header-title" lang="tr">İnceleme Modunu Seçiniz</div>', unsafe_allow_html=True)

mod_secimi = st.radio(
    "Denetim Modu",
    [
        "Kurumsal Kampanya Taslağı Uyum Denetimi (İç Denetim & Revizyon Modu)",
        "Piyasa ve Rakip Reklam İncelemesi (Haksız Rekabet & Şikayet Modu)"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

is_danisan = "İç Denetim" in mod_secimi

# İki Kolonlu Panel
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
            "Ulusal Televizyon Kanalı",
            "Yerel Televizyon / Radyo",
            "Açık Hava (Billboard, Broşür vb.)"
        ])
        
        reklam_url = st.text_input(
            "Web Sayfası / Ürün Linki",
            placeholder="https://www.site.com/urun veya kampanya adresi..."
        )

        if reklam_url and any(sm in reklam_url.lower() for sm in ["instagram.com", "tiktok.com"]):
            st.info("Sosyal medya linkleri doğrudan bot erişimine kapalıdır. İncelemenin eksiksiz yapılması için lütfen metni aşağıya yapıştırınız ve görseli yükleyiniz.")

        reklam_metni = st.text_area(
            "Reklam Metni / Ticari İddialar / Caption",
            height=130,
            placeholder="İncelenmesi talep edilen metin veya iddiaları giriniz..."
        )
        
        yuklenen_gorseller = st.file_uploader(
            "Reklam Görselleri / Taslaklar / Ekran Görüntüleri (Çoklu Yükleme)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        if yuklenen_gorseller:
            gorsel_cols = st.columns(min(len(yuklenen_gorseller), 4))
            for idx, g_dosya in enumerate(yuklenen_gorseller):
                g_img = Image.open(g_dosya).convert("RGB")
                gorsel_cols[idx % 4].image(g_img, caption=f"Görsel {idx+1}", use_container_width=True)

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
                url_metni = ""
                web_gorselleri = []
                
                if reklam_url:
                    with st.spinner("Link içeriği kontrol ediliyor..."):
                        url_metni, web_gorselleri = fetch_url_data(reklam_url)
                
                with st.spinner("Reklam Kurulu içtihatları ve mevzuat çerçevesinde inceleniyor..."):
                    try:
                        birlestirilmis_metin = f"{reklam_metni}\n\n[İncelenen Link/Kaynak]: {reklam_url}\n{url_metni}" if reklam_url else reklam_metni
                        ilgili_emsaller = get_relevant_emsaller(birlestirilmis_metin, sektor)
                        
                        if is_danisan:
                            prompt = f"""
Sen reklam mevzuatı ve haksız ticari uygulamalar denetimi konusunda uzmanlaşmış kıdemli bir Kurumsal Reklam Uyum Denetçisisin.
Şirket yönetimimiz, planlanan reklam taslağının (metinler, yüklenen görseller veya web sayfasındaki afiş/ürün ambalajları) Reklam Kurulu denetimlerinden idari yaptırım almadan geçmesi için bir 'Uyumluluk ve Güvenli Revizyon Raporu' talep etmektedir.

Aşağıda karar arşivinden incelenen iddialarla en yüksek vakıa benzerliği gösteren somut Reklam Kurulu kararları verilmiştir:
=== RESMİ EMSAL METİNLERİ ===
{ilgili_emsaller}
=============================

İNCELENEN KAMPANYA TASLAĞI:
Sektör: {sektor}
Mecra: {mecra}
İçerik: {birlestirilmis_metin}
(Görseller üzerindeki tüm metin, logo ve ambalaj iddialarını da doğrudan incele)

RAPOR FORMATI:

### [RİSK DERECESİ: YÜKSEK (KIRMIZI) / ORTA (SARI) / DÜŞÜK (YEŞİL)] - Risk Skoru: [0-100]

### I. MEVZUAT UYUM ANALİZİ VE RİSKLİ İFADELER
(Taslak metindeki ve görsellerdeki riskli iddiaları tek tek ayıkla. 6502 md. 61, Ticari Reklam Yönetmeliği, TİTCK/TGK Kılavuzları açısından açıkla):
* **[Riskli İfade 1]:** (Neden mevzuata aykırı? Kurul'un ortalama tüketici algısı ve ispat yükü yaklaşımı nedir?)
* **[Riskli İfade 2]:**
* **[Riskli İfade 3]:**

### II. REKLAM KURULU EMSAL KARARLARI VE CEZA EŞLEŞMELERİ
(Arşivdeki emsal metinlerden tespit edilen somut kararlardan EN AZ 2 ADET karar künyesini şu formatta ver):
* **Emsal Karar 1:**
  - **Dosya No & Karar Tarihi:**
  - **Firma / Mecra:** 
  - **Kararda Ceza Alan Orijinal İfade:**
  - **Taslağımızla Benzerliği:**
  - **Uygulanan Yaptırım:** (Durdurma ve ... TL İdari Para Cezası)
* **Emsal Karar 2:**
  - **Dosya No & Karar Tarihi:**
  - **Firma / Mecra:** 
  - **Kararda Ceza Alan Orijinal İfade:**
  - **Taslağımızla Benzerliği:**
  - **Uygulanan Yaptırım:**

### III. ÖNGÖRÜLEN İDARİ PARA CEZASI VE RİSK SKALASI
* **Yayın Mecrası:** {mecra}
* **6502 Sayılı Kanun Md. 77 Ceza Aralığı:** (Mecraya göre geçerli idari para cezası limitleri)
* **Diğer Riskler:** (Durdurma, düzeltme, erişim engeli/içerik çıkarma riski)

### IV. GÜVENLİ VE TİCARİ ETKİSİ YÜKSEK REVİZE METİN
* **Önerilen Güvenli Reklam Metni:** (Cezai riski sıfırlayan ancak reklamın satış gücünü koruyan alternatif metin)
* **Gereken İspat / Dipnot Standartları:** (Hazır bulundurulması gereken test raporu veya görsel altı yasal dipnot)

### V. YASAL ŞERH
"Bu rapor teknik bir ön risk analizi niteliğinde olup, somut uyuşmazlıklarda nihai hukuki mütalaa yerine geçmez."
"""
                        else:
                            prompt = f"""
Sen haksız rekabet, piyasa denetimi ve tüketici mevzuatı alanında uzmanlaşmış kıdemli bir Kurumsal Uyum ve Rekabet Denetçisisin.
Pazardaki bir rakip ürünün / tanıtımın (metin, web sayfası veya görseller üzerindeki ambalaj/banner iddialarının) mevzuata aykırı olduğunu, tüketiciyi aldattığını ve haksız rekabet yarattığını tespit etmek amacıyla detaylı bir ihlal raporu hazırlamaktasın.

Aşağıda karar arşivinden incelenen iddialarla en yüksek vakıa benzerliği gösteren somut Reklam Kurulu kararları verilmiştir:
=== RESMİ EMSAL METİNLERİ ===
{ilgili_emsaller}
=============================

İNCELENEN RAKİP İLETİŞİM:
Sektör: {sektor}
Mecra: {mecra}
İçerik: {birlestirilmis_metin}

RAPOR FORMATI:

### [İHLAL DERECESİ: AĞIR (KIRMIZI) / ORTA (SARI) / HAFİF (YEŞİL)] - İhlal Skoru: [0-100]

### I. HAKSIZ REKABET VE MEVZUATA AYKIRILIK TESPİTİ
(Rakip tanıtımdaki ve görsellerdeki hukuka aykırı unsurları; 6502 md. 61, TTK md. 54-55 Haksız Rekabet ve Kılavuz hükümleri çerçevesinde tek tek gerekçelendir):
* **[Hukuka Aykırı İfade / Uygulama 1]:** (Haksız ticari uygulama ve yanıltıcı niteliği)
* **[Hukuka Aykırı İfade / Uygulama 2]:**

### II. REKLAM KURULU EMSAL İÇTİHATLARI
(Rakibin kullandığı ifadelere benzer iddialara Kurul'un daha önce verdiği EN AZ 2 ADET emsal kararı künyesiyle sun):
* **Emsal Karar 1:**
  - **Dosya No & Karar Tarihi:**
  - **Ceza Alan Şirket / Mecra:**
  - **Karardaki Yasaklı Orijinal İfade:**
  - **Uygulanan Yaptırım:** (Durdurma ve ... TL İdari Para Cezası)
* **Emsal Karar 2:**
  - **Dosya No & Karar Tarihi:**
  - **Ceza Alan Şirket / Mecra:**
  - **Karardaki Yasaklı Orijinal İfade:**
  - **Uygulanan Yaptırım:**

### III. RAKİBE UYGULANABİLECEK İDARİ YAPTIRIMLAR
* **6502 Sayılı Kanun Md. 77 Para Cezası:** (Mecraya göre uygulanacak ceza tutarı)
* **İdari Tedbirler:** (Reklamı durdurma, düzeltme, internetten içerik çıkarma / erişim engeli)

### IV. ŞİKAYET VE BAŞVURU STRATEJİSİ
* **Reklam Kurulu Başvuru Dayanakları:** (Dilekçede öne çıkarılacak en güçlü argümanlar)
* **Gereken Delil Tespiti:** (Noter tespiti, URL kaydı, arşiv kaydı vb.)

### V. YASAL ŞERH
"Bu rapor teknik bir ön risk analizi niteliğinde olup, somut uyuşmazlıklarda nihai hukuki mütalaa yerine geçmez."
"""
                        
                        icerik_listesi = [f"Metin: {birlestirilmis_metin}\nSektör: {sektor}\nMecra: {mecra}"]
                        if yuklenen_gorseller:
                            for g in yuklenen_gorseller:
                                icerik_listesi.append(Image.open(g).convert("RGB"))
                        if web_gorselleri:
                            for wg in web_gorselleri:
                                icerik_listesi.append(wg)
                        
                        st.session_state.rapor_sonucu = generate_content_safe(icerik_listesi, system_instruction=prompt)
                        st.session_state.dilekce_sonucu = None
                        st.session_state.chat_history = []
                    except Exception as err:
                        st.error(f"Analiz sırasında bir hata oluştu: {err}")

        if st.session_state.rapor_sonucu:
            if is_danisan:
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
                tab_ihlal, tab_dilekce = st.tabs(["Haksız Rekabet ve İhlal Raporu", "Reklam Kurulu Şikayet Dilekçesi"])
                
                with tab_ihlal:
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

                with tab_dilekce:
                    st.caption("İncelenen rakip tanıtım hakkında Reklam Kurulu Başkanlığı'na sunulmak üzere doğrudan resmi başvuru formatında dilekçe oluşturur.")
                    
                    if st.button("Resmi Reklam Kurulu Şikayet Dilekçesini Hazırla"):
                        with st.spinner("Şikayet dilekçesi hazırlanıyor..."):
                            try:
                                dilekce_prompt = f"""
Sen tüketici hukuku ve reklam regülasyonları konusunda deneyimli bir Hukuk Müşavirisin.
Aşağıda incelenen rakip iletişim vakıası ve tespit edilen mevzuat aykırılıkları yer almaktadır:

İNCELEME RAPORU VE VAKIA VERİSİ:
{st.session_state.rapor_sonucu}

GÖREVİN:
Yapay zeka robotik şablonlarından tamamen uzak; doğrudan Türk idari yargı ve Reklam Kurulu pratiğine uygun, **AÇIKLAMALAR BÖLÜMÜNDEKİ HER MADDENİN BAŞLIĞI DOĞRUDAN SOMUT VAKIADAKİ İHLALİ ANLATAN TAM BİR CÜMLE OLAN**, net ve etkili bir ŞİKAYET DİLEKÇESİ hazırlamaktır.

DİLEKÇEYİ AYNEN AŞAĞIDAKİ YAPI VE DİLDE OLUŞTUR:

T.C. TİCARET BAKANLIĞI
REKLAM KURULU BAŞKANLIĞINA
ANKARA

ŞİKAYET EDEN : [Şikayet Eden Şirket / Marka Unvanı]
ADRES : [Şirket Adresi]
YETKİLİ / VEKİL : [Şirket Temsilcisi / Hukuk Müşaviri / Vekil]
ŞİKAYET EDİLEN : [Şikayet Edilen Firma / Satıcı / Hesap Bilgisi]
ADRES : [Şikayet Edilen Adres / İnternet Sitesi / Mecra]
ŞİKAYET KONUSU : Şikayet edilen tarafça yürütülen tanıtımlarda yer alan tüketiciyi yanıltıcı, haksız rekabete yol açıcı ve mevzuata aykırı nitelikteki iddialar nedeniyle idari yaptırım uygulanması ve anılan reklamların durdurulması talebidir.

AÇIKLAMALAR:

1. [ŞİKAYET EDİLENİN REKLAM VE AMBALAJLARDA KULLANDIĞI SOMUT İDDİANIN YANILTICI NİTELİĞİNİ ANLATAN TAM BİR CÜMLE BAŞLIK]:
(Şikayet edilenin ürün tanıtımında, sosyal medyada veya ambalajda hangi somut iddia ve ifadeleri kullandığı, bu tanıtımın nerede tespit edildiği ve ortalama tüketici nezdinde nasıl haksız bir algı yarattığı).

2. [İNCELENEN ÜRÜN KATEGORİSİNİN BİLİMSEL / SEKTÖREL GERÇEKLİĞİ KARŞISINDA BU İDDİANIN İMKANSIZ VEYA STANDART BİR ZORUNLULUK OLDUĞUNU BELİRTEN TAM BİR CÜMLE BAŞLIK]:
(Ürünün doğası, kimyasal/teknik içeriği veya kullanım amacı gereği vaat edilen etkinin neden gerçeğe aykırı olduğu veya kategorideki tüm ürünlerde zaten bulunması/bulunmaması gereken genel bir niteliğin münhasır bir üstünlük gibi sunulduğu).

3. [TİTCK / TGK KILAVUZLARI VE SEKTÖREL DÜZENLEMELER UYARINCA BU TÜR İDDİALARIN YASAKLANDIĞINI GÖSTEREN TAM BİR CÜMLE BAŞLIK]:
(İlgili Kılavuz hükümleri uyarınca ürünün sahip olmadığı veya kategorideki tüm ürünlerde zaten mevcut olan genel özelliklerin yalnızca kendisine aitmiş gibi sunulamayacağı ve izin verilmeyen sağlık/üstünlük beyanlarının kullanılamayacağı ilkesi).

4. [6502 SAYILI KANUN VE TİCARİ REKLAM YÖNETMELİĞİ UYARINCA SÖZ KONUSU TANITIMLARIN HAKSIZ REKABET VE ALDATICI REKLAM TEŞKİL ETTİĞİNİ İZAH EDEN TAM BİR CÜMLE BAŞLIK]:
(6502 sayılı Kanun md. 61 ile Ticari Reklam Yönetmeliği md. 7, 9, 10, 11 uyarınca tüketicinin bilgi eksikliğinin istismar edildiği, dürüst rakiplerin haksız yere şaibe altında bırakıldığı ve pazardaki dürüst rekabet ortamının bozulduğu).

SONUÇ VE İSTEM : Yukarıdaki açıklamalar çerçevesinde ve kurulunuzun re’sen dikkate alacağı nedenlerle; dilekçemizde belirtilen ve kurulunuzca belirlenecek diğer mecralarda yayınlanmış ve yayınlanan reklam ve bilgilendirmelerin incelenerek yayınının tedbiren ve nihai olarak DURDURULMASINA, yayından kaldırılmasına ve sorumlu şirket/şahıs hakkında en üst hadden İDARİ PARA CEZASI ile cezalandırılmasına karar verilmesini saygılarımızla arz ve talep ederiz.

[Şikayet Eden Şirket Unvanı]
Yetkilisi / Vekili
"""
                                st.session_state.dilekce_sonucu = generate_content_safe(dilekce_prompt)
                            except Exception as e:
                                st.error(f"Dilekçe hazırlanırken bir hata oluştu: {e}")

                    if st.session_state.dilekce_sonucu:
                        st.markdown(st.session_state.dilekce_sonucu)
                        try:
                            dilekce_pdf = create_pdf(st.session_state.dilekce_sonucu, "T.C. Ticaret Bakanligi Reklam Kurulu Baskanligi Sikayet Dilekcesi")
                            st.download_button(
                                label="Şikayet Dilekçesini İndir (PDF)",
                                data=dilekce_pdf,
                                file_name=f"Reklam_Kurulu_Sikayet_Dilekcesi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf",
                                type="primary"
                            )
                        except Exception as e:
                            st.warning(f"Dilekçe PDF uyarısı: {e}")
        else:
            st.info("Sol panelden parametreleri belirleyip analizi başlattığınızda rapor bu alanda hazır hale gelecektir.")

# İnteraktif Danışman Paneli
if st.session_state.rapor_sonucu:
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-heading" lang="tr">Mevzuat Danışmanı ve Soru-Cevap</div>', unsafe_allow_html=True)
        st.caption("Üretilen rapora, emsal dosyalara veya stratejik adımlara ilişkin sorularınızı iletebilirsiniz.")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        kullanici_sorusu = st.chat_input("Sorunuzu buraya yazınız...")
        if kullanici_sorusu:
            st.session_state.chat_history.append({"role": "user", "content": kullanici_sorusu})
            with st.chat_message("user"):
                st.markdown(kullanici_sorusu)

            with st.chat_message("assistant"):
                with st.spinner("Değerlendiriliyor..."):
                    try:
                        chat_instruction = f"""
Sen kurumsal reklam mevzuatı ve Reklam Kurulu içtihatları konusunda uzmanlaşmış bir Uyum Danışmanısın.
Kullanıcı seçilen mod ({'Kampanya Uyum Modu' if is_danisan else 'Rakip Şikayet Modu'}) kapsamında sorular soruyor.
Rapor: {st.session_state.rapor_sonucu}
Metin: {reklam_metni}
Soruyu doğrudan mevzuat ve içtihat ışığında yanıtla.
"""
                        sohbet_gecmisi_prompt = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in st.session_state.chat_history])
                        cevap_metni = generate_content_safe(sohbet_gecmisi_prompt, system_instruction=chat_instruction)
                        st.markdown(cevap_metni)
                        st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                    except Exception as e:
                        st.error(f"Hata: {e}")
