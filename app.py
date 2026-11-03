import streamlit as st
import pandas as pd
import time

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Hệ Thống Tra Cứu Tốc Độ Cao",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Hệ Thống Tra Cứu & Đối Chiếu Dữ Liệu Tốc Độ Cao")
st.markdown("Hệ thống đã được tối ưu hóa thuật toán tra cứu bằng **Dictionary Indexing** giúp xử lý hàng trăm nghìn dòng tức thì.")

def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip()
    return df

def find_cccd_column(columns):
    for col in columns:
        col_lower = col.lower().strip()
        if col_lower in ['cccd', 'số cccd', 'căn cước công dân', 'so cccd', 'can cuoc cong dan', 'cmnd', 'số cmnd', 'so cmnd']:
            return col
    for col in columns:
        col_lower = col.lower()
        if 'cccd' in col_lower or 'căn cước' in col_lower or 'cmnd' in col_lower:
            return col
    return None

# --- HÀM ĐỌC FILE ĐƯỢC CACHE ĐỂ TĂNG TỐC ---
@st.cache_data
def load_and_process_master(uploaded_file):
    start_time = time.time()
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, dtype=str)
    else:
        df = pd.read_excel(uploaded_file, dtype=str)
    
    df = clean_columns(df)
    cccd_col = find_cccd_column(df.columns)
    
    if cccd_col:
        df[cccd_col] = df[cccd_col].str.strip()
        # Lọc trùng loại bỏ bớt dữ liệu thừa
        df = df.drop_duplicates(subset=[cccd_col], keep='last')
        
    return df, cccd_col, time.time() - start_time

@st.cache_data
def load_search_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, dtype=str)
    else:
        df = pd.read_excel(uploaded_file, dtype=str)
    return clean_columns(df)

# --- UPLOAD FILE ---
st.markdown("---")
col_up1, col_up2 = st.columns(2)

with col_up1:
    uploaded_master = st.file_uploader("1️⃣ Chọn file Dữ Liệu Gốc (Excel/CSV)", type=["xlsx", "xls", "csv"], key="master")

with col_up2:
    uploaded_search = st.file_uploader("2️⃣ Chọn file Cần Tra Cứu / Đối Chiếu", type=["xlsx", "xls", "csv"], key="search")

if uploaded_master is not None and uploaded_search is not None:
    try:
        # Load dữ liệu với cache
        df_master, master_cccd_col, load_time = load_and_process_master(uploaded_master)
        df_input = load_search_file(uploaded_search)
        
        if not master_cccd_col:
            st.error("❌ Không tìm thấy cột CCCD/Căn cước trong file dữ liệu gốc!")
        else:
            st.success(f"⚡ Đã tải xong dữ liệu gốc trong **{load_time:.2f} giây** | Tổng bản ghi: **{len(df_master):,}**")
            
            tab1, tab2 = st.tabs(["🔎 Tra Cứu Thủ Công", "📁 Đối Chiếu Hàng Loạt Tốc Độ Cao"])
            
            # --- TAB 1: TRA CỨU THỦ CÔNG ---
            with tab1:
                st.subheader("Tra cứu thông tin thủ công")
                search_cccd = st.text_input("Nhập số CCCD:", placeholder="Ví dụ: 03809xxxxxxx").strip()
                
                if st.button("Tìm Kiếm", type="primary"):
                    if not search_cccd:
                        st.warning("⚠️ Vui lòng nhập số CCCD!")
                    else:
                        # Tối ưu tra cứu bằng bộ lọc nhanh của pandas
                        result = df_master[df_master[master_cccd_col] == search_cccd]
                        if not result.empty:
                            st.success(f"✅ Tìm thấy thông tin cho CCCD: **{search_cccd}**")
                            st.dataframe(result, use_container_width=True)
                        else:
                            st.error(f"❌ Không có kết quả tra cứu cho số CCCD: **{search_cccd}**")

            # --- TAB 2: ĐỐI CHIẾU HÀNG LOẠT (TỐC ĐỘ CAO DỰA TRÊN DICTIONARY) ---
            with tab2:
                st.subheader("Đối chiếu danh sách tự động (Siêu tốc)")
                
                input_cccd_col = find_cccd_column(df_input.columns)
                if input_cccd_col:
                    match_col_input = input_cccd_col
                    st.info(f"💡 Đã tự động chọn cột **[{input_cccd_col}]** để đối chiếu.")
                else:
                    match_col_input = st.selectbox("Chọn cột CCCD trong File Tra Cứu:", list(df_input.columns))
                
                if st.button("🚀 Chạy Đối Chiếu Siêu Tốc", type="primary"):
                    with st.spinner("Đang xử lý đối chiếu tốc độ cao..."):
                        t_start = time.time()
                        
                        # TẠO DICTIONARY INDEX CHO TOÀN BỘ FILE GỐC ĐỂ TRA CỨU O(1)
                        # Chuyển DataFrame gốc thành dict với key là CCCD, value là toàn bộSeries dòng đó
                        master_dict = df_master.set_index(master_cccd_col).to_dict('index')
                        
                        # Xử lý đối chiếu cho từng dòng của file input
                        results_list = []
                        input_cccd_series = df_input[match_col_input].astype(str).str.strip()
                        
                        master_columns = list(df_master.columns)
                        
                        for val in input_cccd_series:
                            if val in master_dict:
                                # Lấy thông tin từ file gốc gộp vào
                                row_data = master_dict[val].copy()
                                row_data['Trạng_Thái_Kết_Quả'] = "Có trong hệ thống"
                                results_list.append(row_data)
                            else:
                                row_data = {col: "" for col in master_columns if col != master_cccd_col}
                                row_data[master_cccd_col] = val
                                row_data['Trạng_Thái_Kết_Quả'] = "Không có kết quả tra cứu"
                                results_list.append(row_data)
                                
                        # Tạo DataFrame kết quả kết hợp từ file input và thông tin tìm được
                        df_matched_info = pd.DataFrame(results_list)
                        
                        # Ghép nối lại với file input ban đầu để giữ nguyên 100% cấu trúc cột của file input
                        df_result = pd.concat([df_input.reset_index(drop=True), df_matched_info.drop(columns=[master_cccd_col], errors='ignore')], axis=1)
                        
                        t_end = time.time()
                        
                        st.success(f"✅ Hoàn thành đối chiếu trong vòng **{t_end - t_start:.2f} giây**!")
                        st.dataframe(df_result.head(100), use_container_width=True) # Hiển thị 100 dòng đầu cho mượt giao diện
                        
                        output_filename = "Ket_Qua_Doi_Chieu_Sieu_Toc.xlsx"
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
        st.error(f"Lỗi khi xử lý file: {e}")
else:
    st.info("💡 Vui lòng upload đầy đủ file gốc và file tra cứu ở trên để bắt đầu.")
