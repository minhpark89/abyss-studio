# Quy trình biên tập và sản xuất hằng ngày — Abyss Fieldnotes

**Cập nhật phân vai hình/âm:** ở C3 dùng [pipeline theo chức năng](HYBRID_FORM_RUNBOOK.md), không chia tỷ lệ Muse. Mỗi beat ghi việc hình làm và cue âm hoặc chủ ý im lặng; khóa voice–frame–action/text/audio chung một event. Không chèn cinematic giữa nguyên nhân và kết quả. Tham chiếu [fGcgWaswMns](REFERENCE_FUNCTION_LED_ANALYSIS.md).

Mục tiêu đã chốt: **1 video/ngày, 8–10 phút, en-US hướng Mỹ**. Lấy Depth Theory làm benchmark chính về sự liền mạch giữa đóng gói, câu chuyện và hình; giữ thương hiệu riêng. [Bằng chứng so sánh](CHANNEL_BENCHMARK_2026-11-14.md). Đây là quy trình thực hiện trong mỗi phiên, không phải tuyên bố có Scheduled task hoặc worker tự làm trọn tập.

## Trình tự không đổi

| Bước | Việc phải làm | Đầu ra để session sau tiếp tục | Gate |
|---|---|---|---|
| Mở phiên | Đọc START_HERE/handoff/state, chạy validator; giải quyết job/receipt dở | Một active episode và một next action | Gate hiện tại |
| Khóa lời hứa | Một câu hỏi người xem quan tâm, một thay đổi cách hiểu ở kết, hai hướng title/thumbnail | `editorial-packet.json`, BRIEF | C0 |
| Kiểm nội dung | Nguồn sơ cấp, từng claim/certainty, điều chưa biết, facts đủ triển khai câu hỏi | `facts.json` | C1 |
| Viết câu chuyện | Hook thực hiện lời hứa, 3–5 bước suy luận, bằng chứng/phản biện và callback | `script-en.md`, mapping claim | C2 |
| Dàn hình | Khóa nhân vật/style; mỗi beat có visual_answer và động tác; đo voice rồi gắn cue | storyboard/timing, model sheet, thumbnail brief | C3 |
| Sản xuất | Kiểm account/quota/voice; tạo đúng pose/rig/Muse cần; giữ manifest/receipt | assets có nguồn/version/QC, voice/music | C4–C5 |
| Dựng và kiểm | Đồng bộ hình–lời–chữ; mix; xuất; xem/nghe hết và sửa | MP4, SRT, QA/hash, contact sheets | C6–C7 |
| Bàn giao và học | Title/thumbnail/mô tả/sources/chapters; state/journal/handoff; chỉ đọc Analytics sau khi có video được đăng | delivery manifest, metrics snapshots, một giả thuyết cải tiến | C8/sau đăng |

Không mở tập khác để né tập chưa xong. Không kéo loop cho đủ480 giây. Khi chậm vì asset/cloud, làm phần độc lập của **cùng tập** hoặc chuẩn bị facts tập kế tiếp mà không đổi active episode. Không bỏ gate chất lượng để đạt con số một video trong ngày. Cổng nội bộ không có nghĩa hỏi user xác nhận từng bước đã được ủy quyền.

## 1. Lời hứa: chốt trước khi làm hình

Điền packet bằng một câu dễ nói: “Sau video, người xem sẽ hiểu ___ bằng ___.” Ghi đối tượng người xem phổ thông và kiến thức nền cần có. Một thumbnail chỉ đặt một câu hỏi chính; title bổ sung chủ thể/phạm vi, không lặp nguyên chữ trên ảnh.

Chuẩn bị A/B khác ý, không chỉ đổi màu. Mỗi phương án phải chỉ tới một cảnh mở chứng minh lời hứa và một cảnh trả lời đầy đủ. Nếu không xác định được hai cảnh đó, chưa gửi tạo thumbnail hàng loạt. Hai biến thể ban đầu của D001 tiếp tục là mắt/đĩa và giả thuyết cảnh báo, không đổi sang nguy cơ săn người.

## 2. Script: tăng diễn biến thông tin

Khung thử cho khoảng9 phút, thời gian chỉ là **ước tính** tới khi có voice:

- 0:00–0:30: chủ thể, điều lạ, bằng chứng hình đầu tiên và câu hỏi chính. Không intro logo dài.
- 0:30–1:20: định vị điều đang đo/quan sát, giải quyết hiểu nhầm nền tảng.
- 1:20–3:00: cơ chế thứ nhất bằng so sánh/cận bộ phận; trả một câu hỏi nhỏ.
- 3:00–5:00: thay điều kiện hoặc đưa hệ quả khiến lời giải ban đầu chưa đủ.
- 5:00–7:00: bằng chứng và giới hạn/phản biện; không liệt kê nhiều facts rời.
- 7:00–8:30: nối các phần thành lời giải có mức chắc chắn phù hợp.
- 8:30–9:00: callback, ý nghĩa mới, một câu hỏi kế cận. Chỉ dẫn video tiếp theo nếu video đó thật sự có.

Không bắt mỗi tập đúng các mốc này. Với câu trả lời đơn giản, trả sớm rồi mở bài toán sâu hơn. Mỗi đoạn cần ghi `new_information`; nếu chỉ lặp cảm giác “đáng sợ/kỳ lạ” thì sửa hoặc cắt. Mỗi lời hứa chưa trả phải có địa chỉ payoff, không chồng thêm nhiều bí ẩn vô cớ.

Đọc thành tiếng, sửa câu dài và cách phát âm. Hài nhẹ chỉ khi giúp hiểu; không mượn câu đùa đối thủ, không giả trải nghiệm lặn. Mọi số liệu, sự kiện và giả thuyết liên kết claim_id đã kiểm. “Có thể” và “mô hình đề xuất” xuất hiện tự nhiên ở nơi cần, không bị giấu trong một dòng nhỏ cuối phim.

## 3. Brand: khóa trước batch asset

Dùng `branding/video-style.json` và [VIDEO_STYLE_STANDARD.md](../branding/VIDEO_STYLE_STANDARD.md) làm chuẩn. Mỗi loài có master/model sheet với anatomy được kiểm; mỗi scene dùng lại ID, palette, tỷ lệ và điểm nhận dạng. Pose mới vẫn là cùng nhân vật. Không phát prompt độc lập khiến mắt/chi/vây đổi qua từng shot.

Mỗi storyboard scene có: mục đích thông tin, mode, asset_id/version, claim_ids, hành động chính, cue từ voice, pivot/đường đi, vị trí chữ, chuyển cảnh và bằng chứng QA cần lấy. Dùng tám loại cảnh trong style standard để thay cách giải thích. Chọn theo ý; không ép đủ số loại hay cắt cảnh theo đồng hồ.

Động từ như “xoay”, “phát hiện”, “thu ánh sáng”, “kẹp”, “nổi lên” phải có biến đổi nhìn thấy được. Chớp/tín hiệu kết thúc đúng tọa độ cơ quan nhận; head/eye giữ ổn định khi phần khác di chuyển. Nếu cần thay pose, tạo pose/rig cần thiết, không chỉ rung toàn ảnh. Với v6 hiện tại, phải ghi rõ mesh cục bộ chưa phải rig đầy đủ.

## 4. Phân vai hình và kiểm trước render dài

2D giải thích cơ chế; cảnh Muse gợi không gian/cảm xúc khi có vai trò; bằng chứng dùng để phân biệt điều đã quan sát và mô hình. Không có quota phần trăm Muse bắt buộc. Đừng đặt footage đẹp vào giữa câu đang giải thích khiến người xem mất dấu quan hệ.

Trước batch dài: duyệt storyboard toàn tập, kiểm một scene khó nhất cần pose/khớp, một scene cơ chế, một scene có nhiều lớp chữ. Đây là preflight nội bộ của tập thật, không tạo thêm video demo ngoài yêu cầu. Kiểm Muse đúng profile và receipt; chưa đo quota thì thử3 cảnh đại diện theo MUSE_ACCOUNT. Không tự mua credit.

## 5. Checklist bắt buộc ở bản dựng

- [ ] Thumbnail/title và30 giây đầu hứa cùng một điều; có một bằng chứng hình sớm.
- [ ] Mỗi beat thêm thông tin; không kéo cảnh bơi/zoom để lấp thời lượng.
- [ ] Nhân vật không đổi mắt/chi/vây giữa các scene; schematic không giả số đo thật.
- [ ] Nền phủ viewport; cỡ chủ thể phù hợp toàn/cận/cơ chế; phần đang chuyển động nằm trong khung.
- [ ] Chữ ngắn, đọc được ở320×180, không che chủ thể ở **cuối** chuyển động camera.
- [ ] Kiểm động tác đầu–giữa–cuối và từng trigger→kết quả ở MP4 cuối.
- [ ] Contact sheet12 cảnh thể hiện cùng một kênh nhưng có diễn biến hình ảnh.
- [ ] Nhạc/voice/SFX rõ trên loa nhỏ; có ducking; nghe thực tế, không tick từ waveform.
- [ ] Decode toàn file; xem/nghe trọn video; kiểm SRT, cut, khoảng lặng và hash.
- [ ] Metadata, số đo và giới hạn khoa học khớp facts. Không có nhãn kỹ thuật/debug/footer.

Lỗi facts, anatomy trọng yếu, lời hứa không trả, audio khó nghe hoặc cảnh khó hiểu phải sửa trước bàn giao bản sẵn đăng. Không dùng một điểm tổng hợp để che các lỗi này. Khi chỉ kiểm muted hoặc sampled frames thì ghi đúng phạm vi; không tự tick full-view/full-listen.

## 6. Nhịp làm việc để tiến tới một tập/ngày

Trong giai đoạn D001: hoàn thiện đúng tập và ghi giờ bắt đầu/kết thúc từng công đoạn, số lần tạo asset, số giây usable, thời gian sửa. Khi có ba tập dài được kiểm, dùng số thật để điều chỉnh tải. Thời gian cloud và tỷ lệ asset đạt chưa đo nên không hứa số giờ cố định.

Khi dây chuyền chạy được: sản xuất tập đang dở, đồng thời giữ2–3 brief/facts kế cận đủ chín cho ngày sau; gom việc cùng loại như model sheet hoặc sơ đồ dùng chung. Tái dùng **hệ thống hình**, không tái dùng nguyên nội dung rồi thay tên loài. Mục tiêu buffer2 tập đã QC khi năng suất cho phép; đây không phải cớ trì hoãn bàn giao user đã yêu cầu.

## 7. Sau khi có video được đăng

Ghi snapshot24h,72h,7d khi dữ liệu có; retention có thể chưa xử lý ở24h. Mỗi snapshot giữ URL, tuổi video, phiên bản title/thumbnail và traffic source. Không tạo số0 cho dữ liệu chưa có. Không có Scheduled task thật thì các mốc này là lịch xem xét, không phải job nền đã chạy.

| Tình huống quan sát | Việc kiểm trước | Thử nghiệm có thể làm |
|---|---|---|
| Ít impressions | Tuổi video, nguồn traffic, số liệu đã xử lý, mức liên quan chủ đề và các video cùng nhóm | Chờ đủ dữ liệu/ghi thiếu; chưa kết luận bị chặn |
| Impressions đủ để so, ít người chọn xem | Title/thumbnail có rõ câu hỏi và đúng nhóm người xem không | Một phương án đóng gói khác ý, giữ hồ sơ phiên bản |
| Có click nhưng rớt sớm | Lời hứa có lệch, intro có chậm, voice có khó nghe không | Sửa cách mở ở tập kế tiếp; không đổ hết cho thumbnail |
| Rớt ở scene cơ chế | Chữ khó đọc, thiếu bước trung gian, hình/voice lệch hoặc nội dung lặp | Một cách giải thích rõ hơn; kiểm lại hình trước khi thêm hiệu ứng |
| Xem tốt nhưng ít quay lại | Catalog có các câu hỏi liên quan và lý do xem tiếp không | Một tập kế cận thực sự hữu ích, kết nối end screen khi đã có video |

So theo nguồn Browse/Suggested/Search, độ dài và tuổi video; không lấy CTR toàn kênh này so mù với kênh khác. Không suy một spike chắc chắn là đoạn thích nhất. Chỉ chọn1–2 giả thuyết cải tiến mỗi tuần, ghi cả yếu tố gây nhiễu; không đổi toàn bộ brand vì một video ít view.

## Kết thúc phiên

Lưu file thật/hash và phạm vi QA; cập nhật state, journal, handoff, job đang chạy và đúng một next action. Giữ quyền upload/publish theo lệnh user, không coi hoàn tất sản xuất là đã đăng. Câu lệnh tiếp tục: **“Tiếp tục D001 theo checkpoint và quy trình biên tập mới.”**
