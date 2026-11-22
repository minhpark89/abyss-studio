# Vận hành xưởng video

Khi nhận “Tạo tập mới cho niche [tên_niche]”, đọc `niches/[tên_niche]/niche.json`, các luật dựng cạnh hồ sơ và `REPO_REGISTRY.json`. Dùng đúng brief, thời lượng, nhân vật và checkpoint của kênh. Chọn repo theo mục đích và trạng thái trong sổ. Ghim commit trước khi lấy mã.

Tạo `production/<niche>/<tập>/`, chốt beat, bảng cảnh, ảnh và giọng neo. Ghi góc máy, hướng nhìn, người nói, tay cầm đạo cụ và frame phát âm hoặc va chạm. Codex soạn bảng cảnh cho ý tưởng chủ kênh giao. Chạy các module `core/` theo hồ sơ. Bảng cảnh đã có take dùng lại biên nhận hoàn tất. Khi Muse chưa rõ trạng thái, đối chiếu đúng receipt. Dùng API nền trên 4320 và xuất gói cục bộ.

Với karma-drama, điền trường `framing` trên mỗi shot bằng một khóa trong `shot_mix_percent` của niche. Bộ dựng ghi phân bố và trung vị thực vào trace. Khi thoại đi qua mối cắt, ghi người nghe và lý do giữ phản ứng.

Trên MP4 đã mã hóa, đo riêng khẩu hình, thoại, phụ đề và điểm chạm. Xem vùng nghi vấn về mặt, biểu cảm và số đạo cụ. Ghi kết quả thực chạy, ngoại lệ và SHA-256 trong `execution_trace.json`. Dashboard đọc hồ sơ và trace của từng tập. Chạy lệnh save/check của kênh sau mỗi mốc. Việc đăng do chủ kênh quyết định.
