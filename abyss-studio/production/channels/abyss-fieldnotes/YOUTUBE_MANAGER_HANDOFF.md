# Abyss Fieldnotes · Bàn giao quản lý kênh YouTube

Ngày 21/11/2026, chủ kênh xác nhận phần Abyss đang ổn. Mở **Quản lý kênh YouTube** từ màn hình chính để xem **Tổng quan**. Mục **Kết nối** dùng để thêm kênh, thiết lập OAuth và bật vidIQ. Cổng chính 4320 đã phục vụ trực tiếp giao diện và API nhiều kênh. [Mở trang quản lý trên PC](http://127.0.0.1:4320/fieldnotes?panel=youtube) · [Ảnh màn hình đã kiểm](evidence/youtube-manager-2026-11-21.png)

## Trạng thái khi bàn giao

- Lúc 14:58 giờ Việt Nam, API cục bộ trả về đúng mã Abyss Fieldnotes `UC0HHGW2X_MPmuB8CQ_HzV_Q`. Bản đo lúc 13:42 ghi nhận **199 lượt xem tích lũy trên 5 video theo dõi**. Đây là mốc đối chiếu có ngày giờ. [Biên bản kiểm giao diện](evidence/youtube-manager-ui-2026-11-21.json)
- PC đã lưu file OAuth (`configured=true`). Kênh đang chờ chủ kênh chọn **Xác nhận với Google** (`authorized=false`). Không có lượt chờ đang chạy. Sau khi chủ kênh xác nhận, kiểm mã kênh đã chọn, quyền đã lưu và thời điểm Analytics nhận số liệu. Luồng Analytics riêng đã qua kiểm thử bằng dữ liệu mô phỏng. [Biên bản OAuth nhiều kênh](evidence/youtube-multichannel-vidiq-2026-11-21.json)
- Lịch Windows `Abyss Fieldnotes Daily Analytics` đặt lúc **08:00** theo giờ PC. Lần kiểm ghi nhận `LastTaskResult=0`. vidIQ đang tắt cho Abyss. Nếu chủ kênh bật bằng API key chỉ đọc, worker lưu biên nhận theo kênh và ngày trước khi gọi công cụ thống kê. [Mã tích hợp vidIQ](../../../scripts/vidiq_mcp.py)

## Khi có lỗi

| Triệu chứng | Kiểm tra đầu tiên |
| --- | --- |
| Mở app mà chưa thấy số liệu | Vào trang quản lý ở trên và chọn **Tổng quan**. Nếu cổng 4320 chưa trả lời, mở Abyss Studio bằng `abyss-studio/Open-Abyss.cmd`. Nếu API đã có số liệu mà màn hình trống, kiểm tra mục điều hướng và phần hiển thị. [Điều hướng chính](../../../public/native.html) · [Giao diện báo cáo](../../../public/fieldnotes.html) · [Logic hiển thị](../../../public/youtube-panel.js) |
| Đã nhập JSON, hoặc đã đóng cửa sổ Google | Xem `configured`, `authorized`, `authorization` và `busy` trong API trạng thái. Với file đã lưu, dùng **Xác nhận với Google**. Khi lượt chờ còn hoạt động, dùng **Mở lại Google** hoặc **Hủy chờ**. [Điều phối lượt chờ](../../../lib/youtube-dashboard.js) · [Callback và kho quyền Windows](../../../scripts/youtube_account.py) · [Biên bản kiểm hủy và thử lại](evidence/oauth-wait-recovery-2026-11-21.json) |
| Đổi kênh thấy số liệu cũ, thiếu giờ xem hoặc ngày báo cáo sai | So `channel` ở trạng thái với `channelId` trong báo cáo cùng ngày. Xem `source`, `public.checked`, `statisticsAt`, `analyticsAt` và thông báo API. Bản mới nhất của Abyss ở `data/fieldnotes-daily/latest.json`. Kênh bổ sung có thư mục riêng theo mã. [Worker hằng ngày](../../../scripts/fieldnotes-daily.py) · [Truy vấn Analytics và Reach](../../../scripts/youtube_reports.py) |
| Bấm **Hiện trong thư mục** hoặc **Chép đường dẫn MP4** gặp lỗi | Dùng đường dẫn master của tập trong biên bản để đối chiếu file trên PC với đường dẫn giao diện gửi lên. [Biên bản kiểm các MP4](evidence/youtube-api-and-render-files-2026-11-21.json) · [Nút trên giao diện](../../../public/render-file.js) · [Mở file trong Explorer](../../../lib/render-file.js) |

Từ `E:\YOUTUBE`, dùng PowerShell để đọc trạng thái và báo cáo đang lưu. Hai lệnh GET này không khởi động đồng bộ hay mở Google.

```powershell
$channelId = 'UC0HHGW2X_MPmuB8CQ_HzV_Q'
$api = 'http://127.0.0.1:4320/api/studio/youtube'
Invoke-RestMethod "${api}?channel=$channelId" | Select-Object channel,configured,authorized,busy,authorization,vidiqEnabled
Invoke-RestMethod "$api/report?day=latest&channel=$channelId" | Select-Object channelId,day,source,at,statisticsAt,analyticsAt,message,analyticsMessage
```

Sau khi sửa giao diện, chạy `node abyss-studio/scripts/check-youtube-manager-ui.mjs` từ cùng thư mục. Bài kiểm tra mở Electron với hồ sơ tạm và phản hồi API mô phỏng. Nó kiểm đường vào từ màn hình chính, nhập JSON, chuyển sang kênh vừa cấp quyền, đổi ngày, phân biệt số 0 với số liệu còn thiếu và đổi kênh khi báo cáo trước trả về chậm. [Mã kiểm thử](../../../scripts/check-youtube-manager-ui.mjs)
