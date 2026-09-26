# -*- coding: utf-8 -*-
"""交易哨兵 — 核心分析引擎（5-Agent + TF-IDF语义检索）。

技术说明：
- 检索层采用 TF-IDF 向量空间模型 + 余弦相似度
- 使用 jieba 进行中文分词
- 知识库向量预计算，分析时实时计算查询向量并匹配
- 相比纯关键词匹配，能识别部分同义词、近义表达和语序变化
"""
import json
import math
import os
import re
import time

import jieba
from openai import OpenAI

from prompts import (
    SYS_ARBITER,
    SYS_ORCHESTRATOR,
    SYS_RATIONALITY,
    SYS_RULE,
    SYS_SCRIPT,
)

# ---------- 客户端初始化 ----------

def _get_client() -> OpenAI:
    """懒加载 OpenAI 客户端（复用连接）。"""
    if not hasattr(_get_client, "_client"):
        _get_client._client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
    return _get_client._client


def call_agent(system: str, user: str, max_retry: int = 3) -> dict:
    """调用对话 Agent，返回解析后的 JSON。"""
    client = _get_client()
    last_error = None

    for attempt in range(max_retry):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            content = resp.choices[0].message.content or ""
            return json.loads(content)
        except Exception as e:
            last_error = e
            if attempt < max_retry - 1:
                time.sleep(1)

    raise RuntimeError(
        f"call_agent 重试 {max_retry} 次仍失败，最后一次错误: {last_error!r}"
    ) from last_error


# ====================================================================
# 语义检索模块：TF-IDF 向量空间模型 + 余弦相似度
# ====================================================================
#
# 原理大白话：
#   1. 把每段文字切成一个个词（分词）
#   2. 统计每个词出现的频率（TF）
#   3. 给"稀有词"更高的权重（IDF）——越少见的词越有区分度
#   4. 把文字变成一串数字（向量），每个数字对应一个词的权重
#   5. 比较两段文字的向量夹角（余弦相似度），夹角越小越相似
#
# 为什么比关键词匹配好？
#   - 关键词匹配：必须字完全一样才算命中
#   - TF-IDF：一段话里有多个相关词，即使不完全一样，相似度也会高
#   - 比如"保障金"和"保证金押金"，分词后有重叠的语义，相似度会更高
# ====================================================================

# 停用词：这些词太常见，对区分语义没帮助，直接过滤掉
_STOP_WORDS = set(
    "的 了 和 是 就 都 而 及 与 着 或 一个 没有 我们 你们 他们 它们 这个 那个 "
    "这 那 我 你 他 她 它 也 还 又 再 很 更 最 不 没 有 在 从 到 向 对 为 以 "
    "把 被 让 给 比 跟 和 同 因 为 由 于 中 上 下 里 外 前 后 左 右 之 所 等 "
    "啊 呀 吧 呢 吗 哦 嗯 哈 啦 么 的话 一下 一些 什么 怎么 怎样 如何 为什么 "
    "可以 可能 应该 需要 已经 正在 将要 马上 立刻 赶紧 快点 慢点 等等".split()
)


def tokenize(text: str) -> list:
    """中文分词：把一段文字切成词的列表。

    步骤：
    1. 去掉标点符号和特殊字符
    2. 用 jieba 分词
    3. 过滤停用词和单字（单字信息量太低）
    """
    # 去掉非中文字符（保留中文、数字、字母）
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", " ", text)

    # jieba 分词
    words = jieba.lcut(text)

    # 过滤：停用词 + 长度小于2的词（单字基本没区分度）
    result = []
    for w in words:
        w = w.strip()
        if len(w) < 2:
            continue
        if w in _STOP_WORDS:
            continue
        result.append(w)

    return result


def compute_tf(words: list) -> dict:
    """计算词频 TF（Term Frequency）。

    TF = 某个词在文档中出现的次数 / 文档总词数
    词出现得越多，越重要。
    """
    if not words:
        return {}
    tf = {}
    total = len(words)
    for w in words:
        tf[w] = tf.get(w, 0) + 1
    # 归一化（除以总词数），这样长短文档之间可以比较
    for w in tf:
        tf[w] = tf[w] / total
    return tf


def compute_idf(documents: list) -> dict:
    """计算逆文档频率 IDF（Inverse Document Frequency）。

    IDF = log(总文档数 / (包含该词的文档数 + 1))
    一个词在越少的文档中出现，IDF值越大，说明这个词越有"区分度"。
    比如"的"这个字在所有文档里都有，IDF就接近0，没用。
    而"保证金"只在少数文档里出现，IDF就高，很有区分价值。
    """
    n_docs = len(documents)
    if n_docs == 0:
        return {}

    # 统计每个词出现在多少个文档里
    doc_freq = {}
    for doc_words in documents:
        unique_words = set(doc_words)
        for w in unique_words:
            doc_freq[w] = doc_freq.get(w, 0) + 1

    # 计算 IDF
    idf = {}
    for w, df in doc_freq.items():
        idf[w] = math.log(n_docs / (df + 1)) + 1  # +1 平滑，避免除零

    return idf


def compute_tfidf_vector(words: list, idf: dict) -> dict:
    """把词列表转成 TF-IDF 向量（用字典表示，稀疏向量）。

    每个词的权重 = TF × IDF
    词越常见（TF高）且越有区分度（IDF高），权重越大。
    """
    tf = compute_tf(words)
    vector = {}
    for w, tf_val in tf.items():
        idf_val = idf.get(w, 0)
        if idf_val > 0:  # 只保留在IDF词典里的词
            vector[w] = tf_val * idf_val
    return vector


def cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """计算两个稀疏向量的余弦相似度（0~1，越大越相似）。

    余弦相似度 = 向量点积 / (向量a的长度 × 向量b的长度)

    几何意义：把两个向量想象成空间中的两条射线，都从原点出发。
    它们之间的夹角越小，余弦值越接近1，说明两段文字越相似。
    """
    if not vec_a or not vec_b:
        return 0.0

    # 点积：两个向量共有的词的权重相乘再相加
    dot_product = 0.0
    for w, val in vec_a.items():
        if w in vec_b:
            dot_product += val * vec_b[w]

    # 向量长度（模）
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


# ---------- 知识库加载与向量预计算 ----------

def load_kb(path: str = "kb.json") -> list:
    """读取骗局套路知识库（kb.json）。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_kb_vectors(kb: list) -> tuple:
    """预计算知识库每条套路的 TF-IDF 向量。

    返回 (idf_dict, vector_list)：
    - idf_dict: 全局 IDF 词典（基于整个知识库计算）
    - vector_list: 每条套路对应的 TF-IDF 向量列表

    为什么要预计算？
    知识库是固定的，每次分析都重新分词、算TF-IDF是浪费。
    提前算好存起来，分析时直接拿来比就行。
    """
    # 第一步：把每条套路转成词列表
    doc_words_list = []
    for pattern in kb:
        # 把套路的所有文本信息拼起来，分词后作为一个文档
        text_parts = [
            pattern.get("name", ""),
            pattern.get("explanation", ""),
            " ".join(pattern.get("aliases", [])),
            " ".join(pattern.get("trigger_signals", [])),
            pattern.get("category", ""),
            pattern.get("advice", "") and " ".join(pattern.get("advice", [])),
        ]
        text = "。".join(filter(None, text_parts))
        words = tokenize(text)
        doc_words_list.append(words)

    # 第二步：基于整个知识库计算 IDF
    idf = compute_idf(doc_words_list)

    # 第三步：计算每条套路的 TF-IDF 向量
    vectors = []
    for words in doc_words_list:
        vec = compute_tfidf_vector(words, idf)
        vectors.append(vec)

    return idf, vectors


def save_kb_vectors(idf: dict, vectors: list, path: str = "kb_vectors.json"):
    """把预计算好的向量和IDF词典保存到文件。"""
    data = {"idf": idf, "vectors": vectors}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_kb_vectors(path: str = "kb_vectors.json") -> tuple:
    """加载预计算好的向量和IDF词典。

    返回 (idf_dict, vector_list)，如果文件不存在返回 (None, None)。
    """
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("idf"), data.get("vectors")


# ---------- 检索层：TF-IDF语义 + 关键词 混合检索 ----------

def _keyword_score(messages_text: str, pattern: dict) -> int:
    """关键词命中计数（作为补充信号）。"""
    keywords = (pattern.get("aliases") or []) + (
        pattern.get("trigger_signals") or []
    )
    return sum(1 for kw in keywords if kw and kw in messages_text)


def retrieve_patterns(
    messages_text: str,
    kb: list,
    idf: dict = None,
    kb_vectors: list = None,
    top_k: int = 5,
) -> list:
    """混合检索：关键词精确匹配 + TF-IDF 语义补充，各取所长。

    设计思路：
    - 关键词匹配：精确率高，命中即高度相关，但骗子换说法就漏
    - TF-IDF 语义检索：召回率高，能发现部分变体和相关套路，但可能误报
    - 混合策略：先收关键词命中的（高置信），再用语义检索补充（扩大覆盖）
    - 语义结果必须满足最低相似度阈值，避免正常对话产生误报
    """
    # 没有预计算向量时，纯关键词检索（兼容老版本）
    if idf is None or kb_vectors is None:
        scored = []
        for pattern in kb:
            hits = _keyword_score(messages_text, pattern)
            if hits > 0:
                scored.append((hits, pattern))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [pattern for _, pattern in scored[:top_k]]

    # ---- 第一阶段：关键词精确匹配（高置信度）----
    keyword_matches = []
    for pattern in kb:
        hits = _keyword_score(messages_text, pattern)
        if hits > 0:
            keyword_matches.append((hits, pattern))
    keyword_matches.sort(key=lambda x: x[0], reverse=True)

    # ---- 第二阶段：TF-IDF 语义补充（扩大召回）----
    query_words = tokenize(messages_text)
    query_vec = compute_tfidf_vector(query_words, idf)

    semantic_scored = []
    keyword_pattern_ids = {id(p) for _, p in keyword_matches}

    for pattern, pattern_vec in zip(kb, kb_vectors):
        # 已经被关键词命中的，不再重复计算
        if id(pattern) in keyword_pattern_ids:
            continue

        sim = cosine_similarity(query_vec, pattern_vec)
        # 语义相似度阈值：过滤掉偶然的词重叠
        # TF-IDF 相似度通常 0~0.35，0.15 以上才算有实质关联
        # 阈值越高，精确率越高，但召回率越低
        if sim >= 0.15:
            semantic_scored.append((sim, pattern))

    semantic_scored.sort(key=lambda x: x[0], reverse=True)

    # ---- 合并：关键词结果在前，语义补充在后 ----
    results = [p for _, p in keyword_matches]
    for _, p in semantic_scored:
        if len(results) >= top_k:
            break
        results.append(p)

    return results[:top_k]


# ---------- 主分析流程 ----------

def analyze(conversation: str, kb: list, idf: dict = None, kb_vectors: list = None) -> dict:
    """完整的 5-Agent 分析流程：编排 → 检索 → 三路分析 → 仲裁。"""
    # ① 编排：把原始对话解析成结构化数据
    orch = call_agent(SYS_ORCHESTRATOR, f"请解析以下对话：\n{conversation}")

    messages = orch.get("messages", [])
    messages_text = "\n".join(m.get("text", "") for m in messages)

    # 检索层：从知识库挑出最相关的套路，喂给话术识别 Agent
    patterns = retrieve_patterns(messages_text, kb, idf, kb_vectors)

    # ②③④ 三个分析 Agent（并行可优化，当前串行保证稳定性）
    script = call_agent(
        SYS_SCRIPT,
        json.dumps(
            {"messages": messages, "scam_patterns": patterns},
            ensure_ascii=False,
        ),
    )
    rationality = call_agent(
        SYS_RATIONALITY,
        json.dumps(
            {
                "messages": messages,
                "context": orch.get("transaction_context", {}),
            },
            ensure_ascii=False,
        ),
    )
    rule = call_agent(
        SYS_RULE,
        json.dumps({"messages": messages}, ensure_ascii=False),
    )

    # ⑤ 仲裁：综合三路结果，定级 + 给应对策略
    final = call_agent(
        SYS_ARBITER,
        json.dumps(
            {"script": script, "rationality": rationality, "rule": rule},
            ensure_ascii=False,
        ),
    )

    return {
        "orchestrator": orch,
        "script": script,
        "rationality": rationality,
        "rule": rule,
        "final": final,
    }
