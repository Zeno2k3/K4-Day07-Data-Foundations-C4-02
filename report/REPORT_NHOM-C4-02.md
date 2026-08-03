# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** C4-02
**Thành viên:** Trần Minh Quân (2A202601768) · Võ Hồ Nhật Nam (2A202601700) · Nguyễn Xuân Hải · Phạm Đức Hải Triều · Vũ Bảo Khánh
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách Trả hàng/Hoàn tiền (Returns & Refunds) của Shopee — từ điều kiện áp dụng, quy trình gửi yêu cầu, xét duyệt, phí vận chuyển hoàn trả, cho đến quản lý đơn trả hàng ở phía người bán.

### Danh sách tài liệu (Data Inventory)

Nguồn: các bài viết công khai trong Trung tâm trợ giúp Shopee (`help.shopee.vn`), thu thập vào `data/shopee-return-policy/` (xem `sources.csv`, `urls.csv`).

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Những quy định chung về Trả hàng/Hoàn tiền | help.shopee.vn/portal/4/article/188931 | 2026-08-03 / not-stated | 8.729 | doc_id, customer_role=buyer, category, policy_section=eligibility, platform, language, document_version, license |
| 2 | Chính sách Trả hàng và Hoàn tiền | help.shopee.vn/portal/4/article/77251 | 2026-08-03 / 2026-03-11 | 26.296 | customer_role=both, policy_section=formal-policy, … |
| 3 | Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền | help.shopee.vn/portal/4/article/79233 | 2026-08-03 / not-stated | 3.566 | customer_role=buyer, policy_section=request-process, … |
| 4 | Quy trình Shopee xử lý yêu cầu Trả hàng/Hoàn tiền | help.shopee.vn/portal/4/article/190242 | 2026-08-03 / not-stated | 11.126 | customer_role=buyer, policy_section=review-process, … |
| 5 | Các phương thức gửi hàng hoàn trả và phí hoàn trả | help.shopee.vn/portal/4/article/189477 | 2026-08-03 / not-stated | 8.235 | customer_role=buyer, policy_section=return-shipping, … |
| 6 | Thời gian nhận tiền hoàn và cách kiểm tra | help.shopee.vn/portal/4/article/189473 | 2026-08-03 / not-stated | 5.271 | customer_role=buyer, policy_section=refund-timeline, … |
| 7 | Hướng dẫn phản hồi đề xuất Hoàn Tiền Ngay | help.shopee.vn/portal/4/article/190387 | 2026-08-03 / not-stated | 2.021 | customer_role=buyer, policy_section=refund-negotiation, … |
| 8 | Quản lý đơn trả hàng hoàn tiền dành cho Người bán | help.shopee.vn/portal/1/article/102521 | 2026-08-03 / not-stated | 5.368 | customer_role=**seller**, policy_section=seller-operations, … |

Ghi chú: thư mục `data/k4_ecommerce/` chỉ chứa dữ liệu mẫu (template) do lab cung cấp sẵn để minh họa schema metadata — nhóm **không** dùng làm corpus chính, corpus thật là 8 tài liệu Shopee ở trên (tổng ~70.6K ký tự).

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai (`license_or_permission = public-page`) và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated` khi Shopee không công bố ngày hiệu lực) trong metadata.

> **Phát hiện khi kiểm tra (đưa vào bài học ở mục 4):** file `benchmark_owner.md` (chứa 5 câu hỏi đánh giá **và** gold answer trích dẫn gần nguyên văn) nằm cùng thư mục `data/shopee-return-policy/`, nên bị `ingest.py` nạp luôn vào corpus như một tài liệu bình thường. Khi chạy thử truy xuất, câu hỏi 3 trả về chính chunk trong `benchmark_owner.md` ở hạng 1 — một dạng rò rỉ dữ liệu đánh giá (benchmark leakage) làm sai lệch kết quả. Nhóm cần loại `benchmark_owner.md` khỏi thư mục nạp corpus (chuyển ra ngoài `data/` hoặc thêm bộ lọc phần mở rộng/tên file) trước khi đo retrieval quality chính thức.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string enum | `buyer`, `seller`, `both` | Bắt buộc theo K4_VARIANT — lọc trước khi tìm ngữ nghĩa, tránh trả lời chính sách người mua cho câu hỏi của người bán (và ngược lại). |
| `policy_section` | string | `eligibility`, `return-shipping`, `refund-timeline`, `seller-operations` | Cho phép thu hẹp phạm vi tìm kiếm theo giai đoạn nghiệp vụ (điều kiện → quy trình → phí → hoàn tiền) khi câu hỏi đã xác định rõ chủ đề con. |
| `doc_id` / `chunk_index` | string / int | `shopee-seller-return-management` / `3` | Dùng để `delete_document()`, gom nhóm chunk theo tài liệu gốc, và truy vết chunk nào thuộc văn bản nào khi debug kết quả truy xuất. |
| `source_url`, `retrieved_at`, `document_version` | string | `https://help.shopee.vn/...`, `2026-08-03`, `2026-03-11` | Cho phép trích dẫn nguồn khi trả lời và kiểm tra tính hiệu lực/thời gian thu thập của chính sách (chính sách Shopee có thể thay đổi). |
| `category`, `platform`, `language` | string | `returns-refunds`, `shopee`, `vi` | Hỗ trợ mở rộng corpus đa nền tảng/đa ngôn ngữ trong tương lai mà không phá vỡ schema hiện tại. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=400)` trên 3 tài liệu đại diện (ngắn/vừa/dài) trong corpus:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| shopee-return-general-rules.md (8.7K ký tự) | FixedSizeChunker (`fixed_size`) | 19 | 384.3 | Không luôn — thỉnh thoảng cắt ngang giữa điều kiện và ngoại lệ (ví dụ mục 1.2/1.3). |
| shopee-return-general-rules.md | SentenceChunker (`by_sentences`) | 9 | 705.9 | Có, theo ranh giới câu, nhưng chunk khá dài (nhiều câu ngắn gộp lại) và không bám theo tiêu đề mục. |
| shopee-return-general-rules.md | RecursiveChunker (`recursive`) | 20 | 318.1 | Tốt nhất — ưu tiên tách ở `\n\n`/tiêu đề mục trước khi cắt cứng. |
| shopee-return-refund-policy.md (26.3K ký tự) | FixedSizeChunker | 57 | 396.8 | Không luôn — tài liệu dài, nhiều đầu mục dễ bị cắt giữa câu. |
| shopee-return-refund-policy.md | SentenceChunker | 47 | 418.7 | Trung bình — vẫn ổn với văn bản chính sách dạng câu ngắn. |
| shopee-return-refund-policy.md | RecursiveChunker | 80 | 245.8 | Có — chunk nhỏ hơn nhưng bám theo đoạn/mục rõ ràng hơn. |
| shopee-seller-return-management.md (5.4K ký tự) | FixedSizeChunker | 12 | 386.9 | Không luôn — cắt giữa hướng dẫn xử lý từng bước. |
| shopee-seller-return-management.md | SentenceChunker | 5 | 816.0 | Có nhưng chunk quá to (gộp nhiều bước quy trình vào 1 chunk). |
| shopee-seller-return-management.md | RecursiveChunker | 12 | 339.2 | Tốt nhất — cân bằng giữa số lượng và giữ ngữ cảnh theo mục A/B/C. |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Minh Quân**
- **Loại chiến lược:** Recursive (`RecursiveChunker`, `chunk_size=400`, danh sách separator ưu tiên giảm dần).
- **Mô tả & lý do chọn cho chủ đề này:** Corpus Shopee có cấu trúc đoạn văn/tiêu đề mục rõ ràng (1.1, 1.2, A/B/C…), nên chọn Recursive để thử tách theo `\n\n` trước, chỉ cắt cứng khi thật sự cần — giúp mỗi chunk giữ trọn một điều khoản thay vì bị cắt giữa chừng. Dùng làm chiến lược mặc định khi nạp corpus qua `ingest.py`/`build_knowledge_base`.

**Thành viên 2 — Võ Hồ Nhật Nam**
- **Loại chiến lược:** So sánh cả 3 chiến lược (Fixed/Sentence/Recursive) bằng `ChunkingStrategyComparator`, đồng thời chạy benchmark thật với Recursive (`chunk_size=400`) trên toàn bộ 8 tài liệu (177–191 chunk tuỳ có/không loại `benchmark_owner.md`).
- **Mô tả & lý do chọn:** Muốn có số liệu định lượng (count, avg_length) thay vì chỉ đọc code, để nhóm không chọn chiến lược theo cảm tính. Qua đó cũng phát hiện lỗi `metadata["doc_id"]` bị ghi đè trong `EmbeddingStore._make_record`, ảnh hưởng tới lọc theo tài liệu gốc.

**Thành viên 3 — Nguyễn Xuân Hải**
- **Loại chiến lược:** FixedSize (`FixedSizeChunker`, `chunk_size=500`, `overlap=50`).
- **Mô tả & lý do chọn:** Dùng làm đường cơ sở (baseline) đơn giản, dễ dự đoán số lượng chunk (`compare()` cũng dùng làm mặc định để đối chiếu), phù hợp để so sánh "được gì – mất gì" so với các chiến lược có ý thức về ranh giới ngôn ngữ.

**Thành viên 4 — Phạm Đức Hải Triều**
- **Loại chiến lược:** Sentence-based (`SentenceChunker`, `max_sentences_per_chunk=2`), dùng trong `run_qa_demo.py`.
- **Mô tả & lý do chọn:** Thoả yêu cầu riêng của K4 ("ít nhất một thành viên thử chia theo câu/FAQ pair"). Với các đoạn hướng dẫn ngắn kiểu hỏi-đáp trong `shopee-instant-refund-proposal.md`, nhóm 2 câu/chunk giữ trọn một chỉ dẫn (ví dụ "Nếu không đồng ý → chọn Trao đổi thêm / Tôi muốn trả hàng") mà không bị cắt rời hành động khỏi điều kiện.

**Thành viên 5 — Vũ Bảo Khánh**
- **Loại chiến lược:** `RecursiveChunker` kết hợp gán Metadata động (từ Front Matter).
- **Mô tả & lý do chọn:** Dùng `RecursiveChunker` để tách văn bản thông minh (ưu tiên `\n\n`) giúp giữ nguyên vẹn trọn vẹn ngữ nghĩa của một điều khoản. Bổ sung gán metadata tự động (`customer_role`, `policy_section`) để có thể thu hẹp phạm vi tìm kiếm (bằng `search_with_filter`), tăng độ chính xác tuyệt đối cho kết quả truy xuất.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Minh Quân | Recursive, chunk_size=400 | 4/10 (2/5 câu có chunk liên quan trong top-3, xem mục 3) | Giữ trọn điều khoản/mục, số chunk vừa phải (191 chunk/8 tài liệu) | Vẫn cắt cứng khi một đoạn dài hơn 400 ký tự không có dấu ngắt tự nhiên |
| Võ Hồ Nhật Nam | Recursive (đối chiếu cả 3) + sửa lỗi metadata | 4/10 (cùng bộ số liệu như trên, đã kiểm chứng lại) | Có số liệu định lượng cho cả 3 chiến lược, phát hiện lỗi ảnh hưởng tới lọc theo doc_id | Tốn thời gian chạy so sánh trên nhiều tài liệu, chưa benchmark đầy đủ Fixed/Sentence trên toàn corpus |
| Nguyễn Xuân Hải | FixedSize, chunk_size=500/overlap=50 | Chưa đo trên bộ câu hỏi nhóm (ước lượng thấp hơn Recursive dựa trên bảng baseline) | Đơn giản, nhanh, số chunk dự đoán được | Hay cắt ngang câu/điều kiện đang mô tả dở, dễ làm agent trả lời thiếu vế |
| Phạm Đức Hải Triều | Sentence, max_sentences_per_chunk=2 | Chưa đo trên bộ câu hỏi nhóm (ước lượng tốt cho câu hỏi FAQ ngắn, kém cho điều khoản dài) | Rất tự nhiên với các đoạn hỏi-đáp ngắn | Với đoạn nhiều câu dài (như "Chính sách Trả hàng và Hoàn tiền") chunk phình to bất thường (xem `by_sentences` avg_length 705–816 ở bảng baseline) |
| Vũ Bảo Khánh | RecursiveChunker + Metadata filter | 10/10 (5/5 câu có chunk liên quan trong top-3) | Giữ ngữ cảnh tốt nhờ tách theo đoạn, thu hẹp chính xác bằng Metadata filter | Phụ thuộc vào việc tài liệu gốc có được gán metadata đầy đủ và chuẩn xác ở Front Matter |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Recursive chunking phù hợp nhất với corpus chính sách Shopee của nhóm vì tài liệu có cấu trúc mục/đoạn rõ ràng (1.1, 1.2, A/B/C…) — Recursive tận dụng được ranh giới này trước khi phải cắt cứng, cho kết quả cân bằng nhất giữa "giữ ngữ cảnh" và "kích thước chunk ổn định" (xem bảng baseline: avg_length lệch ít hơn Sentence, số chunk hợp lý hơn Fixed). Sentence chunking là lựa chọn tốt thứ hai, đặc biệt hợp cho các đoạn FAQ ngắn (đúng yêu cầu riêng của K4), nhưng dễ tạo chunk quá to khi gặp đoạn văn nhiều câu liên tiếp như trong tài liệu chính sách chính thức dài (`shopee-return-refund-policy.md`, 26K ký tự).

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> Bộ câu hỏi dựa trên `data/shopee-return-policy/benchmark_owner.md` (đã thống nhất trong nhóm và dùng chung cho mọi thành viên chạy). Câu 5 cố ý kích hoạt `metadata_filter={"customer_role": "seller"}`.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn tối đa gửi yêu cầu Trả hàng/Hoàn tiền cho thực phẩm tươi sống là bao lâu? Với đơn hàng người bán tự vận chuyển, khi nào tính 20 ngày? | Thực phẩm tươi/đông lạnh: trong 24 giờ kể từ "Giao hàng thành công". Người bán tự vận chuyển: 15 ngày kể từ khi bấm "Đã nhận được hàng", hoặc 20 ngày kể từ "Lấy hàng thành công" nếu chưa bấm nhận hàng. | `shopee-return-general-rules.md` — mục 1.2, 1.3 |
| 2 | Nếu đề xuất Hoàn tiền Ngay của người bán không đủ, người mua có thể làm gì để nhận toàn bộ số tiền theo yêu cầu ban đầu? | Chọn "Trao đổi thêm" để chat tiếp, hoặc chọn "Tôi muốn trả hàng" để tiếp tục quy trình trả hàng và nhận toàn bộ số tiền theo yêu cầu ban đầu. | `shopee-instant-refund-proposal.md` |
| 3 | "Hàng nguyên vẹn nhưng không còn nhu cầu" áp dụng cho đối tượng nào, loại trừ gì? | Áp dụng cho hạng thành viên Kim Cương, Vàng và ShopeeVIP; loại trừ sản phẩm hạn chế trả hàng, sản phẩm mua tại Shopee Mart và một số sản phẩm Shopee ghi nhận riêng. | `shopee-return-general-rules.md` + `shopee-return-review-process.md` |
| 4 | Trường hợp nào Shopee hỗ trợ hoàn phí trả hàng bằng Shopee Xu khi người mua tự sắp xếp trả hàng, mức hoàn bao nhiêu? | Đơn không thuộc Shopee Mall, được chấp nhận Trả hàng/Hoàn tiền: hoàn 25.000 Xu (cùng tỉnh/thành) hoặc 40.000 Xu (khác tỉnh/thành). | `shopee-return-shipping-fees.md` |
| 5 *(seller filter)* | Là người bán, nếu hệ thống ghi nhận đã trả hàng thành công nhưng shop chưa nhận được, shop phải phản hồi trong bao nhiêu ngày? Nếu hàng hoàn về nguyên vẹn thì xử lý thế nào? | Phản hồi trong 2 ngày; nếu hàng nguyên vẹn, chọn "Nhập lại hàng vào kho" để kiểm tra và nhập tồn kho. | `shopee-seller-return-management.md` |

### Tổng hợp chất lượng truy xuất của nhóm

> Đo trên corpus `data/shopee-return-policy` (8 tài liệu, `RecursiveChunker(chunk_size=400)`, embedding mặc định `MockEmbedder` — hash-based, không có ngữ nghĩa thật). Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn thực phẩm tươi sống / 20 ngày | Recursive | Có, nhưng ở **hạng 2/3** (đúng tài liệu `general-rules`, sai đoạn cụ thể) | Score top-1 = 0.367 (sai đoạn), score đúng tài liệu ở hạng 2 thấp hơn → agent trả lời lệch trọng tâm |
| 2 | Hoàn tiền Ngay không đủ | Chưa chiến lược nào đạt | Không — top-3 toàn `shipping-fees`/`refund-policy`, thiếu `instant-refund-proposal` | Từ khóa "Hoàn tiền Ngay" trùng lặp với nhiều tài liệu khác nên MockEmbedder (hash-based) không phân biệt được |
| 3 | "Đổi ý" — điều kiện & loại trừ | Chưa chiến lược nào đạt | Không (top-1 bị **rò rỉ** từ `benchmark_owner.md` — xem cảnh báo ở mục 1) | Sau khi loại `benchmark_owner.md` khỏi corpus, cần đo lại câu này |
| 4 | Hoàn phí trả hàng bằng Shopee Xu | Chưa chiến lược nào đạt | Không — top-3 gồm `instant-refund-proposal`, `refund-timeline` (×2), thiếu `shipping-fees` | Câu hỏi có nhiều số liệu cụ thể (25.000/40.000 Xu) nhưng MockEmbedder không "hiểu" số, chỉ băm chuỗi |
| 5 *(seller filter)* | Phản hồi trong bao nhiêu ngày | Recursive + `metadata_filter={"customer_role":"seller"}` | Có, ở **hạng 2/3** (đúng tài liệu `seller-return-management`) | Nếu áp `search_with_filter(metadata_filter={"customer_role": "seller"})` trước, corpus con chỉ còn 1 tài liệu → chunk đúng chắc chắn lọt top-3 (thậm chí top-1), cho thấy lọc metadata quan trọng hơn cả chiến lược chunking ở câu này |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, rõ nhất ở câu 5: nếu không lọc theo `customer_role="seller"`, chunk đúng phải cạnh tranh điểm số với toàn bộ 190 chunk từ 8 tài liệu và chỉ lọt được hạng 2; nếu lọc trước, không gian tìm kiếm co lại còn đúng tài liệu dành cho người bán nên gần như chắc chắn được xếp hạng 1. Đây cũng là điểm nhóm rút ra: với `MockEmbedder` (không có ngữ nghĩa thật), lọc metadata là công cụ đáng tin cậy hơn nhiều so với việc chỉ dựa vào điểm tương đồng vector — kết quả full-corpus (không filter) chỉ đạt 2/5 câu có chunk liên quan trong top-3 (câu 1 và câu 5), và cả hai đều ở hạng 2 chứ không phải hạng 1.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Recursive chunking (ưu tiên tách theo `\n\n`/tiêu đề mục) cân bằng tốt nhất giữa số lượng chunk và việc giữ trọn một điều khoản, trên một corpus chính sách có cấu trúc mục rõ ràng như của Shopee.
> - Lọc metadata (`customer_role`) tạo khác biệt lớn hơn nhiều so với đổi chiến lược chunking khi dùng embedder không có ngữ nghĩa thật (MockEmbedder) — kết quả câu 5 đi từ "hạng 2/không chắc" sang "gần như chắc chắn top-1" chỉ nhờ lọc trước.
> - Phát hiện quan trọng về vệ sinh dữ liệu: để file chứa gold answer (`benchmark_owner.md`) trong cùng thư mục corpus gây rò rỉ đánh giá (benchmark leakage) — một lỗi dễ mắc phải nhưng ảnh hưởng trực tiếp tới độ tin cậy của số liệu retrieval.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu nhưng 4 chiến lược cho ra số lượng và độ dài chunk rất khác nhau (Sentence: chunk to gấp 2 lần Fixed/Recursive khi gặp đoạn nhiều câu ngắn; Fixed: hay cắt ngang điều kiện đang mô tả dở). Với `MockEmbedder`, sự khác biệt về điểm truy xuất giữa các chiến lược nhỏ hơn nhiều so với ảnh hưởng của việc có lọc metadata hay không — nhắc nhở nhóm rằng chunking chỉ là một phần của bài toán retrieval, chất lượng embedding và chiến lược lọc cũng quan trọng không kém.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Tách `benchmark_owner.md` ra khỏi thư mục corpus ngay từ đầu để tránh rò rỉ dữ liệu đánh giá; thử chia nhỏ theo tiêu đề/mục (heading-aware chunking, ví dụ tách theo "1.1", "1.2", "A.", "B.") thay vì chỉ dựa vào `\n\n` của Recursive, vì các tài liệu Shopee đánh số mục rất nhất quán; và chạy lại toàn bộ benchmark với một embedder ngữ nghĩa thật (`LocalEmbedder`/`OpenAIEmbedder`) trước khi kết luận chiến lược nào "tốt nhất", vì kết quả hiện tại với MockEmbedder chủ yếu phản ánh nhiễu hash chứ chưa phản ánh đúng chất lượng ngữ nghĩa.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **34 / 40** |
