# Checkpoint và checklist một tập hằng ngày

**Gate mới về form và âm:** C3 bắt buộc role/mode/visual_answer/action và event âm theo voice; C6 kiểm trước/sau event, liền mạch chuỗi2D và biên Muse; C7 tách kiểm đồng bộ/âm lượng khỏi nghe duyệt và style acceptance. Chạy `python scripts/test_hybrid_pipeline.py` khi đổi validator. Xem [runbook](HYBRID_FORM_RUNBOOK.md).

Các cổng dưới đây là kiểm tra nội bộ của người sản xuất/agent. Người dùng không phải xác nhận từng bước. Khi đã có ủy quyền sản xuất cục bộ, tiếp tục các bước đạt điều kiện; chỉ hỏi khi thiếu thông tin thực sự quyết định công việc.

Áp dụng cùng [DAILY_EDITORIAL_SOP.md](DAILY_EDITORIAL_SOP.md) và [VIDEO_STYLE_STANDARD.md](../branding/VIDEO_STYLE_STANDARD.md). `editorial-packet.json` nối các đầu ra, không thay bằng chứng thực tế của mỗi gate. Tiêu chí mới được kiểm khi làm gate tiếp theo; không sửa hash để tự hợp thức hóa gate cũ.

## C0 — Brief và lời hứa

- [ ] Đọc `SESSION_HANDOFF.md`, `state.json`, `content-plan.json` và tập đang làm.
- [ ] Một câu hỏi chính, ít nhất ba bước mới dẫn tới lời giải, một kết có ý nghĩa.
- [ ] Hai title/thumbnail hypotheses; một câu nói rõ người xem nhận gì.
- [ ] Không trùng góc kể tập gần nhất; rõ vì sao đủ nội dung 8–10 phút.
- [ ] Có điểm hỏi hiện chữ, từ nhấn và callback.
- [ ] Packet có audience question, hai lời hứa thumbnail, địa chỉ cảnh chứng minh sớm và payoff cuối; không để lời hứa treo.

Bằng chứng: `episodes/Dxxx/BRIEF.md`. Pass = brief cụ thể đã được kiểm, không đồng nghĩa script đã xong.

## C1 — Facts

- [ ] Đọc nguồn chính, không lấy script đối thủ hay bình luận làm nguồn khoa học.
- [ ] `facts.json` có claim_id, câu diễn đạt, source URL + vị trí, ngày đọc, observation/hypothesis/interpretation, caveat.
- [ ] Mọi số đo, tỷ lệ, ngày tháng và “first/largest/oldest” được kiểm theo phạm vi; đơn vị Mỹ quy đổi đúng.
- [ ] Kiểm khác biệt loài/giới tính/giai đoạn trưởng thành; có reference anatomy.
- [ ] Claim thiếu nguồn bị bỏ hoặc ghi đúng mức bất định trong lời đọc; không chỉ bằng nhãn nhỏ.

Bằng chứng: `facts.json`, nguồn đã đọc, `research-notes.md`. Nguồn khởi đầu trong `sources.json` chưa tự làm C1 pass.

## C2 — Script và giọng kể

- [ ] Lời đọc Anh Mỹ nguyên bản; hook thực hiện lời hứa thumbnail trong 30 giây đầu.
- [ ] Hook có câu hỏi/điều trái kỳ vọng ở câu đầu; 5 giây đầu rõ chủ thể và lý do xem, 10–15 giây có hướng khám phá. Nếu dùng cấu trúc khác, ghi lý do. Xem `HOOK_AUDIO_REVIEW.md`.
- [ ] Mỗi đoạn giải quyết một ý rồi mới mở ý mới; không nhồi danh sách facts.
- [ ] Question beats được đặt có mục đích; có phản ứng/dự đoán tự nhiên, không hài gượng.
- [ ] Mọi claim trỏ claim_id; các ý giả thuyết vẫn giữ từ như may/could/proposed.
- [ ] Đọc thành tiếng và sửa câu khó nghe; chốt pronunciation.
- [ ] Có ước lượng 8–10 phút nhưng ghi rõ chưa đo TTS.

Bằng chứng: `script-en.md`, `script-claims.json`, `pronunciation.json`. Đây là cổng trước tạo voice, không đoán thời gian từ số từ.

## C3 — Storyboard và kế hoạch chữ

- [ ] Mỗi scene có visual_answer/new_information, reference, narration, nguồn, cảnh trả câu hỏi.
- [ ] Có on_screen_text, text_role, emphasis_word, voice_intent, pause_after_ms, answer_scene_id.
- [ ] Mỗi lớp hình/label/subtitle không cạnh tranh cùng lúc; câu hỏi có khoảng để đọc.
- [ ] Mỗi động từ chính có hành động/biến đổi hình tương ứng, ghi cue/timestamp, anticipation/action/result. Shot Muse có mục đích, không chèn ngẫu nhiên cho đẹp.
- [ ] So sánh dùng tỷ lệ; chuyển động có cơ sở giải phẫu. Theo `HYBRID_PRODUCTION_PIPELINE.md`: 2D giải thích, Muse tạo không khí/cảm xúc khi cần, tài liệu làm bằng chứng. Đọc hướng sửa D001 trong `D001_VISUAL_REBUILD.md`; v6 là thử nghiệm trước, không phải chuẩn hình đã được chấp nhận. Rig từng bộ phận chưa hoàn tất. AGENTS 3D áp dụng cho bài toán 3D khác.
- [ ] Khóa master/model sheet và asset_id cho mỗi loài; toàn thân/cận mắt/cắt lớp giữ cùng điểm nhận dạng. Mỗi scene có hành động, cue, điểm gắn cơ quan/tín hiệu và vị trí chữ sau chuyển động.
- [ ] Phân loại cinematic / explanatory / evidence / transition; không biến 8 clip pilot thành 9 phút kéo dài.
- [ ] Thumbnail concept và cảnh mở cùng lời hứa.
- [ ] Đọc bài học [D001 visual rebuild](D001_VISUAL_REBUILD.md): chia theo thay đổi thông tin/cỡ cảnh, không mặc định một đoạn voice là một hình giữ 15 giây. Ghi vị trí máy quay, hướng nhìn, hành động và kết quả nhìn thấy được.

Bằng chứng: `storyboard.json`, `thumbnail-brief.md`, reference sheet. Timing còn estimate cho đến khi có voice.

## C4 — Preflight sản xuất

- [ ] Đúng profile Muse mới, login thật, usage/quota đọc mới; không tự dùng account cũ do fallback.
- [ ] Nếu chưa đo account: thử 3 cảnh đại diện, ghi attempts, usable seconds, quota trước/sau và thời gian; quyết định shot budget từ kết quả.
- [ ] Không mua credit/gói, không đổi account để vượt hạn chế. Chạm hạn mức thì ghi lại và chuyển sang công việc không phụ thuộc.
- [ ] Voice provider và quyền sử dụng đã rõ; font, nhạc, ảnh/footage có provenance.
- [ ] Tạo manifest trước submit; mỗi job có episode, scene, version, prompt hash, profile_key, idempotency marker.

Bằng chứng: `production-preflight.json`, `asset-manifest.json`. Tài khoản login được chưa đồng nghĩa đủ quota cho 7 video/tuần. Chưa có kiểm này thì không gửi cả tập.

## C5 — Assets, voice và thumbnail

- [ ] Lưu receipt trước submit; có thread URL/job ID sau submit. Timeout chỉ chuyển needs_attention, không tự tạo lại.
- [ ] Đọc lại đúng thread đúng account khi resume. Receipt mơ hồ phải đối chiếu lịch sử trước khi gửi mới.
- [ ] Clip tải xong có SHA-256, duration, resolution, fps, provenance và QC giải phẫu.
- [ ] Reject ghi lý do; bản mới có version mới, không đè bản cũ. Không lặp generate vô hạn để đuổi deadline.
- [ ] Voice thực có word timestamps; khoảng nghỉ và trọng âm đúng câu; không giả voice cloning người khác.
- [ ] Thumbnail A/B xuất thật, thử 160×90/320×180, anatomy và quyền dùng đạt.
- [ ] Pose mới khớp nhân vật chuẩn; kiểm đầu–giữa–cuối động tác ở cảnh khó trước khi batch cả tập. Không lấy ảnh cùng loài nhưng khác hình dáng làm các pose của một nhân vật.

Bằng chứng: receipts, media files, voice + timestamps, asset-manifest, thumbnail-manifest. Có job completed chưa bằng có asset đạt.

## C6 — Dựng

- [ ] Dựng theo voice đã đo; tổng 480–600 giây. Không ghi 1080p/4K native nếu nguồn chỉ 720p.
- [ ] Text bám timestamp từ khóa; câu hỏi → pause → reveal đúng trật tự.
- [ ] Mỗi cảnh một ý, thường 2–5 từ nhấn lớn; số đo cạnh đúng vật. Kiểm chữ chính ở 320×180; chuyển nguồn dài sang mô tả, giữ nhãn hypothesis/reconstruction cần thiết.
- [ ] Có stem nhạc có nguồn/quyền rõ, giai điệu/hòa âm nghe được trên loa nhỏ và tự hạ dưới lời đọc; không coi drone trầm rất nhỏ là nhạc đã đạt.
- [ ] Có nhịp nghỉ và biến đổi ý; không nhạc/zoom/impact ở mọi cảnh.
- [ ] Phụ đề, nhãn đo, tên loài và nguồn không chồng; không ghép chữ bị cắt mép.
- [ ] Clean export: không nhãn “2D illustration”/“AI reconstruction”, HUD kỹ thuật hoặc progress bar. Giới hạn khoa học vẫn rõ bằng voice/nội dung, nguồn/credits lưu gói bàn giao.
- [ ] Tư liệu/AI/hypothesis phân biệt rõ khi cần. Hình thật thiếu quyền thì dùng sơ đồ có ghi rõ.
- [ ] Trước render dài khi đổi phong cách: xuất chuỗi 45–90 giây gồm môi trường, cơ chế và chuyển Muse↔2D. Kiểm bản MP4, sửa bố cục và động tác trước khi nhân rộng; không tự coi mẫu đã được chủ kênh chấp nhận.

Bằng chứng: timeline.json, subtitles.srt, render-vNN.mp4. Giữ bản sạch và bản có caption nếu cần.

## C7 — QC thực tế

- [ ] FFprobe: stream, thời lượng, fps, resolution; giải mã toàn bộ file không lỗi.
- [ ] Kiểm matrix/primaries/transfer/range màu từ file cuối. Với nguồn JPEG/BT.601 cần chuyển matrix thật khi xuất BT.709, không chỉ retag. Dùng probe/check/look đã thử trong `FFMPEG_SKILL_REVIEW.md`; đọc `ok`/từng check của công cụ đo, không suy đã duyệt nghệ thuật từ cờ verified. Audio theo mục tiêu dự án; phụ đề rời và track nhúng ghi đúng loại.
- [ ] Xem toàn bộ video từ đầu tới hết, nghe toàn bộ audio, ghi người/công cụ và thời gian duyệt. Nếu chưa nghe/xem được, mục này pending.
- [ ] Kiểm thêm toàn bộ question/emphasis beats ở màn hình nhỏ; không chỉ xem contact sheet.
- [ ] Không biến dạng sinh vật, đổi số chi, sai kích thước, captions chớp, frame đen, tiếng cắt/clipping hay nhạc lấn giọng.
- [ ] Với 2D cutout: kiểm nhiều pha đuôi/xúc tu trong MP4 cuối; không rách mép, lệch mắt/đầu hoặc kéo méo cả thân. Kiểm ảnh và chữ ở 320×180.
- [ ] Áp dụng `VISUAL_RESEARCH_2026-11-14.md`: nền kín viewport, chủ thể đủ lớn, bộ phận chuyển động nằm trong khung, chữ không đè sau zoom, nguồn chớp nằm đúng đối tượng. Ghi rõ mesh cục bộ hay rig bộ phận; không tuyên bố tương đương đối thủ chỉ từ độ phân giải.
- [ ] Đối chiếu facts, thumbnail promise, title, sự khác nhau giữa evidence và reconstruction.
- [ ] Contact sheet 12 cảnh cho thấy cùng brand nhưng có diễn biến hình; kiểm visual_answer/new_information từng beat, cắt phần chỉ lặp lại bơi/zoom. Contact sheet không thay xem/nghe trọn video.
- [ ] Xem cơ chế khi tắt tiếng: chủ thể, tác động, kết quả có đọc được trên hình không? Đối chiếu cảnh tham chiếu có cùng nhiệm vụ hình và cùng kích thước hiển thị. Ghi lỗi dàn cảnh riêng với lỗi kỹ thuật; decode/FPS/LUFS đạt không làm phong cách tự đạt.
- [ ] Issues nghiêm trọng = 0; sửa đúng cảnh rồi kiểm vùng ảnh hưởng. Không dùng số đo âm lượng thay kiểm nghe.

Bằng chứng: qc.json với issue IDs/timestamps/resolution, ffprobe.json, decode.log và hash file cuối. Không tự tick đã nghe nếu chỉ phân tích waveform.

## C8 — Bàn giao

- [ ] Có MP4 cuối, SRT, hai thumbnail, title, description + sources, chapters tính theo timeline thật, credits/rights và upload notes.
- [ ] `delivery-manifest.json` có hashes/versions, không có cookie/profile/token đăng nhập.
- [ ] Mở phát thử file cuối và kiểm link tệp thật tồn tại.
- [ ] Cập nhật state, ledger, session handoff và việc đầu tiên phiên sau.
- [ ] Trạng thái `ready_for_user_review`, chưa phải `published`. Chỉ upload/publish khi có yêu cầu rõ của người dùng.

## Sau khi người dùng đăng

- [ ] Ghi video URL, ngày/giờ đăng và version title/thumbnail. Không đoán đã đăng.
- [ ] Thu Analytics khi có quyền/dữ liệu: impressions, CTR theo nguồn, 30s retention, average view duration, watch time, các điểm rớt, comment themes.
- [ ] 24h/72h/7d là mốc xem xét dự kiến sau khi đăng, không tạo job nền giả. Nếu số liệu còn ít hoặc chưa xử lý thì ghi thiếu.
- [ ] A/B test có thể chưa có kết luận; không chọn thắng chỉ từ CTR hoặc vài giờ view.
- [ ] Mỗi tuần chọn 1–2 thay đổi có lý do; ghi vào decisions. Giữ lịch linh hoạt nếu đề tài gần đây lặp hoặc quota chưa đủ.

## Handoff bắt buộc trước kết thúc mọi phiên

Ghi tập hiện tại, checkpoint đã pass kèm evidence/hash, việc đang chạy và receipt, blocker thật, quyết định mới của user, đúng một next action cụ thể và những file cần đọc. Không ghi “tiếp tục sản xuất” chung chung. Không coi hết phiên là thất bại của job Muse. Không tự mở tập mới để tránh hoàn tất tập đang dang dở.
