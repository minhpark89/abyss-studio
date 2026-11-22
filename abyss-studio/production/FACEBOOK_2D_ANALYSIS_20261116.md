# Phân tích mẫu 2D owner chọn — 16/11/2026

Đã lấy và xem các frame của [reel owner gửi](https://www.facebook.com/reel/1272693095069597): 31,8 giây, 1280×720, 30 fps, 954 frame, có audio. Đây là clip ngang được đăng dưới dạng reel. Trang web tìm kiếm bị throttled nhưng luồng video công khai tải được bằng yt-dlp, không dùng cookie Facebook. Có contact sheet mỗi 2 giây, dải 8 frame quanh đoạn thiết bị phát tín hiệu, và nhận dạng lời kể bằng faster-whisper chạy cục bộ. Bằng chứng nằm ở `research/facebook-2d-20261116/`. Không dùng video/hình/nhạc của reel làm nguyên liệu cho tập mới.

**Hướng nên áp dụng: minh họa vector 2D có hành động giải thích, nền nhiều lớp, chủ thể lớn và chữ xuất hiện đúng bằng chứng.** Không cần biến phần cơ chế thành 3D để có chiều sâu. Ảnh đẹp và thư viện animation chỉ là nguyên liệu; chất lượng nằm ở phân cảnh, thiết kế hình và quan hệ nguyên nhân–kết quả.

## Clip thực sự đang làm gì

| Đoạn quan sát | Điều thấy trên hình | Tác dụng với người xem |
|---|---|---|
| 0–3 s | Cá voi lớn, mặt nước, tàu và dãy núi; sau đó camera lùi | Nhận chủ thể trước, rồi hiểu vị trí của nó trong cả cảnh |
| 3–9 s | Giữ cùng tàu và cá voi; thêm ký hiệu con người, dấu hỏi và cá voi | Đặt câu hỏi về liên lạc mà không phải dựng lại bối cảnh |
| 9–15 s | Thiết bị được hạ xuống; vòng tín hiệu tỏa ra giữa thiết bị và cá voi | Cho thấy cách thí nghiệm diễn ra; chuyển động mang thông tin |
| 15–21 s | Đồng hồ và dải xung tín hiệu hiện lần lượt; cá voi vẫn là chủ thể | Biến thời gian và lượt đáp thành thứ nhìn thấy được |
| 21–25 s | Số 36 đi cùng các ô đếm, rồi cận cảnh cá voi có tên | Con số có vật chứng thị giác; chuyển từ thống kê về một cá thể |
| 25–31,8 s | Camera đổi cỡ, trở lại không gian biển, chữ kết ngắn | Kết nối khám phá vừa thấy với câu hỏi lớn hơn |

Các mốc là khoảng quan sát, không phải ranh giới hard cut: phần lớn clip dùng một sân khấu liên tục với camera, vật thể và nhãn được thay đổi.

## Vì sao dễ nhìn và đẹp

- **Một hệ hình thống nhất.** Cá voi, tàu, núi và thiết bị cùng kiểu mảng màu/nét. Cá voi có bụng, nếp họng, mắt, vây dài, đuôi; đủ chi tiết nhận dạng nhưng không dùng texture rối.
- **Có chiều sâu bằng lớp, không cần phối cảnh 3D.** Nền núi nhiều lớp; mặt nước là đường chia rõ; nước có chuyển sắc; chủ thể sáng trên nền tối. Các thành phần xa ít tương phản hơn.
- **Mắt biết nhìn đâu.** Thường chỉ có một sự kiện mới: thiết bị đi xuống, vòng âm lan ra, đồng hồ tăng, số phản hồi hiện. Những phần khác chuyển động nhẹ hoặc đứng yên.
- **Giữ đối tượng qua các lần giải thích.** Cùng con cá voi và cùng tàu xuyên suốt nên người xem không tốn sức định hướng lại. Camera đưa ta tới chi tiết đang nói.
- **Chữ làm nhiệm vụ.** Tên địa điểm, câu hỏi, tên cá thể và con số xuất hiện tại đúng ý; không phải một slide có toàn bộ lời kể.

Không có bằng chứng từ file video cho biết tác giả dùng Claude, After Effects, SVG hay công cụ nào. Caption người đăng nhắc Claude; đó không phải bằng chứng về mã nguồn. Cũng chưa có analytics để kết luận định dạng này tăng retention hoặc đang “hot”.

## Điều cần sửa khi học cho Abyss

1. Không bê màu nước nông và tia nắng xuống đáy biển sâu. Dùng nền navy phân lớp, độ sáng tập trung vào phần đang giải thích; hình là sơ đồ minh họa, không giả quan sát bằng camera.
2. Bảng đồng hồ và dải âm rất nhỏ ở kích thước điện thoại. Khi nội dung của ta phụ thuộc số liệu, cần một cận cảnh riêng, đơn vị và thước đo đọc được ở 320×180.
3. Không lặp cá bơi và zoom để lấp thời gian 8–10 phút. Mỗi chuỗi 2D phải trả lời một câu hỏi, có thay đổi trạng thái và một kết quả nhìn thấy.
4. Không dựng lại toàn bộ một con vật từ một PNG rồi kéo méo đầu/mắt. Cần các phần riêng theo khớp; khi đổi góc lớn, tạo pose hoặc asset riêng.
5. Giữ mức chắc chắn khoa học trong cả lời và hình. Nghiên cứu thật ghi 38 tiếng gọi phát và 36 tiếng đáp của Twain trong 20 phút; nó không chứng minh con người đã dịch được ngôn ngữ cá voi. [Bài nghiên cứu gốc](https://pmc.ncbi.nlm.nih.gov/articles/PMC10693240/), [UC Davis](https://www.ucdavis.edu/blog/whale-seti-humpback-whale-encounter-reveals-potential-non-human-intelligence-communication).

## Tài nguyên đã rà soát và cách dùng

Kiểm kê thực tế 12 nhóm tài nguyên/repo local và đối chiếu lại catalog 18 repo animation. Danh sách file/mở rộng/số lượng ở `research/facebook-2d-20261116/resource-inventory.json`. Các folder repo nghiên cứu chủ yếu là README/license/metadata đã lưu, **không có nghĩa đã cài và thử toàn bộ runtime**.

| Tài nguyên của chúng ta | Đã có thật | Áp dụng |
|---|---|---|
| Brand Abyss | 47 file trong `branding`, navy–teal–ivory–amber, font và mẫu thumbnail | Giữ bảng màu; vàng cho thông tin/cơ chế mới, ngà cho chủ thể |
| Tranh gốc v4 | 3 PNG cá voi, mực và mắt, kèm provenance/prompt | Dùng đúng loài/góc; cần rig nhiều phần cho vận động rõ. Cá nhà táng không thay được cá voi lưng gù |
| Renderer hybrid dùng chung | 11 module JS + HTML về anatomy, optics, comparison, environment, typography… | Giữ bộ timeline, caption, camera và export; thay art/cách dàn cảnh |
| D001 illustrated | Source modular, rig, voice, bản render và hồ sơ kiểm hình | Lấy chức năng đã kiểm; không lấy bản cũ làm chuẩn đẹp mặc định |
| D002 Motion Canvas | Runtime 3.17.2, Vite 5.4.21, TS 5.7.3 đã cài; scene/component/renderer và MP4 proof | Nền tảng chính cho chuỗi 2D có nhiều hành động cần đồng bộ voice |
| Muse API | Phiên được owner cho phép, direct API đã tạo video thật, app Việt mới | Dẫn cảnh môi trường/sinh vật; không dùng làm nguồn khoa học hay engine vẽ số liệu |
| Kokoro + ASR | Model/voice en-US local; faster-whisper small CUDA | Đo timestamp lời đọc trước animation, kiểm lại lời trong bản mix |
| FFmpeg / GPU | FFmpeg 8.0.1 NVENC, RTX 3050 Ti, ffprobe, Playwright local QA | Xuất frame cố định, encode, loudness, decode, contact sheet và kiểm playback |
| rea-video / ffmpeg-skill | Mã nguồn, docs và các nghiên cứu trước có sẵn | Hỗ trợ phân tích/chia cảnh và đóng gói; không tự tạo art đẹp. Lượt này dùng trực tiếp ffmpeg/ffprobe, không tuyên bố đã chạy lại toàn bộ repo |
| Viral Studio / Viral Research | Module render, voice/caption, media library, hàng đợi và Electron có sẵn | Tái sử dụng hạ tầng cục bộ phù hợp. Không đọc kho khóa hoặc chuyển account dịch vụ khác |
| Mẫu Three.js 42 s | MP4 và source kiểm kỹ thuật trước đây | Giữ để đối chiếu. Hướng 2D mới của owner không bị ép trở lại mẫu 3D |
| Mẫu 2D mới | `visual-lab/whale-fall-2d-v1/`, 7 module art/state/render, lời kể 42 s dùng lại | Proof một cơ chế theo hướng mới; không thay D002 và không phải D003 hoàn chỉnh |

## Chọn repo cho việc gì

| Nhóm | Repo | Quyết định |
|---|---|---|
| Animation giải thích chính | [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | Ưu tiên với scene graph, signal và time event theo voice; runtime đã có. [Time events](https://motion-canvas.io/docs/time-events/), [rendering](https://motion-canvas.io/docs/rendering/) |
| Tích hợp nhẹ trong renderer JS | [Anime.js](https://github.com/juliangarnier/anime) | Tốt cho timeline/SVG; seek theo ms để render xác định. Mẫu mới dùng hàm state theo thời gian sẵn có, chưa cần thêm dependency. [Seek](https://animejs.com/documentation/timeline/timeline-methods/seek/) |
| Dựng cả tập bằng React | [Remotion](https://github.com/remotion-dev/remotion) | Có ích nếu chuyển cả khâu dựng dài; chưa cần thay FFmpeg đang chạy. `remotion-dev/skills` chỉ là hướng dẫn, không phải engine. [Giấy phép hiện hành](https://www.remotion.dev/docs/license/pricing) có điều kiện theo quy mô đội ngũ; không mua trong phiên này |
| Sơ đồ hình học / số liệu | [Manim Community](https://github.com/ManimCommunity/manim) | Chọn cho đường sáng, tỷ lệ, đồ thị có toán; không tự đem lại art sinh vật đồng nhất |
| Vector/editor/asset | Two.js, Konva, Lottie Web | Tốt cho đường cong, chỉnh pose hoặc phát asset đã có; vẫn cần timeline và art |
| Nội suy / hiệu ứng phụ | Motion, Shifty, TweenJS, Ola, Proton, gifenc | Bổ trợ, không phải bộ sản xuất phim. GIF chỉ dùng preview |
| Cảnh thực sự cần 3D/rig phức tạp | Three.js, Blender, Godot, Babylon.js, LUME | Giữ dùng chọn lọc; không thay hướng 2D đã chọn bằng một engine 3D khác |

Không có repo nào sửa được vấn đề bằng cách cài xong là đẹp. Phần thiếu chính là bộ art nhất quán, rig đúng bộ phận, bố cục theo lời và chuỗi động tác chứng minh ý.

## Áp dụng từ D003

Với whale fall: cảnh Muse đưa người xem xuống đáy → chuyển sang cùng bố cục dạng 2D → giữ bộ xương làm mốc → phóng một đốt xương → lộ vật chất hữu cơ → đường tín hiệu tới vi sinh vật → trở về cộng đồng quanh xương. Chuỗi có câu hỏi, bằng chứng và callback; không nhảy qua các sơ đồ rời rạc.

Mẫu mới dùng tranh vector nguyên bản và voice cũ để đối chiếu trực tiếp với proof 3D. Không trích frame, giọng hay nhạc của reel. Nguồn cho cơ chế: [NOAA](https://oceanservice.noaa.gov/facts/whale-fall.html). Hình xương/vi sinh vật và màu tín hiệu là sơ đồ, không phải anatomy của một loài đã định danh hay mô phỏng tỷ lệ/thời gian thật. Chưa chốt mỹ thuật thay owner.

Mỗi cảnh tương lai ghi thêm: `visual_question`, `before_state`, `trigger`, `after_state`, `persistent_object`, `voice_cue`, `emphasis`, `source_claim`. Trước render cả tập, kiểm chuỗi hybrid 45–90 giây có Muse + 2D + chuyển cảnh ở kích thước điện thoại. Không tự đóng C1–C8 từ mẫu 42 giây này. D002 v9 giữ nguyên.
