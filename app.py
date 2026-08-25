import io
import os
import google.generativeai as genai
import requests
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen === canvas  # wait, fix typo: canvas from reportlab.pdfgen import canvas

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="AdShield: Reklam Kurulu Risk ve Uyumluluk Analizi",
    page_icon="🛡️",
    layout="wide",
)

# 2. Güvenli API Anahtar Yönetimi (Sadece API ayarları sol menüde)
try:
  GEMINI_API_KEY_DEFAULT = st.secrets.get("GEMINI_API_KEY", "")
  GOOGLE_CSE_KEY_DEFAULT = st.secrets.get("GOOGLE_CSE_KEY", "")
  GOOGLE_CSE_CX_DEFAULT = st.secrets.get("GOOGLE_CSE_CX", "")
except Exception:
  GEMINI_API_KEY_DEFAULT = ""
  GOOGLE_CSE_KEY_DEFAULT = ""
  GOOGLE_CSE_CX_DEFAULT = ""

st.sidebar.header("⚙️ API ve Sistem Yapılandırması")
gemini_api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=GEMINI_API_KEY_DEFAULT,
    type="password",
    help="Google AI Studio'dan aldığınız Gemini API anahtarınız.",
)
google_search_api_key = st.sidebar.text_input(
    "Google Search API Key",
    value=GOOGLE_CSE_KEY_DEFAULT,
    type="password",
    help="Google Cloud Console Custom Search API anahtarınız.",
)
google_cse_cx = st.sidebar.text_input(
    "Google Search Engine ID (CX)",
    value=GOOGLE_CSE_CX_DEFAULT,
    help="Programmable Search Engine CX kimliğiniz.",
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


# Gemini Risk Analizi Fonksiyonu
def analyze_risk_with_gemini(product_name, sector, search_titles, api_key):
  if not api_key:
    return (
        "⚠️ Gemini API anahtarı girilmediği için yapay zeka analizi"
        " yapılamadı.\nGenel Risk Durumu: Orta Risk"
    )

  genai.configure(api_key=api_key)
  model = genai.GenerativeModel("gemini-1.5-flash")

  prompt = f"""
    Sen bir Ticaret Bakanlığı Reklam Kurulu Uzmanı ve Dijital Uyumluluk Denetmenisin.
    Ürün / Marka: {product_name}
    Sektör: {sector}
    Bulunan Web/Pazaryeri Başlıkları: {search_titles}

    Lütfen bu verileri Ticaret Bakanlığı Reklam Kurulu mevzuatına, Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği'ne göre analiz et:
    1. Tespit edilen olası mevzuat ihlalleri / riskli ifadeler.
    2. Risk Skoru (0-100 arası ve Risk Seviyesi: Düşük/Orta/Yüksek).
    3. Acil düzeltilmesi gereken alanlar için öneriler.
    Profesyonel, net ve resmi bir dille raporla.
    """
  try:
    response = model.generate_content(prompt)
    return response.text
  except Exception as e:
    return f"Gemini Analiz Hatası: {str(e)}"


# Profesyonel PDF Rapor Üretici
def generate_pdf(product_name, sector, analysis_result, results):
  buffer = io.BytesIO()
  p = canvas.Canvas(buffer, pagesize=letter)
  width, height = letter

  p.setFont("Helvetica-Bold", 14)
  p.drawString(50, height - 50, f"AdShield Reklam Kurulu Uyumluluk Raporu")
  p.setFont("Helvetica", 10)
  p.drawString(
      50, height - 70, f"Ürün: {product_name} | Sektör: {sector}"
  )
  p.drawString(
      50, height - 85, "--------------------------------------------------"
  )

  p.setFont("Helvetica-Bold", 11)
  p.drawString(50, height - 110, "Yapay Zeka Risk ve Mevzuat Analizi:")
  p.setFont("Helvetica", 9)

  y = height - 130
  for line in analysis_result.split("\n"):
    if y < 50:
      p.showPage()
      y = height - 50
    p.drawString(50, y, line[:95])
    y -= 15

  p.save()
  buffer.seek(0)
  return buffer


# 4. Ana Ekran - Sayfanın Ortasında Yan Yana Sekmeler (Tabs)
st.title("🛡️ AdShield: Reklam Kurulu Risk ve Uyumluluk Analizi")
st.markdown(
    "Yapay zeka destekli ön denetim, web tarama ve otomatik risk skorlama"
    " aracı."
)

# Üst kısımda yan yana sekmeler
tab1, tab2, tab3 = st.tabs([
    "🚀 360° Canlı Risk Tarama",
    "⚖️ Mevzuat & Kılavuz Kontrolü",
    "📊 Geçmiş Rapor Arşivi",
])

with tab1:
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
      st.warning(
          "⚠️ Lütfen sol menüden Google Search API Key ve CX bilgilerini"
          " girin."
      )
    elif not product_name:
      st.warning("⚠️ Lütfen denetlenecek bir ürün veya marka adı yazın.")
    else:
      with st.spinner(
          "🌐 Google Custom Search üzerinden pazaryerleri taranıyor..."
      ):
        search_results = search_google(
            product_name, google_search_api_key, google_cse_cx
        )

      search_titles = [
          item.get("title", "") for item in search_results
      ] if search_results else ["Web verisi bulunamadı."]

      with st.spinner("🤖 Gemini AI Reklam Kurulu mevzuatına göre analiz ediyor..."):
        analysis_text = analyze_risk_with_gemini(
            product_name, sector, search_titles, gemini_api_key
        )

      st.success("✅ Tarama ve Risk Analizi Tamamlandı!")

      st.subheader("📋 Analiz Özeti ve Bulgular")
      st.markdown(analysis_text)

      pdf_buffer = generate_pdf(
          product_name, sector, analysis_text, search_results
      )
      st.download_button(
          label="📥 Detaylı Risk Raporunu İndir (PDF)",
          data=pdf_buffer,
          file_name=f"{product_name.replace(' ', '_')}_AdShield_Risk_Raporu.pdf",
          mime="application/pdf",
      )

with tab2:
  st.header("⚖️ Ticaret Bakanlığı Reklam Kurulu Kılavuzları")
  st.info(
      "Bu panel üzerinden en güncel Reklam Kurulu ilkelerine ve sektörel"
      " denetim kriterlerine ulaşabilirsiniz."
  )
  st.markdown(
      """
    - **Kozmetik Ürünler:** Tıbbi nitelik taşıyan, tedavi edici, hastalıklara karşı etkili olduğu iddia edilen ifadeler kesinlikle yasaktır.
    - **Sağlık Beyanları:** İlaç niteliğinde ibareler veya tıbbi tavsiye içeren yönlendirmeler yaptırıma tabidir.
    - **Fiyat ve İndirimler:** Kampanya ve indirim reklamlarında indirim öncesi fiyatın doğruluğu ispatlanabilmelidir.
    """
  )

with tab3:
  st.header("📊 Geçmiş Rapor Arşivi")
  st.info(
      "Daha önce oluşturduğunuz ve sisteme kaydedilen denetim raporları bu"
      " alanda saklanır."
  )
  st.write("📁 Henüz arşive kaydedilmiş eski bir rapor bulunmuyor.")
