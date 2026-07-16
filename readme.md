# README dữ liệu RAND HRS Wave 16

Tài liệu này mô tả các cột trong `randhrs_muc_A_perfect_clean.csv`, dựa trên codebook `randhrs1992_2022v1.pdf` và bảng định dạng giá trị `sasfmts.sas7bdat`.

Nguồn chính:

- `randhrs1992_2022v1.pdf`: RAND HRS Longitudinal File 1992-2022, version 1.
- `sasfmts.sas7bdat`: bảng SAS format dùng để giải mã nhãn giá trị.
- `tranform.ipynb`: nơi tạo nhãn dự án `Care_Level`.

## Tổng quan file

- File dữ liệu sạch: `randhrs_muc_A_perfect_clean.csv`
- Số dòng: 9,989
- Số cột: 18
- Các biến `R16...` là biến của Respondent ở Wave 16.
- Trong nhãn RAND HRS:
  - `R` = Respondent.
  - `W16` = Wave 16.
  - `Diff` = người trả lời có khó khăn khi thực hiện hoạt động.
  - `ADL` = Activities of Daily Living, hoạt động sinh hoạt cơ bản.
  - `IADL` = Instrumental Activities of Daily Living, hoạt động sinh hoạt công cụ.

## Bảng mô tả cột

| Cột | Nhãn/ý nghĩa theo RAND HRS | Kiểu | Giá trị |
| --- | --- | --- | --- |
| `HHIDPN` | Mã định danh duy nhất của cá nhân. Dùng để merge với các file HRS/RAND HRS khác. | ID | Số định danh; nên xử lý như chuỗi/ID, không dùng như biến số học. |
| `RAGENDER` | `RAGENDER: R Gender` - giới tính của Respondent. | Phân loại | `1 = Male`, `2 = Female`. |
| `R16AGEY_M` | `R16AGEY_M: W16 R Age (years) at Ivw MidMon` - tuổi của Respondent, tính theo năm tại tháng giữa kỳ phỏng vấn Wave 16. | Liên tục | Tuổi theo năm. |
| `R16DRESS` | `R16DRESS: W16 R Diff-Dressing` - khó khăn khi mặc quần áo. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16BATH` | `R16BATH: W16 R Diff-Bathing or showering` - khó khăn khi tắm. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16EAT` | `R16EAT: W16 R Diff-Eating` - khó khăn khi ăn. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16BED` | `R16BED: W16 R Diff-Get in/out of bed` - khó khăn khi lên/xuống giường. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16TOILT` | `R16TOILT: W16 R Diff-Using the toilet` - khó khăn khi sử dụng nhà vệ sinh. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16PHONE` | `R16PHONE: W16 R Diff-Use telephone` - khó khăn khi sử dụng điện thoại. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16MONEY` | `R16MONEY: W16 R Diff-Managing money` - khó khăn khi quản lý tiền bạc. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16MEDS` | `R16MEDS: W16 R Diff-Take medications` - khó khăn khi uống/dùng thuốc. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16MEALS` | `R16MEALS: W16 R Diff-Preparing hot meals` - khó khăn khi chuẩn bị bữa ăn nóng. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16SHOP` | `R16SHOP: W16 R Diff-Shop for groceries` - khó khăn khi mua thực phẩm/nhu yếu phẩm. | Phân loại ADLA | Xem bảng mã ADLA bên dưới. |
| `R16HLPDYST` | `R16HLPDYST: W16 Total days got help last month` - tổng số ngày nhận trợ giúp trong tháng trước. | Số | Số ngày. Format gốc `AHELPMISS` có các mã missing đặc biệt; trong file sạch hiện còn giá trị số. |
| `R16HLPHRST` | `R16HLPHRST: W16 Total hours got help last month` - tổng số giờ nhận trợ giúp trong tháng trước. | Số | Số giờ. Format gốc `AHELPMISS` có các mã missing đặc biệt; trong file sạch hiện còn giá trị số. |
| `R16ADL5A` | `R16ADL5A: W16 Any Diff-sum of ADLs /0-5` - tổng số ADL có bất kỳ khó khăn nào. | Số đếm | Từ `0` đến `5`. |
| `R16IADL5A` | `R16IADL5A: W16 Any Diff-sum of IADLs /0-5` - tổng số IADL có bất kỳ khó khăn nào. | Số đếm | Từ `0` đến `5` theo codebook; trong file sạch có thể kiểm tra phân phối thực tế theo dữ liệu đã lọc. |
| `Care_Level` | Nhãn do dự án tạo thêm, không phải biến gốc RAND HRS. | Nhãn mục tiêu | `0`, `1`, `2`; xem quy tắc bên dưới. |

## Bảng mã giá trị

### `RAGENDER`

| Giá trị | Ý nghĩa |
| --- | --- |
| `1` | Male |
| `2` | Female |

### Các biến khó khăn ADL/IADL dạng `ADLA`

Áp dụng cho:

`R16DRESS`, `R16BATH`, `R16EAT`, `R16BED`, `R16TOILT`, `R16PHONE`, `R16MONEY`, `R16MEDS`, `R16MEALS`, `R16SHOP`.

| Giá trị | Ý nghĩa |
| --- | --- |
| `0` | No - không có khó khăn. |
| `1` | Yes - có khó khăn. |
| `2` | Can't do - không thể làm. |
| `7` | Don't do - không làm hoạt động đó. |

Trong SAS format gốc còn có các mã missing đặc biệt như `.D = DK`, `.R = RF`, `.M = Oth missing`, `.Q = Not asked this wave`, `.X = Don't do`, `.Z = Don't do/No if did`. Các mã này không xuất hiện trong file CSV sạch hiện tại.

### `R16HLPDYST` và `R16HLPHRST`

Hai cột này dùng format gốc `AHELPMISS` trong RAND HRS. File sạch hiện lưu giá trị số:

- `R16HLPDYST`: số ngày nhận trợ giúp trong tháng trước.
- `R16HLPHRST`: số giờ nhận trợ giúp trong tháng trước.

Trong format gốc có các mã missing đặc biệt. Nếu gặp các mã này trong file SAS gốc, không nên hiểu là số ngày/số giờ thật:

| Mã | Nhãn gốc | Ý nghĩa dễ hiểu |
| --- | --- | --- |
| `.D` | DK | Respondent không biết hoặc không nhớ câu trả lời. |
| `.F` | No FamR | Không có người trả lời thay/đại diện trong phần câu hỏi gia đình. |
| `.H` | No Helpers | Không có người trợ giúp, nên câu hỏi về số ngày/giờ trợ giúp không áp dụng. |
| `.J` | Web interview, missing | Phỏng vấn qua web nhưng câu trả lời bị thiếu. |
| `.M` | Other missing | Thiếu dữ liệu vì lý do khác, không thuộc các nhóm missing cụ thể. |
| `.N` | NA | Không có thông tin/câu trả lời không khả dụng. |
| `.Q` | Not asked this wave | Câu hỏi không được hỏi trong wave này. |
| `.R` | RF | Respondent từ chối trả lời. |
| `.U` | Unmarried | Không có vợ/chồng/bạn đời trong mẫu câu hỏi liên quan đến spouse. |
| `.V` | Spouse NR | Vợ/chồng/bạn đời không trả lời. |
| `.X` | Inapplicable | Không áp dụng cho trường hợp của Respondent. |
| `.Y` | Alternate wave | Respondent thuộc wave/phân nhóm phỏng vấn thay thế, nên biến này không được hỏi theo cách thông thường. |

## Nhóm biến

### Định danh và nhân khẩu học

- `HHIDPN`: khóa cá nhân để quản lý record và merge dữ liệu.
- `RAGENDER`: giới tính.
- `R16AGEY_M`: tuổi tại Wave 16.

### ADL cơ bản

Các biến này phản ánh khó khăn trong hoạt động sinh hoạt cơ bản:

- `R16DRESS`: mặc quần áo.
- `R16BATH`: tắm.
- `R16EAT`: ăn.
- `R16BED`: lên/xuống giường.
- `R16TOILT`: sử dụng nhà vệ sinh.

`R16ADL5A` là tổng số ADL trong 5 hoạt động trên mà Respondent có bất kỳ khó khăn nào.

### IADL công cụ

Các biến này phản ánh khó khăn trong hoạt động sinh hoạt công cụ:

- `R16PHONE`: sử dụng điện thoại.
- `R16MONEY`: quản lý tiền bạc.
- `R16MEDS`: dùng thuốc.
- `R16MEALS`: chuẩn bị bữa ăn nóng.
- `R16SHOP`: mua thực phẩm/nhu yếu phẩm.

`R16IADL5A` là tổng số IADL trong 5 hoạt động trên mà Respondent có bất kỳ khó khăn nào.

### Khối lượng trợ giúp

- `R16HLPDYST`: tổng số ngày nhận trợ giúp trong tháng trước.
- `R16HLPHRST`: tổng số giờ nhận trợ giúp trong tháng trước.

## Quy tắc tạo `Care_Level`

`Care_Level` được tạo trong `tranform.ipynb` từ hai biến tổng hợp `R16ADL5A` và `R16IADL5A`:

| Giá trị | Tên gợi ý | Quy tắc |
| --- | --- | --- |
| `0` | Độc lập | `R16ADL5A == 0` và `R16IADL5A == 0`. |
| `2` | Phụ thuộc cao | `R16ADL5A >= 3`. |
| `1` | Phụ thuộc một phần | Các trường hợp còn lại. |

Lưu ý: `Care_Level` là nhãn do dự án định nghĩa để phục vụ phân tích/huấn luyện mô hình, không phải biến có sẵn trong codebook RAND HRS.
