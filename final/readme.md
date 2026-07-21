# README dữ liệu RAND HRS Wave 16

Tài liệu này mô tả các cột trong `randhrs_muc_A_perfect_clean.csv`, dựa trên codebook `randhrs1992_2022v1.pdf` và bảng định dạng giá trị `sasfmts.sas7bdat`.

Nguồn chính:

- `randhrs1992_2022v1.pdf`: RAND HRS Longitudinal File 1992-2022, version 1.
- `sasfmts.sas7bdat`: bảng SAS format dùng để giải mã nhãn giá trị.
- `tranform.ipynb`: nơi tạo nhãn dự án `Care_Level`.

## Tổng quan file

- File dữ liệu sạch: `randhrs_muc_A_perfect_clean.csv`
- Số dòng: 9,989
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

### Mã định danh và Nhân khẩu học (Identifiers & Demographics)

- **`HHIDPN`**: Mã định danh duy nhất của mỗi cá nhân trong bộ dữ liệu. Nó được tạo ra bằng cách kết hợp mã hộ gia đình (HHID) và số thứ tự cá nhân (PN) theo công thức `1000 × HHID + PN`.
- **`RAGENDER`**: Giới tính của người trả lời. Giá trị: `1` = Nam (Male), `2` = Nữ (Female).
- **`R16AGEY_M`**: Tuổi của người trả lời (tính bằng năm) tại thời điểm giữa của tháng phỏng vấn Đợt 16 (Wave 16). Đây là một biến dạng số liên tục (Continuous).

### Core A: Khó khăn ADL & IADL chi tiết

Nhóm biến này đánh giá mức độ khó khăn khi tự thực hiện các **Hoạt động Sống hàng ngày (ADL)** và **Hoạt động Sống hàng ngày có Dụng cụ (IADL)** do vấn đề sức khỏe. Các giá trị cơ bản bao gồm `0` (Không có khó khăn), `1` (Có khó khăn), `2` (Không thể làm), `7` (Không làm), cùng với các mã khuyết (missing) như `.D` (Không biết), `.R` (Từ chối) và `.S` (Bỏ qua câu hỏi).

- **`R16DRESS`**: Khó khăn khi tự mặc quần áo.
- **`R16BATH`**: Khó khăn khi tự tắm rửa.
- **`R16EAT`**: Khó khăn khi tự ăn uống.
- **`R16BED`**: Khó khăn khi tự ra/vào giường.
- **`R16TOILT`**: Khó khăn khi tự sử dụng nhà vệ sinh.
- **`R16WALK1`**: Khó khăn khi đi bộ một dãy nhà (khoảng 1 block).
- **`R16PHONE`**: Khó khăn khi sử dụng điện thoại.
- **`R16MONEY`**: Khó khăn khi tự quản lý tiền bạc (ví dụ: thanh toán hóa đơn, theo dõi chi tiêu).
- **`R16MEDS`**: Khó khăn khi dùng thuốc đúng theo hướng dẫn.
- **`R16MEALS`**: Khó khăn khi tự chuẩn bị bữa ăn nóng.
- **`R16SHOP`**: Khó khăn khi đi mua sắm tạp hóa.

### Core B & C: Thần kinh & Lâm sàng nguy kịch

Nhóm này đánh giá các dấu hiệu suy giảm nhận thức, các bệnh lý nghiêm trọng và đo lường thể chất thực tế.

- **`R16WANDER`**: Người trả lời có từng đi lang thang và không thể tự về được không. Giá trị: `0` = Không, `1` = Có.
- **`R16LOST`**: Người trả lời có từng bị lạc trong môi trường quen thuộc không. Giá trị: `0` = Không, `1` = Có.
- **`R16HALUC`**: Người trả lời có bị ảo giác (nhìn/nghe thấy những thứ không có thật) không. Giá trị: `0` = Không, `1` = Có.
- **`R16DEMEN`**: Báo cáo có mắc bệnh sa sút trí tuệ (Dementia) ở đợt khảo sát này. Giá trị: `0` = Không, `1` = Có.
- **`R16ALZHE`**: Báo cáo có mắc bệnh Alzheimer ở đợt khảo sát này. Giá trị: `0` = Không, `1` = Có, `7` = Bệnh khác không phải Alzheimer.
- **`REBEDRID`**: Tình trạng phải nằm liệt giường vào khoảng thời gian trước khi qua đời (lấy từ dữ liệu cuộc phỏng vấn sau khi qua đời - Exit Interview).
- **`R16STROK`**: Báo cáo có bị đột quỵ. Giá trị: `0` = Không, `1` = Có, `2` = Cơn thiếu máu não thoáng qua (TIA) hoặc nghi ngờ đột quỵ.
- **`R16SDAPNEA`**: Báo cáo có được chẩn đoán mắc chứng ngưng thở khi ngủ (Sleep apnea). Giá trị: `0` = Không, `1` = Có.
- **`R16TIMWLK`**: Bài kiểm tra đi bộ tính thời gian trong phần đo lường thể chất tại nhà. Biến này ghi lại số giây tối thiểu để người trả lời đi bộ quãng đường 98.5 inch với tốc độ bình thường.
- **`R16BALSEMI`**: Đo lường thể chất về thăng bằng - bài kiểm tra đứng kiểu semi-tandem.
- **`R16BALFUL`**: Đo lường thể chất về thăng bằng - bài kiểm tra đứng kiểu full-tandem.

### Core D: Tâm trạng (Trầm cảm chi tiết)

Các biến này dựa trên thang đo trầm cảm **CES-D**, hỏi xem người trả lời có cảm thấy một trạng thái cụ thể *"phần lớn thời gian trong tuần trước cuộc phỏng vấn"* hay không. Các giá trị thường là `0` = Không, `1` = Có.

- **`R16DEPRES`**: Cảm thấy chán nản/trầm cảm.
- **`R16EFFORT`**: Cảm thấy mọi việc làm đều cần phải nỗ lực/cố gắng.
- **`R16SLEEPR`**: Giấc ngủ bị trằn trọc/không yên giấc.
- **`R16FLONE`**: Cảm thấy cô đơn.
- **`R16FSAD`**: Cảm thấy buồn bã.
- **`R16GOING`**: Cảm thấy không có động lực/không thể bắt đầu làm việc gì.
- **`R16WHAPPY`**: Cảm thấy vui vẻ *(câu hỏi tích cực dùng để đảo ngược điểm khi tính tổng CESD)*.
- **`R16ENLIFE`**: Cảm thấy tận hưởng cuộc sống *(câu hỏi tích cực)*.

### Biến nền tổng hợp

Nhóm này chứa các chỉ số tóm tắt đã được tính toán sẵn về mức độ suy giảm chức năng, sức khỏe tâm thần và tình trạng tài chính.

- **`R16ADL5A`**: Chỉ số tổng hợp đánh giá có bất kỳ khó khăn nào trong 5 hoạt động ADL cốt lõi (tắm, ăn, mặc quần áo, đi lại trong phòng, ra/vào giường). Giá trị: `0` = Không có khó khăn, `1–5` = Số ADL có khó khăn.
- **`R16IADL5A`**: Chỉ số tổng hợp đánh giá có bất kỳ khó khăn nào trong 5 hoạt động IADL cốt lõi (dùng điện thoại, uống thuốc, quản lý tiền, mua sắm, chuẩn bị bữa ăn). Giá trị: `0` = Không, `1–5` = Số IADL có khó khăn.
- **`R16CESD`**: Tổng điểm trầm cảm CES-D. Tính bằng cách tính tổng các câu trả lời dương tính (sau khi đảo ngược các câu hỏi tích cực) từ 8 biến tâm trạng ở Core D.
- **`H16ATOTW`**: Tổng giá trị tài sản ròng của hộ gia đình (Total Household Wealth).
- **`H16ITOT`**: Tổng thu nhập của hộ gia đình (Total Household Income).
- **`H16INPOV`**: Cờ (Flag) xác định xem thu nhập của hộ gia đình có nằm dưới ngưỡng nghèo hay không.
- **`R16IEARN`**: Tổng thu nhập cá nhân từ công việc/tiền lương.
- **`R16IPEN`**: Thu nhập cá nhân từ lương hưu.
- **`R16ISRET`**: Thu nhập từ chế độ hưu trí của Bảo hiểm/An sinh Xã hội (Social Security Retirement Income).
- **`R16OOPMD`**: Tổng chi phí y tế tự bỏ tiền túi của cá nhân (Out-of-pocket Medical Expenditures).

## Quy tắc tạo `Care_Level`

`Care_Level` là nhãn do dự án định nghĩa để phục vụ phân tích/huấn luyện mô hình, không phải biến có sẵn trong codebook RAND HRS. Được tạo trong `tranform.ipynb`.

### Bảng phân loại

| Giá trị | Tên | Mô tả |
| --- | --- | --- |
| `0` | Độc lập | Không rơi vào bất kỳ điều kiện nào ở Lớp 1 hoặc Lớp 2. |
| `1` | Chăm sóc cơ bản | Khó khăn thể chất nhẹ hoặc gặp triệu chứng trầm cảm lâm sàng. |
| `2` | Chăm sóc đặc biệt | Suy giảm ADL nghiêm trọng, liệt giường, hoặc có triệu chứng thần kinh/nhận thức nặng. |

### Điều kiện phân loại (theo thứ tự ưu tiên)

```python
conditions = [
    # Lớp 2 mới: Chăm sóc đặc biệt (Bao gồm cả nguy kịch thể chất lẫn hành vi thần kinh nặng)
    (df_clean['R16ADL5A'] >= 3) | (df_clean['REBEDRID'] == 1) | \
    (df_clean['R16WANDER'] == 1) | (df_clean['R16DEMEN'] == 1) | (df_clean['R16ALZHE'] == 1) | (df_clean['R16HALUC'] == 1),

    # Lớp 1: Khó khăn thể chất nhẹ hoặc gặp triệu chứng trầm cảm lâm sàng
    (df_clean['R16ADL5A'] > 0) | (df_clean['R16IADL5A'] > 0) | (df_clean['R16CESD'] >= 4)
]
```

### Giải thích chi tiết từng điều kiện

**Lớp 2 — Chăm sóc đặc biệt** (ưu tiên kiểm tra trước):

| Điều kiện | Biến | Ý nghĩa |
| --- | --- | --- |
| `R16ADL5A >= 3` | Tổng ADL | Có từ 3 trở lên trong 5 ADL cốt lõi bị suy giảm — mức phụ thuộc thể chất nghiêm trọng. |
| `REBEDRID == 1` | Liệt giường | Người trả lời nằm liệt giường trước khi qua đời (Exit Interview). |
| `R16WANDER == 1` | Lang thang | Có hành vi đi lang thang không về được — dấu hiệu mất định hướng nặng. |
| `R16DEMEN == 1` | Sa sút trí tuệ | Được chẩn đoán hoặc báo cáo mắc chứng sa sút trí tuệ (Dementia). |
| `R16ALZHE == 1` | Alzheimer | Được chẩn đoán hoặc báo cáo mắc bệnh Alzheimer. |
| `R16HALUC == 1` | Ảo giác | Có triệu chứng ảo giác — dấu hiệu rối loạn tâm thần hoặc nhận thức nặng. |

**Lớp 1 — Chăm sóc cơ bản** (kiểm tra sau Lớp 2):

| Điều kiện | Biến | Ý nghĩa |
| --- | --- | --- |
| `R16ADL5A > 0` | Tổng ADL | Có ít nhất 1 ADL cốt lõi bị suy giảm. |
| `R16IADL5A > 0` | Tổng IADL | Có ít nhất 1 IADL cốt lõi bị suy giảm. |
| `R16CESD >= 4` | Điểm CES-D | Điểm trầm cảm CES-D >= 4 — ngưỡng lâm sàng thường dùng để xác định trầm cảm đáng kể. |

> **Lưu ý**: Các điều kiện được kiểm tra theo thứ tự ưu tiên từ Lớp 2 → Lớp 1 → Lớp 0 (mặc định). Nếu một người thỏa mãn cả điều kiện Lớp 2, họ sẽ được gán nhãn `2` bất kể có thỏa mãn điều kiện Lớp 1 hay không.
