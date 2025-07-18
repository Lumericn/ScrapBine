import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import requests
import io
import time
from docx import Document
from PyPDF2 import PdfMerger
from PyPDF2 import PdfReader

st.set_page_config(page_title="📰 Flexible News Scraper", layout="centered")
st.title("📰 Flexible Web Scraper Artikel Berita")

# ===== Sidebar Navigasi Tombol =====
st.sidebar.image("djpblampung.png", width=200)
st.sidebar.markdown("## 🧭 Menu Navigasi")

if "page" not in st.session_state:
    st.session_state.page = "📄 Scrap Satu Artikel"

# Navigasi Sidebar
if st.sidebar.button("📄 Scrap Satu Artikel", use_container_width=True, key="btn_scrap_satu"):
    st.session_state.page = "📄 Scrap Satu Artikel"
if st.sidebar.button("📑 Scrap Banyak Artikel", use_container_width=True, key="btn_scrap_banyak"):
    st.session_state.page = "📑 Scrap Banyak Artikel"
if st.sidebar.button("📎 Gabungkan File", use_container_width=True, key="btn_gabung"):
    st.session_state.page = "📎 Gabungkan File"

st.sidebar.markdown(f"**✅ Halaman Aktif: {st.session_state.page}**")
st.sidebar.markdown("---")
st.sidebar.info(
    """
    💡 *Gunakan tools ini untuk mengambil konten dari situs berita secara fleksibel.*
    Anda hanya perlu menentukan tag HTML dan class untuk elemen Judul, Tanggal, dan Isi Artikel. *Serta mampu digunakan untuk menggabungkan beberapa file dengan format yang sama menjadi 1 file baru.*

    - **Scrap Satu Artikel**: Cocok untuk ekstraksi cepat dari 1 halaman berita.
    - **Scrap Banyak Artikel**: Ambil banyak berita dari daftar halaman sekaligus.
    - **Gabungkan File**: Gabungkan beberapa file dengan format yang sama (**CSV, Excel, Word, atau PDF**) menjadi satu file baru.
    """,
    icon="ℹ️"
)

html_tags = ["div", "article", "section", "span","body", "a", "h1", "h2", "h3", "h4", "h5", "p", "time", "style", "li", "ul", "i", "footer", "header", "figure", "nav", "script"]

# ===== Halaman Scrap Satu Artikel =====
if st.session_state.page == "📄 Scrap Satu Artikel":
    url = st.text_input("🔗 Masukkan URL Berita")

    st.markdown("## 🎯 Selector Elemen HTML")
    with st.expander("🔖 Judul"):
        title_tag = st.selectbox("Tag Judul", options=html_tags, index=html_tags.index("h1"))
        title_class = st.text_input("Class Judul", value="")

    with st.expander("📅 Tanggal"):
        date_tag = st.selectbox("Tag Tanggal", options=html_tags, index=html_tags.index("div"))
        date_class = st.text_input("Class Tanggal", value="")

    with st.expander("📄 Isi Artikel"):
        content_tag = st.selectbox("Tag Isi Artikel", options=html_tags, index=html_tags.index("div"))
        content_class = st.text_input("Class Isi Artikel", value="")

    if st.button("🚀 Ambil Artikel"):
        if not url:
            st.warning("Masukkan URL terlebih dahulu.")
        else:
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.content, "html.parser")

                title_element = soup.find(title_tag, class_=title_class.strip() or None)
                title = title_element.get_text(strip=True) if title_element else "❌ Judul tidak ditemukan"

                date_element = soup.find(date_tag, class_=date_class.strip() or None)
                date = date_element.get_text(strip=True) if date_element else "❌ Tanggal tidak ditemukan"

                content_element = soup.find(content_tag, class_=content_class.strip() or None)
                if content_element:
                    paragraphs = content_element.find_all("p")
                    content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                    content = content or "❌ Isi kosong"
                else:
                    content = "❌ Isi tidak ditemukan"

                st.success("✅ Artikel berhasil diambil")
                st.markdown(f"**📝 Judul:** {title}")
                st.markdown(f"**📅 Tanggal:** {date}")
                st.text_area("📄 Isi Artikel", content, height=300)

                st.session_state["scraped_data"] = pd.DataFrame([{
                    "Tanggal": date,
                    "Judul": title,
                    "Isi": content
                }])

            except Exception as e:
                st.error(f"Gagal mengambil artikel: {e}")

# ===== Halaman Scrap Banyak Artikel =====
elif st.session_state.page == "📑 Scrap Banyak Artikel":
    st.markdown("## 🌐 Konfigurasi Pencarian")
    start_url = st.text_input("🔗 Masukkan URL halaman daftar artikel (satu halaman)")

    st.markdown("## 🎯 Selector Daftar Artikel")
    with st.expander("📝 Daftar List Artikel"):
        article_container_tag = st.selectbox("Tag elemen daftar artikel", options=html_tags)
        article_container_class = st.text_input("Class elemen daftar artikel")

    with st.expander("🔗 Link Artikel"):
        article_link_tag = st.selectbox("Tag untuk link artikel", options=html_tags)
        article_link_class = st.text_input("Class tag link (opsional)")

    st.markdown("## 🎯 Selector Elemen HTML (Dalam Halaman Artikel)")
    with st.expander("🔖 Judul"):
        title_tag = st.selectbox("Tag Judul Artikel", options=html_tags, index=html_tags.index("h1"))
        title_class = st.text_input("Class Judul Artikel")

    with st.expander("📅 Tanggal"):
        date_tag = st.selectbox("Tag Tanggal Artikel", options=html_tags, index=html_tags.index("div"))
        date_class = st.text_input("Class Tanggal Artikel")

    with st.expander("📄 Isi Artikel"):
        content_tag = st.selectbox("Tag Isi Artikel", options=html_tags, index=html_tags.index("div"))
        content_class = st.text_input("Class Isi Artikel")

    def fetch_article(url):
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.find(title_tag, class_=title_class or None)
        date = soup.find(date_tag, class_=date_class or None)
        content_el = soup.find(content_tag, class_=content_class or None)
        content = " ".join(p.get_text(strip=True) for p in content_el.find_all("p")) if content_el else ""
        return (
            title.get_text(strip=True) if title else "Tidak ditemukan",
            date.get_text(strip=True) if date else "Tidak ditemukan",
            content or "Tidak ditemukan"
        )

    if st.button("🚀 Mulai Scraping"):
        if not all([start_url, article_container_tag, article_link_tag, title_tag, date_tag, content_tag]):
            st.error("⚠️ Harap lengkapi semua input tag.")
        else:
            data = {"Tanggal": [], "Judul": [], "Isi": []}

            try:
                response = requests.get(start_url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                containers = soup.find_all(article_container_tag, class_=article_container_class)
                st.write(f"Ditemukan {len(containers)} container artikel")

                links = set()
                for c in containers:
                    link_tags = c.find_all(article_link_tag, class_=article_link_class or None)
                    for tag in link_tags:
                        if tag.name == "a" and tag.get("href"):
                            links.add(tag["href"])

                for link in links:
                    st.write(f"🔗 Mengambil: {link}")
                    title, date, content = fetch_article(link)
                    data["Tanggal"].append(date)
                    data["Judul"].append(title)
                    data["Isi"].append(content)

                st.session_state["scraped_data"] = pd.DataFrame(data)

            except Exception as e:
                st.error(f"❌ Gagal mengambil artikel: {e}")

            result_df = pd.DataFrame(data)
            st.success(f"✅ Selesai! Total artikel: {len(result_df)}")
            st.dataframe(result_df)

# ===== Simpan Hasil =====
if "scraped_data" in st.session_state:
    result_df = st.session_state["scraped_data"]

    st.markdown("---")
    st.subheader("💾 Simpan Hasil")

    filename = st.text_input("📝 Nama file (tanpa ekstensi)", value="hasil_scraping")
    file_format = st.selectbox("📁 Pilih format file", ["CSV", "Excel"])

    if file_format == "CSV":
        csv_data = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv"
        )
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Artikel")
        st.download_button(
            label="⬇️ Download Excel",
            data=output.getvalue(),
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ===== Halaman Gabungkan File =====
elif st.session_state.page == "📎 Gabungkan File":
    st.markdown("## 📎 Gabungkan File")

    uploaded_files = st.file_uploader(
        "📤 Upload 2 atau lebih file sejenis (CSV, Excel, Word, atau PDF)",
        type=["csv", "xls", "xlsx", "docx", "pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        # Ekstensi & validasi
        file_exts = [f.name.split(".")[-1].lower() for f in uploaded_files]
        unique_exts = set(file_exts)

        if len(uploaded_files) < 2:
            st.warning("⚠️ Minimal upload 2 file untuk digabungkan.")
        elif len(unique_exts) > 1:
            st.error("❌ Semua file harus memiliki tipe yang sama.")
        else:
            ext = list(unique_exts)[0]

            if ext in ["csv", "xls", "xlsx"]:
                st.markdown("### 📋 Gabungkan Data (CSV/Excel)")
                data_frames = []

                for file in uploaded_files:
                    try:
                        if ext == "csv":
                            df = pd.read_csv(file)
                        else:
                            df = pd.read_excel(file)
                        data_frames.append(df)
                    except Exception as e:
                        st.error(f"❌ Gagal membaca {file.name}: {e}")

                if data_frames:
                    combined_df = pd.concat(data_frames, ignore_index=True)
                    st.markdown("### 🔍 Pratinjau Hasil Gabungan")
                    st.dataframe(combined_df)

                    result_filename = st.text_input("📝 Nama file hasil gabungan (tanpa ekstensi)", value="hasil_gabungan")
                    save_format = st.selectbox("💾 Simpan sebagai", ["CSV", "Excel"])

                    if st.button("⬇️ Simpan Hasil Gabungan"):
                        if save_format == "CSV":
                            csv_data = combined_df.to_csv(index=False).encode("utf-8")
                            st.download_button("📥 Download CSV", data=csv_data, file_name=f"{result_filename}.csv", mime="text/csv")
                        else:
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                                combined_df.to_excel(writer, index=False, sheet_name="Gabungan")
                            st.download_button("📥 Download Excel", data=output.getvalue(), file_name=f"{result_filename}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            elif ext == "docx":
                st.markdown("### 📄 Gabungkan File Word (.docx)")
                combined_doc = Document()

                for file in uploaded_files:
                    doc = Document(file)
                    for element in doc.element.body:
                        combined_doc.element.body.append(element)

                result_filename = st.text_input("📝 Nama file hasil gabungan Word", value="gabungan_word")
                if st.button("⬇️ Simpan Gabungan Word"):
                    output = io.BytesIO()
                    combined_doc.save(output)
                    st.download_button("📥 Download DOCX", data=output.getvalue(), file_name=f"{result_filename}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            elif ext == "pdf":
                st.markdown("### 📄 Gabungkan File PDF")
                merger = PdfMerger()
                for file in uploaded_files:
                    merger.append(file)

                result_filename = st.text_input("📝 Nama file hasil gabungan PDF", value="gabungan_pdf")
                if st.button("⬇️ Simpan Gabungan PDF"):
                    output = io.BytesIO()
                    merger.write(output)
                    merger.close()
                    st.download_button("📥 Download PDF", data=output.getvalue(), file_name=f"{result_filename}.pdf", mime="application/pdf")

            else:
                st.error("❌ Format file belum didukung.")
