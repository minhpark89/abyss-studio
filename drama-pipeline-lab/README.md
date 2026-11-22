# Drama Pipeline Lab

Repo cục bộ dùng cho phim ngắn Second Bell. Mỗi tập có một hồ sơ vận hành. SB08 chạy hồ sơ `cn` với một đường tạo video qua Muse của Studio. Repo này đọc storyboard, biên nhận, take và bản dựng của tập. Lệnh kiểm tra có thể chạy lại khi Muse đang xử lý và không gửi tác vụ tạo video.

| Thành phần trong hồ sơ CN | Phần thực thi tại máy |
| --- | --- |
| Hao0321/ai-short-drama | Xác thực studio plan của tập bằng JSON Schema ở commit đã khóa. |
| HBAI-Ltd/Toonflow-app | Chạy hàm TypeScript xác định thư mục tài sản nào còn được tham chiếu. Kết quả chỉ là danh sách để xem xét. |
| Echo-Note/localminidrama | Chạy migration SQLite thêm các cột góc máy vào storyboard. |
| xuanyustudio/LocalMiniDrama | Chạy bộ ghi tham số SQL của nhánh này để gắn ảnh đầu/cuối vào đúng shot, sau đó truy vấn lại hai đường dẫn. |
| HKUDS/VideoAgent | Dispatcher gốc gọi hai bước cục bộ theo thứ tự. Bước storyboard lập kiểm kê, bước review đối chiếu kết quả và ghi báo cáo. |

Năm thành phần đọc và ghi các phần khác nhau. Chỉ Studio gửi take qua Muse. Mỗi lần chạy có thư mục bằng chứng riêng, lưu hash của nguồn và đầu vào. Chương trình không ghi registry ACTIVE chung hay thay dịch vụ dashboard. Hồ sơ `us` lưu OpenMontage, video-shotcraft, agentic-video-editor, Generative-Media-Skills và pexo-skills kèm tên đầy đủ, commit, giấy phép và danh sách file, để dùng trong lượt đối chứng sau.

## Chạy trong workspace E:\YOUTUBE

```powershell
python -X utf8 drama-pipeline-lab/pipeline.py profiles
python -X utf8 drama-pipeline-lab/pipeline.py plan --episode abyss-studio/production/episodes/SB08
python -X utf8 drama-pipeline-lab/pipeline.py takes --episode abyss-studio/production/episodes/SB08
python -X utf8 drama-pipeline-lab/pipeline.py review --episode abyss-studio/production/episodes/SB08
python -X utf8 drama-pipeline-lab/test_pipeline.py
```

- `inventory` có thể dùng khi storyboard đang viết. Báo cáo liệt kê beat chưa có shot.
- `plan` yêu cầu từng beat có cảnh thể hiện, tiền điều kiện khớp với trạng thái đang biết, và kết quả từ beat nguyên nhân xuất hiện trong tiền điều kiện của beat sau. SB08 khai báo trạng thái trực tiếp trong `story.json`. Khi chuyển tập cũ, có thể truyền một bản mô tả bằng `--state PATH`. Xem [giao diện tập](INTERFACE.md).
- `takes` kiểm SHA-256 của take/ảnh tham chiếu theo biên nhận. Chương trình giải mã ảnh đầu/cuối các take đã hoàn thành và liệt kê những take còn chờ. Có thể chạy trong lúc render.
- `review` đọc edit thật. Nó kiểm thứ tự beat, số khung, thời lượng, dấu vết Muse, âm thanh hiện diện, lấy mẫu hình giữa mỗi cut và đối chiếu với take nguồn. Điểm vào/ra dùng số khung ở fps gốc. Cảnh đổi tốc độ cần ghi ý đồ, thời lượng sau kéo giãn và biên âm thanh trong timeline dựng. Khung đầu/cuối lấy từ video đã mã hóa rồi mới gắn vào storyboard. Chỉ kết quả chạy thành công mới cập nhật con trỏ `qa/drama-pipeline/review.json`.

Việc so hình giữa cut dùng sai số RGB trung bình trên ảnh nhỏ, với dung sai thời gian hai khung. Đây là kiểm tra nguồn của clip. Khẩu hình, sức nặng của diễn xuất, tiết tấu và mức khán giả hiểu cú lật vẫn cần phát phim và kiểm riêng. Độ chậm vốn đã sinh trong một take 1× cũng cần nhìn chuyển động thực tế. Dữ liệu Studio về audio/lip-sync và duyệt nội dung thuộc quy trình kiểm phim của tập.

## Đạo diễn, thu take và dựng bản xem

Chạy từ thư mục workspace. Lệnh đầu tạo bảng đạo diễn sáu trường cho từng take và nối xung đột, bằng chứng, cái giá phải trả, quyết định và hệ quả với hành động trước máy quay.

```powershell
$episode = 'abyss-studio/production/episodes/SB08'
python -X utf8 drama-pipeline-lab/direct.py plan --episode $episode
python -X utf8 drama-pipeline-lab/muse_take.py --episode $episode --shot T02 --reuse-only
python -X utf8 drama-pipeline-lab/direct.py cuts --episode $episode
python -X utf8 drama-pipeline-lab/render_muse.py $episode --ffmpeg (Resolve-Path abyss-studio/tools/ffmpeg-nvenc/ffmpeg.exe).Path --ffprobe 'E:/OPENCLAW/LONGFORM APP/fix-2026-10-16/LongformStudio/_internal/bin/ffprobe.exe'
```

Truyền đường dẫn tuyệt đối tới hai công cụ dựng khi chạy từ thư mục khác. `direct.py cuts` và `render_muse.py` đọc `edit.json` đã khóa. Để lấy một take mới hoặc chờ biên nhận đang dở, chạy `muse_take.py --episode ... --shot ...` cùng mã shot và `production.project_key` cũ. Studio giữ mã yêu cầu ổn định khi nối lại; các lần chạy kiểm file có `--reuse-only` chỉ đọc đĩa. Nên để một tiến trình điều phối mỗi shot.

Tập kế tiếp có thể mang theo cấu trúc của [bảng đạo diễn SB08](../abyss-studio/production/episodes/SB08/direction.json). Đạo diễn điền sắc thái, chuyển động máy, cảnh trả lời từng câu hỏi kịch tính và các hành động dễ lặp khi đổi góc. Hao cung cấp quy trình phim ngắn cùng trường timeline; hướng dẫn tài sản của Toonflow được dùng để khóa vị trí, nhân vật, đạo cụ và trạng thái. Sáu trường, câu hỏi đòi bằng chứng và các kiểm tra mối nối là phần triển khai của Studio. Số lượng prompt hệ thống LocalMiniDrama chưa được xác minh ở các tệp đã khóa.

Trên bản cắt thật, `direct.py cuts` báo khi thời gian nguồn đi lùi, khi một hành động được đánh dấu xuất hiện hai lần, hoặc khi trạng thái nhìn thấy mâu thuẫn với điều kiện của hành động kế tiếp. Mỗi nhận xét có số khung và mã shot. Với hồi tưởng có chủ ý, người dựng ghi `replay_reason` trên đúng cut. Ví dụ [ghi nhận hình của SB07](examples/SB07.observed.json) gắn sự việc “đã đưa túi lên xe” với khung 53 của C19 và “vẫn nhét đồ ở quầy” với khung 177 của C17. Lệnh bên dưới tái hiện cảnh báo ở giây 114,75 từ đúng bản dựng đã xem.

```powershell
python -X utf8 drama-pipeline-lab/direct.py cuts --episode abyss-studio/production/episodes/SB07 --notes drama-pipeline-lab/examples/SB07.observed.json --out abyss-studio/production/episodes/SB08/qa/direction/sb07-cut-audit.json
```

## Nguồn và môi trường

`profiles.json` khóa dữ liệu theo bản đã kiểm trong `codex-video-factory/production/karma-drama/SB06/research/repos.lock.json`. Thư mục `vendor` giữ đúng byte của năm thành phần và giấy phép tương ứng. Khi chép đã đối chiếu cả SHA-256 lẫn Git blob; trước mỗi lần thực thi đều kiểm lại SHA-256. Các thành phần CN chạy ngoại tuyến với Python 3.11+, Node, TypeScript, jsonschema, PyAV và Pillow đã có trong workspace. Có thể đặt `DRAMA_FACTORY` nếu thư mục factory ở vị trí khác. Kiểm thử tích hợp dùng FFmpeg để dựng mẫu kỹ thuật tạm hai giây.
