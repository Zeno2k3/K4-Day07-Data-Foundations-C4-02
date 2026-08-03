# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Minh Quân
**Nhóm:** C4-02
**Ngày:** 04/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu: Cosine similarity là một thước đo mức độ tương đồng giữa hai vector, không phụ thuộc vào độ lớn của chúng. Trong không gian nhiều chiều của các embedding, các vector có độ tương tự cosine cao thường đại diện cho các khái niệm hoặc ý nghĩa gần giống nhau.*

**Ví dụ có độ tương tự CAO:**
- Câu A: "AI đang thay đổi ngành công nghiệp."
- Câu B: "Trí tuệ nhân tạo đang định hình lại các ngành công nghiệp."
- Tại sao tương đồng: Cả hai câu đều nói về sự thay đổi hoặc định hình lại của ngành công nghiệp bởi AI, do đó có ý nghĩa tương tự và vector embedding sẽ gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Trí tuệ nhân tạo đang định hình lại các ngành công nghiệp."
- Câu B: "Cà chua là một loại quả mọng thường được sử dụng như rau trong ẩm thực."
- Tại sao khác: Câu A nói về AI và công nghiệp, trong khi câu B nói về cà chua và ẩm thực. Chúng hoàn toàn không liên quan đến nhau, do đó vector embedding sẽ rất xa nhau trong không gian nhiều chiều.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu: Độ tương tự cosine đo góc giữa các vector, cho biết hướng và ngữ nghĩa của chúng, không bị ảnh hưởng bởi độ lớn (tần suất từ). Khoảng cách Euclid nhạy cảm với độ lớn, có thể cho kết quả sai lệch khi các văn bản có độ dài hoặc tần suất từ khác nhau nhưng cùng chủ đề.*

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> Số chunk = (Tổng số ký tự - Độ chồng chéo) / (Kích thước chunk - Độ chồng chéo) + 1
> = (10000 - 50) / (500 - 50) + 1 = 9950 / 450 + 1 ≈ 22.11 + 1 = 23.11
> *Đáp án:* Khoảng 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu: Số lượng chunk sẽ giảm xuống còn khoảng 21 chunks. Độ chồng chéo nhiều hơn giúp giữ nguyên ngữ cảnh giữa các chunk liền kề, tránh mất mát thông tin khi chunk bị cắt ngang câu.* 

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `re.split(r'(?<=\.)\s|(?<=!)\s|(?<=\?)\s|(?<=\.)\n', text)` để tìm kiếm ranh giới phân tách câu một cách chính xác dựa trên các dấu chấm, chấm hỏi, chấm than theo sau là khoảng trắng hoặc dấu xuống dòng. Sau đó tiến hành gom cụm tuần tự các câu thành các chunk với số câu tối đa mỗi chunk bằng `max_sentences_per_chunk` và loại bỏ các khoảng trắng thừa ở mỗi câu bằng `.strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Triển khai thuật toán đệ quy chia để trị sử dụng danh sách các dấu phân tách ưu tiên giảm dần. Base case là khi độ dài văn bản hiện tại nhỏ hơn hoặc bằng `chunk_size` thì dừng chia và trả về văn bản, hoặc khi đã thử hết tất cả các dấu phân tách thì cắt cứng theo `chunk_size`. Khi gặp dấu phân tách phù hợp, văn bản được phân rã thành các phần nhỏ và gộp lại cho đến khi đạt ngưỡng `chunk_size`; nếu có phần đơn lẻ nào vượt quá `chunk_size`, nó sẽ được đệ quy xử lý tiếp bằng các dấu phân tách mức ưu tiên thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Hỗ trợ song song cả lưu trữ trong bộ nhớ danh sách (In-memory) và cơ sở dữ liệu vector ChromaDB. Với In-memory, tài liệu được lưu dưới dạng dictionary chuẩn hóa có chứa trường `embedding` và `metadata`. Khi tìm kiếm (`search`), truy vấn được vector hóa rồi tính toán tích vô hướng (dot product) với từng vector chunk trong bộ nhớ thông qua hàm `_dot()`, xếp hạng giảm dần theo score để trả về kết quả top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc siêu dữ liệu trước (pre-filtering): Với In-memory, lọc các bản ghi phù hợp với `metadata_filter` bằng cách so khớp các trường dữ liệu trước rồi mới chạy similarity search trên tập con kết quả. Hàm `delete_document` xóa toàn bộ các chunk thuộc cùng một tài liệu bằng cách lọc và loại bỏ các bản ghi có metadata `doc_id` khớp với `doc_id` cần xóa (đối với ChromaDB sử dụng `collection.delete()`).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Nhận câu hỏi từ người dùng, gọi `store.retrieve()` để lấy ra danh sách nội dung top_k chunks có độ tương đồng cao nhất để làm ngữ cảnh. Sau đó, ngữ cảnh này được đưa trực tiếp vào một cấu trúc prompt tiếng Việt thiết kế sẵn định dạng và chuyển tiếp cho mô hình ngôn ngữ lớn (`self.llm_fn`) để tổng hợp ra câu trả lời chính xác, tránh hiện tượng ảo tưởng (hallucination).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\mquan\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: D:\Project\20K - AI\Day07\K4-Day07-Data-Foundations-C4-02
plugins: anyio-4.14.2, langsmith-0.10.10, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Làm thế nào để tôi yêu cầu trả hàng/hoàn tiền trên Shopee? | Các bước thực hiện trả hàng hoàn tiền Shopee là gì? | Cao | -0.1324 | Không |
| 2 | Thời gian xử lý yêu cầu hoàn tiền của Shopee là bao lâu? | Quy trình đổi trả sản phẩm diễn ra trong mấy ngày? | Cao | 0.1829 | Không |
| 3 | Shopee Mall hỗ trợ đổi trả hàng trong vòng 7 ngày kể từ ngày nhận hàng. | Người mua có thể trả lại sản phẩm Shopee Mall trong thời hạn 7 ngày. | Cao | -0.1648 | Không |
| 4 | Phí vận chuyển trả hàng do ai thanh toán? | Ai là người chịu tiền ship khi trả lại hàng? | Cao | -0.0821 | Không |
| 5 | Làm thế nào để tôi yêu cầu trả hàng/hoàn tiền trên Shopee? | Mật khẩu tài khoản Shopee của tôi bị mất thì phải làm sao? | Thấp | -0.0484 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm thực tế của các cặp câu có sự tương đồng ngữ nghĩa cực kỳ cao (như Cặp 1 và Cặp 3) lại rất thấp (quanh mức 0 hoặc bị âm), không khác biệt nhiều so với cặp câu không liên quan (Cặp 5). Điều này xảy ra bởi vì `MockEmbedder` chỉ băm chuỗi văn bản bằng MD5 thành các vector ngẫu nhiên mà không hề biểu diễn ngữ nghĩa. Nhận xét này nhấn mạnh rằng để biểu diễn ngữ nghĩa của văn bản thật sự, ta bắt buộc phải sử dụng các mô hình ngôn ngữ/nhúng thực tế (như Sentence Transformers) được huấn luyện từ dữ liệu lớn, chứ không thể dùng hàm băm ngẫu nhiên.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nếu tôi cần gửi yêu cầu Trả hàng/Hoàn tiền cho sản phẩm thực phẩm tươi sống thì thời hạn tối đa là bao lâu? Còn với đơn hàng do người bán tự vận chuyển, khi nào được tính 20 ngày? | tiến hành xử lý yêu cầu Trả hàng/Hoàn tiền trên những bằng chứng đã nhận trước đo... (Trích từ shopee-return-review-process.md) | 0.2229 | Không | Trả lời dựa trên ngữ cảnh đã được tìm thấy. |
| 2 | Trong trường hợp đề xuất Hoàn tiền Ngay của người bán không đủ, người mua có thể làm gì để tiếp tục quy trình và nhận toàn bộ số tiền theo yêu cầu ban đầu? | Theo dõi trạng thái và xử lý đơn Trả hàng/ hoàn tiền trên Kênh Quản Lý Shop... (Trích từ shopee-seller-return-management.md) | 0.2683 | Không | Trả lời dựa trên ngữ cảnh đã được tìm thấy. |
| 3 | Trong chính sách Shopee, “Hàng nguyên vẹn nhưng không còn nhu cầu” áp dụng cho đối tượng nào và nó bị loại trừ với loại sản phẩm/nơi bán nào? | bị Shopee loại khỏi gói ShopeeVIP theo các chính sách, quy định của Shopee. Việc chấm dứt... (Trích từ shopee-return-refund-policy.md) | 0.3582 | Không | Trả lời dựa trên ngữ cảnh đã được tìm thấy. |
| 4 | Nếu yêu cầu Trả hàng/Hoàn tiền được chấp thuận và người mua tự sắp xếp trả hàng, trong trường hợp nào Shopee hỗ trợ hoàn phí trả hàng bằng Shopee Xu và mức hoàn là bao nhiêu? | Trường hợp nếu bạn không đồng ý với đề xuất đó hãy nhấn “Trao đổi thêm” để tiếp tục... (Trích từ shopee-return-review-process.md) | 0.2765 | Không | Trả lời dựa trên ngữ cảnh đã được tìm thấy. |
| 5 | Với tư cách là người bán, nếu hệ thống ghi nhận đã trả hàng thành công nhưng shop chưa nhận được, shop phải phản hồi trong bao nhiêu ngày và nếu hàng hoàn về thành công thì cần chọn xử lý nào để nhập lại kho khi hàng nguyên vẹn? | Nếu Shopee đồng ý Hoàn Tiền Ngay: bạn sẽ nhận được tiền hoàn mà không cần trả hàng... (Trích từ shopee-return-review-process.md) | 0.4191 | Không | Trả lời dựa trên ngữ cảnh đã được tìm thấy. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5 *(Lưu ý: Kết quả 0/5 là do sử dụng MockEmbedder theo cấu hình test mặc định cục bộ, không hỗ trợ tìm kiếm ngữ nghĩa).*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được từ các thành viên khác cách thiết kế và tận dụng bộ lọc `metadata_filter` (như lọc vai trò `customer_role` là người mua hay người bán) trước khi chạy thuật toán tương đồng. Việc này giúp cải thiện đáng kể độ chính xác của tìm kiếm và giảm thiểu việc tìm sai văn bản có từ khóa giống nhưng không đúng đối tượng đích.

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
