# Chữ nhấn, câu hỏi và nhịp kể có chủ ý

**Ảnh tư liệu theo lời kể, từ D006.** Mỗi phần của Abyss Fieldnotes có một khoảnh khắc người xem được nhìn tư liệu thật về chính nội dung đang nghe. Chọn ảnh và câu dẫn cùng lúc, cho thấy rõ điều cần quan sát, giữ thẻ đủ lâu để đọc tên và credit tiếng Anh Mỹ. [Quy trình ảnh tư liệu và mẫu hình chủ kênh gửi](channels/abyss-fieldnotes/RENDER.md#ảnh-tư-liệu-cho-từng-phần)

**Góp ý chủ kênh ngày 20/11/2026, áp dụng từ D006.** Dành thêm một nhịp ngắn cho hook. Đặt câu hỏi ngay đầu, cho người xem một chi tiết cụ thể để tự đoán, rồi để hành động trên hình làm họ muốn biết lời giải. Thử nhịp dài hơn trên lời đọc thật và kiểm xem mỗi giây thêm vào có mang đến thông tin mới. Chủ kênh đã duyệt đoạn mở 60,625 giây của D005 để dùng trong bản dài. [Checkpoint Abyss Fieldnotes](channels/abyss-fieldnotes/CHECKPOINT.md)

**Abyss Fieldnotes · thị trường Mỹ (yêu cầu owner, 18/11/2026).** Toàn bộ lời đọc, chữ trên hình và phụ đề giao cho YouTube dùng tiếng Anh Mỹ. Không đóng chữ Việt vào hình, không nhúng track Việt và không kèm SRT/VTT Việt trong gói giao. Quy tắc này thuộc kênh Abyss Fieldnotes; cấu hình ở `channel-setup.json → production.release_language_policy`.

Khi lời kể mở một ý, cho tiêu đề hoặc thẻ số liệu trượt vào rồi dừng để đọc; không bật chữ đột ngột, nảy liên tục hay làm tiêu đề vàng mờ đi. Mẫu D004: tiêu đề trượt khoảng 46 px trong 0,47 giây, thẻ số liệu 28 px trong 0,43 giây, dòng phụ đề Anh dịch lên 12 px trong 0,23 giây. Không khởi động lại chuyển động khi cùng một ý còn trên hình. Kiểm trên MP4 thực ở đầu, giữa và cuối chuyển động, rồi kiểm track và tệp giao bằng `scripts/check-release-language.py`.

**Hiện hành 15/11/2026:** owner xác nhận D001 đã đăng là chuẩn và từ chối D002 v5. D002 được sửa ở revision-v6; yêu cầu đầy đủ và việc còn mở nằm trong CURRENT_BRIEF.md/TASK_LEDGER.md. Các bản thử D001 kể dưới đây là lịch sử hình thành quy trình, không thay yêu cầu mới này.

**Yêu cầu mới về âm:** mỗi tiếng nhấn có hành động/đáp án cụ thể, dùng chung event với hình và chữ. Có mốc giữ im lặng hoặc chỉ hạ nhạc. Không thêm tiếng cho mọi photon/chữ/chuyển cảnh; không coi SFX biên tập là tiếng thật của ánh sáng hay con vật. [Quy trình và mẫu mới](HYBRID_FORM_RUNBOOK.md).

Yêu cầu người dùng bổ sung ngày 13/11/2026: khi đặt câu hỏi có font chữ hiện lên, có điểm nhấn giúp cảm nhận người dẫn chuyện. Áp dụng cho toàn bộ tập mới; đây là yêu cầu sản xuất, không chỉ gợi ý.

**Hướng sửa mới nhất 14/11/2026:** v1 dài bị chủ kênh từ chối vì hình/bối cảnh. Đọc [D001 visual rebuild](D001_VISUAL_REBUILD.md) và xem [mẫu mới 1:21](episodes/D001/visual-v2-proof/D001-visual-rebuild-v2-proof-final.mp4). V6 là thử trước, chưa phải chuẩn được chấp nhận. Ưu tiên câu hỏi có hình trả lời, cỡ cảnh có lý do, chuyển động biểu diễn tác động/kết quả; không chỉ thêm font lớn. Rig từng phần và nghe duyệt vẫn mở. Giữ quy trình [DAILY_EDITORIAL_SOP.md](DAILY_EDITORIAL_SOP.md), [VIDEO_STYLE_STANDARD.md](../branding/VIDEO_STYLE_STANDARD.md) và [CHECKPOINTS.md](CHECKPOINTS.md).

**Bản thử v2 giữ để đối chiếu:** [abyss-fieldnotes-style-test-v2.mp4](preview-v2/abyss-fieldnotes-style-test-v2.mp4), 43,5 giây: so sánh mắt với đĩa ăn → câu hỏi → pupil/light → giả thuyết cảnh báo cá voi → giới hạn bằng chứng. Hình giải thích Three.js/WebGL, chữ theo lời đọc, pause và một cảnh Muse có sẵn. User phản hồi âm nền khó nghe, hook chưa rõ và nhiều chữ nhỏ; đã sửa ở v3 phía trên. Không đánh dấu D001 hoàn tất từ bản thử này.

**Mẫu typography cũ:** [human-style-demo.mp4](preview/human-style-demo.mp4), khoảng 20 giây, gồm 3 cặp câu hỏi–câu trả lời, giọng thử, khoảng nghỉ, chữ màu nhấn và fade nhẹ. Đây là mẫu typography trên nền đơn giản để kiểm chữ/nhịp, chưa phải cảnh giải thích hoàn chỉnh hoặc tập D001. Kết quả kiểm riêng nằm ở `preview/verification.json`; phần nghe duyệt của người vẫn pending.

## Bằng chứng đối thủ và cách chuyển thành phong cách riêng

Ở [Colossal Squid khoảng 03:52](https://www.youtube.com/watch?v=2819-mQEA9M&t=232s), hình mực tối lại và câu hỏi đỏ gạch chân xuất hiện ở đáy: “WHAT SCARES A HALF-TON SQUID?”. Khung đã kiểm: `research/depth-theory/2819-mQEA9M-frames/047.jpg`. Câu hỏi đổi vai của nhân vật: từ thứ đáng sợ thành thứ cũng có thể sợ. Chính chỗ đổi ý làm chữ có tác dụng; hiệu ứng chữ đơn thuần chưa đủ.

Không sao chép câu chữ, nhạc hay timing của đối thủ. Hệ riêng gồm: lời đọc đặt vấn đề → chữ tóm câu hỏi → một khoảng để dự đoán → hình giải thích → câu chốt gọn. Một số câu trả lời xuất hiện ngay; câu hỏi lớn được mở rộng qua nhiều bằng chứng. Không giữ câu trả lời dễ quá lâu để câu giờ.

## Sáu công cụ biên tập

| Công cụ | Khi dùng | Ví dụ nguyên bản cho D001 | Ràng buộc |
|---|---|---|---|
| Question beat | Đổi chương hoặc mở điều chưa rõ | “Why so big?” | 3–7 từ, tối đa 2 dòng, xuất hiện sát lúc voice hỏi; ý chính không bị subtitle dài đè. |
| Guess, then reveal | Người xem có thể tự suy luận | “Better hunting?” → “Earlier warning?” | Không làm đáp án còn tranh luận thành đúng/sai tuyệt đối; giữ dấu hỏi và nhãn hypothesis. |
| Scale surprise | Con số cần hình dung | “ONE EYE” rồi 10.6 in / 27 cm | Nhấn đại lượng thật, không giật zoom làm sai tỷ lệ giữa hai vật. |
| Honest qualification | Bằng chứng chưa đủ | “A hypothesis.” | Voice nói rõ độ chắc chắn; không chỉ giấu vào footnote nhỏ. |
| Visual callback | Kết trả lại hình đầu | Trở lại đĩa ăn và mắt | Hình cũ có ý nghĩa mới; không replay nguyên shot để lấp thời lượng. |
| Dry observation | So sánh quen giúp dễ hiểu | Mắt lớn chưa nói ai là kẻ chiếm ưu thế | Hài là tùy chọn; cắt nếu kéo người xem khỏi cơ chế. Không giả vờ có trải nghiệm lặn cá nhân. |

## Typography và nhịp chuyển động

- Tối đa 2 họ font. Khởi đầu dùng Bahnschrift cho chữ nhấn, Segoe UI cho nhãn/phụ đề; fallback Arial. Chỉ render bằng font hợp lệ có sẵn, không tự đóng gói font hệ thống để phân phối.
- Chuẩn mới sau phản hồi: chữ nhấn thường 2–5 từ; thử 76–88 px ở 1280×720 (114–132 px ở 1080p), đặt trong vùng trống bên trên/cạnh chủ thể. Nhãn phụ phải có chức năng; bỏ brand eyebrow, dòng nguồn dài và câu lặp lại voice khỏi cảnh chính. Không rải cùng lúc nhiều điểm nhấn lớn.
- Question text trên canvas 1920×1080: thử khoảng 114–132 px theo chuẩn v3; label 40–54 px chỉ khi cần. Kích thước thực quyết định sau khi xem ở 320×180. Không dùng cỡ chữ cố định nếu không đọc được trên điện thoại.
- Trắng ngà cho câu, cyan hoặc hổ phách cho một từ trọng tâm. Đỏ chỉ khi nội dung cần cảnh báo thực, không rải đỏ mọi cảnh.
- Vùng an toàn 7% mép. Tạo negative space ngay từ storyboard; chữ đặt cạnh chủ thể, không đè lên mắt, xúc tu hay hướng tín hiệu. Câu hỏi có thể ở giữa trong một thẻ riêng nền giản lược; không đặt headline khổng lồ che cảnh 3D.
- Nhịp mặc định để thử: fade/slide nhẹ 180–260 ms; giữ 2–3,5 giây; rời 150–220 ms. Từ nhấn có thể scale 0,97→1,00, không rung/nhảy liên tục. Đây là thông số dựng, chưa phải kết quả retention.
- Sau câu hỏi, thử khoảng nghỉ voice 350–700 ms; phải nghe tự nhiên trong câu thực. Khi reveal, giảm nhạc nhẹ hoặc một âm nhỏ đủ nghe, không dùng impact bass cho mọi câu.
- Mỗi cảnh chỉ có một việc người xem cần đọc. Phụ đề đầy đủ ở SRT; nếu burn-in, tránh đồng thời phụ đề dài + question card + bảng số liệu mới.
- Cho tập 8–10 phút, dự kiến 4–7 question beats có tác dụng và 6–10 emphasis beats. Không ép đủ nếu câu chuyện ít bước. Có khoảng hình yên để nhận biết quy mô và nghe lời giải thích.
- Không giả lỗi giọng, chèn “uh/um” hàng loạt hay bắt chước một creator để nghe như người. Sự tự nhiên đến từ lựa chọn ý, sự chính xác và nhịp đặt–trả câu hỏi.

## Trường bắt buộc trong storyboard

```json
{
  "scene_id": "D001-S018",
  "question_id": "Q3",
  "narration": "But what if the advantage is seeing danger sooner?",
  "voice_intent": "curious, restrained; turn from confidence to possibility",
  "emphasis_word": "danger",
  "pause_after_ms": 500,
  "on_screen_text": "Earlier warning?",
  "text_role": "question",
  "text_anchor_word": "danger",
  "timing_status": "estimate_until_tts",
  "overlay_start_s": null,
  "overlay_end_s": null,
  "visual_answer": "Schematic whale disturbance → flashes → squid eye",
  "answer_scene_id": "D001-S019",
  "certainty": "hypothesis",
  "source_ids": ["SQ02", "SQ03"]
}
```

Sau TTS phải thay timing ước lượng bằng timestamp thực. Kiểm tra đường tiếng có pause thật, hình hiện đúng từ nhấn và trả lời không đến trước câu hỏi ngoài ý muốn.

## D001 — các điểm nhấn đã chọn

1. Mở đầu hiện tại: câu hỏi “WHY SO BIG?” trên cảnh Muse ngắn → mắt 2D cạnh đĩa. Không intro logo dài. Chuẩn hình theo [HYBRID_PRODUCTION_PIPELINE.md](HYBRID_PRODUCTION_PIPELINE.md), mẫu v5; giữ nhạc và chữ nhấn v3.
2. “Why so big?” → hứa tìm chức năng, không chỉ kể kích thước.
3. “What can light reveal?” → đổi sang sơ đồ ánh sáng; một đường truyền một lần.
4. “Earlier warning?” → chuyển sang giả thuyết cá voi; nói rõ hypothesis.
5. “How do we know?” → phân biệt mẫu vật, mô hình và quan sát sống.
6. “Not the whole answer.” → thừa nhận tranh luận khoa học một cách ngắn gọn.
7. Kết quay lại mắt; lời đọc đưa người xem từ cảm giác quái vật sang bài toán sống sót.

## Checklist để duyệt cảm giác người dẫn chuyện

- [ ] Mỗi question beat ghi được câu trả lời nằm ở cảnh nào; không có câu hỏi chỉ để giữ người xem.
- [ ] Mỗi từ nhấn đi cùng một thay đổi thông tin hoặc cảm xúc.
- [ ] Đọc script thành tiếng: câu dài được sửa, đoạn liệt kê được biến thành quan hệ nguyên nhân–hệ quả.
- [ ] Voice không đều đều ở mọi đoạn; không chèn tiếng cười hay sợ hãi không phù hợp.
- [ ] Xem không tiếng vẫn hiểu ý hình; nghe không hình vẫn hiểu mạch. Hai phần bổ sung nhau khi ghép.
- [ ] Kiểm riêng 30 giây đầu, các question beats và đoạn kết ở kích thước điện thoại.
- [ ] Không có câu “scientists were shocked”, “terrifying secret”, “you won't believe” nếu nội dung không có cơ sở tương ứng.
- [ ] Không gọi hoạt cảnh minh họa là footage thật. Không bịa giai thoại cá nhân, lời phỏng vấn hoặc câu nói của nhà nghiên cứu.
