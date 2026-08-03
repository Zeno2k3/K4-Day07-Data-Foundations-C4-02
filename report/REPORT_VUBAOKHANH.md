# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Bảo Khánh
**Nhóm:** [E403-C4-2]
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Nghĩa là hai văn bản có chung ngữ cảnh, ý nghĩa hoặc chủ đề (góc giữa 2 vector của chúng trong không gian hẹp).

**Ví dụ có độ tương tự CAO:**
- Câu A: "Shopee sẽ hoàn phí trả hàng bằng Shopee Xu cho người mua"
- Câu B: "Tiền phí vận chuyển khi hoàn trả sản phẩm được trả bằng xu trên Shopee"
- Tại sao tương đồng: Cả 2 câu đều nói về một chính sách chung dù sử dụng từ vựng khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Shopee hoàn phí trả hàng bằng Shopee Xu"
- Câu B: "Cách nấu món phở bò ngon tại nhà"
- Tại sao khác: Hai câu thuộc hai chủ đề (domain) hoàn toàn không liên quan đến nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Vì Cosine chỉ quan tâm đến hướng (ngữ nghĩa) của vector mà bỏ qua độ lớn (độ dài văn bản). Một đoạn văn ngắn và một đoạn văn dài có cùng chủ đề vẫn có độ tương tự Cosine cao, nhưng khoảng cách Euclid lại rất lớn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* (10000 - 50) / (500 - 50) = 9950 / 450 = 22.11
> *Đáp án:* Làm tròn lên là 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Số lượng chunk sẽ tăng lên thành 25 chunks ( (10000-100)/(500-100) = 24.75 -> 25). Việc tăng overlap giúp đảm bảo ngữ cảnh không bị đứt đoạn gãy gọn ở giữa một câu hoặc một từ quan trọng, giúp AI hiểu trọn vẹn ngữ cảnh hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

**Chiến lược Chunking:**
Tôi đã chọn triển khai và áp dụng **RecursiveChunker** cho toàn bộ dữ liệu.
Lý do: Bộ tài liệu chính sách của Shopee (Markdown) thường có cấu trúc rõ ràng với các thẻ Header (`#`, `##`) và các đoạn văn cách nhau bằng dòng trống (`\n\n`). RecursiveChunker giúp tách văn bản một cách thông minh bằng cách ưu tiên ngắt ở các đoạn văn lớn, sau đó mới ngắt đến từng câu, giúp giữ nguyên vẹn trọn vẹn ngữ nghĩa của một điều khoản thay vì cắt ngang chừng như FixedSizeChunker.

**Xử lý Metadata:**
Tôi đã thiết kế hàm tách metadata tự động đọc phần "Front Matter" trên cùng của mỗi file Markdown. Qua đó, tôi gắn các trường quan trọng như `customer_role` (buyer/seller) và `policy_section`. Nhờ vậy, khi gặp các câu hỏi yêu cầu lọc theo vai trò (ví dụ: "Với tư cách là người bán..."), hệ thống có thể dùng `search_with_filter` để thu hẹp phạm vi tìm kiếm, giúp kết quả chính xác tuyệt đối.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng regex `/[.!?](\s+|$)/` để phân tách các câu dựa trên các dấu chấm câu kết thúc. Đối với các trường hợp ngoại lệ như tiêu đề hoặc liệt kê, tôi kiểm tra độ dài của đoạn chuỗi để tránh việc tách quá nhỏ gây mất ngữ cảnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán ưu tiên chia theo các ký tự phân cách theo thứ tự: `\n\n`, `\n`, ` `. Base case là khi kích thước đoạn văn nhỏ hơn hoặc bằng `chunk_size`, nếu không, nó sẽ tiếp tục gọi đệ quy để tách nhỏ cho đến khi đạt yêu cầu.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.10.0, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.16s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee hoàn xu cho người mua | Khách hàng nhận được Shopee Xu | cao | 0.82 | Đúng |
| 2 | Giao hàng trong vòng 3 ngày | Đơn hàng vận chuyển khoảng 3 hôm | cao | 0.79 | Đúng |
| 3 | Người bán đóng gói cẩn thận | Khách hàng quay video mở hộp | thấp | 0.35 | Đúng |
| 4 | Miễn phí trả hàng 100% | Shopee không thu phí đổi trả | cao | 0.85 | Đúng |
| 5 | Thanh toán bằng thẻ tín dụng | Cách nướng thịt heo ngon | thấp | 0.12 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:* Bất ngờ nhất là cặp số 3 dù cùng chủ đề "giao nhận hàng hóa" nhưng điểm lại rất thấp (0.35). Điều này cho thấy Embeddings phân biệt rất rõ **chủ thể** và **hành động** (Người bán đóng gói vs Khách hàng mở hộp) chứ không chỉ nhìn vào các từ khóa chung chung.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu Trả hàng/Hoàn tiền cho thực phẩm tươi sống là bao lâu? | 1.2 Thời gian tối đa để gửi yêu cầu; 1.3 Lý do Trả hàng/Hoàn tiền | 0.81 | Có | 24 giờ kể từ lúc giao hàng thành công. |
| 2 | Nếu đề xuất Hoàn tiền của người bán không đủ, người mua làm gì? | bước phản hồi trường hợp không đồng ý | 0.76 | Có | Chọn “Trao đổi thêm” hoặc “Tôi muốn trả hàng” để nhận toàn bộ số tiền. |
| 3 | “Hàng nguyên vẹn nhưng không còn nhu cầu” áp dụng cho đối tượng nào? | Phần Lý do Trả hàng/Hoàn tiền “Đổi ý” | 0.82 | Có | Áp dụng cho hội viên Kim Cương, Vàng, ShopeeVIP. Trừ Shopee Mart. |
| 4 | Shopee hoàn phí trả hàng bằng Shopee Xu như thế nào và bao nhiêu? | 2.2 Phí vận chuyển trả hàng; 3 Điều kiện hỗ trợ | 0.85 | Có | Hoàn 25.000 Xu (cùng tỉnh) và 40.000 Xu (khác tỉnh). |
| 5 | Với tư cách là người bán, shop phải phản hồi trong bao nhiêu ngày nếu hàng hoàn về? | Quản lý đơn trả hàng hoàn tiền dành cho Người bán | 0.41 | Có | Phản hồi trong vòng 2 ngày. Chọn “Nhập lại hàng vào kho”. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:* Tôi nhận ra rằng một hệ thống RAG không chỉ phụ thuộc vào AI mạnh, mà chất lượng dữ liệu đầu vào (cách Chunking và gán Metadata) đóng vai trò quyết định. Đôi khi dùng các Embedder dung lượng nhỏ (như Local) kết hợp với Metadata filter còn ra kết quả tốt hơn là dùng Embedder khổng lồ nhưng tìm mò.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
