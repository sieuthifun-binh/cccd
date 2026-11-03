import streamlit as st
import pandas as pd

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Tra Cứu & Đối Chiếu Dữ Liệu Theo CCCD",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Hệ Thống Tra Cứu & Đối Chiếu Theo CCCD")
st.markdown("Upload file dữ liệu gốc và file cần tra cứu. Hệ thống sẽ **tự động ưu tiên nhận diện cột CCCD** để xử lý chính xác và giữ nguyên số `0` ở đầu.")

def clean_columns(df):
    """Chuẩn hóa tên cột"""
    df.columns = df.columns.astype(str).str.strip()
    return df

def find_cccd_column(columns):
    """Tự động tìm cột CCCD/Căn cước ưu tiên cao nhất"""
    for col in columns:
        col_lower = col.lower().strip()
        if col_lower in ['cccd', 'số cccd', 'căn cước công dân', 'so cccd', 'can cuoc cong dan', 'cmnd', 'số cmnd', 'so cmnd']:
            return col
    for col in columns:
        col_lower = col.lower()
        if 'cccd' in col_lower or 'căn cước' in col_lower or 'cmnd' in col_lower:
            return col
    return None

# --- KHU VỰC UPLOAD FILE ---
st.markdown("---")
col_up1, col_up2 = st.columns(2)

with col_up1:
    st.subheader("1️⃣ File Dữ Liệu Gốc")
    uploaded_master = st.file_uploader("Chọn file nguồn (Excel/CSV)", type=["xlsx", "xls", "csv"], key="master")

with col_up2:
    st.subheader("2️⃣ File Cần Tìm Kiếm / Đối Chiếu")
    uploaded_search = st.file_uploader("Chọn file danh sách tra cứu (Excel/CSV)", type=["xlsx", "xls", "csv"], key="search")

# --- XỬ LÝ DỮ LIỆU KHI ĐÃ CÓ ĐỦ 2 FILE ---
if uploaded_master is not None and uploaded_search is not None:
    try:
        # Đọc file gốc (ép kiểu chuỗi để giữ nguyên số 0 đầu)
        if uploaded_master.name.endswith('.csv'):
            df_master = pd.read_csv(uploaded_master, dtype=str)
        else:
            df_master = pd.read_excel(uploaded_master, dtype=str)
        
        df_master = clean_columns(df_master)
        
        # Đọc file cần tìm kiếm
        if uploaded_search.name.endswith('.csv'):
            df_input = pd.read_csv(uploaded_search, dtype=str)
        else:
            df_input = pd.read_excel(uploaded_search, dtype=str)
            
        df_input = clean_columns(df_input)
        
        # Tự động tìm cột CCCD trong file gốc
        master_cccd_col = find_cccd_column(df_master.columns)
        
        if not master_cccd_col:
            st.error("❌ Không tìm thấy cột CCCD/Căn cước trong file dữ liệu gốc! Vui lòng kiểm tra lại tên cột trong file.")
        else:
            # Chuẩn hóa chuỗi CCCD file gốc và lọc trùng tự động
            df_master[master_cccd_col] = df_master[master_cccd_col].str.strip()
            df_master = df_master.drop_duplicates(subset=[master_cccd_col], keep='last')
            
            st.success(f"✅ Đã tải dữ liệu gốc thành công! Nhận diện cột CCCD chính: **[{master_cccd_col}]** | Tổng số bản ghi duy nhất: **{len(df_master):,}**")
            
            # --- CÁC TAB CHỨC NĂNG ---
            tab1, tab2 = st.tabs(["🔎 Tra Cứu Thủ Công", "📁 Đối Chiếu Hàng Loạt Theo File"])
            
            # --- TAB 1: TRA CỨU THỦ CÔNG ---
            with tab1:
                st.subheader("Tra cứu thông tin thủ công theo số CCCD")
                search_cccd = st.text_input("Nhập số CCCD cần tra cứu:", placeholder="Ví dụ: 03809xxxxxxx").strip()
                
                if st.button("Tìm Kiếm", type="primary"):
                    if not search_cccd:
                        st.warning("⚠️ Vui lòng nhập số CCCD!")
                    else:
                        result = df_master[df_master[master_cccd_col] == search_cccd]
                        if not result.empty:
                            st.success(f"✅ Tìm thấy thông tin cho CCCD: **{search_cccd}**")
                            st.dataframe(result, use_container_width=True)
                        else:
                            st.error(f"❌ Không có kết quả tra cứu cho số CCCD: **{search_cccd}** trong hệ thống dữ liệu gốc!")

            # --- TAB 2: ĐỐI CHIẾU HÀNG LOẠT ---
            with tab2:
                st.subheader("Đối chiếu danh sách tự động theo cột CCCD")
                
                with st.expander("👁️ Xem trước 5 dòng đầu của file cần tra cứu", expanded=False):
                    st.dataframe(df_input.head(), use_container_width=True)
                
                # Tự động tìm cột CCCD ở file upload
                input_cccd_col = find_cccd_column(df_input.columns)
                
                if input_cccd_col:
                    st.info(f"💡 Hệ thống đã **tự động chọn** cột **[{input_cccd_col}]** từ file upload để đối chiếu với cột **[{master_cccd_col}]** của file gốc.")
                    match_col_input = input_cccd_col
                else:
                    st.warning("⚠️ Không tự động nhận diện được cột CCCD trong file upload. Vui lòng chọn thủ công bên dưới:")
                    match_col_input = st.selectbox("Chọn cột chứa CCCD trong File Tra Cứu:", list(df_input.columns))
                
                if st.button("🚀 Tiến Hành Đối Chiếu Theo CCCD", type="primary"):
                    with st.spinner("Đang đối chiếu dữ liệu..."):
                        # Chuẩn hóa khóa so sánh
                        df_input['_Key_Temp'] = df_input[match_col_input].astype(str).str.strip()
                        df_master_copy = df_master.copy()
                        df_master_copy['_Key_Temp'] = df_master_copy[master_cccd_col].astype(str).str.strip()
                        
                        # Merge dữ liệu dựa theo cột CCCD, giữ nguyên cấu trúc file input
                        df_result = pd.merge(
                            df_input,
                            df_master_copy,
                            on='_Key_Temp',
                            how='left',
                            suffixes=('', '_Gốc')
                        )
                        
                        # Xóa cột tạm
                        df_result = df_result.drop(columns=['_Key_Temp'])
                        
                        # Đánh dấu trạng thái kết quả theo yêu cầu mới
                        df_result["Trạng_Thái_Kết_Quả"] = df_result[master_cccd_col].apply(
                            lambda x: "Có trong hệ thống" if pd.notnull(x) and str(x).strip() != "" and str(x).strip() != "nan" else "Không có kết quả tra cứu"
                        )
                        
                        st.success("✅ Đối chiếu thành công!")
                        st.dataframe(df_result, use_container_width=True)
                        
                        # Xuất file Excel kết quả
                        output_filename = "Ket_Qua_Doi_Chieu_CCCD.xlsx"
                        df_result.to_excel(output_filename, index=False)
                        
                        with open(output_filename, "rb") as f:
                            st.download_button(
                                label="📥 Tải Xuống File Kết Quả (Excel)",
                                data=f,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                            
    except Exception as e:
        st.error(f"Lỗi khi đọc hoặc xử lý file: {e}")
else:
    st.info("💡 Vui lòng upload đầy đủ **File Dữ Liệu Gốc** và **File Cần Tìm Kiếm** ở phía trên để bắt đầu sử dụng.")
