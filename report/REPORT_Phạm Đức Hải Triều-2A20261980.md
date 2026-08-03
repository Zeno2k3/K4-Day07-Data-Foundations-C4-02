# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Đức Hải Triều
**Nhóm:** Nhóm E403-c4-02
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Hai vector có độ tương tự cosine cao nghĩa là chúng chỉ về cùng một hướng trong không gian đa chiều, thể hiện rằng hai đoạn văn bản có ý nghĩa ngữ nghĩa rất gần gũi với nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi rất thích ăn phở bò vào buổi sáng.
- Câu B: Bữa sáng yêu thích của tôi là món phở bò.
- Tại sao tương đồng: Dù dùng các từ khác nhau một chút nhưng ý nghĩa tổng thể hoàn toàn giống nhau, cùng nói về sở thích ăn phở bò buổi sáng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Mèo là loài động vật thích bắt chuột.
- Câu B: Điện thoại iPhone 15 mới ra mắt có camera rất đẹp.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn không liên quan (động vật vs công nghệ).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Độ tương tự cosine chỉ quan tâm đến góc giữa hai vector (phản ánh hướng/ý nghĩa) thay vì độ dài của vector. Các câu dài có thể tạo ra vector dài hơn, khiến khoảng cách Euclid lớn, nhưng độ tương tự cosine vẫn sẽ nhận diện được chúng có cùng ngữ nghĩa nếu chúng cùng hướng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* step = chunk_size - overlap = 500 - 50 = 450. Số chunk = (10000 - 50) / 450 = 22.11 -> Làm tròn lên là 23 chunks.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Khi overlap tăng lên 100, step giảm xuống 400, số lượng chunk sẽ tăng lên ((10000 - 100)/400 = 24.75 -> 25 chunks). Ta muốn độ chồng chéo nhiều hơn để đảm bảo không bị mất đi thông tin ngữ cảnh quan trọng tại vị trí cắt giữa hai chunk kề nhau.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?* Tôi sử dụng regex `(?<=[.!?])\s+` để cắt theo các dấu kết thúc câu có khoảng trắng theo sau. Tôi có xử lý ngoại lệ cho các từ viết tắt phổ biến (như Mr., Mrs., Dr.) bằng cách kiểm tra từ cuối cùng trước dấu chấm, nếu nằm trong danh sách viết tắt thì sẽ nối lại với câu tiếp theo thay vì ngắt câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?* Thuật toán hoạt động đệ quy bằng cách thử chia nhỏ đoạn văn theo danh sách các dấu phân cách (như \n\n, \n, " "). Base case là khi chuỗi hiện tại đã nhỏ hơn hoặc bằng chunk_size, hoặc khi đã hết danh sách phân cách thì sẽ chia mạnh bằng cách cắt đều theo số ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?* Tôi lưu trữ các document dưới dạng dictionary trong một list `_store`, mỗi record gồm id, content, metadata và vector embedding. Hàm search tính độ tương tự giữa query vector và vector của mỗi record bằng hàm `compute_similarity` (dùng numpy dot product và norm) rồi sort giảm dần để lấy top k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?* Tôi thực hiện lọc (filter) trước khi search bằng cách duyệt qua `_store` và chỉ giữ lại những record có chứa đầy đủ các key-value trong `metadata_filter`. Xóa bằng cách sử dụng list comprehension để tạo ra list `_store` mới không chứa các record có `doc_id` trùng với ID cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?* Tôi cấu trúc prompt bằng cách lấy top k kết quả từ vector store, định dạng thành các bullet points kèm điểm score. Sau đó, nối (inject) các dòng context này vào trước phần câu hỏi trong prompt string rồi đẩy vào LLM để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: D:\K4-Day07-Data-Foundations
plugins: anyio-4.14.2
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

============================= 42 passed in 0.66s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng hóa | Hướng dẫn trả hàng và hoàn tiền | cao | 0.85 | Đúng |
| 2 | Thanh toán bằng thẻ tín dụng | Phương thức thanh toán VISA | cao | 0.81 | Đúng |
| 3 | Thời gian giao hàng dự kiến | Cách thức vận chuyển đơn hàng | cao | 0.76 | Đúng |
| 4 | Chính sách bảo mật thông tin | Đổi trả sản phẩm lỗi | thấp | 0.23 | Đúng |
| 5 | Phí giao hàng nội thành | Mật khẩu tài khoản bị quên | thấp | 0.12 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:* Bất ngờ nhất là cặp số 2 và số 3, tuy dùng các từ ngữ hoàn toàn khác nhau nhưng embedding vẫn nắm bắt được chúng cùng nói về thanh toán và giao hàng. Điều này chứng tỏ embedding không so sánh bằng keyword matching, mà thực sự mã hóa được ngữ nghĩa tiềm ẩn (semantic meaning) của câu vào không gian vector.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sản phẩm lỗi có được đổi mới không? | Quý khách được quyền đổi mới sản phẩm miễn phí trong vòng 7 ngày nếu có lỗi từ nhà sản xuất... | 0.88 | Có | Được phép đổi mới trong 7 ngày nếu lỗi từ NSX. |
| 2 | Làm sao để thanh toán bằng MoMo? | Các phương thức thanh toán được chấp nhận bao gồm: thẻ tín dụng, chuyển khoản ngân hàng và ví điện tử MoMo... | 0.84 | Có | Bạn có thể chọn ví điện tử MoMo ở bước thanh toán cuối cùng. |
| 3 | Đơn hàng giao trễ xử lý thế nào? | Nếu đơn hàng giao trễ hơn 3 ngày so với dự kiến, chúng tôi sẽ hoàn lại 100% phí vận chuyển... | 0.89 | Có | Khách hàng sẽ được hoàn 100% phí vận chuyển nếu trễ hơn 3 ngày. |
| 4 | Phí ship nội thành là bao nhiêu? | Phí giao hàng nội thành là 20.000 VNĐ cho các đơn hàng dưới 500.000 VNĐ, miễn phí cho đơn lớn hơn... | 0.91 | Có | Phí ship là 20k cho đơn dưới 500k, miễn phí nếu từ 500k trở lên. |
| 5 | Dữ liệu cá nhân có bị chia sẻ cho bên thứ ba không? | Công ty cam kết tuyệt đối bảo mật thông tin khách hàng và không bán dữ liệu cho bất kỳ bên thứ 3 nào... | 0.90 | Có | Công ty cam kết bảo mật và không bán dữ liệu cho bên thứ 3. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:* Tôi học được cách sử dụng recursive chunking với danh sách các dấu phân cách thông minh, giúp các đoạn văn bản (chunk) giữ được ý nghĩa nguyên vẹn hơn thay vì bị cắt đôi ngẫu nhiên như fixed size chunking.

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
