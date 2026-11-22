# Thiết lập kênh mới: Abyss Fieldnotes

User đã giao chọn tên, avatar, banner, giới thiệu và thông tin kênh ngày 13/11/2026. Được áp dụng bộ nhận diện này lên **kênh mới đúng mục tiêu** sau khi đăng nhập; không cần hỏi lại quyền đổi từng field. Quyền upload/công khai video vẫn chưa được giao. Tình trạng thực tế ở `channel-setup.json`.

## Trạng thái đã kiểm ngày 13/11/2026

Đã tạo kênh mới, lưu tên/handle/About/avatar/banner, country Vietnam, 15 keywords, 6 upload tags, mô tả có hashtag, Private, Education và English (United States) cho video cùng tiêu đề/mô tả. Đã reload Studio để đọc lại và xem trang kênh công khai có ảnh tải xong. Kênh cũ không bị sửa; chưa upload video. Evidence: `branding/youtube-profile-receipt.json`, `branding/youtube-settings-receipt.json`, ảnh `branding/qa/`.

Standard features Enabled; Intermediate và Advanced còn Eligible. Chủ tài khoản cần hoàn thành xác minh YouTube để bật thumbnail tùy chỉnh. Chưa có email/link muốn công khai; watermark tùy chọn chưa áp dụng.

## Nội dung đã chuẩn bị

| Trường | Nội dung |
|---|---|
| Tên | **Abyss Fieldnotes** |
| Handle đã nhận | **@AbyssFieldnotesOcean**; handle ưu tiên ban đầu không khả dụng |
| Channel ID | UC0HHGW2X_MPmuB8CQ_HzV_Q |
| Quốc gia đã lưu | **Vietnam**, chủ kênh xác nhận |
| Hashtag mặc định | #DeepSea #MarineBiology #OceanScience |
| Tagline | Deep-sea stories. Clear explanations. |
| About | Dán toàn bộ `../branding/channel-about.txt` |
| Keywords | `../branding/channel-keywords.txt` |
| Avatar | `../branding/avatar-v1.png`; kiểm manifest trước upload |
| Banner | `../branding/banner-v1.png`; kiểm manifest trước upload |
| Hướng nội dung | Deep-sea science stories, 8–10 minutes, US English |

Thiết kế/giọng kể và playlist nằm trong [BRAND_GUIDE.md](../branding/BRAND_GUIDE.md). Prompt gốc và manifest nằm trong `branding/`. Không lấy ảnh đối thủ làm nhận diện kênh. Kiểm tên qua tìm kiếm công khai chưa thấy kênh trùng rõ ràng; **không phải bằng chứng handle còn trống hay kết luận về nhãn hiệu**.

## Checklist theo đúng thứ tự

1. **Login:** chủ kênh mở `Open-YouTube.cmd` và đăng nhập trong Chrome riêng. Chủ tài khoản tự xử lý OTP/xác minh nếu Google yêu cầu.
2. **Tạo/nhận diện kênh:** dùng tên trên cho kênh mới. Nếu tài khoản có kênh cũ, không tự đổi kênh cũ thành kênh mới. Đọc Channel ID, tên và URL thật; lưu binding sau khi xác định đúng kênh mới. Handle chỉ ghi là đã nhận khi UI lưu thành công.
3. **Customization → Profile:** đặt tên, handle khả dụng, About, avatar, banner. Xem crop trên mobile/desktop/TV; Publish để áp dụng nhận diện đã được user giao. Mở lại Profile và trang kênh để kiểm những gì đã lưu. Lưu receipt với channel ID, file hash và thời gian.
4. **Settings → Channel:** keywords liên quan; country theo nơi cư trú thật. Khi chưa biết quốc gia thì giữ nguyên/để chờ, không đoán từ ngôn ngữ khán giả. Audience chọn xem xét từng video; đánh giá thực tế ở mỗi lần upload.
5. **Settings → Upload defaults:** Private, language English hoặc English (United States) nếu UI có, category Education. Mô tả tập dùng template nhưng không lưu placeholder ra công khai. Đọc lại các giá trị sau Save.
6. **Feature eligibility:** ghi quyền hiện có: custom thumbnail, intermediate, advanced và thử thumbnail nếu UI hỗ trợ. User thực hiện phone/ID/video verification nếu cần; không ghi đã xác minh khi chỉ mở trang.
7. **Home và playlists:** chuẩn bị ba playlist trong Brand Guide; đưa lên Home khi có nội dung. D001 có thể làm featured video sau khi đăng. Không tạo trailer giả hoặc playlist trống hàng loạt.
8. **Contact và links:** chờ user cung cấp email kinh doanh hoặc link muốn công khai; không tự tạo thông tin. Chưa cần website để bắt đầu.
9. **Video watermark:** tùy chọn; avatar có thể dùng nếu đạt square ≥150 px, <1 MB. Đặt xuất hiện cuối video để ưu tiên hình giải thích. Chưa áp dụng khi chưa kiểm file/UI.
10. **Upload thử:** chỉ sau D001 đạt QC và user yêu cầu upload, đưa bản thật lên Private, kiểm xử lý/xem lại rồi mới đến lệnh đăng hoặc hẹn giờ.

Không đánh dấu hoàn thành trên checklist chỉ vì tài liệu đã có. `branding/asset-manifest.json` chứng minh file; snapshot Studio và receipt chứng minh việc áp dụng lên kênh.

## Thông số ảnh đã đối chiếu

YouTube khuyên banner 2560×1440; tối thiểu 2048×1152, tỷ lệ 16:9, tối đa 6 MB. Vùng an toàn tại kích thước tối thiểu là 1235×338; thiết kế này giữ chữ ở trung tâm hẹp hơn tỷ lệ đó. Avatar hỗ trợ PNG/JPG, dưới 15 MB và cần đọc được khi hiển thị 98×98. [YouTube — branding](https://support.google.com/youtube/answer/10456525?co=GENIE.Platform%3DDesktop&hl=en).

Upload defaults áp dụng cho upload qua browser; uploader khác vẫn phải đặt giá trị rõ. [YouTube — defaults](https://support.google.com/youtube/answer/2660027?hl=en). Name/handle/description thuộc Profile. [YouTube — profile](https://support.google.com/youtube/answer/2657964?hl=en). Quyền tính năng tùy tài khoản. [YouTube — feature access](https://support.google.com/youtube/answer/9891124?hl=en).

## Kết nối cho các phiên sau

`node scripts/youtube-account.mjs open|check|status` mở Chrome thường hoặc đọc trạng thái Studio. Helper này không sửa settings hay upload. `data/youtube-channel-connection.json` là snapshot; `production/channel-setup.json` lưu binding và checklist. Không coi cookie Google là bằng chứng đang ở đúng channel.

Trước mọi thao tác sửa/upload, đối chiếu Channel ID đang mở với binding. Không lưu cookie, mật khẩu hoặc OTP vào production/branding. Nếu có lỗi sau khi bấm Save/Publish, đọc lại trạng thái trước khi lặp thao tác.
