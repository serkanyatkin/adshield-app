import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
from datetime import datetime
import os
import glob
import re
import requests

# Sayfa Yapılandırması
st.set_page_config(
    page_title="AdShield AI - Reklam Hukuku Denetim Platformu",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kurumsal SaaS CSS Tasarımı
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Üst Banner Kartı */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 24px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        border: 1px solid #334155;
    }
    .hero-title {
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .hero-subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin: 0;
    }

    /* Form ve Kart Kutuları */
    .stTextArea textarea {
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        font-size: 13.5px;
    }
    
    /* Buton Tasarımı */
    .stButton button[kind="primary"] {
        background: #2563eb;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton button[kind="primary"]:hover {
        background: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# Üst Başlık Banner
st.markdown("""
<div class="hero-container">
    <div class="hero-title">⚖️ AdShield AI: Reklam Kurulu Denetim & Emsal Analiz Motoru</div>
    <p class="hero-subtitle">200+ Resmi Bülten İçtihadı • 6502 Sayılı Kanun md. 61/77 Risk Modellemesi • Otomatik Hukuki Mütalaa</p>
</div>
""", unsafe_allow_html=True)

# API Anahtarı
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    with st.sidebar:
        st.header("🔑 Lisans & Erişim")
        api_key = st.text_input("Gemini API Anahtarı:", type="password")

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

# İki Kolonlu Çalışma Alanı
sol_kolon, sag_kolon = st.columns([1, 1.15], gap="medium")

with sol_kolon:
    with st.container(border=True):
        st.markdown("#### 📝 Reklam ve Parametre Girişi")
        
        # Hızlı Test Doldurma Butonları
        st.caption("⚡ Hızlı Örnek Senaryo Yükle:")
        senaryo_cols = st.columns(3)
        if senaryo_cols[0].button("Kozmetik"):
            st.session_state.taslak_metin = "Dermatologların 1 numaralı tercihi! Tamamen %100 bitkisel aktiflerle leke ve kırışıklıkları 48 saatte tamamen yok eder. Sağlık Bakanlığı onaylı formülüyle botoks etkisini evinize getirir."
        if senaryo_cols[1].button("Takviye Gıda"):
            st.session_state.taslak_metin = "Eklem ağrılarına ve kireçlenmeye kesin son! Bağışıklık sisteminizi güçlendirerek dizdeki iltihabı kurutur, ameliyatsız tedavi sağlar."
        if senaryo_cols[2].button("E-Ticaret"):
            st.session_state.taslak_metin = "Yılın en büyük efsane indirimi! Türkiye'nin en ucuz robot süpürgesi sadece bugün 24.999 TL yerine 4.999 TL! Son 3 ürün, tükeniyor."

        sektor = st.selectbox("Sektör", [
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
        
        reklam_metni = st.text_area(
            "Reklam Metni / Caption / İddialar",
            value=st.session_state.taslak_metin,
            height=120,
            placeholder="Denetlemek istediğiniz reklam metnini buraya yapıştırın..."
        )
        
        yuklenen_gorsel = st.file_uploader("Görsel / Story / Taslak Yükle (Opsiyonel)", type=["jpg", "jpeg", "png"])
        if yuklenen_gorsel:
            image = Image.open(yuklenen_gorsel)
            st.image(image, caption="Yüklenen Görsel", use_container_width=True)

        analiz_butonu = st.button("⚖️ Hukuki Denetimi ve Emsal Taramasını Başlat", type="primary")

with sag_kolon:
    with st.container(border=True):
        st.markdown("#### 📊 Denetim ve Hukuki Mütalaa Merkezi")
        
        if analiz_butonu:
            if not api_key:
                st.error("Lütfen sol panelden geçerli bir Gemini API anahtarı girin.")
            elif not reklam_metni and not yuklenen_gorsel:
                st.warning("Lütfen denetim için metin girin veya görsel yükleyin.")
            else:
                with st.spinner("İçtihat veri tabanı taranıyor, maddi vakıa analizi hazırlanıyor..."):
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
                        st.session_state.chat_history = []
                    except Exception as err:
                        st.error(f"Analiz sırasında bir hata oluştu: {err}")

        if st.session_state.rapor_sonucu:
            # Rapor İçeriği
            st.markdown(st.session_state.rapor_sonucu)
            
            # PDF İndirme Butonu
            try:
                pdf_verisi = create_pdf(st.session_state.rapor_sonucu, st.session_state.sektor_bilgisi, st.session_state.mecra_bilgisi)
                st.download_button(
                    label="📥 Resmi Mütalaa Raporunu İndir (PDF)",
                    data=pdf_verisi,
                    file_name=f"AdShield_Hukuki_Risk_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="secondary"
                )
            except Exception as e:
                st.warning(f"PDF oluşturulurken bir uyarı oluştu: {e}")
        else:
            st.info("Sol taraftan parametreleri belirleyip analizi başlattığınızda gerekçeli rapor bu alanda görüntülenecektir.")

# İnteraktif Soru-Cevap & Danışman Paneli
if st.session_state.rapor_sonucu:
    st.write("")
    with st.container(border=True):
        st.markdown("#### 💬 Hukuki Danışman & Revizyon Asistanı")
        st.caption("Üretilen mütalaaya, cezai yaptırımlara veya yeni alternatif metinlerinize dair sorularınızı sorabilirsiniz.")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        kullanici_sorusu = st.chat_input("Örn: '48 saatte' yerine 'düzenli kullanımda' yazarsam ceza riski kalkar mı?")
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
- Sektör: {st.session_state.sektor_bilgisi}
- Mecra: {st.session_state.mecra_bilgisi}
- Orijinal Metin: {st.session_state.aktif_metin}
- Hukuki Rapor:
{st.session_state.rapor_sonucu}

GÖREVİN:
Kullanıcının sorusunu doğrudan Reklam Kurulu içtihatları ve 6502 sayılı Kanun çerçevesinde net, stratejik ve çözüm odaklı bir dille yanıtlamaktır.
"""
                        )
                        
                        sohbet_gecmisi_prompt = ""
                        for h in st.session_state.chat_history:
                            sohbet_gecmisi_prompt += f"\n{h['role'].upper()}: {h['content']}"

                        chat_response = chat_model.generate_content(sohbet_gecmisi_prompt)
                        cevap_metni = chat_response.text
                        st.markdown(cevap_metni)
                        st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                    except Exception as e:
                        st.error(f"Yanıt üretilirken bir hata oluştu: {e}")
