# Task 2 — Chunking Strategy Challenge (Semantic Chunking)

**Goal:** Research and implement at least one *alternative* chunking strategy, then **prove** it retrieves a chunk that the original method missed.

**Original method:** `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)` — splits text at fixed character lengths.

**New method:** `SemanticChunker` (`langchain_experimental`) — embeds every sentence and starts a new chunk only when the **meaning** between consecutive sentences shifts past a threshold (`breakpoint_threshold_type="percentile"`). It keeps a coherent topic together instead of cutting at an arbitrary 500-character boundary.

**Environment:** local embeddings `paraphrase-multilingual-MiniLM-L12-v2` + FAISS. No LLM/API key needed — this is a pure retrieval experiment. (Notebook: `notebooks/02_task2_semantic_chunking.ipynb`.)

---

## Chunk counts

| Strategy | # chunks | Notes |
|---|---|---|
| Original — Recursive 500/100 | **481** | fixed-size slices |
| New — Semantic (percentile) | **82** | meaning-based, variable size |

---

## The Needle

**Query:** *"What are the conditions for dispatching a field technician, and when is data compensation authorized?"*

The correct answer requires **two** facts that both live in the Section 1 SLA policy:
- **dispatch trigger** → line noise margin **below 6dB** (or DSL off/blinking 3 days)
- **compensation** → **5GB mobile data, ONLY if the outage exceeds 72 hours**

### Why the original method *cannot* answer it (deterministic)

The SLA policy is a single coherent block **longer than 500 characters**, so the recursive splitter is forced to cut it in two. Checking every one of the 481 original chunks:

```
chunks containing BOTH "6dB" and "72 hours": []   ← none
chunk 1: dispatch rule (6dB)   ... but NO compensation
chunk 2: compensation (72 hours) ... but NO dispatch rule
```

No single original chunk contains the whole policy — so retrieval can *never* return the complete answer in one chunk, regardless of `k`.

---

## The Proof (retrieval, top-3)

```
ORIGINAL (recursive 500/100): full-answer chunk in top-3? → MISSED ❌
  [1] 6dB=True  72h=False      (dispatch rule only)
  [2] 6dB=False 72h=True       (compensation only)
  [3] 6dB=False 72h=False

NEW (semantic):               full-answer chunk in top-3? → HIT at rank 1 ✅
  [1] 6dB=True  72h=True       ← one 1007-char chunk = the WHOLE SLA policy
```

**The original's top-3 splits the answer across two chunks; the semantic index returns the complete policy as a single rank-1 chunk.** That is the chunk the original method missed.

---

## Broader scan (honesty check)

| Query | Original rank | Semantic rank | Result |
|---|---|---|---|
| dispatch conditions + compensation | ❌ MISS | **1** | ✅ **semantic wins** |
| outage escalation timing + team | 2 | 2 | tie |
| fiber optic cuts escalation + SLA | 1 | 1 | tie |
| resolution protocol for error **E-317** | ❌ MISS | ❌ MISS | both miss |

**Reading the scan:**
- Semantic **wins** when the answer is a **multi-fact coherent policy** that the fixed-size splitter fragments.
- It **ties** on single-fact lookups (both find them).
- It **does not help** for pinpointing one specific **error code** — the 300 error-code entries are near-identical, so semantic *globs many together* and the exact code is still crowded out. For that access pattern, **`MarkdownHeaderTextSplitter`** (one clean chunk per `#### Error Code E-xxx`) is the better alternative.

---

## Conclusion

Because semantic chunking splits on **meaning** rather than a fixed character count, it kept the entire SLA policy intact in a single chunk. A multi-fact query then retrieved the **complete** answer (dispatch rule + compensation rule together at rank 1) that the original 500-character splitter had **fragmented across two chunks and missed**. This satisfies the task: *the new strategy retrieved a chunk the original method missed.*

**Trade-off learned:** no single chunking strategy is universally best. Semantic chunking excels at keeping coherent policies whole (great for reasoning-style queries) but underperforms on dense, repetitive record lookups (error codes), where header-based splitting wins.

---

# End-to-End Business Impact — Real LLM Answers

To show the *practical* effect, both indexes were wired to the **exact original system prompt from `01_telecom_rag_demo`** and the same LLM (`gemini-2.5-flash`, `temperature=0`), retrieving the **single best chunk (`k=1`)** to isolate chunk quality. Only the chunking strategy differs between the two chains.

## Case A — Multi-fact SLA policy → **Semantic WINS**

**Customer inquiry:** «النت مقطوع عندي من 4 أيام ولمبة الـ DSL طافية خالص. هتبعتولي فني؟ وهل ليا أي تعويض؟»
*(Internet down 4 days, DSL light fully off — will you send a technician, and do I get compensation?)*

**Ground truth (Section 1 SLA):** DSL off 3+ days → dispatch technician (contact within 48h); outage > 72h → **5GB** mobile-data compensation.

| | Retrieved chunk | LLM answer |
|---|---|---|
| **Original — Recursive** | `dispatch_rule=True, compensation_rule=False` | Technician: ✅. Compensation: ❌ **"بيتم مراجعته بعد ما المشكلة تتحل"** — *"it's reviewed after the issue is resolved."* **This rule does not exist in the KB — the model invented it** to fill the gap in its fragmented chunk. |
| **New — Semantic** | `dispatch_rule=True, compensation_rule=True` | Technician: ✅ (+48h contact). Compensation: ✅ **"بما إن فترة انقطاع الخدمة تجاوزت الـ 72 ساعة، فحضرتك ليك تعويض 5 جيجا"** — *"since the outage exceeded 72h, you're entitled to 5GB."* Exact and grounded. |

**Full LLM output — Original (Recursive):**
```
أهلاً بحضرتك، أنا موظف خدمة عملاء من مزود خدمة الإنترنت بتاعك.

متأسف جداً على المشكلة اللي حضرتك بتواجهها وإن النت مقطوع عندك بقاله 4 أيام ولمبة الـ DSL طافية خالص.

بناءً على اللي حضرتك ذكرته، بما إن لمبة الـ DSL طافية بقالها 4 أيام متواصلة، ده بيستدعي إننا نبعت لحضرتك فني متخصص عشان يكشف على الخط ويحل المشكلة في أقرب وقت ممكن.

بالنسبة لسؤال حضرتك عن التعويض، ده بيتم مراجعته بعد ما المشكلة تتحل تماماً والخدمة ترجع تشتغل بشكل طبيعي.

ياريت بس نكون متواصلين مع حضرتك عشان ننسق ميعاد زيارة الفني.
```

**Full LLM output — New (Semantic):**
```
أهلاً بحضرتك، أنا موظف خدمة عملاء في مزود خدمة الإنترنت.

متفهم جداً إنقطاع الإنترنت عند حضرتك بقاله 4 أيام وإن لمبة الـ DSL طافية خالص، وده طبعاً شيء مزعج جداً.

بناءً على وصف حضرتك للمشكلة، وخصوصاً إن لمبة الـ DSL طافية بقالها أكتر من 3 أيام، إحنا بالفعل محتاجين نبعت لحضرتك فني متخصص عشان يفحص الخط ويحل المشكلة من جذورها. الفني هيتواصل مع حضرتك خلال 48 ساعة عمل بالكتير عشان ينسق ميعاد الزيارة.

وبخصوص سؤال حضرتك عن التعويض، بما إن فترة انقطاع الخدمة تجاوزت الـ 72 ساعة، فحضرتك ليك تعويض 5 جيجا بايت إنترنت موبايل.

إحنا بنعتذر جداً عن أي إزعاج حصل لحضرتك، وبنأكدلك إننا بنعمل بأقصى سرعة لحل المشكلة.
```

**Impact:** the recursive split forced the agent to give a **wrong/ungrounded** compensation answer (misinforms the customer, SLA-breach risk). Semantic kept the whole policy in one chunk → **correct 5GB / 72-hour** entitlement.

## Case B — Specific error code → **Semantic LOSES**

**Customer inquiry:** «بيظهرلي على الشاشة كود الخطأ E-205 وانا بحاول أستخدم النت، أعمل إيه؟»
*(My screen shows error code E-205 — what do I do?)*

**Ground truth:** E-205 = Line Noise Too High → **Escalate to Tier 2 Network Ops**.

| | Retrieved chunk | LLM answer |
|---|---|---|
| **Original — Recursive** | 468 chars, 4 codes, **contains E-205 ✅** | On point: identifies a **line-quality** problem needing the **specialized support team**, opens a maintenance ticket. Grounded in the retrieved E-205 entry. |
| **New — Semantic** | 2196 chars, **missing E-205 ❌** | Generic deflection: asks the customer to describe router-light colors and suggests a **router restart** — never addresses E-205, because the code was lost in semantic's globbing of the 300-code table. |

**Full LLM output — Original (Recursive):**
```
أهلاً بيك يا فندم، أنا موظف خدمة العملاء من مزود خدمة الإنترنت بتاعك.

متفهم جداً إنك بتواجه مشكلة مع كود الخطأ E-205. الكود ده يا فندم بيشير لمشكلة في جودة الخط، وده بيتطلب تدخل من فريق الدعم الفني المتخصص.

علشان كده، هنحتاج نبعت لحضرتك فني متخصص عشان يفحص الخط ويحل المشكلة من جذورها.

ممكن بعد إذنك تأكدلي رقم حسابك أو رقم التليفون الأرضي المسجل عندنا عشان نقدر نفتح طلب صيانة ونحدد ميعاد مناسب لزيارة الفني؟

متشكرين جداً لتعاونك، وإن شاء الله المشكلة تتحل في أقرب وقت.
```

**Full LLM output — New (Semantic):**
```
أهلاً بيك يا فندم، أنا موظف خدمة العملاء في مزود خدمة الإنترنت.

متفهم جداً إن حضرتك بتواجه مشكلة في استخدام الإنترنت وظهور كود E-205.

علشان نقدر نساعد حضرتك بشكل دقيق، ممكن بعد إذنك توصفلي حالة لمبات الراوتر عندك؟ يعني لمبة الـ DSL لونها إيه وحالتها إيه (ثابتة، بتنور وتطفي، مطفية)؟ ولمبة الإنترنت لونها إيه وحالتها إيه؟

في الغالب، أول خطوة بننصح بيها هي إننا نعمل إعادة تشغيل للراوتر. ممكن تجرب تفصل الراوتر من الكهرباء لمدة دقيقة أو دقيقتين وترجع توصله تاني وتشوف لو المشكلة اتحلت؟

منتظر رد حضرتك علشان نقدر نتابع مع بعض.
```

**Why:** semantic chunking merged the entire 300-code error table into a few giant chunks (**biggest = 36,091 chars / 300 codes**), so a pinpoint code lookup either drowns in the blob or misses. Recursive keeps ~4 codes per chunk, so E-205 stayed retrievable.

## Combined takeaway

> **Same prompt, same question, same LLM — the only variable is chunking.**
> - **Coherent policy (Case A):** semantic wins — keeps the whole rule together → complete, grounded answer.
> - **Dense repetitive records (Case B):** semantic loses — merges records into giant blobs → the specific record becomes unretrievable.
>
> The right chunking strategy depends on the **structure of the data**: semantic for flowing policy/prose, fixed-size (or header-based) for dense repetitive records. Better retrieval directly drives a factually-grounded answer — and lower AHT / SLA risk, the project's original business goal.
