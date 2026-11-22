# Codex Video Factory

Xưởng cục bộ chạy cùng Abyss Studio. Mã dựng, luật từng niche, bảng cảnh và báo cáo nằm trong Git. Take Muse, model, bản âm và MP4 nằm trong thư mục sản xuất trên máy.

## Tạo tập

Chạy `python factory.py list`. Với yêu cầu “Chạy niche karma-drama, tập SB06, chủ đề …”, Codex đọc AGENTS.md, khởi tạo bằng `python factory.py init karma-drama SB06`, soạn beat, cast, shot board và audio cue theo brief, rồi chạy `python factory.py run karma-drama SB06`. Tập đã chạy tiếp tục dùng cùng receipt. Phác thảo shot board trước khi gửi Muse.

Trong `board.json`, mỗi shot có `id`, `frames`, `in_frame` tính từ đầu take sạch. Với take có sẵn, đặt `source` và tùy nguồn đặt `receipt`. Với take mới, đặt `scene`, danh sách khóa `cast`, ảnh `ref` trong refs và mô tả `action`. Bảng cast ánh xạ khóa sang mô tả. Muse dùng backend cục bộ của Studio. Đặt `native_dialogue` khi giữ tiếng take. Track độc lập trong `audio` dùng `source`, `at_frame`, `in_seconds`, `seconds`, `gain_db`. `captions` nhận đường dẫn ASS. Đặt đường dẫn media tương đối từ thư mục tập. Với ADR, chốt mặt và waveform như mô hình SB05 trước khi conform.

Với bảng cảnh mới của `karma-drama`, ghi `beat_id`, `confrontation` (mã cảnh đối chất nếu có), và `line` cho từng shot. Đánh dấu khoảng lời và hành động đã quan sát theo đồng hồ dựng trong `audio_cues.json`. Factory cắt những khoảng trống còn dư rồi dời hình, lời, nhạc và hiệu ứng cùng số khung. Mẫu cue và lệnh mix nằm trong [hướng dẫn Audio Engine](core/audio_engine/INTERFACE.md).

Điền `qa/visual-evidence.json` bằng khung hình đã xem của từng take. Mỗi người trong `cast` có ảnh tham chiếu cùng SHA-256. Mỗi take có mã băm của MP4 và ảnh kiểm, `cast`, `approved_spans`, `shared_spans`, khung cắt `crop` nếu dùng, cùng kết luận và quan sát cụ thể cho `hands_and_wardrobe`, `background_cast` và `beat_emotion`. Các khoảng tính bằng frame nguồn, điểm cuối loại trừ. Điền mã các cảnh đối chất vào `confrontations`. Các cảnh đơn độc có thể ghi trong `non_confrontations` cùng lý do. Với take Muse hỏng, lần chạy tiếp theo dùng biên nhận riêng cho take sửa, rồi chờ kiểm chính take mới. Xem cấu trúc trong [bài kiểm thử chạy hết quy trình](core/assembler/test_drama.py).

## Dựng lại SB05

Với môi trường Python mới, cài `python -m pip install -r requirements.txt` cho bộ dựng theo shot board. Dùng `requirements-sb05.txt` cho bước phục hồi khẩu hình và QA của mẫu SB05. Giữ các model và dữ liệu phim ở thư viện sản xuất như mô tả bên dưới.

Máy sản xuất có Python 3.11, FFmpeg của Studio, OpenCV, NumPy, SciPy, SoundFile, PyAV, librosa, ONNX Runtime DirectML, torch CPU, MediaPipe, Pillow và Playwright. Ba thư mục SB05, revision-2 và rea-pass bên Studio cung cấp take, giọng, model, bằng chứng và timeline nguồn. Đặt `ABYSS_STUDIO` khi chuyển kho media. `FFMPEG` chọn encoder khác có NVENC khi dựng lại SB05.

Khôi phục bản ghim bằng `python repos_vendor/bootstrap.py` rồi `npm ci --ignore-scripts`. SyncNet dùng trọng số từ download_model.sh của bản ghim vào repos_vendor/syncnet_python/data. Cài python_speech_features 0.6 vào .cache/py. Chạy `python factory.py run karma-drama SB05` để xuất lại. Bản SB05 hiện hành dùng nguyên khung Muse và căn màn diễn theo thoại. Timeline chỉnh được và master nằm trong abyss-studio/production/episodes/SB05/source-cut.

## Phòng xem

**SB06 · Seat Seven.** Từ thư mục xưởng, `python -X utf8 factory.py run karma-drama SB06` dựng lại bản đã chốt từ các take có biên nhận. Danh sách cắt nằm trong `abyss-studio/production/episodes/SB06/edit.json`. Một giá trị `native_audio_offset_frames` dương cho biết tiếng của chính take được đưa lên sớm bao nhiêu khung. Hình chạy ở tốc độ gốc. [Phòng xem và bảng vai trò từng repo](http://127.0.0.1:4320/dashboard#watch=/production/episodes/SB06/delivery/review.html).

Các mô-đun của tập ở `production/karma-drama/SB06/`. `research/verify-sources.mjs` khôi phục các tệp upstream theo commit và SHA. `contracts.py` tạo kế hoạch cùng các frame đầu/cuối. Bộ kiểm dùng `jsonschema==4.25.1` (tập này đã cài tại `.cache/sb06-contracts`). `native-av.mjs` đối chiếu frame, sóng âm và khẩu hình của MP4. Trong thư mục tập, `python -X utf8 reproduce.py --resume-review` kiểm lại bản có SHA khớp với danh sách cắt. [Nguồn và giấy phép](production/karma-drama/SB06/research/README.md).

Trong Abyss Studio, chọn **Pipeline & repo** hoặc mở [bảng điều hành](http://127.0.0.1:4320/dashboard). Hai địa chỉ dashboard dùng chung giao diện và máy chủ của app. Bảng đọc các tập trong Studio và Factory, đối chiếu lệnh đã chạy với repo được chọn cho từng công đoạn. Các trace lịch sử thiếu lệnh được đánh dấu để kiểm tra.
