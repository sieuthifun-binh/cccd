import streamlit as st
import pandas as pd
import time
import difflib

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Hệ Thống Tra Cứu Tốc Độ Cao - Argon Hyper-Speed",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Hệ Thống Tra Cứu & Đối Chiếu Siêu Tốc (Argon Hyper-Speed Edition)")
st.markdown("Đã tối ưu hóa toàn bộ thuật toán bằng **Pandas Vectorization**, loại bỏ hoàn toàn vòng lặp Python để đạt hiệu suất tối đa.")

def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip()
    return df

def find_cccd_column(columns):
    keywords = ['cccd', 'số cccd', 'căn cước công dân', 'so cccd', 'can cuoc cong dan', 'cmnd', 'số cmnd', 'so cmnd', 'định danh', 'so dinh danh']
    for col in columns:
        if col.lower().strip() in keywords:
            return col
    for col in columns:
        col_lower = col.lower()
        if any(k in col_lower for k in ['cccd', 'căn cước', 'cmnd', 'định danh', 'dinh danh']):
            return col
    return None

# --- BẢNG ÁNH XẠ MÃ TỈNH (Dùng cho Vectorized Map cực nhanh) ---
PROVINCE_DICT = {
    "001": "Hà Nội", "002": "Hà Giang", "004": "Cao Bằng", "006": "Bắc Kạn", "008": "Tuyên Quang",
    "010": "Lào Cai", "011": "Điện Biên", "012": "Lai Châu", "014": "Sơn La", "015": "Yên Bái",
    "017": "Hoà Bình", "019": "Thái Nguyên", "020": "Lạng Sơn", "022": "Quảng Ninh", "024": "Bắc Giang",
    "025": "Phú Thọ", "026": "Vĩnh Phúc", "027": "Bắc Ninh", "030": "Hải Dương", "031": "Hải Phòng",
    "033": "Hưng Yên", "034": "Thái Bình", "035": "Hà Nam", "036": "Nam Định", "037": "Ninh Bình",
    "038": "Thanh Hóa", "040": "Nghệ An", "042": "Hà Tĩnh", "044": "Quảng Bình", "045": "Quảng Trị",
    "046": "Thừa Thiên Huế", "048": "Đà Nẵng", "049": "Quảng Nam", "051": "Quảng Ngãi", "052": "Bình Định",
    "054": "Phú Yên", "056": "Khánh Hòa", "058": "Ninh Thuận", "060": "Bình Thuận", "062": "Kon Tum",
    "064": "Gia Lai", "066": "Đắk Lắk", "067": "Đắk Nông", "068": "Lâm Đồng", "070": "Bình Phước",
    "072": "Tây Ninh", "074": "Bình Dương", "075": "Đồng Nai", "077": "Bà Rịa - Vũng Tàu", "079": "TP. Hồ Chí Minh",
    "080": "Long An", "082": "Tiền Giang", "083": "Bến Tre", "084": "Trà Vinh", "086": "Sóc Trăng",
    "087": "Đồng Tháp", "089": "An Giang", "091": "Kiên Giang", "092": "Cần Thơ", "094": "Cà Mau"
}

GENDER_CENTURY_MAP = {
    0: ("Nam", "20xx"), 1: ("Nữ", "20xx"), 
    2: ("Nam", "21xx"), 3: ("Nữ", "21xx"),
    4: ("Nam", "22xx"), 5: ("Nữ", "22xx"),
    6: ("Nam", "23xx"), 7: ("Nữ", "23xx"),
    8: ("Nam", "24xx"), 9: ("Nữ", "24xx")
}

def decode_single_cccd(cccd_str):
    cccd_str = str(cccd_str).strip()
    if len(cccd_str) != 12 or not cccd_str.isdigit():
        return "Không hợp lệ", "Không rõ", "Không rõ"
    p_name = PROVINCE_DICT.get(cccd_str[0:2], "Tỉnh/Thành khác")
    g_code = int(cccd_str[2])
    gender, century = GENDER_CENTURY_MAP.get(g_code, ("Không rõ", "Không rõ"))
    birth_two = cccd_str[3:5]
    return p_name, gender, f"{birth_two} ({century})"

# --- QUẢN LÝ SESSION STATE ---
if 'df_master' not in st.session_state:
    st.session_state.df_master = None
if 'master_cccd_col' not in st.session_state:
    st.session_state.master_cccd_col = None

# --- UPLOAD FILE ---
st.markdown("---")
col_up1, col_up2 = st.columns(2)

with col_up1:
    uploaded_master = st.file_uploader("1️⃣ Chọn file Dữ Liệu Gốc (Master DB)", type=["xlsx", "xls", "csv"], key="master_upload")
    if uploaded_master is not None:
        filename = uploaded_master.name.lower()
        df = pd.read_csv(uploaded_master, dtype=str) if filename.endswith('.csv') else pd.read_excel(uploaded_master, dtype=str)
        df = clean_columns(df)
        col_found = find_cccd_column(df.columns)
        if col_found:
            df[col_found] = df[col_found].str.strip()
            df = df.drop_duplicates(subset=[col_found], keep='last')
            st.session_state.df_master = df
            st.session_state.master_cccd_col = col_found

with col_up2:
    uploaded_search = st.file_uploader("2️⃣ Chọn file Cần Tra Cứu / Đối Chiếu", type=["xlsx", "xls", "csv"], key="search_upload")

if st.session_state.df_master is not None:
    st.success(f"⚡ Đã nạp dữ liệu gốc thành công | Tổng bản ghi: **{len(st.session_state.df_master):,}**")
    
    if uploaded_search is not None:
        try:
            filename_s = uploaded_search.name.lower()
            df_input = pd.read_csv(uploaded_search, dtype=str) if filename_s.endswith('.csv') else pd.read_excel(uploaded_search, dtype=str)
            df_input = clean_columns(df_input)
            
            tab1, tab2, tab3 = st.tabs(["🔎 Tra Cứu Thủ Công & Giải Mã", "📁 Đối Chiếu Hàng Loạt Tốc Độ Cao", "📊 Thống Kê Nhanh"])
            
            # --- TAB 1: TRA CỨU THỦ CÔNG ---
            with tab1:
                st.subheader("Tra cứu thông tin thủ công tức thì")
                search_cccd = st.text_input("Nhập số CCCD / Định danh cần tìm:", placeholder="Ví dụ: 03809xxxxxxx").strip()
                
                if st.button("Tìm Kiếm", type="primary"):
                    if not search_cccd:
                        st.warning("⚠️ Vui lòng nhập số CCCD hoặc định danh!")
                    else:
                        master_col = st.session_state.master_cccd_col
                        # Dùng boolean indexing cực nhanh của Pandas
                        result = st.session_state.df_master[st.session_state.df_master[master_col] == search_cccd]
                        
                        if not result.empty:
                            st.success(f"✅ Tìm thấy thông tin cho số: **{search_cccd}**")
                            st.dataframe(result, use_container_width=True)
                            
                            prov, gend, dob = decode_single_cccd(search_cccd)
                            st.info(
                                f"🔮 **Thông tin bóc tách tự động:**\n\n"
                                f"- **Quê quán:** {prov}\n"
                                f"- **Giới tính:** {gend}\n"
                                f"- **Năm/Thế kỷ sinh:** {dob}"
                            )
                        else:
                            st.error(f"❌ Không tìm thấy số: **{search_cccd}**")
                            
                            # Tối ưu Fuzzy Search: Chỉ lấy tối đa 5,000 dòng đầu để gợi ý nhanh, tránh đơ app
                            all_cccds = st.session_state.df_master[master_col].astype(str).head(5000).tolist()
                            close_matches = difflib.get_close_matches(search_cccd, all_cccds, n=3, cutoff=0.7)
                            if close_matches:
                                st.warning("💡 **Gợi ý các số gần giống:**")
                                for match in close_matches:
                                    if st.button(f"🔍 Tra cứu: {match}", key=f"fuzzy_{match}"):
                                        s_res = st.session_state.df_master[st.session_state.df_master[master_col] == match]
                                        st.dataframe(s_res, use_container_width=True)

            # --- TAB 2: ĐỐI CHIẾU HÀNG LOẠT (VECTORIZED MERGE) ---
            with tab2:
                st.subheader("Đối chiếu danh sách tự động (Tốc độ tối đa)")
                
                input_cccd_col = find_cccd_column(df_input.columns)
                if input_cccd_col:
                    match_col_input = input_cccd_col
                    st.info(f"💡 Tự động chọn cột đối chiếu: **[{input_cccd_col}]**")
                else:
                    match_col_input = st.selectbox("Chọn cột đối chiếu trong File Tra Cứu:", list(df_input.columns))
                
                if st.button("🚀 Chạy Đối Chiếu Siêu Tốc", type="primary"):
                    with st.spinner("Đang xử lý bằng thuật toán Vectorized Merge..."):
                        t_start = time.time()
                        
                        df_input_temp = df_input.copy()
                        df_input_temp[match_col_input] = df_input_temp[match_col_input].astype(str).str.strip()
                        
                        master_col = st.session_state.master_cccd_col
                        
                        # Sử dụng pd.merge tối ưu hóa tầng C
                        df_result = pd.merge(
                            df_input_temp,
                            st.session_state.df_master,
                            left_on=match_col_input,
                            right_on=master_col,
                            how='left',
                            suffixes=('_Input', '_Master')
                        )
                        
                        matched_mask = df_result[master_col].notna()
                        df_result['Trạng_Thái_Kết_Quả'] = "Không có kết quả tra cứu"
                        df_result.loc[matched_mask, 'Trạng_Thái_Kết_Quả'] = "Có trong hệ thống"
                        
                        t_end = time.time()
                        st.success(f"✅ Hoàn thành đối chiếu trong vòng **{t_end - t_start:.2f} giây**!")
                        st.dataframe(df_result.head(100), use_container_width=True) 
                        
                        output_filename = "Ket_Qua_Doi_Chieu_HyperSpeed.xlsx"
                        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                            df_result.to_excel(writer, index=False, sheet_name='KetQua')
                            worksheet = writer.sheets['KetQua']
                            for col_idx, col_name in enumerate(df_result.columns, 1):
                                if any(k in str(col_name).lower() for k in ['cccd', 'định danh', 'dinh danh', 'cmnd']):
                                    for row_idx in range(2, len(df_result) + 2):
                                        worksheet.cell(row=row_idx, column=col_idx).number_format = '@'
                        
                        with open(output_filename, "rb") as f:
                            st.download_button(
                                label="📥 Tải Xuống File Kết Quả (Khóa định dạng Text)",
                                data=f,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )

            # --- TAB 3: THỐNG KÊ NHANH ---
            with tab3:
                st.subheader("📊 Thống kê dữ liệu tối ưu hóa")
                if st.button("Chạy Thống Kê Nhanh"):
                    with st.spinner("Đang tính toán..."):
                        master_col = st.session_state.master_cccd_col
                        sample_series = st.session_state.df_master[master_col].dropna().astype(str)
                        
                        # Tối ưu hóa bằng cách xử lý slice string hàng loạt thay vì loop chậm
                        p_codes = sample_series.str[:2]
                        g_codes = sample_series.str[2].apply(lambda x: int(x) if str(x).isdigit() else -1)
                        
                        provinces = p_codes.map(PROVINCE_DICT).fillna('Khác')
                        genders = g_codes.map(lambda x: GENDER_CENTURY_MAP.get(x, ("Không rõ", ""))[0])
                        
                        df_stats_prov = pd.DataFrame({'Tỉnh_Thành': provinces}).value_counts().reset_index(name='Số_Lượng')
                        df_stats_gend = pd.DataFrame({'Giới_Tính': genders}).value_counts().reset_index(name='Số_Lượng')
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("##### 📍 Phân bố Tỉnh/Thành")
                            st.dataframe(df_stats_prov, use_container_width=True)
                        with col2:
                            st.markdown("##### 🚻 Phân bố Giới tính")
                            st.dataframe(df_stats_gend, use_container_width=True)
                            
        except Exception as e:
            st.error(f"❌ Lỗi xử lý: {e}")
    else:
        st.info("💡 Vui lòng upload file cần tra cứu ở ô **2️⃣** để mở khóa các tính năng.")
else:
    st.info("💡 Vui lòng upload file Dữ Liệu Gốc (Master DB) ở ô **1️⃣** để bắt đầu.")
