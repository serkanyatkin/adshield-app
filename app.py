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
    page_title="AdShield - Reklam Uyum & Risk Radarı",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern SaaS Tasarım CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Üst Bar */
    .app-header {
        background: #0f172a;
        padding: 20px 28px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #1e293b;
    }
    .brand-title {
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-tag {
        background: #2563eb;
        color: white;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    
    /* Metrik Kartları */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Butonlar */
    .stButton button[kind="primary"] {
        background: #2563eb;
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 12px 24px;
        border: none;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton button[kind="primary"]:hover {
        background: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37,99,235,0.3);
    }
    
    /* Sekme Başlıkları */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Üst Başlık
st.markdown("""
<div class="app-header">
    <div>
        <div class="brand-title">⚡ AdShield <span class="brand-tag">Reklam Uyum Motoru</span></div>
        <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">Reklam Kurulu İçtihat Taraması • Canlı Risk Puanlama • Güvenli Metin Üretimi</div>
    </div>
</div>
""", unsafe_allow_html=True)

# API Anahtarı
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        api_key = st.text_input("Gemini API Key:", type="password")

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
        return "Karar arşivi bulunamadı."
    
    sektor_keywords = {
        "Kozmetik & Kişisel Bakım": ["kozmetik", "doğal", "bitkisel", "organik", "cilt", "leke", "kırışıklık", "titck", "onaylı", "mucize", "yok eder", "klinik"],
        "Gıda Takviyesi & Sağlık": ["takviye", "gıda", "sağlık beyanı", "tedavi", "hastalık", "kilo", "zayıflama", "bağışıklık", "eklem", "ağrı", "şifa", "kesin son"],
        "E-Ticaret & Kampanyalar": ["indirim", "fiyat", "en ucuz", "tavsiye edilen", "stok", "bedava", "en çok satan", "fiyatı düştü", "efsane", "tükeniyor"],
        "Sosyal Medya & Influencer": ["influencer", "işbirliği", "etiket", "örtülü reklam", "sosyal medya", "tanıtım", "link", "sponsor", "deneyin"]
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
        pdf.cell(0, 9, "AdShield - Reklam Uyum ve Risk Raporu", ln=True, align="C")
        pdf.set_font("Roboto", "", 8.5)
        pdf.cell(0, 5, f"Sektör: {sektor_adi} | Mecra: {mecra_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
        pdf.line(10, 26, 200, 26)
        pdf.ln(6)
        pdf.set_font("Roboto", "", 8.5)
        pdf.multi_cell(0, 4.8, temiz_metin)
    else:
        tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "AdShield - Reklam Uyum ve Risk Raporu", ln=True, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        sub_title = f"Sektor: {sektor_adi} | Mecra: {mecra_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}".translate(tr_map)
        pdf.cell(0, 5, sub_title, ln=True, align="C")
        pdf.line(10, 26, 200, 26)
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 8.5)
        ascii_metin = temiz_metin.translate(tr_map).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4.8, ascii_metin)

    return bytes(pdf.output())

# Session State
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

# Çalışma Alanı
sol_kolon, sag_kolon = st.columns([1, 1.25], gap="large")

with sol_kolon:
    with st.container(border=True):
        st.markdown("### 🎯 Reklam Taslağı")
        
        # Hızlı Şablon Butonları
        st.caption("Örnek Reklam Senaryoları:")
        c1, c2, c3 = st.columns(3)
        if c1.button("Kozmetik"):
            st.session_state.taslak_metin = "Dermatologların 1 numaralı tercihi! Tamamen %100 bitkisel serumumuz leke ve kırışıklıkları 48 saatte yok eder. Sağlık Bakanlığı onaylı formülüyle botoks etkisini evinize getirir."
        if c2.button("Takviye"):
            st.session_state.taslak_metin = "Eklem kireçlenmesine kesin son! Bağışıklığı güçlendirerek dizdeki iltihabı kurutur, ameliyatsız tedavi sağlar."
        if c3.button("E-Ticaret"):
            st.session_state.taslak_metin = "Yılın efsane indirimi! Türkiye'nin en ucuz robot süpürgesi sadece bugün 24.999 TL yerine 4.999 TL! Son 3 ürün, kaçırmayın."

        sektor = st.selectbox("Sektör", [
            "Kozmetik & Kişisel Bakım",
            "Gıda Takviyesi & Sağlık",
            "E-Ticaret & Kampanyalar",
            "Sosyal Medya & Influencer",
            "Diğer"
        ])
        
        mecra = st.selectbox("Yayın Mecrası", [
            "İnternet / Sosyal Medya (Instagram, TikTok, Web Sitesi)",
            "Ulusal Televizyon Kanalı",
            "Yerel Medya / Radyo",
            "Açık Hava (Billboard, Broşür)"
        ])
        
        reklam_metni = st.text_area(
            "Reklam Metni / İddialar",
            value=st.session_state.taslak_metin,
            height=130,
            placeholder="İncelemek istediğiniz reklam metnini buraya yapıştırın..."
        )
        
        yuklenen_gorsel = st.file_uploader("Reklam Görseli / Story Taslağı (Opsiyonel)", type=["jpg", "jpeg", "png"])
        if yuklenen_gorsel:
            image = Image.open(yuklenen_gorsel)
            st.image(image, caption="Yüklenen Görsel", use_container_width=True)

        analiz_butonu = st.button("⚡ Reklam Riskini ve Emsalleri Denetle", type="primary")

with sag_kolon:
    with st.container(border=True):
        st.markdown("### 📊 Denetim ve Risk Özeti")
        
        if analiz_butonu:
            if not api_key:
                st.error("Lütfen API anahtarı girin.")
            elif not reklam_metni and not yuklenen_gorsel:
                st.warning("Lütfen metin girin veya görsel yükleyin.")
            else:
                with st.spinner("İçtihat veri tabanı taranıyor, risk analizi hazırlanıyor..."):
                    try:
                        genai.configure(api_key=api_key)
                        ilgili_emsaller = get_relevant_emsaller(reklam_metni, sektor)
                        
                        prompt = f"""
Sen; Reklam Kurulu kararları, 6502 sayılı Kanun (özellikle md. 61 ve md. 77) ve TİTCK/TGK kuralları konusunda uzmanlaşmış bir Reklam Uyum Denetçisisin.

Aşağıda 200+ bültenden derlenen emsal Reklam Kurulu kararları bulunmaktadır:
=== EMSAL KARARLAR ===
{ilgili_emsaller}
======================

İNCELENEN REKLAM:
Sektör: {sektor}
Mecra: {mecra}
Metin: {reklam_metni}

GÖREVİN:
Ağır bürokratik tabirlerden kaçınarak; doğrudan sonuca odaklı, net, pazarlamacı ve denetçilerin kolayca anlayacağı modern bir 'Reklam Uyum & Risk Raporu' üretmektir.

RAPOR FORMATI:

### [RİSK: YÜKSEK (KIRMIZI) / ORTA (SARI) / DÜŞÜK (YEŞİL)] - Risk Skoru: [0-100]

### 1. RİSKLİ İFADELER VE İHLAL NEDENLERİ
(Metindeki problemli ifadeleri madde madde ayıkla ve neden riskli olduğunu açık bir dille izah et):
* **"[Riskli İfade 1]":** (Neden riskli? Hangi kural ihlal ediliyor? Tüketici algısı ve ispat yükü nedir?)
* **"[Riskli İfade 2]":** (Neden riskli? Hangi kural ihlal ediliyor?)
* **"[Riskli İfade 3]":** (Neden riskli? Hangi kural ihlal ediliyor?)

### 2. REKLAM KURULU EMSAL KARARLARI & SOMUT CEZALAR
(Arşivdeki emsal metinlerden tespit ettiğin EN AZ 2 ADET gerçek kararı birebir detaylarıyla ver):
* **Emsal Karar 1:**
  - **Dosya No & Tarih:** (Örn: Dosya No: 2023/..., Karar Tarihi: ...)
  - **İncelenen Firma / Mecra:** 
  - **Karardaki Yasaklanan Orijinal İfadeler:** (Kararda durdurulan tırnak içi birebir reklam cümleleri)
  - **Bizim Reklamımızla Benzerliği:** (Hangi vaadimiz bu kararla doğrudan çakışıyor?)
  - **Uygulanan Ceza:** (Durdurma ve ... TL İdari Para Cezası)
* **Emsal Karar 2:**
  - **Dosya No & Tarih:**
  - **İncelenen Firma / Mecra:** 
  - **Karardaki Yasaklanan Orijinal İfadeler:**
  - **Bizim Reklamımızla Benzerliği:**
  - **Uygulanan Ceza:**

### 3. TAHMİNİ CEZA VE YAPTIRIM RİSKİ
* **Yayın Mecrası:** {mecra}
* **6502 Sayılı Kanun Kapsamında Ceza Aralığı:** (Seçilen mecra için güncel alt ve üst idari para cezası limitleri)
* **Olası Ek Yaptırımlar:** (Durdurma, düzeltme ilanı veya içerik çıkarma/erişim engeli riski)

### 4. GÜVENLİ VE ETKİLİ REVİZE METİN
* **Önerilen Güvenli Reklam Metni:** (Cezai riski ortadan kaldıran ama reklamın satış/etki gücünü koruyan alternatif metin)
* **Gereken İspat & Dipnot Standartları:** (Metnin denetimden sorunsuz geçmesi için hazır bulundurulması gereken test/anket veya görsel altı açıklaması)
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
                        st.error(f"Analiz sırasında hata oluştu: {err}")

        if st.session_state.rapor_sonucu:
            st.markdown(st.session_state.rapor_sonucu)
            
            # PDF İndir
            try:
                pdf_verisi = create_pdf(st.session_state.rapor_sonucu, st.session_state.sektor_bilgisi, st.session_state.mecra_bilgisi)
                st.download_button(
                    label="📥 Risk Raporunu İndir (PDF)",
                    data=pdf_verisi,
                    file_name=f"AdShield_Risk_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    type="secondary"
                )
            except Exception as e:
                st.warning(f"PDF uyarısı: {e}")
        else:
            st.info("Sol taraftan reklam metnini girip denetimi başlattığınızda risk analizi burada listelenecektir.")

# Soru-Cevap & Revizyon Asistanı
if st.session_state.rapor_sonucu:
    st.write("")
    with st.container(border=True):
        st.markdown("### 💬 Hızlı Revizyon & Soru-Cevap Asistanı")
        st.caption("Önerilen metni değiştirmek veya aklınıza takılan cezai riskleri sormak için yazabilirsiniz.")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        kullanici_sorusu = st.chat_input("Örn: '48 saat' yerine 'kısa sürede' yazarsam ceza riski biter mi?")
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
Sen bir Reklam Uyum Danışmanısın. Kullanıcı daha önce denetlenen reklam ve rapor hakkında sorular soruyor veya yeni alternatif reklam cümlelerini test ediyor.

BAĞLAM:
- Sektör: {st.session_state.sektor_bilgisi}
- Mecra: {st.session_state.mecra_bilgisi}
- Reklam: {st.session_state.aktif_metin}
- Risk Raporu:
{st.session_state.rapor_sonucu}

GÖREVİN:
Kullanıcının sorusunu net, modern, doğrudan çözüme odaklı bir dille yanıtlamak; yeni cümle öneriyorsa risk analizini anında yapmaktır.
"""
                        )
                        sohbet_gecmisi_prompt = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in st.session_state.chat_history])
                        chat_response = chat_model.generate_content(sohbet_gecmisi_prompt)
                        cevap_metni = chat_response.text
                        st.markdown(cevap_metni)
                        st.session_state.chat_history.append({"role": "assistant", "content": cevap_metni})
                    except Exception as e:
                        st.error(f"Hata: {e}")
