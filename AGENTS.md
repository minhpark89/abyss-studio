<!-- BEGIN Managed by ch-relay (undo: ch-relay unsync) -->
# Quy tắc làm việc

- Làm đúng và đủ 100% yêu cầu của người dùng.
- Không tự publish/deploy/push trừ khi được yêu cầu rõ.
- Kiểm chứng thực tế trước khi bàn giao.
- Không dùng skill `visualize` và không dùng skill `sites` trừ khi người dùng yêu cầu đích danh.
- Khi làm bài toán mô phỏng / 3D / cảnh vật / nhân vật chuyển động:
  - Luôn dựng **3D thực tế bằng Three.js / WebGL** (không làm Canvas 2D phẳng trừ khi người dùng yêu cầu rõ 2D).
  - **Không làm giao diện kiểu tạp chí / landing page quảng cáo** (không đặt tiêu đề chữ lớn đè lên giữa khung cảnh 3D); dành trọn không gian cho viewport 3D và bảng điều khiển HUD gọn gàng, không che khuất chủ thể.
  - **Tách dự án thành các file module riêng biệt theo trách nhiệm** (`state.js`, `character.js` / `creatures.js`, `world.js`, `cameras.js`, `ui.js`, `main.js` — mỗi lượt tạo/sửa 1 file module hoàn chỉnh, sâu chi tiết; cấm gom toàn bộ vào 1 file HTML hoặc 1 file `main.js` sơ sài).
  - Xây dựng hình học 3D giàu chi tiết (khớp nối phân cấp cha-con, vật liệu, ánh sáng, môi trường) và suy dẫn chuyển động/động học (2-bone IK chân/cánh/bàn đạp/dáng chạy, bánh xe, camera bám mục tiêu) khớp toán học thật từ `state` chung; animation luôn tự chạy (`running = true`) ngay khi mở trang.
<!-- END Managed by ch-relay -->

## Chọn kênh khi mở phiên Codex CLI

Khi lệnh có dạng “Tạo tập mới cho niche …” hoặc “Chạy niche …”, vào [codex-video-factory](codex-video-factory/AGENTS.md), đọc hồ sơ `niches/<niche>/niche.json` cùng [sổ repo](codex-video-factory/REPO_REGISTRY.json). Ghi kết quả dưới `production/<niche>/<tập>/execution_trace.json` trong repo đó và cập nhật đúng checkpoint kênh sau khi kiểm bản xuất.

- Mở [danh mục kênh](abyss-studio/production/channels/README.md). Khi người dùng ghi tên kênh hoặc mã tập, đọc `CHECKPOINT.md` và `RENDER.md` trong đúng thư mục. **Abyss Fieldnotes** dùng [abyss-fieldnotes](abyss-studio/production/channels/abyss-fieldnotes/CHECKPOINT.md) cho loạt D. **Second Bell Pictures** dùng [second-bell](abyss-studio/production/channels/second-bell/CHECKPOINT.md) cho loạt SB. Nếu đang làm một kênh trong cùng phiên, “tiếp tục” nối việc của kênh đó.
- Checkpoint của kênh cho biết bản nào là mẫu, bản nào là toàn tập, ý kiến mới nhất của chủ kênh, tình trạng duyệt/đăng, biên nhận còn mở và hành động kế tiếp. Khi người dùng giao dựng một tập cụ thể, làm theo phạm vi được giao và giữ checkpoint của các kênh khác độc lập. Chuẩn bị để chủ kênh tự đăng kết thúc ở gói cục bộ.
- Khi chuyển phiên hoặc sau một mốc sản xuất, cập nhật `checkpoint.json` trong đúng thư mục kênh. Từ `E:\YOUTUBE`, chạy `python -X utf8 abyss-studio/scripts/channel-checkpoint.py save <kênh>` rồi `check <kênh>` với cùng script. Ghi cả phần còn dở, lỗi, đường dẫn bằng chứng và việc tiếp theo. Các sổ kỹ thuật chung của Studio vẫn ghi tiến độ theo quy trình từng tập. Xem [quy cách bàn giao và câu lệnh](abyss-studio/production/channels/README.md).
- Muse dùng API chạy nền. Khi có lỗi 502 sau khi gửi, đối chiếu biên nhận cũ trước khi thử lại và giữ lại mã tác vụ chưa rõ trạng thái. Không tự mở Chrome, thay cookie/hồ sơ, mua credit hoặc đăng video.

Với **Second Bell Pictures**, theo bốn bước trong [quy trình phim Muse](abyss-studio/production/channels/second-bell/RENDER.md#dựng-từ-shot-list-đến-bản-duyệt). Từ kịch bản, chốt nhịp lật, trục nhìn và hồ sơ nhân vật trước khi tạo take. Dùng bảng cảnh, trình gửi Muse nền, timeline HyperFrames và kiểm phim đã mã hóa trong thư mục của tập.

## Tiếp tục công việc Abyss Studio / video biển sâu

Phần quy trình biển sâu dưới đây áp dụng khi làm **Abyss Fieldnotes** trong `abyss-studio`. Trạng thái tập hiện hành nằm trong [checkpoint Abyss Fieldnotes](abyss-studio/production/channels/abyss-fieldnotes/CHECKPOINT.md).

**Abyss Fieldnotes · thị trường Mỹ:** Dùng tiếng Anh Mỹ cho giọng, chữ trên hình và phụ đề. Không đóng, nhúng hoặc kèm phụ đề tiếng Việt trong gói video của kênh. Dựng tiêu đề và thẻ giải thích di chuyển vào theo lời đọc rồi giữ yên; kiểm trực tiếp trên bản mã hóa. Trước bàn giao chạy `python abyss-studio/scripts/check-release-language.py <thư mục delivery>` và kiểm chữ trên hình. Xem `production/channel-setup.json` và `production/HUMAN_STORYTELLING.md` của Abyss Studio.

1. Đọc `abyss-studio/production/START_HERE.md`, `CURRENT_BRIEF.md`, `SESSION_HANDOFF.md`, `state.json` trước khi làm. `CURRENT_BRIEF.md` liên kết yêu cầu đã chốt, chuẩn D001 và hồ sơ đối thủ; không suy hướng mỹ thuật chỉ từ checkpoint render. Chạy `python abyss-studio/scripts/daily-status.py --validate` để biết checkpoint và evidence còn hợp lệ.
2. User đã chọn **1 video/ngày, 8–10 phút, en-US hướng Mỹ**, yêu cầu cốt truyện có chiều sâu, hình giải thích dễ hiểu, thumbnail riêng và chữ nhấn hiện khi đặt câu hỏi. Áp dụng `HUMAN_STORYTELLING.md` cùng `CHECKPOINTS.md`.
3. User đã giao quản lý sản xuất và dùng account Muse mới. Tiếp tục việc cục bộ đã được ủy quyền, không hỏi lại cho mỗi bước. Không publish/deploy/push/mua credit khi chưa được yêu cầu rõ.
4. Daily profile là `abyss-studio/data/muse-daily-profile` (`muse-daily-01`); pilot cũ dùng profile khác. Đọc `MUSE_ACCOUNT.md`. Không chạy pilot/render-all để tạo tập Dxxx. Không submit lại job có receipt mơ hồ; đọc đúng thread trước.
5. D001–D030 là thứ tự sản xuất, chưa phải lịch đăng. Không tuyên bố tự chạy hằng ngày khi chưa có Scheduled task thật. Không đổi lịch/đề tài chỉ để tránh hoàn thành tập dở.
6. Trước khi kết thúc phiên, cập nhật `state.json`, `journal.jsonl`, `SESSION_HANDOFF.md` với evidence, công việc đang chạy, thay đổi yêu cầu và next action cụ thể. Đừng lưu mật khẩu/cookie/OTP vào các file sản xuất.
7. Áp dụng `abyss-studio/production/MEDIA_QA_ADDENDUM_20261117.md` từ nghiên cứu 2D bổ sung: kiểm mốc từ/cue, xem khung hình sau mã hóa và điểm chuyển cảnh, kiểm loudness đầu ra; không tự cắt mọi khoảng nghỉ hoặc áp LUT/fps cố định. Phân biệt công cụ đã chạy với kỹ thuật chỉ tham khảo; không coi timestamp hay danh sách repo là bảo đảm chất lượng 100%.
8. Hiện hành 17/11: owner từ chối D003 thuần 2D 9:49 và yêu cầu sửa bố cục mẫu 40 giây. Chỉ làm một đoạn hybrid ngắn có **video Muse chuyển động thật** để owner kiểm trước. Đọc bản mới của `Phân tích 2D bổ sung.txt` (7 lỗi thị giác), không nhầm với danh sách repo cũ. Không render lại toàn tập khi chưa có yêu cầu tiếp tục. Phạm vi/evidence hiện hành ở `abyss-studio/production/episodes/D003/hybrid-proof-v3/brief.json`; bản v2 giữ để đối chiếu.
9. Owner xác nhận Muse web vẫn tạo được ngày17/11. **Cấm dùng Muse biến ảnh minh họa2D thành video để tính là cảnh hybrid.** 2D giải thích phải dựng bằng mã/repo đã chọn; Muse tạo cảnh chân thực có chuyển động của chủ thể và môi trường, bám nội dung lời kể. Mẫu image-to-video ảnh xương2D ở backend-preflight chỉ là lịch sử kiểm kỹ thuật, không được dùng làm cảnh sản xuất.

## Chuẩn hình 2D bắt buộc cho TẤT CẢ video từ 17/11/2026

Đây là yêu cầu trực tiếp của owner, áp dụng cho mọi cảnh 2D hiện tại và các tập sau, không chỉ mẫu Osedax. 2D được dựng bằng mã/module từ repo đã chọn. Mẫu hiện hành phải được sửa theo các quy tắc này trước khi mở rộng toàn tập.

### 1. MANDATORY FULL-BLEED GEOMETRY — cấm môi trường bị cắt lơ lửng

- Mọi đáy biển, bề mặt xương, trầm tích, mặt nước và tầng địa chất phải tràn cả hai mép: hình học tối thiểu `x=-300..2220`, kéo xuống `y=1080..1300` trên khung `1920×1080`. Phải kiểm sau phép biến đổi camera, không chỉ tọa độ nguồn.
- Không vẽ địa hình thành sticker/khối có cạnh đứng bị cắt giữa màn hình; không để khoảng đen hở dưới nền.
- Cảnh Osedax `00:09–00:40`: bề mặt xương uốn lượn tràn ngang ít nhất `x=-200..2120`, đáy chạm `y=1080`; hoặc khúc xương đặt giữa, `width>=1400px`, nối liên tục với bùn đáy biển tràn hai bên. Ưu tiên hình học chung rộng `-300..2220` và sâu `1300`.

### 2. 3-PLANE DEPTH ARCHITECTURE — đủ ba lớp, lấp đầy khung

- `BackgroundPlane`: gradient môi trường rõ chiều sâu (`#0B3B54` trên → `#020D16` dưới); 6–8 luồng sáng chéo/polygon, opacity `0.07–0.12`; bóng bối cảnh xa opacity `0.12–0.18`, blur `2px`. Ở Osedax phải có các dải xương sườn cá voi lớn và 5–6 giun mờ ở nhiều độ sâu, trải cả bên phải. Ánh sáng biển sâu là ánh đèn/ánh khuếch tán minh họa, không gán thành ánh mặt trời.
- `MidgroundSubject`: chủ thể lớn, cân đối, bố cục tối thiểu khoảng `45–60%` khung; không thu nhỏ để dành một nửa màn hình trống. Cutaway/X-ray mở mượt bên trong môi trường tràn viền bằng clip/mask hữu cơ, viền sáng `#5BC0BE`, không thành hộp chữ nhật rời.
- `ForegroundHUDPlane`: đúng 35 hạt bụi/sáng phân bố toàn `1920×1080`; thước kỹ thuật mảnh ở một mép dọc, opacity `0.25`. Không bịa độ sâu/kích thước đo; khi phóng đại phải ghi tỷ lệ minh họa.

### 3. BALANCED HUD & CALLOUT CARDS — cân bằng bốn góc

- Mọi nhãn giải thích (`RED PLUMES`, `ROOT-LIKE TISSUE`, `ACID AT THE TIPS`...) nằm trong `GlassHUDCard`: nền `rgba(8,20,32,0.78)`, viền `1px solid rgba(255,255,255,0.18)`, có dòng chức năng/thông số phụ như `FUNCTION: OXYGEN UPTAKE`, `DEPTH: BONE MATRIX`, `SECRETION: ACID`. Dữ kiện phải có nguồn; không thêm số đo giả để lấp chỗ.
- Kiểm từng góc phần tư ở các frame đại diện và điểm chuyển: trên trái có tiêu đề hai tầng; dưới trái/giữa có chủ thể và cutaway tràn đáy; trên phải có HUD bối cảnh/thông số/sơ đồ; dưới phải có callout/kính lúp hoặc môi trường tiếp tục sang phải. Không góc nào để trống rỗng.
- Thẻ và leader phải tránh che cấu trúc đang giải thích; đầu leader bám đúng hình học sau camera.

### 4. HIGH-CONTRAST TITLE RULE — tiêu đề chính không bị mờ

- Sub-title: `#FFFFFF`, opacity `0.90`, weight `600`, letter-spacing `0.2em`.
- Main title: `#F5B82E`, opacity luôn `1.0` trong toàn cảnh, weight `800`, shadow `0 4px 20px rgba(0,0,0,0.6)`. Không dùng fade opacity theo beat khiến đầu cảnh (đặc biệt `00:12 HIDDEN IN THE BONE`) bị mờ. Chuyển động/đổi tiêu đề phải giữ tương phản; không để hai tiêu đề chồng nhau.
- `ENLARGED BIOLOGICAL ILLUSTRATION` phải là badge bo góc có viền ở trên phải hoặc gắn với thước; không đặt sát đáy/vùng phụ đề.

### 5. Quy trình mẫu ngắn và Muse chạy nền

- Trước render: xem still tại `00:09.5`, `00:12`, `00:16`, `00:25`, `00:30`, `00:37` và điểm nối Muse/2D; kiểm full-bleed, đủ ba lớp, bốn góc, opacity tiêu đề, leader và phụ đề. Sau render phải xem frame từ MP4 thực, kiểm âm lượng và phát thử. Không tuyên bố đạt bằng tọa độ/đếm lớp đơn thuần.
- Chỉ xuất mẫu ngắn mới để owner kiểm; giữ bản trước để đối chiếu. Không render toàn tập khi chưa được yêu cầu.
- Muse mặc định dùng API cục bộ chạy nền. Cửa sổ Abyss riêng hiển thị tiến độ/job, trạng thái dịch vụ và preview; thu gọn xuống khay hệ thống vẫn tiếp tục công việc.
- **Không tự mở Chrome để khởi động app, tạo video, kiểm trạng thái hoặc bảo trì phiên.** Không fallback âm thầm từ API sang browser. Nếu phiên API cần thao tác tài khoản, hiện trạng thái rõ trong Abyss và giữ receipt; chỉ mở luồng đăng nhập khi owner chủ động yêu cầu. Không đổi account/vùng/proxy, mua credit hoặc gửi lại job mơ hồ.
