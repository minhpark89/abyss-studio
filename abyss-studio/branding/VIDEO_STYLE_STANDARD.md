# Chuẩn hình và thương hiệu trong video — Abyss Fieldnotes v1

Áp dụng từ nghiên cứu bốn kênh ngày14/11/2026. Giữ tên/avatar/banner đã setup; tài liệu này chuẩn hóa nội dung phim, không yêu cầu đổi nhận diện công khai. Thông số dùng chung nằm trong `video-style.json`. Đây là đặc tả sản xuất; chưa tự động áp lên mọi renderer cũ.

## Lời hứa nhận diện

**Deep-sea stories. Clear explanations.** Người xem nhận một bí ẩn sinh học có thật, thấy cơ chế bằng hình, rồi hiểu giới hạn của câu trả lời. Tò mò và bất ngờ là giọng chính; không biến mọi sinh vật thành quái vật săn người.

Sự nhất quán nằm ở cùng cách vẽ, cùng nhân vật, cùng màu có ý nghĩa và cùng cách dẫn mắt. Không dùng logo/khẩu hiệu lặp trên mọi cảnh để thay việc này. Thumbnail được xử lý tương phản mạnh hơn, nhưng hình trong phim phải nhận ra là cùng sinh vật và thực hiện cùng lời hứa.

## Bộ hình cố định

| Thành phần | Quy tắc |
|---|---|
| Nền | Navy `#061722`; có thể chuyển sang teal tối `#173647` cho môi trường. Nền phủ bốn cạnh, tương phản thấp hơn chủ thể; hạt/đường nước chỉ hỗ trợ không gian. |
| Chữ | Ivory `#F4EDDD`; Bahnschrift cho câu hỏi/số, Segoe UI cho nhãn khi cần; tối đa2 họ font. Không phân phối lại font hệ thống. |
| Màu ý nghĩa | Amber `#F8CF61`: câu hỏi/số quan trọng. Cyan `#64E6E8`: tín hiệu/ánh sáng/đường giải thích. Không đổi ý nghĩa màu giữa các cảnh. Màu tự nhiên của loài không bị ép về palette. |
| Nét vẽ | Minh họa lịch sử tự nhiên 2D, silhouette rõ, bóng chia mảng dễ đọc; hatch tập trung ở bộ phận cần xem gần. Không tăng texture khắp cảnh chỉ để “chi tiết hơn”. |
| Chữ nhấn | Thường2–5 từ, một ý; thử96–110px ở1080p, rồi kiểm320×180. Nhãn chỉ xuất hiện khi có vai trò; không chép toàn bộ voice. |
| Bố cục | Chủ thể to đủ hiểu; toàn thân phải thấy chi/vây đang giải thích. Cận cảnh được crop có chủ đích. Khoảng trống phục vụ chữ và hướng chuyển động. Không bắt mọi shot có cùng phần trăm phủ khung. |
| Tư liệu/Muse | Có vai trò cụ thể trong script, đặt gần một ý hoặc cảm xúc cần thiết. Giữ continuity về hướng nhìn, loài, màu. Không dùng như bằng chứng quan sát hay hình đo giải phẫu. Không tỷ lệ cinematic bắt buộc. |

## Khóa nhân vật trước khi tạo hàng loạt

Mỗi loài có một `asset_id` và model sheet: silhouette toàn thân, cận bộ phận chính, palette, tỷ lệ, số chi, vị trí mắt/miệng/vây và nguồn anatomy. Pose/góc mới phải đối chiếu lại master; không tạo sinh vật mới độc lập cho từng scene bằng cùng một prompt chung.

Với phần hoạt hình cần nhiều động tác: tách thân, đầu, bộ phận chuyển động và điểm nối; ghi pivot, khoảng góc, pha và thứ tự che khuất. Head/eye anchor giữ ổn định khi đuôi/tay di chuyển. Không kéo dãn toàn PNG để giả mọi động từ. Khi chỉ cần chỉ số/thước thì dùng sơ đồ đơn giản, không làm rig thừa.

Các asset v4/v6 hiện là tranh gốc và mesh cục bộ, **chưa được coi là bộ nhân vật giải phẫu đã duyệt cho phim dài**. ImageGen hiện lỗi token; giữ receipt, không khai đã có model sheet/rig mới. Tiếp tục viết nội dung và lập danh sách pose cần tạo.

## Tám loại cảnh để thay đổi cách giải thích mà giữ thương hiệu

1. Toàn cảnh định vị: nhân vật, môi trường, vấn đề.
2. So kích thước: cùng tỷ lệ khi có số đo, vật quen để hình dung.
3. Cận bộ phận: nối vị trí trên toàn thân với cận cảnh; không đổi loài/hình mắt.
4. Cơ chế: tác nhân → tác động → kết quả, cùng tọa độ và timeline.
5. Đối chiếu: hai điều kiện/thông số, đổi đúng một biến nếu đó là mục tiêu giải thích.
6. Bản đồ/độ sâu: mốc ổn định, đối tượng chuyển động; đơn vị rõ.
7. Bằng chứng: mẫu vật/quan sát/mô hình được phân biệt trong nội dung, nguồn giữ trong hồ sơ.
8. Callback: trở lại hình mở sau khi người xem có cách hiểu mới.

Không ép đủ cả8 loại trong mỗi tập. Mỗi cảnh phải ghi một câu `visual_answer`; hình đẹp nhưng không thêm thông tin phải có lý do cảm xúc rõ hoặc cắt.

## Chuyển động và âm thanh

Mỗi beat có động tác chính khớp từ khóa, một nhịp chuẩn bị và một kết quả nhìn thấy được. Chuyển động phụ nhỏ hơn; camera không chạy đồng thời nhiều hướng. Cắt cảnh khi thay ý/điều kiện, không theo quy tắc cứng “cứ3 giây đổi cảnh”. Giữ thời gian để đọc, dự đoán và hiểu kết quả.

Nhạc có chủ đề và nhịp cảm xúc phù hợp, tự hạ dưới lời đọc. SFX chỉ làm rõ động tác hoặc chuyển ý; phân biệt âm tái dựng và âm quan sát trong hồ sơ. Dùng cùng voice production đã chốt quyền sử dụng; không giả trải nghiệm cá nhân hoặc nhồi tiếng ngập ngừng để “human”.

## Cổng kiểm nhận diện

- [ ] Đặt12 khung rải đều của tập cạnh nhau: có nhận ra cùng một kênh và cùng loài không?
- [ ] So thumbnail với frame đầu/cận cảnh: cùng bộ phận, cùng lời hứa, không đổi silhouette tùy cảnh.
- [ ] Xem320×180 và một cận1080p: ý chính rõ, nét không rối, nhãn thật sự cần đọc được.
- [ ] Xem đầu/giữa/cuối chuyển động: không trượt mắt, rách khớp hoặc chữ che chủ thể khi zoom.
- [ ] Hình minh họa cơ chế vẫn hiểu được khi tắt tiếng; voice giải thích rõ khi không nhìn hình.
- [ ] Có nhạc nhưng lời vẫn rõ trên loa nhỏ; nghe thực tế và đo âm lượng là hai việc riêng.
- [ ] Export sạch: không “2D illustration”, engine/debug/footer; không bỏ giới hạn khoa học khỏi lời kể.

Chuẩn này là giả thuyết thiết kế của Abyss Fieldnotes, không phải công thức CTR đã được chứng minh. Chỉ thay một nhóm quy tắc có lý do sau khi có dữ liệu/feedback đủ rõ; không đổi palette/font mỗi ngày.
