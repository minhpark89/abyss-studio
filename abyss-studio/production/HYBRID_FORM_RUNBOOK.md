# Pipeline theo chức năng hình và âm

**Nhiệm vụ hiện hành (15/11/2026):** D002 v5 bị owner từ chối; chuẩn là D001 đã đăng. Đọc CURRENT_BRIEF.md, TASK_LEDGER.md và state.json để lấy phiên bản/job/next action. Các lệnh và mẫu D001 dưới đây giải thích pipeline lịch sử, không phải chỉ dẫn quay về sản xuất lại D001 hoặc bỏ dở D002.

Nguồn quy tắc: [phân tích fGcgWaswMns](REFERENCE_FUNCTION_LED_ANALYSIS.md). Ưu tiên mới nhất: giải thích/so sánh bằng 2D, cảnh không gian bằng Muse khi có ích; âm thanh khớp diễn tả. Không ép tỷ lệ chất liệu.

## Mở và chạy thật

Từ `E:\YOUTUBE\abyss-studio`, đọc state/handoff rồi:

```powershell
python scripts/daily-status.py --validate
python scripts/hybrid_pipeline.py validate --plan production/episodes/D001/hybrid-form-v1/plan.json
```

Mẫu xuất: `production/episodes/D001/hybrid-form-v1/D001-hybrid-form-v1.mp4`. Mở `review.html` cùng thư mục hoặc mở MP4 trực tiếp. Không chạy lại render trên version có output; script bảo vệ file cũ.

Với **plan/version mới** đã biên tập và có asset:

```powershell
python scripts/hybrid_pipeline.py stills --plan <plan-moi.json>
python scripts/hybrid_pipeline.py all --plan <plan-moi.json>
```

`all` chạy render → audio → assemble → QA. Nó không tự viết script, tạo model/pose, gọi Muse, đăng video hay duyệt mỹ thuật. Có thể chạy riêng `render`, `audio`, `assemble`, `qa` khi tiếp tục việc dở. Không chạy `prepare-function-led-proof.py` lần hai để reset mẫu; script từ chối overwrite plan.

Sau khi MP4 cuối qua QA, kiểm playback liên tục riêng:

```powershell
node scripts/check-hybrid-playback.mjs --plan <plan-moi.json>
```

Đây là phát tự động1× tắt tiếng để kiểm lỗi/rớt frame, không thay nghe duyệt. Mẫu đầu phát hiện thiếu transfer/primaries; bản cuối đã chuyển từ sRGB của canvas sang709 thật, bỏ ICC cũ, không chỉ gắn nhãn. Renderer mới làm chuyển đổi trong một lần encode; mẫu đầu dùng một bước sửa riêng, có log trong `qa/color-conversion.json`. Những file có `before-color-fix` và `picture-before-rain-sync` là thử trung gian, không phải bản giao.

## Contract

Plan gồm episode, output, output_filename, rig_path, fps, total_frames, source_start/end, đường facts/audio, assets có hash/provenance/trạng thái confirmed_local, shots và events. Timeline dùng số frame nguyên, phủ liên tục không gap/overlap. `source_start/end` xác định đoạn voice gốc; thời lượng render chốt bằng frame để không trôi khi ghép.

Mỗi shot: `in/out`, `mode`, `role`, `template`, `visual_answer`, `action`, claim IDs nếu giải thích khoa học, nhóm cơ chế `causal_group` và chữ có thời điểm. Muse thêm asset và offset; không tự loop/freeze kéo đủ thời lượng. Template đã chạy: cinema, depth, signal, collection, area. Template khác cần module thật và kiểm khung; validator chặn tên chưa triển khai. Các template hiện tại là thư viện khởi đầu, chưa bao phủ mọi tập biển sâu.

Mỗi event: ID, frame, anchor segment/word/source_seconds, loại âm hoặc none, peak và ý nghĩa. Renderer và mixer cùng đọc event. `none` là lựa chọn chủ ý. Âm tổng hợp trong mẫu là accent biên tập, không nhận là bản ghi tiếng động vật.

## Checkpoint hàng ngày

- [ ] **C1–C2:** claim có nguồn, câu hỏi có đáp án/giới hạn; script không đổi chỉ để dễ dựng.
- [ ] **C3:** chọn đúng chức năng; biên Muse/2D ở chỗ đổi ý; toàn/cận/so/cắt lớp có lý do. Chốt cả cue âm.
- [ ] **C4:** đúng account/quota/receipt trước generation; quyền voice/nhạc và provenance. Hai receipt Muse mơ hồ hiện có phải đối chiếu, không submit lại.
- [ ] **C5:** model/pose cùng silhouette; asset đủ; thấy trước–tác động–sau. Thước/tỷ lệ đúng. Muse không đóng vai bằng chứng.
- [ ] **C6:** xem still và trước/sau mỗi event; mute hiểu được quan hệ; tiếng không che lời. Một chuỗi45–90s khó nhất đạt rồi mới chạy dài.
- [ ] **C7 kỹ thuật:** contract, frame count, decode, màu709/range, âm lượng, phụ đề, full playback. Chạy negative tests khi sửa validator.
- [ ] **C7 biên tập:** nghe tai nghe + loa nhỏ; xem điện thoại; hình trả lời đúng động từ; không nhãn kỹ thuật; không lẫn giả thuyết với footage. Số kỹ thuật không thay việc duyệt này.
- [ ] **C8:** MP4/SRT/thumbnail/title/description/provenance/manifest; state/journal/handoff. Không upload/publish khi chưa được yêu cầu.

## Mẫu68,2s để kiểm gì

| Thời gian mẫu | Việc hình và âm làm |
|---|---|
| 0:00–0:06,27 | Muse đặt không gian; lời dẫn vào biển tối |
| 0:06,27–0:18,87 | 2D mốc độ sâu; tick tại đại lượng |
| 0:18,87–0:35,87 | Nước tối và tín hiệu; flash và accent chung event; photon không có tiếng riêng |
| 0:35,87–0:51,87 | Hai xô cùng mưa → khẩu độ cùng ánh sáng; mưa ngắn, sweep ở chuyển phép so |
| 0:51,87–1:08,20 | Đường kính/diện tích; tick tại kết quả; hạ nhạc ở giới hạn khoảng nhìn |

Đây là mẫu chạy form, không phải đã đạt mỹ thuật đối thủ. Muse nguồn720p, đầu ra1080p. Voice review hiện tại chưa xác nhận quyền phát hành. Bản D001 dài và mẫu81s trước giữ nguyên.

## Next action

Next action cụ thể nằm trong state.json và đầu SESSION_HANDOFF.md. Hiện tiếp tục D002 revision-v6 theo D001 đã đăng, với phụ đề Anh gắn vào bản xem MP4; không quay về bản chỉ một mô hình 3D và không chuyển sang D003 để bỏ dở. Chưa có Scheduled task; 1 video/ngày vẫn là mục tiêu cần đo qua các tập thật.

Tiêu chí kiểm mẫu vẫn áp dụng: không nghe có hiểu quan hệ không; chỉ nghe có bị SFX tranh lời không; đổi Muse/2D có đúng lúc ý thay đổi không. Chỉ gọi một phần đã kiểm khi có evidence đúng phạm vi.
