# Góc máy và âm thanh

## Nối diễn xuất qua hai take

Từ phim tham chiếu, chọn một đoạn có cùng chức năng kịch tính và ghi lại điều khiến mỗi lần đổi góc có ý nghĩa. Với cảnh nhục mạ, chẳng hạn, đó có thể là trang giấy rơi, phản ứng của người bị xúc phạm rồi mới đến câu đáp. Đo nhịp trên hai cửa sổ cùng độ dài với cùng bộ dò. Cảnh mới cần một hành động hay phản ứng riêng để biện minh cho điểm cắt.

Trong shot list và prompt của take tiếp, ghi tư thế ở khung vào, hướng nhìn, tay giữ đạo cụ, trạng thái nước mắt và hành động đưa diễn xuất sang khung ra. Nếu nhân vật đang khóc, chọn khung cuối đã dùng của take trước làm tham chiếu khi cần và dành thời gian trên hình để hai tay hạ xuống hoặc hơi thở dịu lại. Khi chỉ cần nhìn rõ vật chứng, có thể cắt sang chi tiết từ cùng take và cho câu thoại tiếp tục trên đồng hồ tiếng gốc.

Trên MP4, xem hai phía mối cắt và mọi đoạn có người trong hình khi thoại gốc bị tắt. Nếu miệng đang tạo từ, tìm đúng câu thoại hoặc lấy take mới diễn phản ứng im lặng. Bộ dò giọng chỉ đánh dấu nơi cần nghe lại. Ở SB09, lời ngoài kịch bản tại 02:57 nằm trong take gốc, nên kiểm riêng bản mix sẽ bỏ sót.

`factory.py init` bật `performance_review` trên board drama mới. Board cũ có thể bật cùng trường. Sau lần dựng đầu, mở `qa/cut-continuity/index.html` để kiểm phim. Trong `review.json`, lưu `windows_sha256` của `windows.json` và `observations` theo từng mã cửa sổ, gồm `decision` và `observation`. Chọn `keep` khi diễn xuất phù hợp, sửa các đoạn còn lỗi và kiểm lại trên MP4 mới.

## Đối chất

Đánh dấu từng đoạn đối chất bằng một mã cảnh. Trong mỗi đoạn, tối thiểu 30% số góc máy trên bản dựng phải thấy cả hai nhân vật đang tương tác trong cùng khung. Góc qua vai có thể dùng vai và đường nhìn của đối phương. Một cận cảnh chỉ có một mặt, một phản chiếu ngoài ý đồ hoặc hai cận cảnh cắt nối không đủ điều kiện. Đếm trên khung đã crop và tách theo góc quay thật. Dựng hành động cùng phản ứng trong không gian rõ trục. Dùng ánh sáng thương mại giữ chi tiết trên cả hai gương mặt và vật chứng.

Ghi người giữ đạo cụ, tay áo/cổ tay, ánh sáng và các diễn viên nền vào bằng chứng hình của từng đoạn chọn. Đối chiếu cận tay với đúng người vừa thực hiện hành động. Chỉ dùng khoảng take đã kiểm được người ở hậu cảnh và ý nghĩa biểu cảm ở đầu, giữa và cuối khoảng. Thiếu bằng chứng, sai người hoặc sai cảm xúc phải chọn lại khoảng đạt hoặc cấp mã take thay thế rồi kiểm lại trước khi ghép.

Giữ thoại ở tốc độ thật. Khi không có thoại, tắt âm gốc và dựng lại âm nền/SFX từ manifest. Chừa 0,8 giây cuối take Muse ngoài cả đường hình lẫn đường tiếng. Khoảng trống dài hơn 0,8 giây phải có hành động, quyết định hoặc thay đổi thị giác thấy rõ. Trước câu phản đòn, dành 0,5 giây ngắt nhạc. Nửa giây cuối master giảm dần đến im lặng.

## Ví dụ giữ trục từ SB05

Giữ Marcus bên trái và Eli bên phải trong cùng pha đối thoại. Trong góc đáp ngang tầm mắt Marcus, vai Eli đánh dấu phía đối diện. Ghi cỡ cảnh theo tác dụng chính để thống kê tỷ lệ góc của hồ sơ. Đổi trục sau góc toàn tái lập vị trí hai người.

Khóa mặt, tóc, cổ áo, bánh xe và số bóng bằng ảnh tham chiếu. Ghi số bảng rổ theo góc máy thực tế. Kiểm tay có bóng ở hai phía mối nối. Cho khán đài phản ứng sau khi lưới nhận bóng.

Khớp giọng khô với chính khung phát âm. Khi thoại chạy qua góc người nghe, ghi J-cut hoặc L-cut và vị trí người nói. Sóng âm va chạm có khoảng lấy đà trong mẫu tiếng. Đặt đỉnh xung vào frame tiếp xúc. Xem MP4 ở 1× cùng các cận cảnh miệng và nghe riêng âm nền.
