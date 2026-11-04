import streamlit as st
import pandas as pd
import time
import difflib

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Hệ Thống Tra Cứu & Trí Tuệ Định Danh - Argon Ultimate",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Hệ Thống Tra Cứu, Đối Chiếu & Giải Mã Định Danh (Argon Ultimate)")
st.markdown("Tích hợp **Vectorized Merge**, **Smart Fuzzy Search**, **CCCD Decoder** và cơ chế lưu trữ phiên làm việc chống mất dữ liệu trên Cloud.")

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

# --- HÀM BÓC TÁCH THÔNG TIN CCCD 12 SỐ (ĐẶC QUYỀN VIỆT NAM) ---
def decode_cccd_info(cccd_str):
    cccd_str = str(cccd_str).strip()
    if len(cccd_str) != 12 or not cccd_str.isdigit():
        return "Không hợp lệ", "Không rõ", "Không rõ"
    
    # Mã tỉnh/thành (2 số đầu)
    province_dict = {
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
    
    p_code = cccd_str[0:2]
    province_name = province_dict.get(p_code, "Tỉnh/Thành khác")
    
    # Giới tính & Thế kỷ (ký tự thứ 3)
    g_code = int(cccd_str[2])
    gender_map = {
        0: ("Nam", "20xx"), 1: ("Nữ", "20xx"), 
        2: ("Nam", "21xx"), 3: ("Nữ", "21xx"),
        4: ("Nam", "22xx"), 5: ("Nữ", "22xx"),
        6: ("Nam", "23xx"), 7: ("Nữ", "23xx"),
        8: ("Nam", "24xx"), 9: ("Nữ", "24xx")
    }
    gender, century = gender_map.get(g_code, ("Không rõ", "Không rõ"))
    
    birth_two = cccd_str[3:5]
    return province_name, gender, f"{birth_two} ({century})"

# --- QUẢN LÝ SESSION STATE ĐỂ CHỐNG MẤT DỮ LIỆU KHI REFRESH TAB ---
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
    st.success(f"⚡ Hệ thống đã sẵn sàng dữ liệu gốc | Tổng bản ghi lưu trữ: **{len(st.session_state.df_master):,}**")
    
    if uploaded_search is not None:
        try:
            filename_s = uploaded_search.name.lower()
            df_input = pd.read_csv(uploaded_search, dtype=str) if filename_s.endswith('.csv') else pd.read_excel(uploaded_search, dtype=str)
            df_input = clean_columns(df_input)
            
            tab1, tab2, tab3 = st.tabs(["🔎 Tra Cứu Thủ Công & Giải Mã", "📁 Đối Chiếu Hàng Loạt Tốc Độ Cao", "📊 Phân Tích Dữ Liệu Thông Minh"])
            
            # --- TAB 1: TRA CỨU THỦ CÔNG & GIẢI MÃ ---
            with tab1:
                st.subheader("Tra cứu thông tin thủ công & Trí tuệ định danh")
                search_cccd = st.text_input("Nhập số CCCD / Định danh cần tìm:", placeholder="Ví dụ: 03809xxxxxxx").strip()
                
                if st.button("Tra Cứu & Giải Mã", type="primary"):
                    if not search_cccd:
                        st.warning("⚠️ Vui lòng nhập số CCCD hoặc số định danh!")
                    else:
                        master_col = st.session_state.master_cccd_col
                        result = st.session_state.df_master[st.session_state.df_master[master_col] == search_cccd]
                        
                        if not result.empty:
                            st.success(f"✅ Tìm thấy thông tin chính xác cho số: **{search_cccd}**")
                            st.dataframe(result, use_container_width=True)
                            
                            # Giải mã thông tin thông minh từ CCCD
                            prov, gend, dob = decode_cccd_info(search_cccd)
                            st.info(
                                f"🔮 **Phân tích thông tin định danh tự động từ số CCCD:**\n\n"
                                f"- **Nơi đăng ký khai sinh / Quê quán:** {prov}\n"
                                f"- **Giới tính dự kiến:** {gend}\n"
                                f"- **Thế kỷ / Thập kỷ sinh:** {dob}"
                            )
                        else:
                            st.error(f"❌ Không tìm thấy chính xác số: **{search_cccd}**")
                            
                            # TÍNH NĂNG TIẾN TIẾN: FUZZY SEARCH GỢI Ý KHI GÕ SAI
                            all_cccds = st.session_state.df_master[master_col].astype(str).tolist()
                            close_matches = difflib.get_close_matches(search_cccd, all_cccds, n=3, cutoff=0.6)
                            if close_matches:
                                st.warning("💡 **Hệ thống thông minh gợi ý các số gần giống (có thể bạn nhập sai 1-2 ký tự):**")
                                for match in close_matches:
                                    if st.button(f"🔍 Tra cứu gợi ý: {match}", key=f"fuzzy_{match}"):
                                        s_res = st.session_state.df_master[st.session_state.df_master[master_col] == match]
                                        st.dataframe(s_res, use_container_width=True)

            # --- TAB 2: ĐỐI CHIẾU HÀNG LOẠT ---
            with tab2:
                st.subheader("Đối chiếu danh sách tự động (Vectorized Merge tốc độ cao)")
                
                input_cccd_col = find_cccd_column(df_input.columns)
                if input_cccd_col:
                    match_col_input = input_cccd_col
                    st.info(f"💡 Đã tự động nhận diện cột đối chiếu: **[{input_cccd_col}]**")
                else:
                    match_col_input = st.selectbox("Chọn cột CCCD/Định danh trong File Tra Cứu:", list(df_input.columns))
                
                if st.button("🚀 Chạy Đối Chiếu Siêu Tốc", type="primary"):
                    with st.spinner("Đang chạy thuật toán hợp nhất dữ liệu..."):
                        t_start = time.time()
                        
                        df_input_temp = df_input.copy()
                        df_input_temp[match_col_input] = df_input_temp[match_col_input].astype(str).str.strip()
                        
                        master_col = st.session_state.master_cccd_col
                        df_result = pd.merge(
                            df_input_temp,
                            st.session_state.df_master,
                            left_on=match_col_input,
                            right_on=master_col,
                            how='left',
                            suffixes=('_Input', '_Dữ_Liệu_Gốc')
                        )
                        
                        matched_mask = df_result[master_col].notna()
                        df_result['Trạng_Thái_Kết_Quả'] = "Không có kết quả tra cứu"
                        df_result.loc[matched_mask, 'Trạng_Thái_Kết_Quả'] = "Có trong hệ thống"
                        
                        t_end = time.time()
                        st.success(f"✅ Hoàn thành đối chiếu trong vòng **{t_end - t_start:.2f} giây**!")
                        st.dataframe(df_result.head(100), use_container_width=True) 
                        
                        output_filename = "Ket_Qua_Doi_Chieu_Argon.xlsx"
                        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                            df_result.to_excel(writer, index=False, sheet_name='KetQua')
                            worksheet = writer.sheets['KetQua']
                            for col_idx, col_name in enumerate(df_result.columns, 1):
                                if any(k in str(col_name).lower() for k in ['cccd', 'định danh', 'dinh danh', 'cmnd']):
                                    for row_idx in range(2, len(df_result) + 2):
                                        worksheet.cell(row=row_idx, column=col_idx).number_format = '@'
                        
                        with open(output_filename, "rb") as f:
                            st.download_button(
                                label="📥 Tải Xuống File Kết Quả (Khóa định dạng Text chuẩn)",
                                data=f,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )

            # --- TAB 3: PHÂN TÍCH DỮ LIỆU THÔNG MINH ---
            with tab3:
                st.subheader("📊 Bảng điều khiển phân tích thông tin định danh")
                if st.button("Chạy Thống Kê Dữ Liệu Tra Cứu"):
                    master_col = st.session_state.master_cccd_col
                    valid_series = st.session_state.df_master[master_col].dropna().astype(str)
                    
                    provinces = []
                    genders = []
                    for cccd in valid_series:
                        prov, gend, _ = decode_cccd_info(cccd)
                        provinces.append(prov)
                        genders.append(gend)
                        
                    df_stats_prov = pd.DataFrame({'Tỉnh_Thành': provinces}).value_counts().reset_index(name='Số_Lượng')
                    df_stats_gend = pd.DataFrame({'Giới_Tính': genders}).value_counts().reset_index(name='Số_Lượng')
                    
                    col_st1, col_st2 = st.columns(2)
                    with col_st1:
                        st.markdown("##### 📍 Phân bố theo Tỉnh/Thành phố")
                        st.dataframe(df_stats_prov, use_container_width=True)
                    with col_st2:
                        st.markdown("##### 🚻 Phân bố theo Giới tính dự kiến")
                        st.dataframe(df_stats_gend, use_container_width=True)
                        
        except Exception as e:
            st.error(f"❌ Lỗi xử lý file tra cứu: {e}")
    else:
        st.info("💡 Vui lòng upload thêm file cần tra cứu ở mục **2️⃣** phía trên để mở khóa các tab tính năng.")
else:
    st.info("💡 Vui lòng upload file Dữ Liệu Gốc (Master DB) ở ô **1️⃣** để bắt đầu khởi tạo hệ thống.")
