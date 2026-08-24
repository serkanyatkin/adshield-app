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
    page_title="AdShield - Reklam Kurulu Emsal & Hukuki Risk Analizi",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AdShield: Reklam Hukuku ve Emsal Risk Analiz Sistemi")
st.caption("Resmi Reklam Kurulu İçtihatları, Birebir Emsal Kıyaslaması ve İnteraktif Uyum Danışmanı")

# API Anahtarı
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    st.sidebar.header("Ayarlar")
    api_key = st.sidebar.text_input("Gemini API Anahtarı:", type="password")

secilen_model = "gemini-3.6-flash"

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

# Hukuki Süzgeç ve Emsal Karar Eşleştirici
def get_relevant_emsaller(metin, sektor, top_k=8):
    if not karar_arsivi:
        return "Karar arşivi yüklenemedi."
    
    sektor_keywords = {
        "Kozmetik & Kişisel Bakım / Anne-Bebek": [
            "kozmetik", "doğal", "bitkisel", "organik", "cilt", "leke", "kırışıklık", 
            "bebek", "titck", "onaylı", "tedavi", "mucize", "yok eder", "klinik", "günde"
        ],
        "Takviye Edici Gıda & Sağlık": [
            "takviye", "gıda", "sağlık beyanı", "tedavi", "hastalık", "kilo", 
            "zayıflama", "bağışıklık", "eklem", "ağrı", "şifa", "onay", "kesin son", "iltihap"
        ],
        "E-Ticaret & İndirim Kampanyaları": [
            "indirim", "fiyat", "en ucuz", "tavsiye edilen", "stok", "bedava", 
            "en çok satan", "fiyatı düştü", "efsane", "tükeniyor", "orijinal fiyat"
        ],
        "Sosyal Medya & Influencer Reklamları": [
            "influencer", "işbirliği", "etiket", "örtülü reklam", "sosyal medya", 
            "tanıtım", "link", "ortaklık", "sponsor", "reklam", "deneyin"
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

# Türkçe Karakter Destekli PDF Motoru
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
        pdf.cell(0, 9, "AdShield - Reklam Kurulu Emsal Karar ve Risk Raporu", ln=True, align="C")
        pdf.set_font("Roboto", "", 8.5)
        pdf.cell(0, 5, f"Sektör: {sektor_adi} | Mecra: {mecra_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        pdf.line(10, 26, 200, 26)
        pdf.ln(6)
        pdf.set_font("Roboto", "", 8.5)
        pdf.multi_cell(0, 4.8, temiz_metin)
    else:
        tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "AdShield - Reklam Kurulu Emsal Karar ve Risk Raporu", ln=True, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        sub_title = f"Sektor: {sektor_adi} | Mecra: {mecra_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}".translate(tr_map)
        pdf.cell(0, 5, sub_title, ln=True, align="C")
        pdf.line(10, 26, 200, 26)
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 8.5)
        ascii_metin = temiz_metin.translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4.8, ascii_metin)

    return bytes(pdf.output())

# Oturum Durumu Yönetimi
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

# Arayüz
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. İnceleme Parametreleri")
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

    analiz_butonu = st.button("Hukuki İnceleme ve Emsal Taramasını Başlat", type="primary")

with col2:
    st.subheader("2. Hukuki Uyum ve İçtihat Raporu")
    if analiz_butonu:
        if not api_key:
            st.error("Lütfen bir Gemini API anahtarı sağlayın.")
        elif not reklam_metni and not yuklenen_gorsel:
            st.warning("Lütfen analiz için en az bir metin veya görsel yükleyin.")
        else:
            with st.spinner("Reklam Kurulu içtihatları taranıyor ve hukuki risk analizi hazırlanıyor..."):
                try:
                    genai.configure(api_key=api_key)
                    ilgili_emsaller = get_relevant_emsaller(reklam_metni, sektor)
                    
                    prompt = f"""
Sen; Ticaret Bakanlığı Reklam Kurulu kararları, 6502 sayılı Tüketicinin Korunması Hakkında Kanun (özellikle md. 61 ve md. 77), Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği ile TİTCK ve TGK Kılavuzları konusunda uzmanlaşmış kıdemli bir Reklam Hukuku Denetçisi ve Danışmansın.

Aşağıda karar külliyatından incelenen iddialarla en yüksek vakıa benzerliği gösteren somut Reklam Kurulu kararları verilmiştir:
=== RESMİ REKLAM KURULU EMSAL METİNLERİ ===
{ilgili_emsaller}
==========================================

İNCELENECEK REKLAM VAKIASI:
Sektör: {sektor}
Yayın Mecrası: {mecra}
İçerik: {reklam_metni}

GÖREVİN:
Yapay zeka şablonlarından uzak, akıcı, doyurucu ve gerekçeli bir 'Hukuki İnceleme Memorandumu' kaleme almaktır.

RAPOR FORMATI:

### [RİSK DERECESİ: KIRMIZI / SARI / YEŞİL] - Risk Skoru: [0-100]

### I. HUKUKİ RİSK TEŞHİSİ VE VAKIA DEĞERLENDİRMESİ
(İncelenen reklamdaki tüm iddiaları akıcı ve gerekçeli hukuki paragraflarla ele al. Her iddiayı; ihlal edilen kanun/yönetmelik maddeleri, ortalama tüketici nezdinde uyandırdığı algı ve mevzuatın aradığı ispat külfeti açısından derinlemesine açıkla):

### II. REKLAM KURULU İÇTİHATLARI VE BİREBİR EMSAL ALINTILAR
(Arşivdeki emsal metinlerden tespit edilen somut kararları kıyaslayarak EN AZ 2 ADET emsal kararı şu detayda sun):
* **Emsal Karar 1:**
  - **Dosya No & Karar Tarihi:** (Örn: Dosya No: 2023/..., Karar Tarihi: ..., Toplantı No: ...)
  - **Firma & Mecra:** (Varsa karardaki firma ve yayın mecrası)
  - **Kararda Ceza Alan Orijinal İfadeler:** (Kurul kararında ceza alan şirketin kullandığı tırnak içi tam ifadeler)
  - **İncelenen Reklamla Somut Kıyas:** (Bizim reklamımızdaki hangi kelime/vaat bu karardaki cezalı ifadeyle maddi vakıa olarak örtüşüyor?)
  - **Kurulun Hüküm Gerekçesi:** (Kurulun ihlale esas aldığı temel hukuki prensip)
  - **Uygulanan Yaptırım:** (Durdurma / ... TL İdari Para Cezası)
* **Emsal Karar 2:**
  - **Dosya No & Karar Tarihi:**
  - **Firma & Mecra:**
  - **Kararda Ceza Alan Orijinal İfadeler:**
  - **İncelenen Reklamla Somut Kıyas:**
  - **Kurulun Hüküm Gerekçesi:**
  - **Uygulanan Yaptırım:**

### III. YAPTIRIM VE İDARİ PARA CEZASI PROJEKSİYONU
* **Seçilen Mecra:** {mecra}
* **6502 Sayılı Kanun Md. 77 Kapsamında Ceza Skalası:** (İlgili mecra için geçerli güncel alt ve üst idari para cezası tutarları)
* **İdari Tedbir ve Erişim Engeli Riski:** (Durdurma, düzeltme veya Kanun md. 77/A uyarınca erişim engeli/içerik çıkarma riski)

### IV. TİCARİ ETKİYİ KORUYAN GÜVENLİ REVİZYON STRATEJİSİ
* **Revize Reklam Metni:** (Cezai riski sıfırlayan, iddianın pazarlama etkisini koruyan alternatif metin)
* **İçtihat Odaklı Gerekçe & İspat Şartı:** (İfadenin Kurul denetiminden geçebilmesi için gereken klinik test, tüketici araştırması veya görsel altı dipnot standardı)

### V. YASAL ŞERH
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
                    st.session_state.aktif_metin = reklam_metni
                    st.session_state.chat_history = []  # Yeni analizde sohbeti sıfırla
                except Exception as err:
                    st.error(f"Analiz sırasında bir hata oluştu: {err}")

    if st.session_state.rapor_sonucu:
        st.markdown(st.session_state.rapor_sonucu)
        try:
            pdf_verisi = create_pdf(st.session_state.rapor_sonucu, st.session_state.sektor_bilgisi, st.session_state.mecra_bilgisi)
            st.download_button(
                label="📄 Hukuki Risk ve Emsal Raporunu İndir (PDF)",
                data=pdf_verisi,
                file_name=f"AdShield_Hukuki_Risk_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                type="secondary"
            )
        except Exception as e:
            st.warning(f"PDF oluşturulurken bir uyarı oluştu: {e}")

# Raporun Altında İnteraktif Soru-Cevap ve Revizyon Danışmanı
if st.session_state.rapor_sonucu:
    st.write("---")
    st.subheader("💬 Hukuki Danışman & Revizyon Asistanı")
    st.caption("Üretilen rapora, emsal kararlara veya yeni alternatif metin önerilerinize dair aklınıza takılanları sorabilirsiniz.")

    # Geçmiş mesajları listele
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Yeni soru girişi
    kullanici_sorusu = st.chat_input("Örn: '3 günde' yerine 'düzenli kullanımda' dersem ceza riski biter mi?")
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
Sen bir Reklam Hukuku Danışmanısın. Kullanıcı daha önce sistem tarafından denetlenen bir reklam ve üretilen rapor hakkında sana soru soruyor veya alternatif reklam metinlerini test etmek istiyor.

BAĞLAM BİLGİLERİ:
- İncelenen Sektör: {st.session_state.sektor_bilgisi}
- Yayın Mecrası: {st.session_state.mecra_bilgisi}
- Orijinal Reklam Metni: {st.session_state.aktif_metin}
- Üretilen Hukuki Rapor:
{st.session_state.rapor_sonucu}

GÖREVİN:
Kullanıcının sorusunu doğrudan Reklam Kurulu içtihatları, 6502 sayılı Kanun ve ispat kuralları ışığında, net ve çözüm odaklı bir hukukçu diliyle yanıtlamak; yeni metin öneriyorsa risk analizini anında yapmaktır.
"""
                    )
                    
                    # Sohbet geçmişini modele aktar
                    sohbet_gecmisi_prompt = ""
                    for h in st.session_state.chat_history:
                        sohbet_gecmisi_prompt += f"\n{h['role'].upper()}: {h['content']}"

                    chat_response = chat_model.generate_content(sohbet_gecmisi_prompt)
                    cevap_metni = chat_response.text
                    st.markdown(cevap_metni)
                    st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                except Exception as e:
                    st.error(f"Yanıt üretilirken bir hata oluştu: {e}")
