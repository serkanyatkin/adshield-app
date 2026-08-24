import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="AdShield - Reklam Risk Denetimi", layout="wide")

st.title("🛡️ AdShield: Reklam Kurulu Risk ve Uyumluluk Analizi")
st.caption("Yapay zeka destekli ön denetim ve risk skorlama aracı")

# API Anahtarı
api_key = st.secrets.get("GEMINI_API_KEY", None)

if not api_key:
    st.sidebar.header("Ayarlar")
    api_key = st.sidebar.text_input("Gemini API Key Girin:", type="password")

secilen_model = "gemini-3.6-flash"

SYSTEM_INSTRUCTION = """
Sen, Türkiye Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği, Tüketicinin Korunması Hakkında Kanun ve Reklam Kurulu İlke Kararları konusunda uzmanlaşmış bir Reklam Kalite ve Hukuki Risk Analiz Motorusun.

GÖREVİN:
Kullanıcının ilettiği reklam metnini ve görselini analiz ederek Reklam Kurulu nezdinde ceza riski doğurabilecek unsurları tespit etmek, puanlamak ve risksiz revizyon önerisi sunmaktır.

DENETİM ALANLARI:
1. Sağlık Beyanı: Kozmetik/gıda/temizlik ürünlerinde tıbbi veya tedavi edici iddialar.
2. Kanıtlanmamış İddialar: "En çok satan", "1 numara", "%100 doğal", "%0 fosfat" gibi kanıt/rapor gerektiren beyanlar ve dipnot standartları.
3. Fiyat/İndirim: Yanıltıcı indirim algısı ve referans fiyat kuralları.
4. Sosyal Medya/Influencer: #işbirliği etiketinin görünürlüğü ve konumu.

ÇIKTI FORMATI:
### [RİSK SEVİYESİ: YEŞİL / SARI / KIRMIZI]
- **Risk Skoru:** [0-100]
- **Tespit Edilen Riskler ve Gerekçeleri:** (Mevzuat maddesi veya kurul ilke kararı belirterek)
- **Güvenli Revizyon Önerisi:** (Pazarlamacının doğrudan kullanabileceği risksiz metin/tasarım alternatifi)
- **Yasal Şerh:** "Bu rapor teknik bir ön risk analizidir; 1136 sayılı Kanun kapsamında hukuki mütalaa teşkil etmez."
"""

def clean_for_pdf(text):
    if not text:
        return ""
    replacements = {
        "ı": "i", "İ": "I", "ğ": "g", "Ğ": "G",
        "ü": "u", "Ü": "U", "ş": "s", "Ş": "S",
        "ö": "o", "Ö": "O", "ç": "c", "Ç": "C",
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "—": "-", "–": "-", "•": "-", "…": "..."
    }
    for tr_char, en_char in replacements.items():
        text = text.replace(tr_char, en_char)
    return text.encode('latin-1', 'replace').decode('latin-1')

def create_pdf(report_text, sektor_adi):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, clean_for_pdf("AdShield - Reklam Uyumluluk ve Risk Raporu"), ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, clean_for_pdf(f"Sektor: {sektor_adi} | Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), ln=True, align="C")
    pdf.line(10, 28, 200, 28)
    pdf.ln(8)
    
    temiz_metin = report_text.replace("### ", "").replace("**", "")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, clean_for_pdf(temiz_metin))
    
    return bytes(pdf.output())

if "rapor_sonucu" not in st.session_state:
    st.session_state.rapor_sonucu = None
if "sektor_bilgisi" not in st.session_state:
    st.session_state.sektor_bilgisi = None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Reklam İçeriğini Girin")
    sektor = st.selectbox("Sektör Seçin", [
        "Kozmetik & Kişisel Bakım / Anne-Bebek",
        "Takviye Edici Gıda",
        "E-Ticaret & İndirim",
        "Sağlık & Estetik",
        "Diğer"
    ])
    reklam_metni = st.text_area("Reklam Metni / Caption / İddialar (Varsa)", height=120)
    yuklenen_gorsel = st.file_uploader("Reklam Görseli / Taslak Yükle", type=["jpg", "jpeg", "png"])
    
    if yuklenen_gorsel:
        image = Image.open(yuklenen_gorsel)
        st.image(image, caption="Yüklenen Taslak", use_container_width=True)

    analiz_butonu = st.button("Risk Analizini Başlat", type="primary")

with col2:
    st.subheader("2. Risk ve Uyumluluk Raporu")
    if analiz_butonu:
        if not api_key:
            st.error("Lütfen bir Gemini API anahtarı sağlayın.")
        elif not reklam_metni and not yuklenen_gorsel:
            st.warning("Lütfen analiz için en az bir metin veya görsel yükleyin.")
        else:
            with st.spinner("Reklam Kurulu mevzuatı taranıyor, riskler hesaplanıyor..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(
                        model_name=secilen_model,
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                    
                    icerik_listesi = [f"Sektör: {sektor}\nMetin: {reklam_metni}"]
                    if yuklenen_gorsel:
                        icerik_listesi.append(image)
                    
                    response = model.generate_content(icerik_listesi)
                    st.session_state.rapor_sonucu = response.text
                    st.session_state.sektor_bilgisi = sektor
                except Exception as err:
                    st.error(f"Analiz sırasında bir hata oluştu: {err}")

    if st.session_state.rapor_sonucu:
        st.markdown(st.session_state.rapor_sonucu)
        pdf_verisi = create_pdf(st.session_state.rapor_sonucu, st.session_state.sektor_bilgisi)
        st.download_button(
            label="📄 Risk Raporunu PDF Olarak İndir",
            data=pdf_verisi,
            file_name=f"AdShield_Risk_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            type="secondary"
        )
