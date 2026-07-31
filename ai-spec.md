# AI SPEC — Chat hỏi đáp theo slide & tạo note · Nhóm [XX] · Zone [X]

Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới

## §1. User & Job

* Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):
  Học viên đang trong buổi học, tải slide lên → hỏi về nội dung chưa hiểu → đọc câu trả lời → bấm tạo note sau khi học xong.
* Core JTBD (không tên sản phẩm/AI trong câu):
  Hiểu nội dung bài giảng nhanh hơn và ghi lại ý chính để ôn tập sau.
* Problem statement (KHÔNG chữ AI):
  Học viên thường phải tự đọc slide, hỏi lại nhiều lần hoặc ghi chú rời rạc nên tốn thời gian, dễ sót ý quan trọng và khó ôn tập lại sau buổi học.
* Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):

  * Số liệu mining / kết quả khảo sát (n = 21):
    Khảo sát người dùng, n = 21, 71.4% (15/21) người xác nhận họ từng bỏ lỡ kiến thức quan trọng vì quên lưu lại sau khi chat với AI, 71.4% thường xuyên/thỉnh thoại rơi vào tình trạng "chat xong để đấy, không bao giờ mở lại", 57.1% gặp khó khăn trong việc lọc ý quan trọng để ghi chép, và 95% (19/20) đánh giá ý tưởng trợ lý tự động tạo note/flashcard ở mức từ 3 đến 5/5 về độ hữu ích.
  * ≥5 quote/ví dụ nguyên văn + nguồn:

    1. “Hiểu đúng trọng tâm, có trích nguồn” — Người trả lời khảo sát (Câu hỏi: Điều kiện để tin tưởng & dùng thật)
    2. “Nhanh, có link tới chỗ phần nó được nói đến thì càng tốt” — Người trả lời khảo sát (Câu hỏi: Điều kiện để tin tưởng & dùng thật)
    3. “Trả lời nhanh, ngắn gọn đầy đủ ý” — Người trả lời khảo sát (Câu hỏi: Điều kiện để tin tưởng & dùng thật)
    4. “Ghi chép ngắn gọn nhưng đủ ý” — Người trả lời khảo sát (Câu hỏi: Điều kiện để tin tưởng & dùng thật)
    5. “Giốnv notebooklm” — Người trả lời khảo sát (Câu hỏi: Điều kiện để tin tưởng & dùng thật)

## §2. Impact & quyết định chọn

* Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):

| Ứng viên                                                           |                                                                                            Bao nhiêu người gặp |  Tần suất | Mỗi lần tốn gì                                                          | Khả thi    | Chọn?       |
| -------------------------------------------------------------------- | -----------------------------------------------------------------------------------------------------------------: | ----------: | --------------------------------------------------------------------------- | ----------- | ------------ |
| Tự động trích xuất Note & Tóm tắt trọng tâm từ đoạn chat |  **12/21 (57.1%)** không biết chọn ý quan trọng; <br />**15/21 (71.4%)** hay quên lưu / bỏ xó |         Cao | Mất**2–30 phút** copy-paste thủ công, gián đoạn mạch tư duy | Cao         | Chọn        |
| Tự động sinh Flashcard chuẩn bị ôn thi (Anki/Quizlet)         | **12/21 (57.1%)** chat AI để chuẩn bị ôn thi; <br />**6/21 (28.6%)** ghi xong không mở lại ôn | Trung bình | Mất công sức tự thiết lập câu hỏi/đáp, dễ nản giữa chừng      | Trung bình | Có thể sau |
| Đồng bộ Note tự động lên Notion / Obsidian                    |                                          **5/21 (23.8%)** dùng Notion, **2/21 (9.5%)** dùng Obsidian | Trung bình | Tốn công cấu hình API, chỉnh sửa định dạng thủ công              | Trung bình | Có thể sau |



### Ứng viên CHỌN + vì sao

Nhóm chọn **“Tự động trích xuất Note & Tóm tắt trọng tâm từ đoạn chat”** vì **12/21 người (57.1%)** khó chọn lọc ý quan trọng và **15/21 người (71.4%)** thường quên lưu hoặc bỏ xó nội dung. Việc ghi chú thủ công mất **2–30 phút mỗi lần** và làm gián đoạn quá trình học. Đây là hướng có **tần suất cao, tác động rõ ràng và khả thi cao** để triển khai prototype.

## §3. Giải pháp tương tự đã nghiên cứu

* NotebookLM: lấy tài liệu làm nguồn chính, trả lời có dẫn chứng tốt; đáng học ở cách bám nguồn và cách trình bày câu trả lời rõ ràng; mình khác ở chỗ giới hạn theo từng slide của buổi học và có bước tạo note sang Notion sau hội thoại.
* ChatGPT/Claude khi dùng riêng: linh hoạt nhưng không tự giới hạn theo một slide; đáng né ở việc dễ trả lời vượt phạm vi nếu user không đưa context rõ; mình khác ở cơ chế truy xuất đúng `slide_id`.
* Quizlet/duolingo-style study tools: mạnh ở nhịp học ngắn và nhắc lại; đáng học ở trải nghiệm đơn giản; mình khác ở việc tập trung vào hỏi đáp trực tiếp từ slide và tạo note theo buổi học.

## §4. Thiết kế

* Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):
  Một học viên trong buổi học chọn đúng slide, hỏi một câu về nội dung chưa hiểu, hệ thống chỉ truy xuất dữ liệu của slide đó để trả lời có căn cứ và sau khi học xong tạo note tóm tắt sang Notion.
* Non-goals (≥3 thứ KHÔNG build):

  1. Không xây chatbot trả lời toàn bộ kiến thức ngoài slide.
  2. Không làm hệ thống học cá nhân hoá theo hồ sơ người dùng.
  3. Không làm tự động tạo quiz/flashcard ở phiên bản này.
  4. Không cho phép chatbot truy cập chéo giữa các slide khác nhau.
* Mức prototype nhắm tới: [ ] Sketch [x] Mock [ ] Working — phần nào mock, phần nào thật:

  * Thật: upload file, tách text, chunking, embedding, lưu ChromaDB, retrieve theo `slide_id`.
  * Mock/đơn giản hoá: giao diện, bước tạo note, một phần formatting note.
  * Thật ở lõi: trả lời theo context và tạo markdown tóm tắt từ hội thoại.
* Automation: [ ] augment [x] conditional [ ] automate — lý do theo cost-of-error:
  Hệ thống tự trả lời khi có đủ căn cứ trong đúng slide; nếu thiếu căn cứ thì báo không đủ thông tin thay vì tự đoán. Sai trong học tập gây hiểu nhầm kiến thức nên không nên auto hoàn toàn.
* §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):

| Nguyên tắc                               | Áp cụ thể vào đâu trong prototype                                           |
| ------------------------------------------ | --------------------------------------------------------------------------------- |
| G1 — Làm rõ hệ thống làm được gì | Màn hình upload và chọn slide nêu rõ chỉ hỏi đáp trong slide đã chọn |
| G2 — Làm rõ nó làm tốt đến đâu   | Hiển thị nguồn theo trang/chunk trong câu trả lời                           |
| G10 — Thu hẹp phạm vi khi nghi ngờ     | Nếu context không đủ thì nói không đủ thông tin thay vì đoán         |
| G9 — Sửa dễ dàng                       | User có thể hỏi lại, đổi slide, hoặc bấm tạo note lại từ hội thoại   |
| G11 — Giải thích vì sao                | Câu trả lời kèm nguồn “Trang X” để user kiểm tra lại                   |
| G8 — Gạt bỏ dễ dàng                   | User có thể bỏ qua gợi ý hoặc câu trả lời và tiếp tục hỏi câu khác |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8)

| Tình huống                                                        | Lớp                           | Hành vi mong muốn                                                                     | Nguyên tắc áp |
| ------------------------------------------------------------------- | ------------------------------ | --------------------------------------------------------------------------------------- | ---------------- |
| Câu hỏi không có trong slide                                    | ① Nguồn sự thật            | Báo không tìm thấy căn cứ trong slide                                             | G10, G2          |
| User hỏi mơ hồ “phần đó là gì?”                           | ② Mơ hồ / thiếu thông tin | Hỏi lại để làm rõ trang/ý/cụm từ                                               | G10              |
| User yêu cầu trả lời từ slide khác                            | ③ Ngoài phạm vi             | Từ chối truy xuất chéo, nhắc đang ở slide hiện tại                             | G1, G10          |
| Context có nhiều đoạn gần giống nhau                          | ① Nguồn sự thật            | Chọn đoạn phù hợp nhất và nêu nguồn                                            | G2, G11          |
| Slide có lỗi OCR hoặc text trích xuất sai                      | ④ Đặc thù domain           | Báo có thể trích xuất thiếu/chệch và cho phép user thử lại file khác        | G9, G10          |
| User hỏi tóm tắt toàn bộ nhưng chỉ có vài chunk liên quan | ② Mơ hồ / thiếu thông tin | Chuyển sang lấy toàn bộ chunk để summarize                                        | G10              |
| Note tạo ra thiếu ý vì hội thoại ngắn                        | ④ Đặc thù domain           | Ghi rõ note chỉ phản ánh nội dung đã trao đổi                                  | G2, G11          |
| User muốn sửa note ngay sau khi tạo                              | ③ Ngoài phạm vi             | Cho tạo lại note từ hội thoại mới hoặc chỉnh nội dung trước khi đẩy Notion | G9               |

## §6. Bốn đường đi của trải nghiệm

* Happy path: User upload slide → chọn slide → hỏi câu hỏi → nhận câu trả lời có nguồn → bấm tạo note → note được đẩy sang Notion.
* Low-confidence (②): User hỏi mơ hồ hoặc nội dung thiếu căn cứ → hệ thống nói rõ chưa đủ thông tin và gợi ý hỏi lại.
* Failure/không căn cứ (①): Không tìm thấy đoạn liên quan trong slide → trả lời “slide này chưa có đủ nội dung để trả lời”.
* Correction (user sửa): User đổi câu hỏi, đổi slide hoặc yêu cầu tạo lại note với nội dung mới.
* Khi bị đòi ngoài phạm vi (③): Hệ thống nhắc chỉ trả lời trong slide đã chọn và không truy xuất tài liệu khác.
* Case đặc thù domain (④): Nếu text slide bị lỗi OCR hoặc slide quá dài, hệ thống ưu tiên báo giới hạn và cho phép người dùng thử lại / xem nguồn.

## §7. Kiểm thử

* Chiều chất lượng + định nghĩa kiểm chứng được:

  * Đúng theo nguồn: câu trả lời phải bám đúng chunk của slide đã chọn.
  * Đủ căn cứ: mọi thông tin chính phải trace được về nguồn.
  * Đúng phạm vi: không lấy dữ liệu từ slide khác.
  * Hữu ích cho học tập: câu trả lời và note phải dễ đọc, ngắn gọn, rõ ý.
* Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):

  * [ ] 8 case thường
  * [ ] 4 case mơ hồ
  * [ ] 4 case không có trong slide
  * [ ] 2 case ngoài phạm vi
  * [ ] 2 case tóm tắt toàn bộ slide
    File: `eval/golden_set.json`
* Quality bar (chốt từ thời điểm nộp spec, giữ nguyên sau đó):
  “Đạt khi ≥ [điền %] qua bộ, và không có case nào sai phạm vi slide.”
* Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

| Lượt chạy | Tỉ lệ đạt | Lỗi chính | Ghi chú |
| ------------ | ------------: | ----------- | -------- |
| Run 1        |          [ ]% | [điền]    | [điền] |
| Run 2        |          [ ]% | [điền]    | [điền] |
| Run 3        |          [ ]% | [điền]    | [điền] |

## §8. Phân công & kế hoạch

* Phân công có tên: spec / evidence / prompt / code / demo

  * Khoa: code RAG, trích xuất, chunking, ChromaDB, retrieve theo `slide_id`.
  * An: prompt, summary, Notion integration, demo flow.
  * Cả hai: spec, evidence, test, slide demo.
* Willing users (≥3 tên) + kế hoạch vòng validation CP5 (3 câu hỏi, ai log):

  * User 1: [tên/vai]
  * User 2: [tên/vai]
  * User 3: [tên/vai]
  * 3 câu hỏi:

    1. Phần nào khó hiểu nhất?
    2. Kết quả này có đáng tin không?
    3. Bạn có dùng lại không, vì sao?
  * Ai log: [điền người phụ trách log]
* Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:

  * Phương án 1: trả lời ngắn, có nguồn theo trang.
  * Phương án 2: trả lời ngắn + bullet “ý chính”.
  * Chọn phương án [điền] vì dễ đọc hơn và phù hợp học tập nhanh.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
| ------------ | --------- | ------------------------------------- |
| [điền]     | [điền]  | [điền]                              |
| [điền]     | [điền]  | [điền]                              |
| [điền]     | [điền]  | [điền]                              |
