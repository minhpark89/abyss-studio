# Dựng phim cho Second Bell Pictures

**SB05 · Check Ball.** Lệnh `python factory.py run karma-drama SB05` dựng từ nguyên khung hình của các take Muse đã có biên nhận. Các góc thấy người nói lấy đoạn có đúng câu thoại và căn thời điểm từng âm với giọng đã khóa. Bản dựng giữ âm thanh xuyên qua góc nhìn của người nghe hoặc động tác khi cần. Mỗi khung xuất có mã take, số frame và phép cắt khung trong `source-cut/frame-map.json`. [Phòng xem ba phiên bản ở cùng mốc](../../episodes/SB05/source-cut/review.html) · [Hình đối chiếu tìm nguyên nhân](../../episodes/SB05/source-cut/diagnosis.jpg).

[Checkpoint và bản mẫu](CHECKPOINT.md) · [Chuẩn gói YouTube](../README.md#gói-bàn-giao-để-chủ-kênh-tự-đăng-youtube)

Kênh làm phim hư cấu đời thường 20–30 phút cho khán giả Mỹ. Mỗi tập có dàn nhân vật mới, nói tiếng Anh Mỹ. Giữ nhất quán khuôn mặt, dáng người, tóc, phục trang, giọng và bối cảnh trong toàn tập. Hình, giọng, nhạc, âm thanh hiện trường và khung hình gốc dùng cho thumbnail đều lấy từ Muse. [Kế hoạch kênh](KE_HOACH.md) · [Hướng kể chuyện chủ kênh đã chọn](scripts-v2/DINH_HUONG.md)

1. **Viết để khán giả hiểu ngay.** Cho thấy ai đang bị coi thường, chuyện gì vừa xảy ra và họ có thể mất gì. Để người đó bộc lộ tài năng qua việc khán giả tận mắt thấy hoặc nghe. Gieo một chi tiết có thể nhận ra trước lúc nó làm thay đổi quyết định. Sau cú lật, cho người chịu ảnh hưởng được lựa chọn và cho thấy cái giá của lựa chọn ấy. Học nhịp kể từ phim ông lão giấu tài của Neural Pictures, viết tình huống, nhân vật, thoại và kết cục riêng. Hai phim tham khảo có lượt xem công khai toàn cầu. [Đối chiếu phim và mốc hook](scripts-v2/DINH_HUONG.md)
2. **Khóa nhận diện trước khi tạo cảnh.** Với mỗi vai, lưu ảnh tham chiếu rõ mặt, tóc, trang phục cùng một đoạn giọng đã chọn. Khóa những đạo cụ có vai trò trong cốt truyện. So cảnh mới với bộ tham chiếu và cảnh liền trước, kiểm ai đang nói, hướng nhìn, vị trí tay và đạo cụ ở hai phía điểm cắt. Đổi nhân vật khi chuyển sang tập có câu chuyện mới. [Bộ tham chiếu của SB01](../../episodes/SB01/hook-v2/refs/index.json)
3. **Theo sát mỗi cảnh Muse.** Lưu mã cảnh, biên nhận và take được chọn. Nếu gặp 502 sau khi gửi, đối chiếu đúng biên nhận và thread qua API nền để xác định tác vụ đã nhận hoặc kết thúc ở đâu. Tận dụng clip đã có, ghi phần còn chờ và bước cụ thể vào checkpoint. [Đối chiếu biên nhận mẫu SB01](../../episodes/SB01/hook-v2/qa/receipt-review.json)
4. **Dựng và nghe toàn mạch.** Chọn take theo hành động và câu thoại, kiểm nhịp giữa các phản ứng, độ rõ của thoại, giọng từng vai, tiếng phòng và nhạc ở mối nối. Trên bản mã hóa, xem cả trước và sau mỗi lần lộ tài hoặc ra quyết định. Kiểm xem khán giả có thể hiểu ai muốn gì và vì sao kết quả đổi. So phụ đề en-US với lời nói thực. [Các take và mối nối của mẫu](../../episodes/SB01/hook-v2/qa/opening-selections.json) · [Kiểm hình và tiếng bản mẫu](../../episodes/SB01/hook-v2/qa/release-check.json)
5. **Bàn giao đúng phạm vi.** Với mẫu, ghi thời lượng, cảnh đã xong, nội dung cần chủ kênh duyệt và mốc nối tiếp. Với phim toàn tập, kiểm tới cảnh kết và làm gói YouTube gồm master, phụ đề, thumbnail từ phim, tựa, mô tả và thông tin khai báo cảnh hư cấu tạo bằng AI.

## Dựng từ shot list đến bản duyệt

Với mỗi tập SB, dựng theo bốn bước dưới đây. SB01 có [hai phiếu chỉ đạo gửi Muse](../../episodes/SB01/director-cut/shots.json), [bản tập máy 3D 10 giây](../../episodes/SB01/director-cut/previs/camera-reference.mp4) và [danh sách điểm cắt theo khung hình](../../episodes/SB01/director-cut/timeline.json).

1. **Xác định điều khán giả biết ở mỗi nhịp.** Trong vài giây đầu, cho thấy một bất công cụ thể. Đặt manh mối vào hành động hoặc âm thanh có thể nhận ra. Thử một đoạn mở trong đó khán giả tự đoán rồi nhân vật mới xác nhận. Với SB01, câu báo vắng mở phim, sau đó là bản thu từ điện thoại, tiếng đàn trực tiếp và cuối cùng mới tới lời June. Để cú lật sau dẫn đến lựa chọn của Lena.
2. **Khóa góc đối thoại và nhận diện.** Lưu gương mặt, áo, tóc, giọng, ánh sáng và đạo cụ trong hồ sơ của riêng tập. Ghi mục đích, cỡ cảnh, tiêu cự dự kiến, chiều cao máy, phía của trục diễn, khung đầu, chuyển động, điểm dừng, hành động và tiếng đồng bộ vào từng phiếu. Cho người đáp nhìn về phía người hỏi. Với góc khó, tập máy bằng Three.js, kiểm khung đầu, giữa, cuối và hướng nhìn tại mối nối. Muse API nhận prompt và một ảnh khóa vai hoặc đạo cụ. Clip tập máy dành cho người dựng kiểm bố cục. [Shot Director](https://github.com/AustinZ21/cinematic-skills/tree/0e5b3fe575740cd022d9ffdec7b7568684c885a5/skills/shot-director) · [Cinematic Previs](https://github.com/sirioberati/ai-filmmaking-camera-control-seedance-2-5/tree/602aa2348b0ae67589ce533fff571adced724811/skills/cinematic-previs)
3. **Chỉ gửi cảnh còn thiếu.** Từ gốc workspace, lệnh dưới in ra prompt đầy đủ sau khi kiểm SHA-256 của ảnh khóa. Thêm `--submit MÃ_CẢNH` để gửi đúng cảnh qua API nền. API Studio hiện yêu cầu 720p và 10 giây mỗi take. Chọn khoảng dùng được theo hành động, thường 3–5 giây cho một phản ứng, dài hơn khi cần nghe hết câu hát. Đối chiếu đúng receipt nếu gặp 502. Chỉ cấp mã take kế tiếp sau khi xác nhận yêu cầu cũ đã kết thúc.

   ```powershell
   python -X utf8 abyss-studio/production/channels/second-bell/direct-shots.py abyss-studio/production/episodes/SB01/director-cut/shots.json
   ```

4. **Dựng HyperFrames và kiểm bản mã hóa.** Cắt theo điểm đổi ý, ánh mắt hoặc nốt nhạc. Cho nghe một manh mối từ hai vị trí nếu âm thanh quyết định câu chuyện. Bản SB01 dành 12 frame tiếng phòng cho độ ngân cuối câu đàn. Giữ khoảng ngân ở đoạn hát. Kiểm đồng bộ miệng, khoảng lặng, âm lượng và hướng nhìn trên cả hai phía của từng mối nối. So bản nghe có phụ đề en-US và bản xem tắt phụ đề. Lưu SHA-256, take được chọn, danh sách frame, lần phát kiểm, tình trạng nhận xét của chủ kênh. [Quy cách HyperFrames](https://github.com/heygen-com/hyperframes/tree/4fd96e3533365e89ca1700cf9d1ab5501ea93a08/skills/hyperframes)

Ở mối nối 00:27 của SB01, tay áo June trông dài và vàng hơn trong cảnh cận phím. Khi quay thêm cảnh tay hoặc đạo cụ, lấy khung cuối của cảnh liền trước làm tham chiếu cho chiều dài tay áo, bàn tay đang di chuyển và ánh sáng trên vật thể. [Khung hình từ bản xuất](../../episodes/SB01/director-cut/qa/pickup-sequence.jpg)

### Dựng lại mẫu đã bàn giao

Trong `production/episodes/SB01/director-cut`, chạy lần lượt các lệnh dưới. Dùng FFmpeg của Studio, ffprobe và Node 22.17+ trên PATH. Trên Windows đặt `HYPERFRAMES_BROWSER_PATH` tới `msedge.exe` để HyperFrames chạy Edge headless cục bộ. Bước `assemble.py` dựng lại các nguồn theo biên nhận và viết timeline HyperFrames cùng bản mix PCM. `finish.py` xuất hai bản xem và `inspect_cut.py` trích khung hình, đối chiếu thoại, mô-típ đàn và mức tiếng của bản dựng gọn.

```powershell
python -X utf8 assemble.py
npx.cmd --yes hyperframes@0.9.72 lint hyperframes
npx.cmd --yes hyperframes@0.9.72 check hyperframes
npx.cmd --yes hyperframes@0.9.72 render hyperframes --fps 24 --output "$PWD/qa/hyperframes-picture.mp4"
python -X utf8 finish.py
python -X utf8 inspect_cut.py
python -X utf8 check_matched.py
python -X utf8 review_playback.py
```

## Năm tiêu chí trước khi render bản dài

1. **Xung đột trong 10 giây đầu.** Xem đoạn mở tắt tiếng và tắt phụ đề. Ghi hai frame cho thấy ai tước quyền gì của ai và người kia phản ứng ra sao.
2. **Đổi không gian hoặc góc máy lớn.** So khung hình trước và sau các lần đổi vị trí đặt máy hoặc bối cảnh. Khi viết shot list, nhắm tới một thay đổi có lý do ở mốc 45–60 giây; đoạn dài quá 60 giây giữa hai lần đổi cần dựng lại. Đoạn thử dưới 45 giây chỉ kiểm được nhịp cắt trong đoạn đó.
3. **Ít nhất 30% thời lượng có hai nhân vật trở lên.** Tính theo số frame thực. Ghi hai vùng nhân vật của two-shot hoặc OTS, rồi chạy YuNet trên từng frame. Số tự động là mức tối thiểu vì máy có thể bỏ sót vai quay lưng.
4. **Cú lật có người thấy, có người mất, có người được.** Đánh dấu frame nhân chứng, hành động làm đổi cục diện, cái giá người gây khó dễ thực sự chịu và điều nhân vật chính nhận được trên màn hình.
5. **Âm thanh có lớp và điểm cắt.** Đối chiếu toàn bộ thoại với phụ đề, tìm tiếng nói thừa ngoài cue; đo độ liên tục của nền phòng, vị trí SFX so với cú lật và thời gian tiếng qua mối cắt. Kiểm các lớp đồng bộ, nền và SFX ghép lại khớp đúng tệp sẽ render.

Trên máy dựng hoặc máy Linux có aaPanel, chạy `python render_checked.py <thư-mục-bản-dựng>` từ thư mục kênh. Lệnh cần HyperFrames trên PATH, Python có NumPy, PyAV, OpenCV, faster-whisper, model YuNet ở `DRAMA_FACE_MODEL` và model Whisper cục bộ ở `DRAMA_ASR_MODEL`. Để chỉ chấm, chạy `python drama_qa.py <thư-mục-bản-dựng>`. Các sự kiện kể chuyện cần nhận xét gắn với frame của proxy sau khi xem tắt tiếng. Script đếm frame, đối chiếu thời gian, âm thanh và bằng chứng, trả mã lỗi khi một mục còn cần xem. Kết quả ở `qa/drama-score.json`; đổi proxy, timeline hoặc mix sẽ làm kết quả cũ hết hiệu lực.

## Tiếp tục đúng tập

### SB09 · Nối diễn xuất và kiểm lời bị tắt

Trong `codex-video-factory/production/karma-drama/SB09`, chạy `python -X utf8 reproduce.py` sau khi khóa edit và cue. Lần dựng tạo [bảng kiểm mối cắt](../../episodes/SB09/qa/cut-continuity/index.html) từ MP4, gồm sáu khung cho mỗi điểm nối và các khoảng tắt thoại gốc. Mở các đoạn có cảnh báo giọng, so miệng với hình và tiếng, ghi quyết định cùng quan sát vào `qa/cut-continuity/review.json` của tập. Mã SHA của bảng kiểm gắn quyết định với đúng bản phim. Chạy lại lệnh để hoàn tất phép đo, cập nhật phòng xem và kiểm phát đến hết phim. [Đối chiếu nhịp với Neural Pictures](../../episodes/SB09/qa/cut-continuity/pacing.json) · [So sánh take kết trước và sau](../../episodes/SB09/qa/cut-continuity/ending-regression.json)

### Kiểm mối cắt và người nói từ SB04 bản 36,67 giây

Dùng [phân tích tại từng mốc](../../episodes/SB04/court-v3/PHAN_TICH.md) và [phòng xem bản hiện hành](../../episodes/SB04/court-v3/delivery/review.html). Bản 32,5 giây bên dưới dùng để so sánh.

1. Khi có phim tham chiếu cục bộ, chạy `python measure_pacing.py reference.mp4 reference-qa --seconds 60 --source URL`. Xem lại các góc ứng viên trước khi ghi mốc vào hồ sơ đối chiếu. Trong `editorial.json`, trường `benchmark` trỏ tới hồ sơ của đúng đề tài. Báo cáo dùng hai cửa sổ có độ dài bằng nhau.
2. Chỉ đạo Muse bằng hành động, góc máy, hướng nhìn và vai được nói. Giữ mẫu giọng dưới dạng take, đoạn frame và SHA trong `voices.json`. Phiếu câu thoại ghi vai, chữ, take, thời điểm âm thanh nguồn, hình người nói. Khi có nhiều câu trong cùng góc, khóa từng câu bằng ID góc + `@` + frame bắt đầu trên timeline. Với J/L-cut cắt qua lời nói, khai báo `bridge.kind`, `bridge.reason` và góc thấy người nói. Hai tài liệu Shot Director và Cinematic Previs được ghim theo commit, kèm giấy phép, tại [director-rules](director-rules/upstream.json).
3. Chạy `python assemble.py` trong thư mục bản dựng rồi `python ../../../channels/second-bell/continuity.py . --prepare`. Mở `qa/continuity/index.html` để xem sáu frame hai phía mỗi mối cắt, ba frame đầu–giữa–cuối từng góc và nghe câu chuẩn cạnh câu trong mix. Điền nhận xét thực vào `continuity-review.json`, dùng mã bằng chứng của đúng lần dựng. Mẫu của SB04 có [chín nhận xét nối hình và hai vai thoại](../../episodes/SB04/court-v3/continuity-review.json).
4. `run-local.ps1` chạy quy trình dựng và kiểm trên Windows. Với Linux, chạy theo thứ tự `assemble.py`, `render_checked.py <cut>` của kênh, `assemble.py --finish`, `verify.py` và `review.py`. Dùng HyperFrames CLI 0.9.72, FFmpeg/ffprobe, trình duyệt headless và hai model QA như trên. `HYPERFRAMES_FFMPEG_PATH` chọn FFmpeg, `SECOND_BELL_ENCODER=libx264` chọn encode CPU. Đổi codec có thể đổi hash proxy và cần kiểm bộ hình mới. Quy trình đã chạy cục bộ trên Windows, gồm cả thử nghiệm encode CPU. Máy aaPanel chưa được triển khai hoặc kiểm.
5. Bộ kiểm so câu nguồn với PCM trong mix, đối chiếu hình người nói với biên bản, rồi kiểm 5 tiêu chí của kênh. Sau HyperFrames, mọi frame trong MP4 được đối chiếu lại với proxy. Công cụ không suy giới tính từ giọng. Xem [bằng chứng chặn sai người nói, lệch tiếng và biên bản hết hiệu lực](../../episodes/SB04/court-v3/qa/continuity-regression.json).

- **SB04 · Next Five.** [Xem mẫu Marcus ở sân bóng](../../episodes/SB04/court-v2/delivery/review.html). Đoạn 32,5 giây kết khi Marcus mặc áo cam và chuyền bóng cho đồng đội. Eli vừa phải rời sân trước mặt cả khán đài. Nối từ cuối cảnh 1 sang lúc Nate đến ở [kịch bản Marcus](../../episodes/SB04/court-v2/screenplay.md). [Năm tiêu chí trên bản dựng](../../episodes/SB04/court-v2/qa/drama-score.json) · [Bản Val 25 giây để đối chiếu](../../episodes/SB04/opening/delivery/review.html)

- **SB01 · The Empty Bench.** [Phòng xem](../../episodes/SB01/director-cut/delivery/review.html) có hai bản 2:51 để so góc máy ở cùng thời điểm. Chọn **June at the piano** để xem từ 00:24. Trong bản mới, June ngồi xuống đàn, còn Lena ngước mắt ở cuối câu nhạc trước khi June xác nhận mình từng chơi trong bản thu. Hai lựa chọn 5:00 cho phép so phần mở 44 giây ở nhịp của mẫu dài. Cả bốn đi đến lời nhận lỗi của Dean. Chủ kênh đang duyệt nhịp phim. Khi được giao nối toàn tập, mở [kịch bản đầy đủ](scripts-v2/SB01-THE-EMPTY-BENCH.md) ở “What the panel will hear” và đối chiếu cảnh cuối của bản được chọn. Giữ hình và giọng June Porter, Lena Park, Dean Walsh theo bộ tham chiếu đã dùng. Bản toàn tập cần timeline và biên bản QA phủ đến cảnh cuối.
- **SB02 · One Pin Left** và **SB03 · Room at the Table.** Hai tập đã có [kịch bản SB02](scripts-v2/SB02-ONE-PIN-LEFT.md) và [kịch bản SB03](scripts-v2/SB03-ROOM-AT-THE-TABLE.md). Khi được gọi đúng mã tập, bắt đầu từ cảnh mở và bộ nhân vật trong kịch bản của tập đó.
