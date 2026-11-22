# Phòng xem SB09

Từ `E:\YOUTUBE`, sau khi khóa hình ở `delivery/picture.mp4` và cue, gọi mixer qua `node codex-video-factory/production/karma-drama/SB09/mix.mjs` (tùy chọn `--voice <stem.wav>`). Trình này gọi giao diện Python của Audio Engine và lưu biên nhận thực thi Pedalboard. Chạy các lệnh dưới sau khi kiểm bản mix cuối:

```powershell
node codex-video-factory/production/karma-drama/SB09/room.mjs
python -X utf8 codex-video-factory/production/karma-drama/SB09/playback.py
node codex-video-factory/production/karma-drama/SB09/room.mjs
```

Đầu vào nằm trong `abyss-studio/production/episodes/SB09/`:

- `delivery/The-Stolen-Label.mp4`, `delivery/audio-trace.json`, `delivery/QA.json`, báo cáo Vision QA và `edit.json`. Truyền đường dẫn khác bằng `--master`, `--audio`, `--qa`, `--vision`, `--edit` (tính từ thư mục tập). Báo cáo QA ghi `sha256` của MP4 đã giải mã, `duration_seconds`, `issues: []`. Vision ghi `ok: true` hoặc `passed: true` và phải khớp master, edit hoặc được QA ghim bằng `vision_sha256`. Audio ghi hash master cùng danh sách cue BGM/SFX thực dùng. Mỗi cue có tên file hoặc mã cue cùng thời điểm (giây). 
- Các biên nhận lệnh thành công nằm trong chính báo cáo, hoặc các file JSON bổ sung qua `--commands <file>` (dùng lặp lại). Các file bổ sung phải ghim hash của master, edit hoặc picture đã dùng. Mỗi lệnh có `argv` hoặc `command`, `exit_code`, `cwd` và, nếu thực sự dùng repo trong sổ, `repo`, `stage`, `commit` khi sổ đã ghim. Giữ lệnh thật, kể cả khi còn thiếu công đoạn trong sổ.
- Chapter lấy từ `edit.cuts[].beat_id` hoặc `shots[].beat_id`; tên tiếng Việt tùy chọn trong `story.beats[].title_vi`. Chỉ các beat có trong bản dựng mới xuất hiện.

Lệnh tạo `delivery/review.html`, `delivery/execution_trace.json` và bản trace đọc từ bảng điều khiển. Khi chạy lại sau khi kiểm phát hết phim, trace tự bổ sung biên nhận phát đúng mã SHA-256.

Phòng xem nằm tại [Dashboard SB09](http://127.0.0.1:4320/dashboard#watch=/production/episodes/SB09/delivery/review.html).

Máy 4320 đang phục vụ các tác vụ Muse có biên nhận. Khi native server còn giữ module registry phiên bản cũ trong bộ nhớ, dashboard trên cùng địa chỉ dùng trình phục vụ registry tạm tại loopback 14320. Trình này chỉ nhận Origin của Studio trên 4320 và tự thoát sau lần native server kế tiếp nạp module mới. Nếu cần khởi động lại riêng trình phục vụ tạm, chạy `node codex-video-factory/core/dashboard_4320/live-registry.mjs`.
