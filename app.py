def create_pdf(vaka_listesi, baslik_metni="AdShield Denetim Raporu"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for idx, veri in enumerate(vaka_listesi, 1):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"{baslik_metni} - Vaka #{idx}", ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        
        if veri.get("url"): 
            # URL çok uzunsa hatayı önlemek için zorla bölüyoruz
            guvenli_url = textwrap.fill(veri['url'], width=80)
            pdf.multi_cell(0, 6, f"Kaynak:\n{guvenli_url}")
            pdf.ln(3)
            
        if veri.get("gorsel"):
            temp_img = f"temp_adshield_{int(time.time())}_{idx}.png"
            veri["gorsel"].save(temp_img, format="PNG")
            pdf.image(temp_img, w=170)
            os.remove(temp_img)
            
        pdf.ln(5)
        rapor_metni = veri.get("rapor", "")
        
        for line in rapor_metni.split('\n'):
            # Türkçe karakterleri desteklemesi için güvenli dönüştürme
            guvenli_metin = line.encode('latin-1', 'replace').decode('latin-1')
            
            # Yatay boşluk hatası (FPDFException) almamak için:
            # Metni ve sayfaya sığmayan çok uzun kelimeleri manuel olarak parçalıyoruz
            sarmalanmis_satirlar = textwrap.wrap(guvenli_metin, width=95, break_long_words=True)
            
            if not sarmalanmis_satirlar:
                pdf.ln(5) # Boş satırları atla ama mesafe bırak
            
            for w_line in sarmalanmis_satirlar:
                pdf.multi_cell(0, 6, w_line)
                
    return bytes(pdf.output())
