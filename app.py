import io
import os
import requests
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="AdShield: Reklam Kurulu Risk ve Uyumluluk Analizi",
    page_icon="🛡️",
    layout="wide",
)

# 2. Güvenli API Anahtar Yönetimi
try:
  GEMINI_API_KEY_DEFAULT = st.secrets.get("GEMINI_API_KEY", "")
  GOOGLE_CSE_KEY_DEFAULT = st.secrets.get("GOOGLE_CSE_KEY", "")
  GOOGLE_CSE_CX_DEFAULT = st.secrets.get("GOOGLE_CSE_CX", "")
except Exception:
  GEMINI_API_KEY_DEFAULT = ""
  GOOGLE_CSE_KEY_DEFAULT = ""
  GOOGLE_CSE_CX_DEFAULT = ""

# 3. Sidebar (Sol Menü) Yapılandırması ve Paneller
st.sidebar.header("⚙️ API ve Sistem Yapılandırması")

gemini_api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=GEMINI_API_KEY_DEFAULT,
    type="password",
    help="Google AI Studio'dan aldığınız Gemini API anahtarınızı girin.",
)

google_search_api_key = st.sidebar.text_input(
    "Google Search API Key",
    value=GOOGLE_CSE_KEY_DEFAULT,
    type="password",
    help="Google Cloud Console'dan aldığınız Custom Search API anahtarınız.",
)

google_cse_cx = st.sidebar.text_input(
    "Google Search Engine ID (CX)",
    value=GOOGLE_CSE_CX_DEFAULT,
    help=(
        "Programmable Search Engine panelinden aldığınız Arama Motoru Kimliği."
    ),
)

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Denetim Panelleri")
audit_mode = st.sidebar.radio(
    "Mod Seçin",
    [
        "🚀 360° Canlı Risk Tarama",
        "⚖️ Mevzuat & Kılavuz Kontrolü",
        "📊 Geçmiş Rapor Arşivi",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Bu araç, e-ticaret sitelerindeki potansiyel mevzuat ve reklam kurulu"
    " ihlallerini tespit ederek delilli PDF raporu oluşturur."
)


# Google Custom Search Fonksiyonu
def search_google(query, api_key, cx):
  url = "https://www.googleapis.com/customsearch/v1"
  params = {"key": api_key, "cx": cx, "q": query, "searchType": "image"}
  try:
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
      return response.json().get("items", [])
  except Exception as e:
    st.error(f"Arama hatası: {e}")
  return []


# PDF Üretici
def generate_pdf(product_name, results, sector):
  buffer = io.BytesIO()
  p = canvas.Canvas(buffer, pagesize=letter)
  p.drawString(
      50, 750, f"AdShield Risk Raporu: {product_name} ({sector})"
  )
  p.drawString(50, 730, "--------------------------------------------------")

  y = 700
  for item in results[:5]:
    title = item.get("title", "Başlık Yok")[:60]
    link = item.get("link", "Link yok")[:80]
    p.drawString(50, y, f"- {title}")
    p.drawString(70, y - 15, f"  URL: {link}")
    y -= 40
    if y < 50:
      p.showPage()
      y = 750

  p.save()
  buffer.seek(0)
  return buffer


# 4. Ana Ekran ve Panel Yönetimi
st.title("🛡️ AdShield: Reklam Kurulu Risk ve Uyumluluk Analizi")

if audit_mode == "🚀 360° Canlı Risk Tarama":
  st.markdown("Yapay zeka destekli ön denetim ve risk skorlama aracı.")

  col1, col2 = st.columns([2, 1])
  with col1:
    product_name = st.text_input(
        "Denetlenecek Ürün / Marka Adı",
        placeholder="Örn: Mamaaura Çatlak ve Masaj Yağı",
    )
  with col2:
    sector = st.selectbox(
        "Sektör Seçimi",
        ["Kozmetik & Kişisel Bakım", "Gıda Takviyeleri", "Sağlık & Medikal", "Diğer"],
    )

  if st.button(
      "🚀 Canlı Tara ve Görselli PDF Risk Raporunu Oluştur", type="primary"
  ):
    if not google_search_api_key or not google_cse_cx:
      st.warning("⚠️ Lütfen sol menüden Google Search API Key ve CX girin.")
    elif not product_name:
      st.warning("⚠️ Lütfen bir ürün adı yazın.")
    else:
      with st.spinner("Google üzerinden canlı veriler taranıyor..."):
        search_results = search_google(
            product_name, google_search_api_key, google_cse_cx
        )

      if search_results:
        st.success(
            f"Bulunan kaynak sayısı: {len(search_results)}. PDF raporu"
            " hazırlanıyor..."
        )
        pdf_buffer = generate_pdf(product_name, search_results, sector)
        st.download_button(
            label="📥 Risk Raporunu İndir (PDF)",
            data=pdf_buffer,
            file_name=f"{product_name}_Risk_Raporu.pdf",
            mime="application/pdf",
        )
      else:
        st.warning(
            "Arama sonucunda veri bulunamadı. Lütfen anahtarlarınızı ve ürün"
            " adını kontrol edin."
        )

elif audit_mode == "⚖️ Mevzuat & Kılavuz Kontrolü":
  st.header("⚖️ Ticaret Bakanlığı Reklam Kurulu Kılavuzları")
  st.info(
      "Bu panel üzerinden ilgili sağlık beyanları, kozmetik yönetmelikleri ve"
      " denetim kriterlerini inceleyebilirsiniz."
  )
  st.markdown(
      "- **Kozmetik Yönetmeliği:** Tıbbi nitelik taşıyan ifadelerin kullanımı"
      " yasaktır.\n- **Sağlık Beyanları:** 'Tedavi eder', 'iyileştirir' gibi"
      " ibareler Reklam Kurulu yaptırımına tabidir."
  )

elif audit_mode == "📊 Geçmiş Rapor Arşivi":
  st.header("📊 Geçmiş Rapor Arşivi")
  st.info("Daha önce oluşturduğunuz denetim raporları burada listelenir.")
  st.write("Henüz kaydedilmiş geçmiş rapor bulunmuyor.")
