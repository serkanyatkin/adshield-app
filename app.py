import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
from datetime import datetime
import os
import glob
import re
import requests

st.set_page_config(
    page_title="Sezer Kara Hukuk Bürosu | Reklam Hukuku Denetim Sistemi",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kurumsal CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .firm-header {
        background-color: #5D728B;
        padding: 20px 30px;
        border-radius: 4px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(93, 114, 139, 0.15);
    }
    .firm-title {
        font-family: 'Cinzel', serif;
        font-size: 20px;
        letter-spacing: 2px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .firm-subtitle {
        font-size: 11px;
        letter-spacing: 1.5px;
        color: #DCE4EC;
        text-transform: uppercase;
        margin-top: 3px;
    }
    .firm-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #ffffff;
        font-size: 11px;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 2px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .section-heading {
        font-family: 'Cinzel', serif;
        font-size: 14px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #2C3848;
        font-weight: 700;
        margin-bottom: 14px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
    }

    .stButton button[kind="primary"] {
        background-color: #5D728B !important;
        color: #ffffff !important;
        font-family: 'Cinzel', serif !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        border-radius: 3px !important;
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
<div class="firm-header">
    <div>
        <div class="firm-title">Sezer Kara Hukuk Bürosu</div>
        <div class="firm-subtitle">Reklam Kurulu İçtihat & Risk Denetim Sistemi</div>
    </div>
    <div class="firm-badge">Reklam & Rekabet Hukuku Departmanı</div>
</div>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    with st.sidebar:
        st.header("Sistem Ayarları")
        api_key = st.text_input("Gemini API Key:", type="password")

secilen_model = "gemini-3.6-flash"

def fetch_url_content(url):
    if not url or not url.strip().startswith(("http://", "https://")):
        return ""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url.strip(), headers=headers, timeout=8)
        if res.status_code == 200:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(res.text, 'html.parser')
                for s in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                    s.decompose()
                text = soup.get_text(separator=' ')
            except ImportError:
                text = re.sub(r'<[^>]+>', ' ', res.text)
            return ' '.join(text.split())[:4500]
    except Exception as e:
        return f"[Web içeriği çekilemedi: {e}]"
    return ""

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
        tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, baslik_metni.translate(tr_map), ln=True, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.cell(0, 5, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        pdf.line(10, 24, 200, 24)
        pdf.ln(5)
        pdf.set_font("Helvetica", "", 8.5)
        ascii_metin = temiz_metin.translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4.8, ascii_metin)

    return bytes(pdf.output())

# Session State
if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
if "dilekce_sonucu" not in st.session_state:
    st.session_state.dilekce_sonucu = None
if "aktif_mod" not in st.session_state:
    st.session_state.aktif_mod = "danisan"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "taslak_metin" not in st.session_state:
    st.session_state.taslak_metin = ""

# ÜST SEVİYE MOD SEÇİCİ
mod_secimi = st.radio(
    "İŞLEM AMACINI SEÇİNİZ:",
    ["🛡️ Kendi Reklam Taslağımızın Uyumluluk Denetimi (Danışan Modu)", 
     "⚖️ Rakip Ürün & Reklam İncelemesi (Şikayet & İhbar Modu)"],
    horizontal=True
)

is_danisan = "Danışan" in mod_secimi
st.session_state.aktif_mod = "danisan" if is_danisan else "rakip"

sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

with sol_kolon:
    with st.container(border=True):
        if is_danisan:
            st.markdown('<div class="section-heading">Kendi Reklam Taslağımız / İddialarımız</div>', unsafe_allow_html=True)
            st.caption("⚡ Hızlı Test İçin Örnek Yükle:")
            sc1, sc2, sc3 = st.columns(3)
            if sc1.button("Kozmetik Taslak"):
                st.session_state.taslak_metin = "Dermatologların 1 numaralı tercihi! Tamamen %100 bitkisel serumumuz leke ve kırışıklıkları 48 saatte tamamen yok eder. Sağlık Bakanlığı onaylı formülüyle botoks etkisini evinize getirir."
            if sc2.button("Gıda Takviyesi"):
                st.session_state.taslak_metin = "Eklem kireçlenmesine kesin son! Bağışıklığı güçlendirerek dizdeki iltihabı kurutur, ameliyatsız tedavi sağlar."
            if sc3.button("Kampanya / İndirim"):
                st.session_state.taslak_metin = "Yılın efsane indirimi! Türkiye'nin en ucuz robot süpürgesi sadece bugün 24.999 TL yerine 4.999 TL! Son 3 ürün, tükeniyor."
        else:
            st.markdown('<div class="section-heading">İncelenecek Rakip Ürün & Reklam Materyali</div>', unsafe_allow_html=True)
            st.caption("⚡ Rakip İhlal Örneği Yükle:")
            rc1, rc2 = st.columns(2)
            if rc1.button("Rakip Bebek Kremi (SLS İddiası)"):
                st.session_state.taslak_metin = "Sudocrem markalı bebek bakım kreminin eczane stantlarında 'SLS İçermez' simgesi ve iddiasıyla satıldığı tespit edilmiştir. Durulanmayan bebek kreminde SLS zaten kullanılamayacağı halde bu ifade haksız üstünlük sağlamaktadır."
            if rc2.button("Rakip Dermokozmetik"):
                st.session_state.taslak_metin = "Rakip marka Instagram ve web sitesinde 'Doktorların reçete ettiği tek leke giderici serum, 3 günde ameliyatsız gençleşme garantisi' şeklinde tanıtım yapmaktadır."

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
            "Web Sayfası / Ürün / Reklam Linki (Opsiyonel)",
            placeholder="https://www.site.com/urun veya reklam URL'si..."
        )

        reklam_metni = st.text_area(
            "Reklam Metni / Ticari İddialar / Açıklamalar",
            value=st.session_state.taslak_metin,
            height=110,
            placeholder="İncelenmesini istediğiniz metin veya iddiaları giriniz..."
        )
        
        yuklenen_gorseller = st.file_uploader(
            "Reklam Görselleri / Taslaklar / Stant Fotoğrafları",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        if yuklenen_gorseller:
            gorsel_cols = st.columns(min(len(yuklenen_gorseller), 4))
            for idx, g_dosya in enumerate(yuklenen_gorseller):
                g_img = Image.open(g_dosya)
                gorsel_cols[idx % 4].image(g_img, caption=f"Görsel {idx+1}", use_container_width=True)

        buton_etiketi = "🛡️ Uyum Analizi & Güvenli Revizyonu Başlat" if is_danisan else "⚖️ Rakip İhlal Analizini Başlat"
        analiz_butonu = st.button(buton_etiketi, type="primary")

with sag_kolon:
    with st.container(border=True):
        panel_baslik = "Hukuki Uyum & Güvenli Revizyon Raporu" if is_danisan else "Rakip İhlal Tespiti & Şikayet Merkezi"
        st.markdown(f'<div class="section-heading">{panel_baslik}</div>', unsafe_allow_html=True)
        
        if analiz_butonu:
            if not api_key:
                st.error("Lütfen geçerli bir API anahtarı sağlayınız.")
            elif not reklam_metni and not yuklenen_gorseller and not reklam_url:
                st.warning("Lütfen metin giriniz, link paylaşınız veya görsel yükleyiniz.")
            else:
                url_metni = ""
                if reklam_url:
                    with st.spinner("Web sayfası taranıyor..."):
                        url_metni = fetch_url_content(reklam_url)
                
                with st.spinner("Reklam Kurulu içtihatları ve 6502 sayılı Kanun taranıyor..."):
                    try:
                        genai.configure(api_key=api_key)
                        birlestirilmis_metin = f"{reklam_metni}\n\n[Web İçeriği]: {url_metni}" if url_metni else reklam_metni
                        ilgili_emsaller = get_relevant_emsaller(birlestirilmis_metin, sektor)
                        
                        if is_danisan:
                            prompt = f"""
Sen Sezer Kara Hukuk Bürosu bünyesinde çalışan kıdemli bir Reklam Hukuku ve Mevzuat Uyum Danışmanısın.
Müvekkilimiz, kendi reklam taslağının Reklam Kurulu denetimlerinden ceza almadan geçmesi için bir 'Uyumluluk ve Güvenli Revizyon Raporu' talep etmektedir.

Aşağıda karar arşivinden incelenen iddialarla en yüksek vakıa benzerliği gösteren somut Reklam Kurulu kararları verilmiştir:
=== RESMİ EMSAL METİNLERİ ===
{ilgili_emsaller}
=============================

İNCELENEN REKLAM TASLAĞI:
Sektör: {sektor}
Mecra: {mecra}
İçerik: {birlestirilmis_metin}

RAPOR FORMATI:

### [RİSK DERECESİ: YÜKSEK (KIRMIZI) / ORTA (SARI) / DÜŞÜK (YEŞİL)] - Risk Skoru: [0-100]

### I. MEVZUAT UYUM ANALİZİ VE RİSKLİ İFADELER
(Taslak metindeki riskli ifadeleri tek tek ayıkla. 6502 md. 61, Ticari Reklam Yönetmeliği, TİTCK/TGK Kılavuzları açısından açıkla):
* **[Riskli İfade 1]:** (Neden mevzuata aykırı? Kurul'un ortalama tüketici algısı ve ispat yükü yaklaşımı nedir?)
* **[Riskli İfade 2]:**
* **[Riskli İfade 3]:**

### II. REKLAM KURULU EMSAL KARARLARI VE CEZA EŞLEŞMELERİ
(Arşivdeki emsal metinlerden tespit edilen somut kararlardan EN AZ 2 ADET karar künyesini şu formatta ver):
* **Emsal Karar 1:**
  - **Dosya No & Karar Tarihi:** (Örn: Dosya No: 2023/..., Karar Tarihi: ...)
  - **Firma / Mecra:** 
  - **Kararda Ceza Alan Orijinal İfade:** (Kararda ceza alan şirketin kullandığı tırnak içi tam reklam cümlesi)
  - **Taslağımızla Benzerliği:** (Taslağımızdaki hangi vaat bu kararla örtüşüyor?)
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
"Bu rapor teknik bir ön risk analizi niteliğinde olup, somut uyuşmazlıklarda nihai hukuki danışmanlık yerine geçmez."
"""
                        else:
                            prompt = f"""
Sen Sezer Kara Hukuk Bürosu bünyesinde görev yapan kıdemli bir Reklam ve Haksız Rekabet Avukatısın.
Müvekkilimiz, pazardaki bir rakip ürünün / reklamın mevzuata aykırı olduğunu, tüketiciyi aldattığını ve haksız rekabet yarattığını düşünerek inceleme talep etmektedir.

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
(Rakip tanıtımdaki hukuka aykırı unsurları; 6502 md. 61, TTK md. 54-55 Haksız Rekabet ve Kılavuz hükümleri çerçevesinde tek tek gerekçelendir):
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
* **Reklam Kurulu Başvuru Dayanakları:** (Dilekçede öne çıkarılacak en güçlü 2 argüman)
* **Gereken Delil Tespiti:** (Noter tespiti, URL kaydı, arşiv kaydı vb.)

### V. YASAL ŞERH
"Bu rapor teknik bir ön risk analizi niteliğinde olup, somut uyuşmazlıklarda nihai hukuki danışmanlık yerine geçmez."
"""
                        
                        model = genai.GenerativeModel(model_name=secilen_model, system_instruction=prompt)
                        icerik_listesi = [f"Metin: {birlestirilmis_metin}\nSektör: {sektor}\nMecra: {mecra}"]
                        if yuklenen_gorseller:
                            for g in yuklenen_gorseller:
                                icerik_listesi.append(Image.open(g))
                        
                        response = model.generate_content(icerik_listesi)
                        st.session_state.rapor_sonucu = response.text
                        st.session_state.dilekce_sonucu = None
                        st.session_state.chat_history = []
                    except Exception as err:
                        st.error(f"Analiz sırasında bir hata oluştu: {err}")

        # SONUÇ GÖRÜNÜMÜ: Danışan Modunda Sadece Uyum Raporu, Rakip Modunda Sekmeli Dilekçe
        if st.session_state.rapor_sonucu:
            if is_danisan:
                # DANIŞAN MODU: Şikayet dilekçesi YOK
                st.markdown(st.session_state.rapor_sonucu)
                try:
                    pdf_verisi = create_pdf(st.session_state.rapor_sonucu, "Sezer Kara Hukuk Burosu - Reklam Uyum Raporu")
                    st.download_button(
                        label="📄 Hukuki Uyum ve Revizyon Raporunu İndir (PDF)",
                        data=pdf_verisi,
                        file_name=f"SezerKara_Uyum_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        type="secondary"
                    )
                except Exception as e:
                    st.warning(f"PDF uyarısı: {e}")
            else:
                # RAKİP MODU: İhlal Raporu + Şikayet Dilekçesi Sekmeleri
                tab_ihlal, tab_dilekce = st.tabs(["📋 Haksız Rekabet & İhlal Raporu", "⚖️ Reklam Kurulu Şikayet Dilekçesi"])
                
                with tab_ihlal:
                    st.markdown(st.session_state.rapor_sonucu)
                    try:
                        pdf_verisi = create_pdf(st.session_state.rapor_sonucu, "Sezer Kara Hukuk Burosu - Rakip Reklam İhlal Raporu")
                        st.download_button(
                            label="📄 Rakip İhlal Raporunu İndir (PDF)",
                            data=pdf_verisi,
                            file_name=f"SezerKara_Rakip_Ihlal_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                            type="secondary"
                        )
                    except Exception as e:
                        st.warning(f"PDF uyarısı: {e}")

                with tab_dilekce:
                    st.caption("İncelenen rakip iletişim hakkında Reklam Kurulu'na sunulmak üzere resmi 4 maddeli avukat şikayet dilekçesi oluşturur.")
                    
                    if st.button("📜 Resmi Reklam Kurulu Şikayet Dilekçesini Hazırla"):
                        with st.spinner("Şikayet dilekçesi yazılıyor..."):
                            try:
                                dilekce_prompt = f"""
Sen Sezer Kara Hukuk Bürosu'nda görev yapan deneyimli bir Reklam ve Tüketici Hukuku Avukatısın.
Aşağıdaki rakip inceleme verisini kullanarak Reklam Kurulu Başkanlığı'na sunulmak üzere net, somut ve 4 ana maddeden oluşan bir ŞİKAYET DİLEKÇESİ kaleme al:

İNCELEME RAPORU:
{st.session_state.rapor_sonucu}

DİLEKÇE FORMATI:

T.C. TİCARET BAKANLIĞI
REKLAM KURULU BAŞKANLIĞINA
ANKARA

ŞİKAYET EDEN : [Müvekkil Şirket Unvanı]
VEKİLİ : Av. [Vekil Adı Soyadı] - Sezer Kara Hukuk Bürosu
ŞİKAYET EDİLEN : [Şikayet Edilen Firma / Satıcı / Hesap Bilgisi]
ŞİKAYET KONUSU : Şikayet edilen tarafça {mecra} üzerinden yürütülen tanıtımlarda yer alan hukuka aykırı, yanıltıcı ve haksız rekabete yol açan iddiaların incelenerek idari yaptırım (durdurma ve idari para cezası) uygulanması talebidir.

AÇIKLAMALAR:
1. (Somut Vakıa ve İnceleme Konusu İddia: Şikayet edilen tarafın tanıtımlarında hangi somut ifadelerin yer aldığı, nerede yayınlandığı ve bu iddianın neden mevzuata aykırı ve tüketiciyi yanıltıcı olduğuna dair net tespit).
2. (Teknik / Sektörel / Bilimsel Gerçeklik: İddia edilen etkinin, sürenin, içeriğin veya üstünlük vaadinin ürün kategorisinin doğası ve bilimsel/sektörel gerçekler karşısında neden gerçeğe aykırı, imkansız veya kategorideki tüm ürünler için zaten geçerli olan bir standart olduğu).
3. (İlgili Kılavuz ve Özel Mevzuat İhlali: TİTCK / TGK / İndirim / Fiyat Kılavuzları hükümleri uyarınca kategoride zaten bulunmayan/bulunması gereken özelliklerin üstünlük gibi sunulamayacağı ve izin verilmeyen beyanların kullanılamayacağı ilkesi).
4. (6502 sayılı Kanun md. 61 ve Ticari Reklam Yönetmeliği md. 7, 9, 10, 11 İhlali & Tüketici Algısı: Ortalama tüketicinin bilgi eksikliğinin istismar edilmesi, dürüst rakiplerin haksız yere şaibe altında bırakılması ve pazarda doğan haksız rekabet ortamının gerekçelendirilmesi).

SONUÇ VE İSTEM : Yukarıdaki açıklamalar çerçevesinde ve kurulunuzun re’sen dikkate alacağı nedenlerle; dilekçemizde belirtilen ve kurulunuzca belirlenecek diğer mecralarda yayınlanmış ve yayınlanan reklam ve bilgilendirmelerin incelenerek yayınının tedbiren ve nihai olarak DURDURULMASINA, yayından kaldırılmasına ve sorumlu şirket/şahıs hakkında en üst hadden İDARİ PARA CEZASI ile cezalandırılmasına karar verilmesini vekaleten saygılarımızla arz ve talep ederiz.

[Müvekkil Şirket Unvanı]
Vekili Av. [İsim Soyisim]
Sezer Kara Hukuk Bürosu
"""
                                d_model = genai.GenerativeModel(model_name=secilen_model)
                                d_res = d_model.generate_content(dilekce_prompt)
                                st.session_state.dilekce_sonucu = d_res.text
                            except Exception as e:
                                st.error(f"Dilekçe hazırlanırken bir hata oluştu: {e}")

                    if st.session_state.dilekce_sonucu:
                        st.markdown(st.session_state.dilekce_sonucu)
                        try:
                            dilekce_pdf = create_pdf(st.session_state.dilekce_sonucu, "T.C. Ticaret Bakanligi Reklam Kurulu Baskanligi Sikayet Dilekcesi")
                            st.download_button(
                                label="📥 Şikayet Dilekçesini İndir (PDF)",
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
        st.markdown('<div class="section-heading">Hukuki Danışman & Soru-Cevap</div>', unsafe_allow_html=True)
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
                        chat_model = genai.GenerativeModel(
                            model_name=secilen_model,
                            system_instruction=f"""
Sen Sezer Kara Hukuk Bürosu bünyesinde görev yapan bir Reklam Hukuku Danışmanısın.
Kullanıcı seçilen mod ({'Danışan Uyum Modu' if is_danisan else 'Rakip Şikayet Modu'}) kapsamında sorular soruyor.
Rapor: {st.session_state.rapor_sonucu}
Metin: {reklam_metni}
Soruyu doğrudan mevzuat ve içtihat ışığında yanıtla.
"""
                        )
                        sohbet_gecmisi_prompt = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in st.session_state.chat_history])
                        chat_response = chat_model.generate_content(sohbet_gecmisi_prompt)
                        cevap_metni = chat_response.text
                        st.markdown(cevap_metni)
                        st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                    except Exception as e:
                        st.error(f"Hata: {e}")
