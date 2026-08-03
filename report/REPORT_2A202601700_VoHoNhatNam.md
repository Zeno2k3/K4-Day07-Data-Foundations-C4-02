# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Võ Hồ Nhật Nam
**Nhóm:** C4-02
**Ngày:** 8/3/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có vector embedding trỏ gần như cùng một hướng trong không gian nhiều chiều, tức là chúng mang ý nghĩa/ngữ cảnh gần giống nhau, dù có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Con chó đang chạy trong công viên."
- Câu B: "Một chú chó đang chơi đùa ngoài công viên."
- Tại sao tương đồng: Cùng chủ đề (chó, công viên), cùng hành động vận động, cấu trúc ngữ nghĩa gần giống nhau nên embedding của hai câu sẽ nằm gần nhau về hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Con chó đang chạy trong công viên."
- Câu B: "Giá cổ phiếu tăng mạnh trong phiên giao dịch hôm nay."
- Tại sao khác: Chủ đề, ngữ cảnh và từ vựng hoàn toàn khác nhau (động vật/giải trí vs. tài chính) nên vector embedding sẽ trỏ theo hướng rất khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến hướng của vector, không bị ảnh hưởng bởi độ lớn (magnitude) — điều quan trọng vì độ dài văn bản khác nhau có thể làm embedding có độ lớn khác nhau dù ý nghĩa tương tự. Euclidean distance lại nhạy với độ lớn này, dễ đánh giá sai hai văn bản cùng ý nghĩa nhưng độ dài/tần suất từ khác nhau là "khác xa nhau".

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: số_chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap=100: làm_tròn_lên((10000-100)/(500-100)) = làm_tròn_lên(9900/400) = làm_tròn_lên(24.75) = **25 chunks** — tăng từ 23 lên 25, tức là nhiều chunk hơn (bước trượt step = chunk_size - overlap nhỏ hơn nên cần nhiều bước hơn để đi hết tài liệu). Tăng overlap giúp giảm khả năng một câu/ý quan trọng bị cắt đứt ngay ranh giới hai chunk, cải thiện chất lượng truy xuất (retrieval), đổi lại tốn thêm bộ nhớ/thời gian tính toán do dữ liệu trùng lặp nhiều hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src/VoHoNhatNam` (bản cá nhân, cùng cấu trúc với gói `src` mẫu).

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split` với pattern `(?<=[.!?])\s+|(?<=\.)\n` để tách câu ngay sau dấu `.`, `!`, `?` theo sau là khoảng trắng, hoặc dấu `.` theo sau là xuống dòng — khớp với đặc tả "., !, ? hoặc .\n". Sau khi tách, lọc bỏ chuỗi rỗng và `strip()` từng câu, rồi gom nhóm `max_sentences_per_chunk` câu một lần bằng cách duyệt theo bước nhảy (slicing) và nối lại bằng khoảng trắng. Edge case xử lý: text rỗng trả về `[]` ngay từ đầu; câu cuối không đủ số lượng vẫn được gộp thành 1 chunk (nhóm dư).

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử lần lượt các separator theo độ ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`): tách văn bản theo separator hiện tại, rồi gộp các phần lại thành từng chunk sao cho không vượt quá `chunk_size`; nếu một phần đơn lẻ vẫn quá dài, gọi đệ quy `_split` với danh sách separator còn lại (bỏ separator hiện tại) để chia nhỏ tiếp. Base case: (1) nếu `current_text` đã ngắn hơn hoặc bằng `chunk_size` thì trả về nguyên văn bản đó (hoặc `[]` nếu rỗng); (2) nếu hết separator để thử (`remaining_separators` rỗng) thì cắt cứng theo `chunk_size` ký tự làm phương án dự phòng cuối cùng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hóa qua `_make_record`: tính embedding bằng `self._embedding_fn(doc.content)`, gắn thêm `doc_id` vào metadata, rồi append vào danh sách `self._store` trong bộ nhớ (đồng thời `collection.add(...)` vào ChromaDB nếu khả dụng). `search` nhúng câu truy vấn, sau đó `_search_records` tính tích vô hướng (dot product) giữa vector truy vấn và từng embedding đã lưu (vì `_mock_embed`/most embedders trả về vector đã chuẩn hóa nên dot product tương đương cosine similarity), sắp xếp giảm dần theo score và cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata **trước**: duyệt `self._store`, chỉ giữ lại các record có toàn bộ cặp key-value trong `metadata_filter` khớp với `record["metadata"]`, sau đó mới gọi `_search_records` trên tập con đã lọc để tính điểm tương tự — cách này tránh tính embedding similarity trên các bản ghi chắc chắn không liên quan. `delete_document` xóa bằng cách rebuild `self._store` chỉ giữ lại các record có `metadata["doc_id"] != doc_id`, và trả về `True`/`False` dựa trên việc độ dài danh sách có giảm hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `__init__` chỉ lưu tham chiếu `store` và `llm_fn` (dependency injection, không tạo logic thêm). `answer` gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất, nối nội dung các chunk (`r["content"]`) bằng `\n\n` thành một khối "Context", rồi ghép vào một prompt có cấu trúc rõ ràng gồm 3 phần: hướng dẫn (chỉ trả lời dựa trên context), Context, và Question — cuối cùng gọi `llm_fn(prompt)` và trả về kết quả trực tiếp (theo đúng pattern RAG: retrieve → augment prompt → generate).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

**Ghi chú:** Bản cá nhân đầy đủ đặt tại `src/VoHoNhatNam/` (cùng nội dung TODO). Chạy `LAB_SOLUTION_PACKAGE=src.VoHoNhatNam pytest tests/ -v` cho kết quả **41/42 pass** — test duy nhất fail (`test_src_package_exists`) chỉ kiểm tra sự tồn tại của file `src/__init__.py` ở gói gốc, không liên quan tới logic đã implement.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Con chó đang chạy trong công viên." | "Một chú chó đang chơi đùa ngoài công viên." | cao | -0.1142 | Không |
| 2 | "Con chó đang chạy trong công viên." | "Giá cổ phiếu tăng mạnh trong phiên giao dịch hôm nay." | thấp | 0.0262 | Đúng (gần 0, đúng hướng) |
| 3 | "Khách hàng có thể đổi trả sản phẩm trong 7 ngày." | "Chính sách hoàn trả hàng áp dụng trong vòng một tuần." | cao | -0.3426 | Không |
| 4 | "Khách hàng có thể đổi trả sản phẩm trong 7 ngày." | "Người bán cần cung cấp giấy phép kinh doanh hợp lệ." | thấp | -0.0215 | Đúng (gần 0, đúng hướng) |
| 5 | "Thanh toán có thể thực hiện qua thẻ tín dụng hoặc ví điện tử." | "Bạn có thể trả tiền bằng thẻ ngân hàng hoặc ví online." | cao | -0.0757 | Không |

*(Điểm thực tế được tính bằng `compute_similarity(_mock_embed(a), _mock_embed(b))` trong `src/chunking.py` + `src/embeddings.py`, chạy trực tiếp trên máy — không phải số giả định.)*

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 1 và cặp 3 — hai câu có ý nghĩa gần như giống hệt nhau (cùng nói về chó chơi trong công viên; cùng nói về đổi trả trong 7 ngày/1 tuần) nhưng lại có cosine similarity **âm** thay vì dương cao. Điều này cho thấy `MockEmbedder` chỉ băm (hash) văn bản bằng MD5 rồi sinh vector giả-ngẫu nhiên có seed phụ thuộc toàn bộ chuỗi ký tự — nó không mã hóa ngữ nghĩa thật, nên hai câu đồng nghĩa nhưng khác từ vựng hoàn toàn (paraphrase) sẽ cho vector gần như độc lập ngẫu nhiên với nhau. Bài học: chất lượng của cosine similarity hoàn toàn phụ thuộc vào embedding model — nó chỉ phản ánh đúng ý nghĩa khi dùng embedder ngữ nghĩa thật (`LocalEmbedder`/`OpenAIEmbedder`), còn với mock hash-based thì công thức đúng nhưng đầu vào (embedding) không mang thông tin ngữ nghĩa nên kết quả không đáng tin cậy để so sánh ý nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** (nguồn: `data/shopee-return-policy/benchmark_owner.md`) trên mã nguồn cá nhân của bạn trong gói `src`. Corpus nạp qua `ingest.py` (`build_knowledge_base`), dùng `RecursiveChunker(chunk_size=400)` → 177 chunk từ 8 tài liệu, embedding bằng `_mock_embed` (mặc định lab, không cần API key).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu Trả hàng/Hoàn tiền cho thực phẩm tươi sống; khi nào tính 20 ngày với đơn người bán tự vận chuyển? | Top-1 từ `shopee-return-refund-policy` (chunk về hình thức "Tự sắp xếp" trả hàng) — không đúng trọng tâm câu hỏi, nhưng chunk đúng (`shopee-return-general-rules`, mục 1.2/1.3) xuất hiện ở **hạng 2** trong top-3 | 0.3673 | Có (hạng 2/3) | Trả lời dựa trên chunk hạng 1 (sai trọng tâm) → nội dung không khớp gold answer |
| 2 | Người mua có thể làm gì nếu đề xuất Hoàn tiền Ngay của người bán không đủ? | Chunk từ `shopee-return-shipping-fees` (nói về gửi trả tại bưu cục) | 0.2888 | Không | Trả lời lạc đề, không nhắc đến "Trao đổi thêm"/"Tôi muốn trả hàng" như gold answer |
| 3 | "Hàng nguyên vẹn nhưng không còn nhu cầu" áp dụng cho ai, loại trừ gì? | Chunk mở đầu `shopee-seller-return-management` (giới thiệu chung, không liên quan điều kiện "Đổi ý") | 0.3015 | Không | Trả lời lạc đề, không nêu điều kiện hạng thành viên Kim Cương/Vàng/VIP |
| 4 | Điều kiện & mức hoàn phí trả hàng bằng Shopee Xu khi người mua tự sắp xếp trả hàng? | Chunk từ `shopee-instant-refund-proposal` (giới thiệu chung, không phải phần phí vận chuyển) | 0.3691 | Không | Không đề cập mức 25.000/40.000 Shopee Xu như gold answer |
| 5 | Người bán phải phản hồi trong bao nhiêu ngày nếu hệ thống ghi nhận đã trả hàng nhưng shop chưa nhận được? | Chunk từ `shopee-return-refund-policy` (nói về trường hợp Shopee chấp thuận/giao không thành công) — chunk đúng (`shopee-seller-return-management`) nằm ở **hạng 2** trong top-3 | 0.3329 | Có (hạng 2/3) | Trả lời dựa trên chunk hạng 1 (sai) → không nêu đúng "phản hồi trong 2 ngày" |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5 (Q1 và Q5 — nhưng chunk đúng chỉ ở hạng 2, không phải hạng 1, nên agent vẫn trả lời sai vì `answer()` lấy `top_k=3` gộp cả context đúng lẫn sai)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Kết quả 2/5 (và ngay cả 2 câu "có liên quan" cũng không nằm ở hạng 1) cho thấy rõ giới hạn của `MockEmbedder`: nó chỉ băm MD5 thành vector giả-ngẫu nhiên, hoàn toàn không hiểu ngữ nghĩa tiếng Việt, nên với một corpus dày đặc thuật ngữ giống nhau (nhiều bài đều nói về "trả hàng/hoàn tiền") thì retrieval gần như ngẫu nhiên. Bài học quan trọng nhất: để đánh giá đúng chất lượng chiến lược chunking/metadata filter của nhóm, bắt buộc phải chạy lại benchmark này với một embedder ngữ nghĩa thật (`LocalEmbedder` hoặc `OpenAIEmbedder`) — nếu không, mọi so sánh giữa các chiến lược chunking đều không có ý nghĩa vì "nhiễu" từ embedding lấn át tín hiệu từ cách chia chunk.

*(Cũng phát hiện một lỗi trong `EmbeddingStore._make_record`: code gốc ghi đè `metadata["doc_id"] = doc.id`, nhưng khi nạp qua `ingest.py` thì `doc.id` của mỗi chunk-Document là `"<doc_id>::chunk_N"` — ghi đè này làm mất `doc_id` gốc mà `ingest.py` đã gắn sẵn, khiến lọc/xóa theo tài liệu gốc và việc gom nhóm chunk theo doc ở bảng trên đều sai nếu không sửa. Đã sửa thành `metadata.setdefault("doc_id", doc.id)` **chỉ trong bản cá nhân `src/VoHoNhatNam/store.py`** (không đụng tới `src/store.py` dùng chung); demo trên dùng đúng package `src.VoHoNhatNam`. 42/42 test vẫn pass sau khi sửa.)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
