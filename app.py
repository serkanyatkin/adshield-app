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
    page_title="AdShield - Reklam Kurulu Emsal ve Ceza Risk Denetimi",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AdShield: Reklam Kurulu Emsal Karar & Ceza Analiz Motoru")
st.caption("200+ Resmi Bülten Külliyatı, Hukuki Kıyaslama, Dosya No Atfı ve İdari Para Cezası Simülasyonu")

# API Anahtarı Yönetimi
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    st.sidebar.header("Ayarlar")
    api_key = st.sidebar.text_input("Gemini API Anahtarı:", type="password")

secilen_model = "gemini-3.6-flash"

# Karar Metinlerini Belleğe Alma ve İndeksleme
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
    
    # Karar bloklarını ayır
    karar_bloklari = re.split(r'=== EMSAL KARAR / BÜLTEN:|\n(?=Dosya No\s*:|\d{4}/\d+)', corpus)
    temiz_bloklar = [k.strip() for k in karar_bloklari if len(k.strip()) > 80]
    return temiz_bloklar

karar_arsivi = load_and_index_kararlar()

# Hukuki Vakıa ve Anahtar Kelime Bazlı Karar Filtresi
def get_relevant_emsaller(metin, sektor, top_k=8):
    if not karar_arsivi:
        return "Karar arşivi yüklenemedi veya dosya bulunamadı."
    
    sektor_keywords = {
        "Kozmetik & Kişisel Bakım / Anne-Bebek": [
            "kozmetik", "doğal", "bitkisel", "organik", "cilt", "leke", "kırışıklık", 
            "bebek", "titck", "onaylı", "tedavi", "mucize", "yok eder", "klinik"
        ],
        "Takviye Edici Gıda & Sağlık": [
            "takviye", "gıda", "sağlık beyanı", "tedavi", "hastalık", "kilo", 
            "zayıflama", "bağışıklık", "eklem", "ağrı", "şifa", "onay"
        ],
        "E-Ticaret & İndirim Kampanyaları": [
            "indirim", "fiyat", "en ucuz", "tavsiye edilen", "stok", "bedava", 
            "en çok satan", "fiyatı düştü", "efsane", "tükeniyor"
        ],
        "Sosyal Medya & Influencer Reklamları": [
            "influencer", "işbirliği", "etiket", "örtülü reklam", "sosyal medya", 
            "tanıtım", "link", "ortaklık", "sponsor", "reklam"
        ]
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
        if skor > 0:
            skorlu.append((skor, karar[:3500]))

    skorlu.sort(key=lambda x: x[0], reverse=True)
    secilenler = [k[1] for k in skorlu[:top_k]]
    
    return "\n\n--- [EMSAL KARAR METNİ] ---\n\n".join(secilenler if secilenler else karar_arsivi[:4])

# PDF Raporlama ve Font Desteği
FONT_PATH = "Roboto-Regular.ttf"
FONT_URL = "https://cdn.jsdelivr.net/gh/googlefonts/roboto@main/src/hinted/Roboto-Regular.ttf"

def ensure_font():
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL, timeout=10)
            if r.status_code == 200:
                with open(FONT_PATH, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass
    return os.path.exists(FONT_PATH)

def clean_markdown_text(text):
    if not text:
        return ""
    text = text.replace("### ", "").replace("## ", "").replace("# ", "")
    text = text.replace("**", "").replace("*", "")
    return text

def create_pdf(report_text, sektor_adi, mecra_adi):
    font_available = ensure_font()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    main_font = "Roboto" if font_available else "Helvetica"
    pdf.set_font(main_font, "" if font_available else "B", 14)
    pdf.cell(0, 9, "AdShield - Reklam Kurulu Emsal Karar ve Risk Raporu", ln=True, align="C")
    
    pdf.set_font(main_font, "", 8.5)
    pdf.cell(0, 5, f"Sektör: {sektor_adi} | Mecra: {mecra_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
    pdf.line(10, 26, 200, 26)
    pdf.ln(6)
    
    temiz_metin = clean_markdown_text(report_text)
    if font_available:
        pdf.set_font(main_font, "", 9)
        pdf.multi_cell(0, 5, temiz_metin)
    else:
        tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, temiz_metin.translate(tr_map).encode('latin-1', 'replace').decode('latin-1'))
    return bytes(pdf.output())

# Oturum Durumu (Session State)
if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
if "sektor_bilgisi" not in st.session_state:
    st.session_state.sektor_bilgisi = None
if "mecra_bilgisi" not in st.session_state:
    st.session_state.mecra_bilgisi = None

# Kullanıcı Arayüzü
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Reklam ve Mecra Parametreleri")
    sektor = st.selectbox("Sektör Seçin", [
        "Kozmetik & Kişisel Bakım / Anne-Bebek",
        "Takviye Edici Gıda & Sağlık",
        "E-Ticaret & İndirim Kampanyaları",
        "Sosyal Medya & Influencer Reklamları",
        "Diğer"
    ])
    mecra = st.selectbox("Yayın Mecrası", [
        "İnternet / Sosyal Medya (Instagram, TikTok, Web Sitesi)",
        "Ulusal Televizyon Kanalı",
        "Yerel Televizyon / Radyo",
        "Açık Hava (Billboard, Broşür vb.)"
    ])
    reklam_metni = st.text_area("Reklam Metni / Caption / İddialar", height=130)
    yuklenen_gorsel = st.file_uploader("Reklam Görseli / Taslak / Story Yükle", type=["jpg", "jpeg", "png"])
    
    if yuklenen_gorsel:
        image = Image.open(yuklenen_gorsel)
        st.image(image, caption="Analize Alınan Taslak", use_container_width=True)

    analiz_butonu = st.button("Hukuki Muhakeme ve Emsal Analizini Başlat", type="primary")

with col2:
    st.subheader("2. Hukuki Değerlendirme & Emsal Künyesi")
    if analiz_butonu:
        if not api_key:
            st.error("Lütfen bir Gemini API anahtarı sağlayın.")
        elif not reklam_metni and not yuklenen_gorsel:
            st.warning("Lütfen analiz için en az bir metin veya görsel yükleyin.")
        else:
            with st.spinner("72 MB'lık karar arşivi taranıyor, maddi vakıa kıyası yapılıyor..."):
                try:
                    genai.configure(api_key=api_key)
                    ilgili_emsaller = get_relevant_emsaller(reklam_metni, sektor)
                    
                    prompt = f"""
Sen; Ticaret Bakanlığı Reklam Kurulu kararları, 6502 sayılı Tüketicinin Korunması Hakkında Kanun (özellikle md. 61 ve md. 77), Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği ile TİTCK Kılavuzları konusunda uzmanlaşmış kıdemli bir Reklam Hukuku Denetçisi ve Hukuki Danışmansın.

Aşağıda 72 MB'lık resmi karar arşivinden incelenen iddialarla en yüksek vakıa benzerliği gösteren somut Reklam Kurulu kararları verilmiştir:
=== RESMİ REKLAM KURULU EMSAL METİNLERİ ===
{ilgili_emsaller}
==========================================

İNCELENECEK REKLAM VAKIASI:
Sektör: {sektor}
Yayın Mecrası: {mecra}
İçerik: {reklam_metni}

GÖREVİN (HUKUKÇU MUHAKEMESİ):
1. Reklamdaki iddiaların hukuki nitelendirmesini yap (sağlık beyanı, yanıltıcı etki, ispat külfeti, süperlatif iddia vb.).
2. Arşivdeki somut kararlarla doğrudan maddi vakıa kıyası kur; Kurul'un yerleşik içtihat gerekçesini ve dosya numarasını açıkça göster.
3. Kurul kararlarından çıkardığın hukukçu mantığıyla, markanın pazarlama gücünü koruyan ama cezai riski sıfırlayan stratejik revizyon öner.

RAPOR FORMATI (Eksiksiz bu başlık düzeninde oluştur):

### [RİSK DERECESİ: KIRMIZI / SARI / YEŞİL] - Risk Skoru: [0-100]

### 1. REKLAM KURULU EMSAL İÇTİHATLARI VE ATIFLAR
(Arşivdeki emsal metinlerden doğrudan tespit edilen somut kararları kıyaslayarak EN AZ 2 ADET karar künyesi aktar):
* **Emsal Karar 1:**
  - **Dosya No & Karar Tarihi:** (Örn: Dosya No: 2023/..., Karar Tarihi: ...)
  - **Maddi Vakıa & İhlal Konusu:** (Kurul önüne gelen benzer reklam iddiası)
  - **Kurulun Hukuki Gerekçesi:** (Ortalama tüketici algısı, ispat yükü veya mevzuat maddesine dayalı temel gerekçe)
  - **Uygulanan Yaptırım:** (Durdurma / ... TL İdari Para Cezası)
* **Emsal Karar 2:**
  - **Dosya No & Karar Tarihi:**
  - **Maddi Vakıa & İhlal Konusu:**
  - **Kurulun Hukuki Gerekçesi:**
  - **Uygulanan Yaptırım:**

### 2. İDARİ PARA CEZASI SİMÜLATÖRÜ (6502 SAYILI KANUN MD. 77)
* **Mecra Bazlı Risk:** {mecra}
* **Öngörülen İdari Para Cezası Skalası:** (İlgili mecraya göre kanuni alt ve üst ceza aralığı)
* **Diğer Yaptırım Riski:** (Durdurma, Düzeltme, Siteden İçerik Çıkarma/Erişim Engeli)

### 3. HUKUKİ VAKIA DEĞERLENDİRMESİ
* (Tespit edilen hukuki risklerin mevzuat maddeleriyle fıkra fıkra analizi)

### 4. İÇTİHADA UYGUN PAZARLAMA STRATEJİSİ & GÜVENLİ REVİZYON
* **Alternatif Reklam Metni:** (Kurul'un onayladığı/ceza vermediği terminolojiye uygun, ticari cazibesini koruyan metin)
* **İçtihat Odaklı Gerekçe & İspat Şartı:** (Kurul denetiminden geçebilmesi için gereken klinik test, tüketici araştırması veya görsel dipnot standardı)

### 5. YASAL ŞERH
"Bu rapor teknik bir ön risk analizidir; 1136 sayılı Avukatlık Kanunu kapsamında hukuki mütalaa teşkil etmez."
"""
                    model = genai.GenerativeModel(model_name=secilen_model, system_instruction=prompt)
                    icerik_listesi = [f"Metin: {reklam_metni}\nSektör: {sektor}\nMecra: {mecra}"]
                    if yuklenen_gorsel:
                        icerik_listesi.append(image)
                    
                    response = model.generate_content(icerik_listesi)
                    st.session_state.rapor_sonucu = response.text
                    st.session_state.sektor_bilgisi = sektor
                    st.session_state.mecra_bilgisi = mecra
                except Exception as err:
                    st.error(f"Analiz sırasında bir hata oluştu: {err}")

    if st.session_state.rapor_sonucu:
        st.markdown(st.session_state.rapor_sonucu)
        pdf_verisi = create_pdf(st.session_state.rapor_sonucu, st.session_state.sektor_bilgisi, st.session_state.mecra_bilgisi)
        st.download_button(
            label="📄 Emsal Kararlı & Ceza Tahminli Raporu İndir (PDF)",
            data=pdf_verisi,
            file_name=f"AdShield_Emsal_Ceza_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            type="secondary"
        )
