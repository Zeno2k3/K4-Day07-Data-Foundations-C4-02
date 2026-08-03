# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Xuân Hải  
**Nhóm:** E403-C4-02  
**Ngày:** 2026-08-03

> Báo cáo sử dụng package cá nhân `src.NguyenXuanHai_2A202602022`. Kết quả retrieval được chạy trên corpus 8 tài liệu chính sách Trả hàng/Hoàn tiền Shopee trong `data/k4_returns_shopee`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

**Độ tương tự cosine cao nghĩa là gì?**  
Hai embedding có cosine similarity cao khi chúng gần cùng hướng trong không gian vector. Điều này thường cho thấy hai đoạn văn biểu đạt nội dung hoặc ý nghĩa gần nhau, dù không nhất thiết dùng cùng từ ngữ.

**Ví dụ có độ tương tự cao:**

- Câu A: “Tôi muốn trả lại sản phẩm bị lỗi và nhận hoàn tiền.”
- Câu B: “Khách hàng yêu cầu hoàn tiền vì hàng nhận được bị hỏng.”
- Lý do: Hai câu cùng mô tả yêu cầu hoàn tiền do sản phẩm lỗi.

**Ví dụ có độ tương tự thấp:**

- Câu A: “Shopee xử lý yêu cầu trả hàng trong vài ngày làm việc.”
- Câu B: “Python là ngôn ngữ lập trình phổ biến trong khoa học dữ liệu.”
- Lý do: Hai câu thuộc hai chủ đề hoàn toàn khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**  
Cosine tập trung vào hướng của vector nên ít bị ảnh hưởng bởi độ lớn vector hoặc độ dài văn bản. Euclidean distance đo khoảng cách tuyệt đối, vì vậy hai vector cùng hướng nhưng khác độ lớn vẫn có thể bị xem là xa nhau.

### Bài toán tính toán Chunking

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:

```text
ceil((10000 - 50) / (500 - 50))
= ceil(9950 / 450)
= 23 chunks
```

Khi tăng overlap lên 100:

```text
ceil((10000 - 100) / (500 - 100))
= ceil(9900 / 400)
= 25 chunks
```

Overlap lớn hơn tạo thêm chunk và tăng chi phí embedding, nhưng giúp giữ lại ngữ cảnh nằm ở ranh giới giữa hai chunk và giảm khả năng cắt mất điều kiện hoặc ngoại lệ quan trọng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ

**`SentenceChunker.chunk`**  
Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\r?\n+)` để tách sau dấu kết thúc câu nhưng vẫn giữ dấu câu trong nội dung. Hàm trả `[]` với chuỗi rỗng, loại các phần chỉ có whitespace rồi gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk.

**`RecursiveChunker.chunk` / `_split`**  
Thuật toán thử separator theo thứ tự đoạn văn, dòng, câu, từ rồi mới cắt cứng. Base case là text rỗng, text đã nhỏ hơn `chunk_size`, hoặc không còn separator; các phần quá lớn tiếp tục được xử lý đệ quy bằng separator nhỏ hơn.

**`compute_similarity` và comparator**  
Cosine similarity được tính bằng tích vô hướng chia cho tích hai chuẩn vector, trả `0.0` nếu có vector zero và báo lỗi nếu số chiều khác nhau. Comparator chạy `FixedSizeChunker`, `SentenceChunker` và `RecursiveChunker`, sau đó trả số chunk, độ dài trung bình và danh sách chunk của từng chiến lược.

### Lớp EmbeddingStore

**`add_documents` và `search`**  
Mỗi `Document` được chuẩn hóa thành record gồm ID nội bộ duy nhất, content, metadata và embedding. Khi tìm kiếm, query chỉ được embed một lần; store tính dot product với các embedding đã chuẩn hóa, sắp xếp score giảm dần và trả tối đa `top_k` kết quả.

**`search_with_filter` và `delete_document`**  
Metadata được lọc trước similarity search bằng phép AND giữa các cặp key/value, nhờ đó giảm nhiễu trước khi xếp hạng. `delete_document` tìm và xóa tất cả record có cùng `metadata['doc_id']`, nên một tài liệu có nhiều chunk vẫn được xóa đầy đủ.

### Tác tử KnowledgeBaseAgent

`answer` lấy top-k chunks, gắn `doc_id` và `source_url` cho từng khối ngữ cảnh rồi tạo prompt yêu cầu mô hình chỉ trả lời từ bằng chứng được cung cấp. Nếu không có kết quả, agent trả thông báo thiếu dữ liệu; nếu có, prompt được chuyển cho `llm_fn` và kết quả được trả về dưới dạng chuỗi có thể truy vết nguồn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Package được kiểm tra với biến môi trường:

```powershell
$env:LAB_SOLUTION_PACKAGE = "src.NguyenXuanHai_2A202602022"
python -m unittest tests.test_solution -v
```

Kết quả xác minh:

```text
Ran 42 tests in 0.020s

OK
```

Các nhóm test đã vượt qua gồm ba chunker, cosine similarity, comparator, `EmbeddingStore`, metadata filter, delete và `KnowledgeBaseAgent`.

**Số lượng bài test vượt qua:** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các dự đoán được xác định trước khi gọi OpenAI `text-embedding-3-small`. Quy ước kiểm tra: score từ `0.60` trở lên được xem là cao.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---:|---|---|---|---:|---|
| 1 | Tôi muốn trả lại sản phẩm bị lỗi và nhận hoàn tiền. | Khách hàng yêu cầu hoàn tiền vì hàng nhận được bị hỏng. | Cao | 0.6146 | Đúng |
| 2 | Shopee xử lý yêu cầu trả hàng trong vòng vài ngày làm việc. | Python là ngôn ngữ lập trình phổ biến trong khoa học dữ liệu. | Thấp | 0.2513 | Đúng |
| 3 | Người bán phải phản hồi yêu cầu trả hàng trong vòng hai ngày. | Shop có hai ngày để trả lời khiếu nại về hàng hoàn. | Cao | 0.6160 | Đúng |
| 4 | Người mua được hoàn phí vận chuyển trả hàng. | Người mua không được hoàn phí vận chuyển trả hàng. | Thấp | 0.8840 | Sai |
| 5 | Nếu tự sắp xếp trả hàng, người mua cần thanh toán phí vận chuyển trước. | Khách hàng ứng trước cước gửi trả khi tự chọn đơn vị vận chuyển. | Cao | 0.6694 | Đúng |

Kết quả bất ngờ nhất là cặp 4: hai câu trái nghĩa nhưng similarity đạt `0.8840`. Hai câu gần như dùng cùng toàn bộ từ vựng nên embedding nhận diện chúng rất gần về chủ đề, nhưng không thể hiện tốt phủ định “không”; điều này cho thấy similarity cao không đồng nghĩa với hai câu có cùng tính đúng/sai hoặc quan hệ suy luận.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Cấu hình:** OpenAI `text-embedding-3-small`, Agent `gpt-4.1-mini`, `PolicySectionChunker(chunk_size=700)`, 8 tài liệu, 94 chunks, `top_k=3`.

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Relevant? | Câu trả lời Agent (tóm tắt) |
|---:|---|---|---:|---|---|
| 1 | Thời hạn với thực phẩm tươi sống và điều kiện tính 20 ngày của đơn tự vận chuyển? | `shopee-return-general-rules`, chunk 1: mốc 24 giờ, 15 ngày và 20 ngày | 0.6971 | Có | Thực phẩm tươi sống/đông lạnh: 24 giờ; đơn tự vận chuyển: 20 ngày khi chưa bấm “Đã nhận được hàng”. |
| 2 | Không đồng ý đề xuất Hoàn tiền Ngay thì người mua làm gì? | `shopee-instant-refund-proposal`, chunk 1: “Trao đổi thêm” và “Tôi muốn trả hàng” | 0.6933 | Có | Có thể thương lượng thêm hoặc tiếp tục trả sản phẩm để nhận toàn bộ số tiền theo yêu cầu ban đầu. |
| 3 | “Hàng nguyên vẹn nhưng không còn nhu cầu” áp dụng và loại trừ thế nào? | `shopee-return-review-process`, chunk 5: điều kiện tình trạng sản phẩm | 0.6054 | Có, nhưng thiếu một phần bằng chứng | Agent nêu điều kiện hàng nguyên vẹn và ngoại lệ Shopee Mart, nhưng chưa lấy đủ nhóm hạng thành viên từ tài liệu còn lại. |
| 4 | Tự sắp xếp trả hàng được hoàn Shopee Xu khi nào và bao nhiêu? | `shopee-return-general-rules`, chunk 9 | 0.7766 | Không ở top-1; có nguồn đúng trong top-3 | Agent tổng hợp đúng thời gian 3–5 ngày và hai mức 25.000/40.000 Shopee Xu từ các nguồn sau. |
| 5 | Người bán phản hồi hàng hoàn chưa nhận trong bao lâu và nhập lại kho thế nào? | `shopee-seller-return-management`, chunk 1, lọc `customer_role=seller` | 0.6687 | Có | Phản hồi trong 2 ngày; chọn “Nhập lại hàng vào kho” khi hàng nguyên vẹn. |

**Số câu hỏi có tài liệu liên quan trong top-3:** **5 / 5**  
**Điểm retrieval theo rubric:** **8 / 10**

Metadata filter ở câu 5 giới hạn toàn bộ top-3 về tài liệu dành cho người bán. Failure case chính là câu 3: gold answer nằm trên hai tài liệu, nhưng top-k ưu tiên chunk mô tả tình trạng sản phẩm và chưa giữ đủ phần hạng thành viên. Cách cải thiện là tách query thành hai ý hoặc tăng khả năng truy xuất đa tài liệu, đồng thời lặp lại heading/điều khoản liên quan trong các continuation chunks.

Bài học quan trọng từ việc so sánh chiến lược là số chunk nhỏ hoặc score cao chưa đủ chứng minh retrieval tốt. Chunk phải giữ trọn điều kiện và ngoại lệ; metadata giúp giảm nhiễu theo vai trò, còn câu hỏi nhiều ý có thể cần bằng chứng từ nhiều tài liệu thay vì chỉ tối ưu top-1.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
