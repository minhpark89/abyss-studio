# Hướng hiện hành — 2D theo reel owner chọn, 16/11/2026

Owner chọn rõ [reel 2D](https://www.facebook.com/reel/1272693095069597) vì dễ hiểu và đẹp. Áp dụng từ các tập sau D002: đọc [phân tích trực tiếp và tài nguyên](FACEBOOK_2D_ANALYSIS_20261116.md). Chuỗi 2D giữ cùng đối tượng, nền nhiều lớp, một hành động chứng minh mỗi ý, chữ đi theo lời. Đây là quyền dùng 2D rõ ràng; không ép hình cơ chế sang 3D.

Đã có mẫu vector nguyên bản 42 giây tại `visual-lab/whale-fall-2d-v1/whale-fall-2d.mp4`, hiển thị trong app. Mẫu kiểm luồng xương → chất hữu cơ → năng lượng hóa học → vi sinh vật; không phải full D003 hay mỹ thuật đã được owner duyệt. Mẫu Three.js cũ giữ để đối chiếu. Mỗi cảnh ghi trước/sau, tác nhân, đối tượng xuyên suốt và voice cue; kiểm chuỗi hybrid 45–90 giây trước tập dài. D002 v9 giữ nguyên.

---

# Chuẩn minh họa 2D — cập nhật 14/11/2026

Phản hồi mới nhất: hình 2D phải chi tiết, chiếm khung hợp lý và chuyển động rõ, hài hòa. Bản so sánh mới [v6, 37 giây, 1080p30](preview-v6/abyss-fieldnotes-style-test-v6.mp4) dùng toàn 2D để kiểm phần này. Cảnh Muse/v5 vẫn giữ để đan xen khi kịch bản cần. Đọc [nghiên cứu và checklist mới](VISUAL_RESEARCH_2026-11-14.md). Không burn nhãn kỹ thuật vào video. Lựa chọn 2D rõ ràng phù hợp ngoại lệ AGENTS; không tự quay lại khối 3D cho phần giải thích.

## Phần đã làm trong bản thử

- Ba hình gốc: cá nhà táng, mực khổng lồ Nam Cực và mắt. Nét viền, hatch nhẹ, màu phẳng; nền navy, chữ ngà và vàng. Tạo bằng built-in ImageGen, không trích hình đối thủ.
- V6 dùng mesh texture có điều khiển gốc/chóp đuôi, vây và vùng tay; giữ đầu/mắt ổn định. Cỡ cảnh thay đổi toàn/cận/cơ chế, nền phủ bốn cạnh. Chưa phải bộ rig giải phẫu đầy đủ với từng xúc tu độc lập.
- So sánh mắt/đĩa bằng đường kính bằng nhau; cảnh cá voi/mực là sơ đồ không theo tỷ lệ, ghi trong hồ sơ, không footer kỹ thuật. Không thêm số đo chưa kiểm nguồn.
- Giữ nguyên voice, nhạc và SRT v3 để so hình. Nhạc nguyên bản có ducking, câu hỏi ở ngay câu đầu, chữ chính thường 2–4 từ.
- Giả thuyết vẫn được nói rõ bằng lời kể. Hình minh họa không được trình bày như quan sát trực tiếp.

## Checklist hình cho mỗi cảnh hằng ngày

- [ ] Viết một câu: hình này giúp người xem hiểu điều gì mới? Chọn chủ thể chính, vật so sánh hoặc cơ chế.
- [ ] Kiểm loài, hình dáng, chi/vây và số đo theo reference khoa học trước khi duyệt asset. Không dùng AI image như nguồn anatomy.
- [ ] Chọn một bố cục: so kích thước / gặp nhau / cận bộ phận / cơ chế / bằng chứng / callback. Có biến đổi thông tin giữa các cảnh.
- [ ] Chủ thể dễ nhận ra ở 320×180. Nét vẽ và tương phản phải đủ rõ trên nền tối.
- [ ] Nền phủ cả viewport; không dải trống do CSS/canvas sai kích thước. Cỡ hình dựa vào thông tin cảnh, không để sinh vật nhỏ như icon. Cận cảnh được crop có chủ đích, cảnh vận động phải thấy bộ phận cần diễn tả.
- [ ] Kiểm chữ cả khi camera đã zoom tới cuối, không chỉ frame giữa cảnh. Không che mắt, xúc tu hoặc điểm nhấn.
- [ ] Một chuyển động chính phục vụ lời kể; chuyển động phụ vừa đủ. Cần đổi tư thế/góc nhìn rõ thì tạo pose mới hoặc rig riêng, không kéo méo một ảnh.
- [ ] Uốn ở phần đuôi/xúc tu phù hợp; đầu, mắt và hình dáng loài ổn định. Xem MP4 ở nhiều pha để tìm mép rách/răng cưa.
- [ ] Chữ chính thường 2–5 từ, một từ/số có màu nhấn. Gắn số đo vào đúng đối tượng bằng thước/đường chỉ. Kiểm chữ sau khi thu xuống kích thước điện thoại.
- [ ] Reveal hình/chữ theo timestamp lời đọc; không đưa toàn bộ sơ đồ ngay trước câu hỏi.
- [ ] Giữ nguồn, prompt, phiên bản và hash từng asset. PNG alpha thật; tách khỏi chữ để chỉnh bằng code.
- [ ] Có nhạc nền nghe được, hạ dưới voice; kiểm nghe thực tế là bước riêng với đo loudness.
- [ ] Kiểm decode, phát file cuối tới hết, ảnh từng beat và các pha chuyển động; ghi rõ phần nào còn chờ chủ kênh đánh giá.

## Tái sử dụng cho sản xuất

Thư viện hiện tại: `preview-v4/assets/`. Prompt chính xác: `GENERATION_PROMPTS.json`; provenance và hash: `manifest.json`. Chỉ tái sử dụng asset khi đúng loài và góc nhìn. Học cách giải thích của đối thủ, không dùng lại hình, nhạc hay lời của họ.

Module mẫu v6: `state.js` (timeline), `assets.js` (PNG/alpha), `rig.js` (mesh/pivot), `creatures.js` (đối tượng), `environment.js` (nền), `motion.js` (hành động/tín hiệu), `world.js` (cảnh/cơ chế), `cameras.js` (pan/zoom), `ui.js` (chữ), `main.js` (chạy/phát). Không gộp tất cả vào một file. Mỗi tập tạo storyboard/timing riêng theo voice đã đo. ImageGen đang lỗi token; không khai có tranh mới hoặc full rig chỉ vì bản v6 đã render.

Bản v3 vẫn giữ để đối chiếu. V4 chứng minh hướng hình 2D khả thi; chưa phải bằng chứng tăng retention và không làm các checkpoint của tập dài tự đạt. D001 8–10 phút vẫn cần hoàn thiện facts, script và storyboard.
