# Chọn kênh sản xuất

Mỗi kênh có một thư mục riêng. Mở checkpoint để biết tập nào đang làm, xem bản dựng và đọc việc cần tiếp tục. Hướng dẫn dựng nằm cạnh checkpoint.

| Tên dùng với Codex | Checkpoint | Hướng dẫn dựng |
| --- | --- | --- |
| Abyss Fieldnotes · loạt `D` | [Mở bàn giao](abyss-fieldnotes/CHECKPOINT.md) | [Dựng phim biển sâu](abyss-fieldnotes/RENDER.md) |
| Second Bell Pictures · loạt `SB` | [Mở bàn giao](second-bell/CHECKPOINT.md) | [Dựng phim truyện](second-bell/RENDER.md) |

## Gọi từ PowerShell

Mở một phiên mới từ bất kỳ thư mục nào. Đặt tên kênh ngay đầu câu. Nếu muốn một mẫu, ghi thời lượng. Nếu muốn dựng hết phim, ghi “toàn tập”. Trên máy này dùng `codex.cmd` để gọi đúng chương trình. Tham số `-C` mở workspace có hướng dẫn và tư liệu của cả hai kênh. [Tài liệu lệnh Codex CLI](https://learn.chatgpt.com/docs/developer-commands?surface=cli)

Dùng câu sau khi chỉ muốn đọc bàn giao để chuyển phiên.

```powershell
codex.cmd -C "E:\YOUTUBE" "Kênh Second Bell Pictures. Đọc checkpoint, cho tôi xem bản mẫu mới nhất và cho biết đang chờ tôi duyệt gì."
```

Dùng câu sau để kiểm gói đăng của một tập đã dựng.

```powershell
codex.cmd -C "E:\YOUTUBE" "Kênh Abyss Fieldnotes. Kiểm lại gói D004 và đưa tôi các file cần để tự đăng YouTube."
```

Khi muốn bắt đầu sản xuất, chọn một lệnh theo kênh.

```powershell
codex.cmd -C "E:\YOUTUBE" "Kênh Abyss Fieldnotes. Dựng toàn tập D005 theo brief, kiểm bản xuất và chuẩn bị gói để tôi tự đăng YouTube."
codex.cmd -C "E:\YOUTUBE" "Kênh Second Bell Pictures. Dựng toàn tập SB01 The Empty Bench, nối từ mẫu 05:00, giữ nguyên dàn nhân vật và chuẩn bị gói để tôi tự đăng YouTube."
```

## Lưu cho phiên sau

- Codex đọc `CHECKPOINT.md` và `RENDER.md` của kênh được gọi, sau đó mở kịch bản, bản dựng và hồ sơ duyệt được liên kết. Nếu người dùng chỉ ghi mã tập, chọn kênh theo tiền tố trong bảng.
- Khi có kết quả mới hoặc cần chuyển phiên, cập nhật `checkpoint.json` trong đúng thư mục kênh. Ghi ngày theo giờ địa phương, tập, quyết định của chủ kênh, phạm vi mẫu/toàn tập, trạng thái duyệt và đăng, việc tiếp theo, tệp bằng chứng và biên nhận còn mở. Đường dẫn trong JSON tính từ `abyss-studio`. Chỉ lưu mã biên nhận, trạng thái và vị trí hồ sơ cục bộ.
- Dùng `save` cho kênh vừa cập nhật. Lệnh tạo trang `CHECKPOINT.md` và giữ từng phiên bản nội dung trong `history/`, kể cả khi đang dở hoặc đang chờ Muse. Dùng `check` để đối chiếu bản bàn giao, tệp thực, SHA-256 của master có biên bản và các tệp trong manifest đã khai báo. Ghi kết quả còn thiếu vào checkpoint để người sau biết cần kiểm tiếp.
- Các script cũ của từng tập vẫn có thể cập nhật sổ kỹ thuật chung. Sau khi dùng chúng, ghi kết quả vào checkpoint của kênh đang làm. Khi mở thêm kênh, tạo thư mục cùng cấu trúc, chọn tiền tố tập riêng và thêm một hàng vào bảng trên.

Các lệnh sau đọc hoặc lưu checkpoint từ workspace.

```powershell
Set-Location 'E:\YOUTUBE'
python -X utf8 abyss-studio/scripts/channel-checkpoint.py list
python -X utf8 abyss-studio/scripts/channel-checkpoint.py show "Second Bell Pictures"
python -X utf8 abyss-studio/scripts/channel-checkpoint.py save second-bell
python -X utf8 abyss-studio/scripts/channel-checkpoint.py check second-bell
```

## Gói bàn giao để chủ kênh tự đăng YouTube

1. Giao bản MP4 cuối với hình và tiếng đã kiểm. Hai kênh dùng khung ngang. Giữ tốc độ khung hình theo nguồn và timeline đã duyệt. Với MP4 H.264, xuất progressive, âm thanh AAC-LC 48 kHz và đặt thông tin phát ở đầu file để phát qua mạng. [Thiết lập mã hóa YouTube khuyến nghị](https://support.google.com/youtube/answer/1722171?hl=en)
2. Giao tựa và mô tả tiếng Anh Mỹ có thể sao chép, thumbnail đúng nội dung và dễ đọc ở kích thước điện thoại, phụ đề tiếng Anh khớp lời nói. Thêm chương khi có ích cho tập. Liệt kê nguồn, quyền sử dụng và chọn khai báo phù hợp trong YouTube Studio với cảnh tổng hợp chân thực. [Hướng dẫn khai báo của YouTube](https://support.google.com/youtube/answer/14328491?hl=en)
3. Trên chính MP4 cuối, kiểm phát từ đầu đến cuối, khung mở/kết, điểm nối, thoại hoặc lời kể, độ lớn âm thanh, chữ và thời điểm phụ đề xuất hiện. Chạy `python -X utf8 abyss-studio/scripts/check-release-language.py "<đường dẫn thư mục delivery>"` từ workspace. Ghi kết quả, SHA-256 của master, danh sách file giao và phần chờ người duyệt.
4. Đặt link tới thư mục hoặc trang bàn giao trong checkpoint. Ghi riêng tình trạng kiểm kỹ thuật, chủ kênh duyệt và thực tế đã đăng. Khi chủ kênh xác nhận đăng, ghi URL và thời điểm. Lệnh “chuẩn bị gói để tôi tự đăng” kết thúc ở bản giao cục bộ.
