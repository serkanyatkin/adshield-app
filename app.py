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
    page_title="Sezer Kara Hukuk Bürosu | Reklam Hukuku & Uyum Denetimi",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kurumsal Hukuk Bürosu CSS Tasarımı
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .firm-header {
        background-color: #5D728B;
        padding: 22px 32px;
        border-radius: 4px;
        color: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
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
        font-size: 15px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #2C3848;
        font-weight: 700;
        margin-bottom: 16px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 8px;
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

# Web Sitesinden / Linkten İçerik Çekme Fonksiyonu
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
            
            clean_text = ' '.join(text.split())
            return clean_text[:4500]
    except Exception as e:
        return f"[Web sayfası içeriği çekilemedi: {e}]"
    return ""

# Karar Metinlerini Belleğe Yükleme
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
        "Kozmetik & Kişisel Bakım / Anne-Bebek": ["kozmetik", "doğal", "bitkisel", "organik", "cilt", "leke", "kırışıklık", "titck", "onaylı", "tedavi", "mucize", "yok eder", "klinik", "günde"],
        "Takviye Edici Gıda & Sağlık": ["takviye", "gıda", "sağlık beyanı", "tedavi", "hastalık", "kilo", "zayıflama", "bağışıklık", "eklem", "ağrı", "şifa", "onay", "kesin son", "iltihap"],
        "E-Ticaret & İndirim Kampanyaları": ["indirim", "fiyat", "en ucuz", "tavsiye edilen", "stok", "bedava", "en çok satan", "fiyatı düştü", "efsane", "tükeniyor", "orijinal fiyat"],
        "Sosyal Medya & Influencer Reklamları": ["influencer", "işbirliği", "etiket", "örtülü reklam", "sosyal medya", "tanıtım", "link", "ortaklık", "sponsor", "reklam", "deneyin"]
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

def create_pdf(report_text, sektor_adi, mecra_adi):
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
        pdf.set_font("Roboto", "", 13)
        pdf.cell(0, 9, "Sezer Kara Hukuk Burosu - Reklam Hukuku Denetim Raporu", ln=True, align="C")
        pdf.set_font("Roboto", "", 8.5)
        pdf.cell(0, 5, f"Sektör: {sektor_adi} | Mecra: {mecra_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        pdf.line(10, 26, 200, 26)
        pdf.ln(6)
        pdf.set_font("Roboto", "", 8.5)
        pdf.multi_cell(0, 4.8, temiz_metin)
    else:
        tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Sezer Kara Hukuk Burosu - Reklam Hukuku Denetim Raporu", ln=True, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        sub_title = f"Sektor: {sektor_adi} | Mecra: {mecra_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}".translate(tr_map)
        pdf.cell(0, 5, sub_title, ln=True, align="C")
        pdf.line(10, 26, 200, 26)
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 8.5)
        ascii_metin = temiz_metin.translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4.8, ascii_metin)

    return bytes(pdf.output())

# Session State Tanımlamaları
if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
if "sektor_bilgisi" not in st.session_state:
    st.session_state.sektor_bilgisi = None
if "mecra_bilgisi" not in st.session_state:
    st.session_state.mecra_bilgisi = None
if "aktif_metin" not in st.session_state:
    st.session_state.aktif_metin = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "taslak_metin" not in st.session_state:
    st.session_state.taslak_metin = ""

sol_kolon, sag_kolon = st.columns([1, 1.2], gap="large")

with sol_kolon:
    with st.container(border=True):
        st.markdown('<div class="section-heading">İncelenecek Reklam & Veri Girişi</div>', unsafe_allow_html=True)
        
        inceleme_turu = st.radio(
            "İnceleme Amacı",
            ["Kendi Reklam Taslağımızın Uyumluluk Denetimi (Danışan Modu)", 
             "Rakip Ürün / Reklam İncelemesi (Şikayet & İhbar Ön Değerlendirmesi)"],
            horizontal=False
        )

        st.caption("Örnek Senaryo Yükle:")
        sc1, sc2, sc3 = st.columns(3)
        if sc1.button("Kozmetik"):
            st.session_state.taslak_metin = "Dermatologların 1 numaralı tercihi! Tamamen %100 bitkisel serumumuz leke ve kırışıklıkları 48 saatte tamamen yok eder. Sağlık Bakanlığı onaylı formülüyle botoks etkisini evinize getirir."
        if sc2.button("Takviye Gıda"):
            st.session_state.taslak_metin = "Eklem kireçlenmesine kesin son! Bağışıklığı güçlendirerek dizdeki iltihabı kurutur, ameliyatsız tedavi sağlar."
        if sc3.button("E-Ticaret"):
            st.session_state.taslak_metin = "Yılın efsane indirimi! Türkiye'nin en ucuz robot süpürgesi sadece bugün 24.999 TL yerine 4.999 TL! Son 3 ürün, tükeniyor."

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
            "İncelenecek Web Sayfası / Ürün / Reklam Linki (Opsiyonel)",
            placeholder="https://www.ornek-site.com/urun-sayfasi veya reklam linki..."
        )

        reklam_metni = st.text_area(
            "Reklam Metni / Ticari İddialar / Açıklamalar",
            value=st.session_state.taslak_metin,
            height=120,
            placeholder="İncelenmesi talep edilen reklam metnini veya iddiaları buraya giriniz..."
        )
        
        # Çoklu Görsel Yükleme
        yuklenen_gorseller = st.file_uploader(
            "Reklam Görselleri / Taslaklar / Carousel / Story (Çoklu Yükleme)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        if yuklenen_gorseller:
            st.caption(f"Yüklenen Görseller ({len(yuklenen_gorseller)} Adet):")
            gorsel_cols = st.columns(min(len(yuklenen_gorseller), 4))
            for idx, g_dosya in enumerate(yuklenen_gorseller):
                g_img = Image.open(g_dosya)
                gorsel_cols[idx % 4].image(g_img, caption=f"Görsel {idx+1}", use_container_width=True)

        analiz_butonu = st.button("Hukuki Denetimi ve Emsal Taramasını Başlat", type="primary")

with sag_kolon:
    with st.container(border=True):
        st.markdown('<div class="section-heading">Hukuki Denetim ve Risk Analiz Raporu</div>', unsafe_allow_html=True)
        
        if analiz_butonu:
            if not api_key:
                st.error("Lütfen sistem yöneticisinden temin edilen geçerli API anahtarını giriniz.")
            elif not reklam_metni and not yuklenen_gorseller and not reklam_url:
                st.warning("Lütfen denetim için metin giriniz, link paylaşınız veya görsel yükleyiniz.")
            else:
                url_metni = ""
                if reklam_url:
                    with st.spinner("Girilen web adresi taranıyor ve ürün içerikleri çekiliyor..."):
                        url_metni = fetch_url_content(reklam_url)
                
                with st.spinner("Reklam Kurulu içtihatları ve 6502 sayılı Kanun çerçevesinde taranıyor..."):
                    try:
                        genai.configure(api_key=api_key)
                        birlestirilmis_metin = f"{reklam_metni}\n\n[Web Linki İçeriği]: {url_metni}" if url_metni else reklam_metni
                        ilgili_emsaller = get_relevant_emsaller(birlestirilmis_metin, sektor)
                        
                        prompt = f"""
Sen; Ticaret Bakanlığı Reklam Kurulu kararları, 6502 sayılı Tüketicinin Korunması Hakkında Kanun (özellikle md. 61 ve md. 77), Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği ile TİTCK ve TGK Kılavuzları konusunda uzmanlaşmış kıdemli bir Reklam Hukuku Denetçisisin.

Aşağıda karar külliyatından incelenen iddialarla en yüksek vakıa benzerliği gösteren somut Reklam Kurulu kararları verilmiştir:
=== RESMİ REKLAM KURULU EMSAL METİNLERİ ===
{ilgili_emsaller}
==========================================

İNCELEME BİLGİLERİ:
- İnceleme Amacı / Modu: {inceleme_turu}
- Sektör: {sektor}
- Yayın Mecrası: {mecra}
- Reklam Metni / İddialar: {reklam_metni}
- İncelenen Web Sayfası İçeriği (Varsa): {url_metni[:2000] if url_metni else "Belirtilmedi"}

GÖREVİN:
Yapay zeka şablonlarından uzak, doğrudan mevzuat ve somut içtihatlara dayanan, net ve gerekçeli bir Hukuki Denetim Raporu hazırlamaktır.
Eğer mod 'Rakip Ürün İncelemesi' ise; 4. bölümde Reklam Kurulu nezdinde şikayet/ihbar dilekçesinde kullanılabilecek somut hukuki gerekçeleri vurgula.
Eğer mod 'Danışan Modu' ise; 4. bölümde cezai riski sıfırlayan ticari revizyon önerilerini ve ispat belgelerini sun.

RAPOR FORMATI:

### [RİSK DERECESİ: YÜKSEK (KIRMIZI) / ORTA (SARI) / DÜŞÜK (YEŞİL)] - Risk Skoru: [0-100]

### I. HUKUKİ RİSK DEĞERLENDİRMESİ VE MEVZUAT AYKIRILIKLARI
(İncelenen reklamdaki/web sitesindeki iddiaları tek tek ele al. İhlal edilen mevzuat maddeleri, tüketici nezdindeki intiba ve ispat külfeti açısından açıkla):
* **[İncelenen İfade/İddia 1]:** (Hukuki değerlendirme, ihlal edilen mevzuat ve Kurul yaklaşımı)
* **[İncelenen İfade/İddia 2]:**
* **[İncelenen İfade/İddia 3]:**

### II. REKLAM KURULU EMSAL KARARLARI VE CEZALI İFADE EŞLEŞMELERİ
(Arşivdeki emsal metinlerden tespit edilen somut kararlardan EN AZ 2 ADET karar künyesini şu formatta ver):
* **Emsal Karar 1:**
  - **Dosya No & Karar Tarihi:** (Örn: Dosya No: 2023/..., Karar Tarihi: ..., Toplantı No: ...)
  - **Firma / Mecra:** 
  - **Kararda Ceza Alan Orijinal İfade:** (Kararda ceza alan şirketin kullandığı tırnak içi tam reklam cümlesi)
  - **İncelenen İletişimle Somut Kıyas:** (İncelediğimiz materyaldeki hangi vaat bu kararla örtüşüyor?)
  - **Uygulanan Yaptırım:** (Durdurma ve ... TL İdari Para Cezası)
* **Emsal Karar 2:**
  - **Dosya No & Karar Tarihi:**
  - **Firma / Mecra:** 
  - **Kararda Ceza Alan Orijinal İfade:**
  - **İncelenen İletişimle Somut Kıyas:**
  - **Uygulanan Yaptırım:**

### III. ÖNGÖRÜLEN İDARİ PARA CEZASI VE YAPTIRIM SKALASI
* **Yayın Mecrası:** {mecra}
* **6502 Sayılı Kanun Md. 77 Uyarınca Ceza Aralığı:** (Mecraya göre güncel idari para cezası limitleri)
* **Diğer Yaptırımlar:** (Durdurma, düzeltme veya md. 77/A uyarınca erişim engeli/içerik çıkarma riski)

### IV. STRATEJİK HUKUKİ SONUÇ VE EYLEM PLANI
(Seçilen inceleme moduna göre güvenli revizyon veya Reklam Kurulu şikayet dayanaklarını açıkla):
* **Stratejik Değerlendirme & Metin:** (Danışan için risksiz alternatif metin / Rakip için şikayet dayanağı)
* **Gereken İspat / Delil Standartları:** (Klinik test, noter tespiti, arşiv kaydı vb.)

### V. YASAL ŞERH
"Bu rapor teknik bir ön risk analizi niteliğinde olup, somut uyuşmazlıklarda nihai hukuki danışmanlık yerine geçmez."
"""
                        model = genai.GenerativeModel(model_name=secilen_model, system_instruction=prompt)
                        icerik_listesi = [
                            f"İnceleme Türü: {inceleme_turu}\nSektör: {sektor}\nMecra: {mecra}\nMetin/İddialar: {reklam_metni}\nWeb İçeriği: {url_metni}"
                        ]
                        
                        if yuklenen_gorseller:
                            for g in yuklenen_gorseller:
                                icerik_listesi.append(Image.open(g))
                        
                        response = model.generate_content(icerik_listesi)
                        st.session_state.rapor_sonucu = response.text
                        st.session_state.sektor_bilgisi = sektor
                        st.session_state.mecra_bilgisi = mecra
                        st.session_state.aktif_metin = birlestirilmis_metin
                        st.session_state.chat_history = []
                    except Exception as err:
                        st.error(f"Analiz sırasında bir hata oluştu: {err}")

        if st.session_state.rapor_sonucu:
            st.markdown(st.session_state.rapor_sonucu)
            
            try:
                pdf_verisi = create_pdf(st.session_state.rapor_sonucu, st.session_state.sektor_bilgisi, st.session_state.mecra_bilgisi)
                st.download_button(
                    label="Hukuki Risk Raporunu İndir (PDF)",
                    data=pdf_verisi,
                    file_name=f"SezerKara_Hukuki_Risk_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="secondary"
                )
            except Exception as e:
                st.warning(f"PDF oluşturma uyarısı: {e}")
        else:
            st.info("Sol panelden reklam parametrelerini, görselleri veya linki ekleyip analizi başlattığınızda rapor bu alanda listelenecektir.")

# İnteraktif Danışman Paneli
if st.session_state.rapor_sonucu:
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-heading">Hukuki Danışman & Revizyon Asistanı</div>', unsafe_allow_html=True)
        st.caption("Üretilen rapora, emsal dosyalara, şikayet süreçlerine veya revize metin alternatiflerinize ilişkin sorularınızı iletebilirsiniz.")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        kullanici_sorusu = st.chat_input("Sorunuzu buraya yazınız (Örn: Bu rakip ürün için Reklam Kurulu'na başvursak durdurma kararı ne kadar sürede çıkar?)...")
        if kullanici_sorusu:
            st.session_state.chat_history.append({"role": "user", "content": kullanici_sorusu})
            with st.chat_message("user"):
                st.markdown(kullanici_sorusu)

            with st.chat_message("assistant"):
                with st.spinner("Hukuki değerlendirme yapılıyor..."):
                    try:
                        chat_model = genai.GenerativeModel(
                            model_name=secilen_model,
                            system_instruction=f"""
Sen Sezer Kara Hukuk Bürosu bünyesinde görev yapan bir Reklam Hukuku Danışmanısın. Kullanıcı daha önce denetlenen reklam, web sayfası veya rakip analizi hakkında sorular soruyor.

BAĞLAM:
- Sektör: {st.session_state.sektor_bilgisi}
- Mecra: {st.session_state.mecra_bilgisi}
- İncelenen İçerik: {st.session_state.aktif_metin}
- Hukuki Rapor:
{st.session_state.rapor_sonucu}

GÖREVİN:
Kullanıcının sorusunu doğrudan Reklam Kurulu içtihatları, 6502 sayılı Kanun ve ispat kuralları ışığında net, kurumsal ve stratejik bir dille yanıtlamaktır.
"""
                        )
                        sohbet_gecmisi_prompt = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in st.session_state.chat_history])
                        chat_response = chat_model.generate_content(sohbet_gecmisi_prompt)
                        cevap_metni = chat_response.text
                        st.markdown(cevap_metni)
                        st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                    except Exception as e:
                        st.error(f"Hata: {e}")
