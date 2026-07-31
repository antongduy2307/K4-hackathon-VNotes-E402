
### Reflection cá nhân

**Vai trò:** Phụ trách phát triển các AI tools của hệ thống, bao gồm  **Chat (RAG Question Answering)** , **Slide Summarization**

**AI hỗ trợ như thế nào:** AI được sử dụng để trả lời câu hỏi dựa trên nội dung của slide, tóm tắt tài liệu và tổng hợp cuộc hội thoại thành ghi chú.

**Bài học từ case fail:** Ban đầu agent có xu hướng trả lời hoặc suy đoán khi câu hỏi mơ hồ hoặc không có đủ thông tin trong slide. Sau khi xây dựng Golden Set và bổ sung các guardrail (clarify, không hallucinate, chỉ trả lời khi có căn cứ), hệ thống ổn định và đáng tin cậy hơn. Qua đó mình nhận ra rằng việc thiết kế luồng agent và kiểm thử bằng các edge case quan trọng không kém việc cải thiện chất lượng mô hình.
