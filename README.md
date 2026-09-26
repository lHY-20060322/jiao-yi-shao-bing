# jiao-yi-shao-bing
二手交易反诈智能分析系统
[README.md](https://github.com/user-attachments/files/32680459/README.md)
# 🛡️ 交易哨兵 · Fraud Sentinel

> 基于多 Agent 协作的二手交易反诈智能分析系统
> 粘贴对话，AI 帮你识别诈骗信号，守护你的每一笔交易

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/DeepSeek-5C4BFF?style=flat-square" alt="DeepSeek">
  <img src="https://img.shields.io/badge/Agent-5个-2563eb?style=flat-square" alt="Agents">
  <img src="https://img.shields.io/badge/知识库-50条-059669?style=flat-square" alt="Knowledge Base">
</p>

---

## ✨ 项目简介

交易哨兵是一款面向二手交易场景的 AI 反诈工具。用户只需粘贴交易对话，系统通过 **5 个 AI Agent 协同工作**，从话术识别、交易合理性、平台规则三个维度进行分析，最终综合判定风险等级并给出具体的应对建议。

### 🎯 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 **五 Agent 协作** | 编排 + 话术识别 + 交易合理性 + 平台规则 + 仲裁，分工专业、交叉验证 |
| 📚 **50 条骗局知识库** | 覆盖 8 大类诈骗类型，每条附真实案例 |
| 🔍 **混合检索引擎** | 关键词精确匹配 + TF-IDF 语义补充，兼顾精确率和召回率 |
| 🎯 **五级风险评级** | 安全 / 低危 / 中危 / 高危 / 确认诈骗 |
| 🛠️ **三套应对方案** | 安全方案 / 试探方案 / 止损方案，按需选择 |
| ⚡ **零门槛使用** | 无需注册、粘贴即用 |

---

## 🏗️ 系统架构

```
用户输入对话
    │
    ▼
┌─────────────────┐
│  📋 编排 Agent    │  解析对话结构、提取交易上下文
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  🔍 混合检索引擎  │  关键词匹配 + TF-IDF 语义补充
└────────┬────────┘
         │
    ┌────┴────┬───────────┐
    ▼         ▼           ▼
┌───────┐ ┌───────┐ ┌───────┐
│🎯 话术 │ │⚖️ 合理│ │📜 规则│
│ 识别   │ │ 性    │ │       │
└───┬───┘ └───┬───┘ └───┬───┘
    │         │         │
    └────┬────┘         │
         ▼              │
  ┌───────────┐         │
  │ 👨‍⚖️ 仲裁 Agent ◄─────┘
  └─────┬─────┘
        │
        ▼
  风险等级 + 置信度 + 关键证据 + 应对方案
```

### 五个 Agent 分工

| Agent | 职责 |
|-------|------|
| 📋 **编排Agent** | 解析对话结构，识别双方身份，提取交易上下文 |
| 🎯 **话术识别Agent** | 匹配诈骗话术套路，引用原文证据 |
| ⚖️ **交易合理性Agent** | 从价格、紧迫感、凭证等维度判断合理性 |
| 📜 **平台规则Agent** | 检查是否违反平台安全红线 |
| 👨‍⚖️ **仲裁Agent** | 综合三路分析，给出最终判定和应对建议 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/lHY-20060322/jiao-yi-shao-bing.git
cd jiao-yi-shao-bing

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
# 复制 .env.example 为 .env，填入你的 API Key
# 或者设置环境变量：export DEEPSEEK_API_KEY=你的APIKey

# 4. （可选）生成知识库向量，启用语义检索
python build_vectors.py

# 5. 启动应用
streamlit run app.py
```

浏览器会自动打开应用界面。

### 在线体验

> 🌐 **在线 Demo**：[点击访问](https://jiao-yi-shao-bing-kwemct78sqdduszdtdtwa.streamlit.app)

---

## 📊 知识库

### 概况

- **套路总数**：50 条
- **高危类型**：21 条
- **覆盖分类**：8 大类

### 分类体系

| 分类 | 数量 | 典型套路 |
|------|------|---------|
| 资金类 | 11 条 | 保证金诈骗、私下转账、刷单返利等 |
| 流程类 | 5 条 | 脱离平台交易、提前确认收货等 |
| 身份类 | 7 条 | 假客服、盗图冒用、AI换脸等 |
| 信息类 | 5 条 | 钓鱼链接、索要验证码等 |
| 商品类 | 12 条 | 假货冒充、空包裹、星期猫等 |
| 心理类 | 3 条 | 制造紧迫感、卖惨人设等 |
| 服务类 | 4 条 | 代抢代拍、租房诈骗等 |
| 人身类 | 1 条 | 同城面交抢劫 |

---

## 🧪 测试与评估

### 测试数据集

包含 30 个测试用例（22 个正例 + 8 个负例），覆盖标准话术、变体说法、多信号叠加、新型诈骗、学生高发等多种场景。

### 运行评估

```bash
# 检索层效果评估（对比关键词 vs 混合检索）
python evaluate_retrieval.py
```

### 评估指标

- **Top1 准确率**：排名第一的结果是否正确
- **Top3 召回率**：前3个结果是否包含正确答案
- **精确率 P**：命中结果中相关的比例
- **召回率 R**：应该命中的实际命中比例
- **F1 值**：精确率和召回率的调和平均

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit + 自定义 CSS |
| AI 引擎 | DeepSeek API |
| 检索层 | jieba 分词 + TF-IDF + 余弦相似度 |
| 知识库 | JSON 结构化存储 |
| 部署 | Streamlit Community Cloud |

---

## 📁 项目结构

```
.
├── app.py                  # Streamlit 前端界面
├── core.py                 # 核心分析引擎（5 Agent + 混合检索）
├── prompts.py              # Agent 提示词
├── kb.json                 # 50 条诈骗套路知识库
├── kb_vectors.json         # 预计算的知识库向量（可选）
├── build_vectors.py        # 知识库向量预计算脚本
├── evaluate_retrieval.py   # 检索层评估脚本
├── test_dataset.json       # 测试数据集
├── run_app.py              # 桌面应用启动器
├── requirements.txt        # Python 依赖
└── README.md               # 本文件
```

---

## 🎯 应用场景

- 🛡️ **C 端工具**：二手交易用户自查风险
- 🏫 **高校教育**：学生反诈宣传教育
- 🔌 **平台内嵌**：二手交易平台反诈功能
- 📊 **数据分析**：诈骗类型趋势研究

---

## 🗺️ 未来规划

### 短期（1-3个月）
- [ ] 扩充知识库到 80-100 条
- [ ] 优化 Agent prompt，提升准确率
- [ ] 收集用户反馈，持续迭代

### 中期（3-6个月）
- [ ] 引入深度学习 embedding 模型（BGE/text2vec）
- [ ] 开发浏览器插件版本
- [ ] 尝试与高校合作

### 长期（6-12个月）
- [ ] 探索商业化路径
- [ ] 构建反诈知识库开放平台
- [ ] 打造有影响力的反诈科技品牌

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如果你发现了新的诈骗类型，或者有改进建议，欢迎：
1. 提交 Issue 描述
2. Fork 仓库并修改
3. 提交 Pull Request

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🙏 致谢

- 感谢所有反诈工作者的付出
- 知识库内容参考了各地反诈中心的公开宣传资料
- 感谢 DeepSeek 提供 AI 能力支持

---

<p align="center">
  <b>🛡️ 交易哨兵 — 守护你的每一笔交易</b>
</p>
