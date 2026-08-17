# Task 1 — Prompt Engineering Challenge (Negative Constraints)

**Goal:** Write and test a minimum of 3 different System Prompts using *negative constraints*, and document how the LLM's output changed with each iteration.

**Setup:** Telecom RAG system — FAISS retriever (`k=20`) over the internal knowledge base, LLM = `gemini-2.5-flash` (`temperature=0`), multilingual embeddings (`paraphrase-multilingual-MiniLM-L12-v2`). All three prompts were tested on the **same two tickets** so the comparison is apples-to-apples.

## Fixed Test Tickets

- **Ticket A — Billing:** «أنا دافع الفاتورة من يومين أونلاين والفلوس اتخصمت من الفيزا، لكن النت لسه مرجعش لحد دلوقتي ومكتوبلي إن الخدمة موقوفة!»
- **Ticket B — Error E-204:** «النت شغال بس بطيء جداً وبيظهرلي رسالة على الشاشة فيها كود الخطأ E-204. أعمل إيه؟»

Ground truth in the KB: E-204 = *"Line Noise Too High" → instruct customer to change DNS to `8.8.8.8`*. Billing issues → route to Billing (internal extension **111**, which must **not** be exposed to the customer). The KB contains **no** step-by-step OS instructions for changing DNS.

---

## Iteration 1 — `prompt_v1` (a single negative constraint)

**Constraint:** only *"do not mention any real telecom company name."*

```
أنت موظف خدمة عملاء في مزود خدمة إنترنت. رد على شكوى العملاء.
قيد سلبي وحيد: لا تذكر أي اسم شركة اتصالات حقيقية.

السياق الداخلي:
{context}

شكوى العميل:
{question}

الرد:
```

**Observations:**

*Ticket A – Billing*
- Tone drifted to **formal MSA** ("أتفهم تماماً مدى إحباطك… بطاقتك الائتمانية").
- **Leaked the internal extension "111"** ("تحويل… على الرقم 111").
- **Invented an unstated cause** ("يبدو أن هناك تأخيراً في تحديث حالة الدفع على نظامنا").
- ✅ No competitor named; correct routing to Billing.

*Ticket B – Error E-204*
- **Hallucinated a full Windows + macOS click-by-click DNS guide** that does **not exist in the KB** (the KB only says "change DNS to 8.8.8.8").
- Tone drifted to **formal MSA**; very verbose (~25+ lines).
- ✅ Correct core fact (E-204 → DNS 8.8.8.8); no competitor named.

**Takeaway:** A single negative constraint blocks exactly one failure mode. The model reverted to its default behavior — formal, verbose, **ungrounded (invented steps)**, and **leaking internal data**.

---

## Iteration 2 — `prompt_v2` (+ grounding / anti-hallucination)

**Added constraints:** don't use any info outside the context; don't invent steps/codes/compensation/prices; if the answer isn't in the context, don't guess — apologize and offer to escalate.

```
أنت موظف خدمة عملاء في مزود خدمة إنترنت. التزم بالتأكيد بالقيود السلبية التالية:

لا تذكر أي اسم شركة اتصالات حقيقية.

لا تستخدم أي معلومة غير موجودة في (السياق الداخلي).

لا تخترع خطوات حل أو أشكال أخطاء أو مبالغ تعويض أو أسعار من عندك.

إذا لم تكن الإجابة موجودة في السياق، لا تخمن؛ اعتذر بأدب واعرض تحويل العميل للقسم المختص.

السياق الداخلي:
{context}

شكوى العميل:
{question}

الرد:
```

**Observations:**

*Ticket A – Billing*
- ✅ **Fixed hallucination:** dropped the invented "payment-delay" cause.
- ❌ **Still leaks "111"** — because 111 *is* in the context (Escalation Matrix), a grounding rule *permits* it. Needs an explicit **confidentiality** rule.
- ❌ **Still formal MSA.**

*Ticket B – Error E-204*
- ✅ **Big win:** the invented Windows/macOS guide is **gone** — now just "change DNS to 8.8.8.8" + offers help.
- ✅ Concise and grounded.
- ❌ Still formal MSA.

**Takeaway:** Grounding constraints **killed the ungrounded invented steps** and reduced speculation. But grounding alone does **not** stop internal-data leakage, and does not fix tone.

---

## Iteration 3 — `prompt_v3` (+ confidentiality + tone/format)

**Added constraints:** don't reveal internal details (error codes, team/tier names, VLAN IDs, existence of an internal manual) — convert them to simple customer instructions; reply in Egyptian colloquial only (no English, no MSA); don't promise timelines/compensation not stated in context; don't ask for sensitive data.

```
أنت موظف خدمة عملاء في مزود خدمة إنترنت. التزم بكل القيود السلبية التالية بدقة تامة:
- لا تذكر أي اسم شركة اتصالات حقيقية.
- لا تستخدم أي معلومة خارج (السياق الداخلي)، ولا تخترع خطوات أو أسعار أو تعويضات.
- إذا لم تكن الإجابة في السياق، لا تخمن؛ اعتذر واعرض التحويل للقسم المختص.
- لا تكشف أي تفاصيل داخلية (أكواد الأخطاء، أسماء الفرق أو التيرات، أرقام الـ VLAN، أو وجود دليل داخلي). حوّل الخطوات لتعليمات بسيطة للعميل بس.
- لا ترد بالإنجليزية ولا بالفصحى؛ استخدم العامية المصرية فقط.
- لا تعد بأي مواعيد أو تعويضات غير منصوص عليها صراحة في السياق.
- لا تطلب من العميل أي بيانات حساسة (رقم كارت أو باسورود).

السياق الداخلي:
{context}

شكوى العميل:
{question}

الرد:
```

**Observations:**

*Ticket A – Billing*
- ✅ **"111" leak CLOSED** — now says only "القسم المختص بالفواتير" (the accounts/billing department), with no internal extension.
- ✅ **Egyptian colloquial** ("أهلاً بحضرتك يا فندم… عشان").
- ✅ No invented cause.

*Ticket B – Error E-204*
- ✅ **Egyptian colloquial**, grounded on DNS `8.8.8.8`.
- ✅ Steps reduced to **simple, generic customer instructions** — not V1's fabricated OS menus.
- ⚠️ Minor: gives a light generic "open network settings → change DNS → save" (slightly beyond the literal KB, but intentionally allowed by the "simplify steps" rule). Echoing "E-204" is fine — the customer reported it.

**Takeaway:** Adding a confidentiality constraint finally closed the internal-data leak, and the Egyptian-only rule fixed the tone — while keeping V2's grounding gains.

---

## Final Iteration Summary

| Failure mode | V1 (1 constraint) | V2 (+grounding) | V3 (+confidentiality+tone) |
|---|---|---|---|
| Invented OS/DNS steps (hallucination) | ❌ Yes | ✅ Fixed | ✅ Fixed |
| Fabricated billing cause | ❌ Yes | ✅ Fixed | ✅ Fixed |
| Leaked internal extension "111" | ❌ Yes | ❌ Still leaks | ✅ **Fixed** |
| Formal MSA instead of Egyptian | ❌ Yes | ❌ Still MSA | ✅ **Fixed** |
| Named a real competitor | ✅ Never | ✅ Never | ✅ Never |

## Conclusion

Each added negative constraint removed a **distinct, non-overlapping** failure mode:

- **Grounding constraints (V2)** stop **hallucination** (invented DNS steps, fabricated causes).
- A grounding rule alone does **not** stop **internal-data leakage** — the extension "111" *is* in the context, so it's technically "allowed." Suppressing it required an explicit **confidentiality constraint (V3)**.
- The **Egyptian-only constraint (V3)** was needed to fix tone drift to formal Arabic.

**Key insight:** Negative constraints are **additive** — one failure mode needs one dedicated constraint. Layering them (grounding → confidentiality → tone) turned a loose, leaky, hallucinating assistant into a grounded, on-brand, confidential one, without ever having to add positive "do this" instructions.
