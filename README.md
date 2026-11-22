# Abyss Studio

Ứng dụng Windows chạy trên máy của chủ kênh. Abyss Fieldnotes làm phim tài liệu biển sâu tiếng Anh Mỹ. Second Bell Pictures làm phim truyện. Phiên AI mới bắt đầu ở [bàn giao Abyss](abyss-studio/production/channels/abyss-fieldnotes/CHECKPOINT.md) hoặc [bàn giao Second Bell](abyss-studio/production/channels/second-bell/CHECKPOINT.md).

## Mở trên PC khác

Cài Git, Node.js 22.12 trở lên và Python 3.11 trên Windows. Clone repo riêng bằng tài khoản có quyền. Từ thư mục đã clone, chạy PowerShell:

```powershell
.\Setup.ps1
.\Start.ps1
```

Cửa sổ Electron mở bảng kênh. Muốn dùng dashboard cục bộ chỉ với Node, chạy `.\Start.ps1 -Headless` rồi mở [Abyss Studio](http://127.0.0.1:4320/fieldnotes). Tắt tiến trình Node bằng Ctrl+C. Mã server nằm ở [native-server.js](abyss-studio/native-server.js), giao diện ở [public](abyss-studio/public), API và sổ tập ở [lib](abyss-studio/lib).

Chạy `.\Verify.ps1` để kiểm tra bản clone. Lệnh mở một máy chủ tạm và kiểm tra cả hai kênh, danh mục tích hợp, dashboard và các trang duyệt phim. Đọc [bàn giao phiên](abyss-studio/production/SESSION_HANDOFF.md) để xem quyết định đang chờ ở từng kênh. Các đường dẫn tới phim và bằng chứng lịch sử trong checkpoint trỏ về kho sản xuất của chủ kênh.

## Kết nối dịch vụ trên máy mới

- **Muse.** Cài Go 1.24 trở lên và chạy `.\Setup.ps1 -Headless -BuildMuse` để biên dịch backend kèm theo. Mở lại cửa sổ desktop, vào mục tài khoản và kết nối tài khoản được phép dùng trên PC này. Gateway tạo kho bí mật và khóa cục bộ khi khởi động. Tác vụ có biên nhận phải được đối chiếu với đúng backend đã nhận tác vụ. Xem [mã nguồn và giấy phép gateway](gateway/LICENSE).
- **Số liệu YouTube.** Chạy `python -m pip install requests pywin32 tzdata`. Chủ kênh nhập OAuth Desktop trong app và cấp quyền trên PC mới. Để cài tác vụ báo cáo lúc 08:00 theo giờ máy, chạy `abyss-studio\scripts\install-fieldnotes-daily.ps1`. Dữ liệu riêng thuộc thư mục `abyss-studio/data/` trên từng máy. Hoàn thành mỗi tập bằng cách kiểm MP4 và lưu checkpoint trong đúng kênh.
- **Render phim.** Máy sản xuất hiện dùng FFmpeg/NVENC, FFprobe, Electron/WebGL, giọng Kokoro và bộ căn từ WhisperX. Bản dựng D007 nằm ở [full-v1](abyss-studio/production/episodes/D007/full-v1). Các script của các tập cũ ghi lại đường dẫn máy sản xuất lúc render. Trên máy mới cần cài các công cụ, model và cập nhật những đường dẫn này trước khi render lại. `VIRAL_RESEARCH_ROOT`, `ABYSS_FFMPEG` và `FFPROBE_PATH` cấu hình các công cụ dùng chung trong phần Node.

## Tiếp tục sản xuất

- **Abyss Fieldnotes.** Theo dõi mốc 24 giờ, 48 giờ và 7 ngày trong [bảng kênh](http://127.0.0.1:4320/fieldnotes). Dùng lịch nội dung, feedback và nguồn khoa học của tập trước để dựng tập tiếp theo. Kiểm bản mã hóa, phụ đề và âm lượng trước khi chủ kênh tự đăng.
- **Second Bell Pictures.** Mẫu hiện hành là SB09 *The Stolen Label*. Xem [hướng dựng còn mở](abyss-studio/production/episodes/SB09/PRODUCTION_HANDOFF.md), [shot và bản dựng](abyss-studio/production/episodes/SB09), [các bước kiểm khẩu hình](codex-video-factory/production/karma-drama/SB09) và [bộ điều phối](codex-video-factory/AGENTS.md). Các thành phần bên thứ ba được nhận diện theo URL, commit và đường dẫn trong [sổ repo](codex-video-factory/REPO_REGISTRY.json).
- **Khôi phục media.** Repo lưu kịch bản, bảng cảnh, hình tham chiếu, mã ghép, phụ đề, nguồn và kết quả QA. Master, take Muse, audio trung gian và trọng số model là tài sản cục bộ. Để phát hoặc dựng lại bản cũ, dùng `python restore-media.py E:\YOUTUBE` khi ổ sao lưu workspace gốc được gắn. Công cụ kiểm hash trước khi sao chép những media có trong danh mục. Có thể tiếp tục sửa code và phát triển tập mới ngay từ bản clone.

