# Áp dụng nghiên cứu 2D bổ sung cho D003

Owner giao đọc `E:/YOUTUBE/Phân tích 2D bổ sung.txt` và dùng các phần phù hợp. Đã đối chiếu trực tiếp các repo ngày 17/11/2026. URL X gốc trả 403; không coi lời tóm tắt trong tài liệu là bằng chứng về khả năng của từng công cụ.

## Những thay đổi dùng ngay

- **Mốc từ:** chạy riêng WhisperX 3.8.6 + WAV2VEC2_ASR_BASE_960H trên voice v2, so với timestamp Kokoro. Lưu sai lệch từng từ và điểm tin cậy; không tự ghi đè timeline bằng một kết quả căn chỉnh khác. ASR độc lập trên bản mix đã có từ trước. Forced alignment không chứng minh lời phát âm đúng hoặc nghe tự nhiên.
- **Đúng từ kích hoạt:** kiểm cả logic chọn từ. Đã phát hiện bộ đếm 22 đốt sống dùng từ “two” trong năm 2012 thay vì “twenty-two”. Sửa cue, xử lý từ có gạch nối và render lại riêng S20 để ghép vào toàn tập.
- **Hình sau mã hóa:** contact sheet theo từng chương và các điểm trước/trong/sau hành động; xem thêm khung 320px và cụm frame sát điểm chuyển cảnh. Kiểm typography, chủ thể, màu, phụ đề trên MP4 cuối, không chỉ trên canvas nguồn.
- **Chuyển cảnh:** dùng PySceneDetect đã có để rà các điểm cắt bất ngờ và so với storyboard. Với B-roll tương lai, lập catalog gồm provenance, đoạn dùng, điểm cắt và contact sheet; chỉ split khi cần. D003 bản thử 2D này chưa có media Muse đạt.
- **Hậu kỳ:** dùng ffmpeg-skill hiện có cho probe, thử style ASS, look, đo khoảng nghỉ/loudness và kiểm đầu ra. Giữ renderer Canvas/NVENC riêng cho hình gốc; `--hw` của bản ffmpeg-skill đang cài là VideoToolbox, không phải NVENC. Không gắn nhãn rằng mọi công đoạn được tool này thực hiện.

## Điều chỉnh các khẳng định trong nghiên cứu

WhisperX cải thiện căn chỉnh, nhưng tài liệu của dự án nêu giới hạn từ ngoài từ điển và lời nói chồng nhau. “Có timestamp đến mili-giây” không đồng nghĩa “sai số dưới 1/60 giây”. Dùng số đo và xem lại cue quan trọng. [WhisperX](https://github.com/m-bain/whisperX)

`auto-editor --margin 0.15sec` đặt phần đệm quanh vùng nói; nó không tự định nghĩa chính sách “chỉ cắt khoảng nghỉ trên 0,4 giây”. Với phim tài liệu 8–10 phút, giữ nhịp câu hỏi và khoảng thở có chủ đích; xuất danh sách khoảng lặng để xét từng trường hợp. [auto-editor](https://github.com/WyattBlue/auto-editor)

Scene detection đưa ra ứng viên điểm cắt, không bảo đảm phát hiện mọi dissolve hoặc không có false positive khi HUD đổi mạnh. Chuyển clip 24fps thành 60fps cũng không tạo thêm chuyển động thật. Giữ fps nguồn trong catalog, xác định chính sách lặp/nội suy theo từng clip. [PySceneDetect](https://github.com/Breakthrough/PySceneDetect)

Không phủ chung `brightness=-0.05` lên mọi clip: cần nhìn exposure và color space trước. Màu D003 dùng chuyển sRGB → BT.709 có tính toán và tags/range đúng. Không thêm sonar/HUD beep chỉ vì xuất hiện bảng số; sound event phải phục vụ câu chuyện.

`sidechaincompress` là bộ nén có ngưỡng/tỉ lệ/attack/release; không tự bảo đảm nhạc chuyển chính xác từ -18 xuống -28 dB. Bản mix D003 hiện có ducking và được đo khoảng -16 LUFS/-1,55 dBTP. Đo lại AAC cuối; không nâng lên -14 chỉ để khớp một preset. [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html#sidechaincompress)

## Quyết định cho 14 repo

| Repo | Cách dùng trong công việc này |
| --- | --- |
| [video-use](https://github.com/browser-use/video-use) | Tham khảo kiểm ranh giới edit và bộ nhớ dự án. README có hỗ trợ animation qua Remotion/Manim/HyperFrames; không đúng khi nói nó chỉ dùng talking-head. Không cài thêm một orchestrator chồng lên pipeline hiện tại. |
| [ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) | Dùng bản local đã kiểm, lưu plan/receipt/probe/look; giới hạn GPU nêu ở trên. |
| [Claude Eyes](https://github.com/moritzkremb/claude-eyes) | Áp dụng cách index → xem tổng thể → burst/crop tại điểm cần kiểm. Công cụ hiện có đã tạo các evidence này; chưa cài CLI Eyes. Contact sheet là mẫu, không phải nghe/xem toàn bộ bằng người. |
| [WhisperX](https://github.com/m-bain/whisperX) | Cài cục bộ tách biệt `tools/alignment-python`, dùng forced alignment độc lập; không cài lại bộ voice đang dùng. |
| [Silero VAD](https://github.com/snakers4/silero-vad) | Có runtime ONNX qua faster-whisper; dùng để đo vùng nói/khoảng nghỉ, không quyết định nhịp kể. |
| [auto-editor](https://github.com/WyattBlue/auto-editor) | Chưa cần cài cho voice TTS đã phân đoạn; giữ nguồn, chỉ cắt khoảng nghỉ sau đánh giá riêng. |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | Runtime local có sẵn; dùng detect-adaptive và đối chiếu cut với storyboard, không auto-split bản hoạt hình hoàn chỉnh. |
| [editly](https://github.com/mifi/editly) | Không thay renderer hiện tại; không kết luận khả năng “yếu hơn rất nhiều” khi chưa benchmark cùng bài toán. |
| [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO) | Hữu ích khi cần trao đổi timeline; chưa có nhu cầu xuất timeline cho phần mềm khác. |
| [DaVinci Resolve MCP](https://github.com/samuelgursky/davinci-resolve-mcp) | Chỉ dùng khi workflow thực sự cần Resolve Studio; không mở thêm app trong D003. |
| [Uncut](https://github.com/blazejkustra/uncut) | Repo nhắm macOS; máy hiện tại là Windows. |
| [Yap Studio](https://github.com/cathrynlavery/yap-studio) | Nhắm macOS và video dọc người nói; tham khảo chu trình ghi chú/QC, không cài vào D003. |
| [Take One](https://github.com/talsiach/take-one) | Tham khảo mô tả chuyển động theo hành động/kết quả và review; không biến phim tài liệu thành launch/ad. README nói mới chạy thử macOS. |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | Engine local đã dùng, kiểm encoder/màu/frame/audio thực tế. |

## Quy tắc tiếp tục

### Kết quả đã đo trên D003

- WhisperX căn được 1.316/1.316 từ trong 26 đoạn. Chênh lệch đầu từ so với Kokoro: trung vị 81 ms, p95 143,75 ms, lớn nhất 213 ms. Đây là chênh lệch giữa hai hệ căn thời gian, không phải sai số đo bằng tai người.
- Dùng 150 onset phụ đề có score từ 0,8 và lệch không quá 200 ms; giữ đuôi đọc và toàn bộ từ. Có 230 cue không chồng nhau. S20 sửa logic chọn từ và ghép theo receipt 420,45–443,933333 giây.
- Silero ghi 118 vùng nói; các khoảng nghỉ dài nhất nằm ở ranh giới đoạn. Đã đo lại bằng FFmpeg silencedetect, không tự cắt những khoảng thở này.
- Hai MP4 cuối được ffmpeg-skill đo khoảng −16,1 LUFS / −1,6 dBTP. Cảnh báo duy nhất của check định dạng là không có track phụ đề nhúng; bản đốt chữ, SRT/VTT rời và trình xem nhúng WebVTT đã được chuẩn bị. Không gọi 13/13 check là PASS khi còn cảnh báo này.
- `qa/final/` chứa kết quả scan, contact sheet, điểm chuyển cảnh, kiểm trình xem và phần đánh giá thị giác riêng. Chỉ coi bước nào có kết quả hoàn tất là đã làm; ảnh mẫu và ASR không thay thế nghe duyệt toàn bộ.

Lấy file media và kết quả đo thật làm đầu vào. Giữ nguồn và receipt. Không tự cắt silence, thêm LUT, ép fps hoặc đổi loudness chỉ vì preset. Phân biệt tool đã chạy, kỹ thuật tham khảo, kiểm bằng máy và duyệt bằng người. Kết quả D003 được ghi tại `episodes/D003/reel-v1/qa/`; không tuyên bố 100% chất lượng/retention từ danh sách repo.
