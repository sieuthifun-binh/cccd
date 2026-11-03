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
st.markdown("Hệ thống tối ưu hóa thuật toán **Dictionary Indexing** giúp xử lý hàng trăm nghìn dòng tức thì, chống lỗi trùng tên cột.")

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
                        result = df_master[df_master[master_cccd_col] == search_cccd]
                        if not result.empty:
                            st.success(f"✅ Tìm thấy thông tin cho CCCD: **{search_cccd}**")
                            st.dataframe(result, use_container_width=True)
                        else:
                            st.error(f"❌ Không có kết quả tra cứu cho số CCCD: **{search_cccd}**")

            # --- TAB 2: ĐỐI CHIẾU HÀNG LOẠT ---
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
                        
                        # Chuyển DataFrame gốc thành Dictionary (Bỏ index CCCD để tránh lặp)
                        master_dict = df_master.set_index(master_cccd_col).to_dict('index')
                        
                        results_list = []
                        input_cccd_series = df_input[match_col_input].astype(str).str.strip()
                        
                        # Lấy danh sách tên cột để kiểm tra trùng lặp
                        input_columns = set(df_input.columns)
                        
                        for val in input_cccd_series:
                            if val in master_dict:
                                row_data = master_dict[val]
                                new_row = {}
                                # Kiểm tra và thêm hậu tố _Dữ_Liệu_Gốc nếu trùng tên cột
                                for k, v in row_data.items():
                                    if k in input_columns:
                                        new_row[f"{k}_Dữ_Liệu_Gốc"] = v
                                    else:
                                        new_row[k] = v
                                new_row['Trạng_Thái_Kết_Quả'] = "Có trong hệ thống"
                                results_list.append(new_row)
                            else:
                                new_row = {}
                                for k in df_master.columns:
                                    if k != master_cccd_col:
                                        if k in input_columns:
                                            new_row[f"{k}_Dữ_Liệu_Gốc"] = ""
                                        else:
                                            new_row[k] = ""
                                new_row['Trạng_Thái_Kết_Quả'] = "Không có kết quả tra cứu"
                                results_list.append(new_row)
                                
                        df_matched_info = pd.DataFrame(results_list)
                        
                        # Ghép nối an toàn không lo lỗi Duplicate Columns
                        df_result = pd.concat([df_input.reset_index(drop=True), df_matched_info], axis=1)
                        
                        t_end = time.time()
                        
                        st.success(f"✅ Hoàn thành đối chiếu trong vòng **{t_end - t_start:.2f} giây**!")
                        st.dataframe(df_result.head(100), use_container_width=True) 
                        
                        output_filename = "Ket_Qua_Doi_Chieu_Sieu_Toc.xlsx"
                        df_result.to_excel(output_filename, index
