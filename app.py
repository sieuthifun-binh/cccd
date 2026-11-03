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
st.markdown("Hệ thống tối ưu hóa thuật toán **Dictionary Indexing** và bảo toàn tuyệt đối số `0` ở đầu của CCCD/Số định danh.")

def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip()
    return df

def find_cccd_column(columns):
    for col in columns:
        col_lower = col.lower().strip()
        if col_lower in ['cccd', 'số cccd', 'căn cước công dân', 'so cccd', 'can cuoc cong dan', 'cmnd', 'số cmnd', 'so cmnd', 'định danh', 'so dinh danh']:
            return col
    for col in columns:
        col_lower = col.lower()
        if 'cccd' in col_lower or 'căn cước' in col_lower or 'cmnd' in col_lower or 'định danh' in col_lower or 'dinh danh' in col_lower:
            return col
    return None

# --- HÀM ĐỌC FILE ĐƯỢC CACHE ĐỂ TĂNG TỐC ---
@st.cache_data
def load_and_process_master(uploaded_file):
    start_time = time.time()
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, dtype=str)
    else:
        df = pd.read_excel(uploaded_file, dtype=str, engine='openpyxl')
    
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
        df = pd.read_excel(uploaded_file, dtype=str, engine='openpyxl')
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
            st.error("❌ Không tìm thấy cột CCCD/Căn cước/Định danh trong file dữ liệu gốc!")
        else:
            st.success(f"⚡ Đã tải xong dữ liệu gốc trong **{load_time:.2f} giây** | Tổng bản ghi: **{len(df_master):,}**")
            
            tab1, tab2 = st.tabs(["🔎 Tra Cứu Thủ Công", "📁 Đối Chiếu Hàng Loạt Tốc Độ Cao"])
            
            # --- TAB 1: TRA CỨU THỦ CÔNG ---
            with tab1:
                st.subheader("Tra cứu thông tin thủ công")
                search_cccd = st.text_input("Nhập số CCCD / Định danh:", placeholder="Ví dụ: 03809xxxxxxx").strip()
                
                if st.button("Tìm Kiếm", type="primary"):
                    if not search_cccd:
                        st.warning("⚠️ Vui lòng nhập số CCCD hoặc số định danh!")
                    else:
                        result = df_master[df_master[master_cccd_col] == search_cccd]
                        if not result.empty:
                            st.success(f"✅ Tìm thấy thông tin cho số: **{search_cccd}**")
                            st.dataframe(result, use_container_width=True)
                        else:
                            st.error(f"❌ Không có kết quả tra cứu cho số: **{search_cccd}**")

            # --- TAB 2: ĐỐI CHIẾU HÀNG LOẠT ---
            with tab2:
                st.subheader("Đối chiếu danh sách tự động (Siêu tốc)")
                
                input_cccd_col = find_cccd_column(df_input.columns)
                if input_cccd_col:
                    match_col_input = input_cccd_col
                    st.info(f"💡 Đã tự động chọn cột **[{input_cccd_col}]** để đối chiếu.")
                else:
                    match_col_input = st.selectbox("Chọn cột CCCD/Định danh trong File Tra Cứu:", list(df_input.columns))
                
                if st.button("🚀 Chạy Đối Chiếu Siêu Tốc", type="primary"):
                    with st.spinner("Đang xử lý đối chiếu tốc độ cao..."):
                        t_start = time.time()
                        
                        master_dict = df_master.set_index(master_cccd_col).to_dict('index')
                        
                        results_list = []
                        input_cccd_series = df_input[match_col_input].astype(str).str.strip()
                        input_columns = set(df_input.columns)
                        
                        for val in input_cccd_series:
                            if val in master_dict:
                                row_data = master_dict[val]
                                new_row = {}
                                for k, v in row_data.items():
                                    if k in input_columns:
                                        new_row[f"{k}_Dữ_Liệu_Gốc"] = str(v) if v is not None else ""
                                    else:
                                        new_row[k] = str(v) if v is not None else ""
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
                        df_result = pd.concat([df_input.reset_index(drop=True), df_matched_info], axis=1)
                        
                        t_end = time.time()
                        
                        st.success(f"✅ Hoàn thành đối chiếu trong vòng **{t_end - t_start:.2f} giây**!")
                        st.dataframe(df_result.head(100), use_container_width=True) 
                        
                        output_filename = "Ket_Qua_Doi_Chieu_Sieu_Toc.xlsx"
                        
                        # Sử dụng openpyxl để ép định dạng text (@) cho các cột chứa CCCD/Định danh
                        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                            df_result.to_excel(writer, index=False, sheet_name='KetQua')
                            worksheet = writer.sheets['KetQua']
                            
                            # Quét qua các cột, nếu tên cột chứa từ khóa cccd/định danh thì set định dạng Text cho toàn bộ cell
                            for col_idx, col_name in enumerate(df_result.columns, 1):
                                col_name_lower = str(col_name).lower()
                                if 'cccd' in col_name_lower or 'định danh' in col_name_lower or 'dinh danh' in col_name_lower or 'cmnd' in col_name_lower:
                                    for row_idx in range(2, len(df_result) + 2):
                                        cell = worksheet.cell(row=row_idx, column=col_idx)
                                        cell.number_format = '@' # Ép kiểu Text để không bị mất số 0
                        
                        with open(output_filename, "rb") as f:
                            st.download_button(
                                label="📥 Tải Xuống File Kết Quả (Excel chuẩn định danh)",
                                data=f,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
    except Exception as e:
        st.error(f"Lỗi khi xử lý file: {e}")
else:
    st.info("💡 Vui lòng upload đầy đủ file gốc và file tra cứu ở trên để bắt đầu.")
