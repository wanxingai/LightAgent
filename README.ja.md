
![LightAgent Banner](docs/images/lightagent-banner.jpg)
<div align="center">
  <p>
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
    <a href="https://github.com/wanxingai/LightAgent/releases"><img src="https://img.shields.io/github/release/wanxingai/LightAgent.svg" alt="GitHub release"></a>
    <a href="https://github.com/wanxingai/LightAgent/issues"><img src="https://img.shields.io/github/issues/wanxingai/LightAgent.svg" alt="GitHub issues"></a>
    <a href="https://github.com/wanxingai/LightAgent/stargazers"><img src="https://img.shields.io/github/stars/wanxingai/LightAgent.svg" alt="GitHub stars"></a>
    <a href="https://github.com/wanxingai/LightAgent/network"><img src="https://img.shields.io/github/forks/wanxingai/LightAgent.svg" alt="GitHub forks"></a>
    <a href="https://github.com/wanxingai/LightAgent/graphs/contributors"><img src="https://img.shields.io/github/contributors/wanxingai/LightAgent.svg" alt="GitHub contributors"></a>
    <a href="https://sufe-aiflm-lab.github.io/LightAgent/"><img src="https://img.shields.io/badge/docs-latest-brightgreen.svg" alt="Docs"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/v/lightagent.svg" alt="PyPI"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/dm/lightagent.svg" alt="Downloads"></a>
    <a href="https://pypi.org/project/lightagent/"><img src="https://img.shields.io/pypi/pyversions/lightagent.svg" alt="Python Version"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style"></a>
  </p>
</div>
<div align="center">
  <p>
    <a href="README.md">English</a> | 
    <a href="README.zh-CN.md">简体中文</a> | 
    <a href="README.zh-TW.md">繁體中文</a> | 
    <a href="README.es.md">Español</a> | 
    <a href="README.fr.md">Français</a> | 
    <a href="README.de.md">Deutsch</a> | 
    日本語 | 
    <a href="README.ko.md">한국어</a> | 
    <a href="README.pt.md">Português</a> | 
    <a href="README.ru.md">Русский</a> 
  </p>
</div>


<div align="center">
  <h1>LightAgent🚀（次世代エージェンティックAIフレームワーク）</h1>
</div>

**LightAgent** は、記憶（`mem0`）、ツール（`Tools`）、思考ツリー（`ToT`）を備えた非常に軽量な能動的エージェントフレームワークであり、完全にオープンソースです。これは、OpenAI Swarm よりも簡単なマルチエージェント協調をサポートし、自己学習能力を持つエージェントを簡単に構築でき、stdio および sse 方式で MCP プロトコルに接続できます。基盤モデルは、OpenAI、智谱 ChatGLM、DeepSeek、階跃星辰、Qwen通义千问大モデルなどをサポートしています。同時に、LightAgent は OpenAI ストリーム形式 API サービス出力をサポートし、主要なチャットフレームワークにシームレスに接続できます。🌟

---

## ニュース
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2026-06-24]** LightAgent v0.9.0：永続化 LightFlow checkpoint、resume/rerun、承認ノード、明確なステップ状態、trace メタデータ、Guardrails テンプレート、MemoryPolicy 制御、SharedMemoryPool プロトタイプを追加。
- **[2026-06-14]** LightAgent v0.8.1：MemoryScope 規約と MemoryPolicy の出所・範囲・信頼度フィルタを追加。
- **[2026-06-02]** LightAgent v0.8.0：決定的な複数ステップ workflow のための LightFlow を導入。

過去のリリースノートは [GitHub Releases](https://github.com/wanxingai/LightAgent/releases) を参照してください。

---

## ✨ 特徴

- **軽量で効率的** 🚀：極限のシンプル設計で迅速なデプロイが可能、あらゆるスケールのアプリケーションシーンに適しています。（No LangChain, No LlamaIndex）100% Pythonで実装され、追加の依存関係は不要、コアコードはわずか1000行、完全にオープンソースです。
- **メモリサポート** 🧠：各ユーザーのためにカスタマイズ可能な長期メモリをサポートし、対話の過程でユーザーの個性に応じたメモリを自動管理することにより、エージェントをより賢くします。
- **自主学習** 📚️：各エージェントは自ら学ぶ能力を持ち、アクセス権を持つ管理者はそれぞれのエージェントを管理できます。
- **ツール統合** 🛠️：カスタマイズ可能なツール（`Tools`）をサポートし、自動ツール生成が可能で、多様なニーズに応えます。
- **複雑な目標** 🌳：反省を伴う思考ツリーモジュール（ToT）を内蔵しており、複雑なタスクの分解と多段階推論をサポートし、タスク処理能力を向上させます。
- **マルチエージェント協調** 🤖：Swarmよりも簡単に実現できるマルチエージェント協調作業をサポートし、内蔵のLightSwarmが意図の判断とタスクの移転機能を実装し、より賢くユーザー入力を処理できます。
- **独立した実行** 🤖：人的介入なしに自律的にタスクツールを呼び出して完了します。
- **多モデルサポート** 🔄：OpenAI、智谱ChatGLM、百川大モデル、StepFun、DeepSeek、Qwenシリーズの大モデルと互換性があります。
- **ストリームAPI** 🌊：OpenAIストリーム形式のAPIサービス出力をサポートしており、主流のチャットフレームワークとのシームレスな統合により、ユーザー体験を向上させます。
- **Toolsツールジェネレーター** 🚀：APIドキュメントを[Toolsツールジェネレーター]に渡すだけで、数百のカスタマイズツールを短時間で自動生成し、効率を向上させ、創造的な可能性を解放します。
- **エージェントの自己学習** 🧠️：各エージェントは自身のシーンメモリ機能を持ち、ユーザーの対話から自己学習する能力を備えています。
- **適応型ツールメカニズム** 🛠️：無限のツールを追加可能、大量のツールの中から大モデルが候補ツールの集合を選び、無関係なツールをフィルタリングした後、文脈を再び大モデルに提出することによって、トークン消費を大幅に削減できます。
- **ワークフロー編成** 🔁：LightFlow は明示的な依存関係、出力受け渡し、リトライ、checkpoint、resume/rerun、承認ノード、fallback agent、追跡可能な実行を備えた決定的 workflow を構成します。
- **共有メモリプロトタイプ** 🧠：SharedMemoryPool は出所メタデータ、スコープ付き検索、MemoryPolicy 互換結果を備えたインメモリ共有メモリを提供します。
- **Guardrails テンプレート** 🛡️：入力、ツール、出力の再利用可能な安全ポリシーにより、個人情報の遮断、機密ツールの確認、高リスク引数の検証、出力のマスキングを行えます。

## 🧭 アーキテクチャ概要

| レイヤー | 主な API | 用途 |
| --- | --- | --- |
| 単一 Agent 実行 | `LightAgent` | モデル呼び出し、ツール、メモリ、ストリーミング、trace、guardrails。 |
| マルチ Agent ルーティング | `LightSwarm` | 専門 Agent 間の役割ベース委譲。 |
| 決定的 workflow | `LightFlow` | DAG、リトライ、checkpoint、承認、resume、rerun。 |
| ツールと統合 | `tools`、`ToolRegistry`、MCP | Python ツール、生成ツール、実行時ロード、MCP サーバー。 |
| メモリ境界 | `MemoryPolicy`、`MemoryScope` | テナント分離、出所、信頼、期限、書き込み許可。 |
| 共有メモリ | `SharedMemoryPool` | Agent 間の共有メモリ実験。 |
| 安全制御 | `input_guardrails`、`tool_guardrails`、`output_guardrails` | プライバシー、ツール確認、リスク引数、出力マスキング。 |
| 可観測性 | `trace=True`、`agent.export_trace()` | 実行、モデル、ツール、エラー、workflow の構造化イベント。 |

## 主要な利用パターン

LightAgent はデフォルトの呼び出しを簡単に保ちつつ、本番向け制御を段階的に追加できます。

| パターン | 最小呼び出し | 説明 |
| --- | --- | --- |
| 基本応答 | `agent.run(query)` | デフォルトで文字列を返します。 |
| ストリーミング | `agent.run(query, stream=True)` | OpenAI 互換 chunk を返します。 |
| 構造化結果 | `agent.run(query, result_format="object")` | 内容とメタデータを返します。 |
| Trace | `agent.run(query, trace=True)` | デフォルトの文字列返却を変えずにイベントを記録します。 |
| ユーザーメモリ | `agent.run(query, user_id="alice")` | 設定済みメモリ backend と MemoryPolicy を使います。 |
| ツール | `LightAgent(..., tools=[fn])` | 関数は `tool_info` を持つべきです。 |
| Guardrails | `LightAgent(..., input_guardrails=[...])` | 入力、ツール、出力ポリシーを追加します。 |
| Workflow | `LightFlow().step(...).run(query)` | 決定的な多段階実行に使います。 |

## 📋 ドキュメント

- インストール、モデル、ツール、メモリ、MCP、Skills、ストリーミング、LightSwarm については [FAQ](docs/FAQ.md) を参照してください。
- 決定的 workflow、checkpoint、resume/rerun、承認、fallback agent、ステップ状態については [LightFlow](docs/lightflow.md) を参照してください。
- カスタムツール、ToolRegistry、ToolLoader、AsyncToolDispatcher、MCP については [Tools Guide](docs/tools.md) を参照してください。
- 共有長期メモリまたはグラフメモリについては [Memory Security Guidance](docs/memory_security.md) を参照してください。
- SharedMemoryPool については [SharedMemoryPool](docs/shared_memory_pool.md) を参照してください。
- メモリ書き込みの受け入れ制御と期限については [Memory Admission And Mutation Controls](docs/memory_admission.md) を参照してください。
- 入力、ツール、出力の安全ポリシーについては [Guardrails](docs/guardrails.md) を参照してください。
- OpenRouter、ローカルモデル、OpenAI 互換プロバイダーについては [Model Provider Configuration](docs/model_providers.md) を参照してください。
- 構造化 trace については [Trace Observability](docs/tracing.md) を参照してください。

## 🚧 近日公開

- **エージェント協調通信** 🛠️：エージェント間で情報を共有し、メッセージを伝達することができ、複雑な情報通信とタスク協調を実現します。
- **エージェント評価** 📊：エージェントの評価ツールを内蔵しており、構築したエージェントを評価および最適化し、ビジネスシーンに直結し、知能レベルを継続的に向上させます。

## 🌟 なぜLightAgentを選ぶのか？

- **オープンソースで無料** 💖：完全にオープンソース、コミュニティ主導で継続的に更新されています。貢献を歓迎します！  
- **簡単に始められる** 🎯：文書が詳細で、サンプルが豊富で、迅速に始められ、プロジェクトに簡単に組み込むことが可能です。  
- **コミュニティサポート** 👥：活発な開発者コミュニティがあり、いつでも支援と解答を提供します。  
- **高性能** ⚡：最適化された設計で高効率に実行され、高い同時実行性のシーンのニーズに応えます。  

---

## 🛠️ クイックスタート

### LightAgent最新バージョンのインストール

```bash
pip install lightagent
```

（オプションでMem0パッケージをインストール）：

```bash
pip install mem0ai
```

または、ホスティングプラットフォーム上でMem0をワンボタンで使用できます。[こちらをクリック](https://www.mem0.ai/)。

### Hello worldのサンプルコード

```python
from LightAgent import LightAgent

# エージェントの初期化
agent = LightAgent(model="gpt-4o-mini", api_key="your_api_key", base_url="your_base_url")

# エージェントを実行
response = agent.run("こんにちは、あなたは誰ですか？")
print(response)
```

### 実行 Trace を確認する（v0.7.0）

Trace は opt-in で、`agent.run()` のデフォルト動作との互換性を保ちます。

```python
from LightAgent import LightAgent

agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

result = agent.run("Hello, who are you?", result_format="object", trace=True)
print(result.content)
print(result.trace_id)
print(result.trace)

for event in agent.export_trace():
    print(event["type"], event["data"])
```

### LightFlow 実行を checkpoint する（v0.9.0）

`LightFlow` は workflow checkpoint を永続化し、失敗した実行を最初からではなく途中から再開できます。

```python
from LightAgent import JsonLightFlowStore, LightAgent, LightFlow

research_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")
writer_agent = LightAgent(model="gpt-4.1", api_key="your_api_key", base_url="your_base_url")

store = JsonLightFlowStore(".lightflow_runs")
flow = (
    LightFlow(store=store)
    .step("research", agent=research_agent, timeout=30)
    .step("write", agent=writer_agent, depends_on=["research"], max_retry=2)
)

result = flow.run("Analyze this company", run_id="report-001", trace=True)

if not result.success:
    result = flow.resume("report-001")

print(result.status)
print(flow.get_run("report-001")["steps"])
```

### SharedMemoryPool を使う（v0.9.0）

`SharedMemoryPool` はマルチ Agent 共有メモリ実験向けの軽量インメモリプロトタイプです。

```python
from LightAgent import LightAgent, MemoryPolicy, SharedMemoryPool

shared_memory = SharedMemoryPool(agent_name="writer")

agent = LightAgent(
    name="writer",
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    memory=shared_memory,
    memory_policy=MemoryPolicy(
        namespace="tenant-a",
        allow_unattributed_results=False,
        allowed_sources=("user",),
        allowed_scopes=("user",),
    ),
)

agent.run("Remember that I prefer concise reports.", user_id="alice")
print(shared_memory.list_records(user_id="tenant-a:alice"))
```


### systemプロンプトを使ってモデルの自己認識を設定する

```python
from LightAgent import LightAgent

# エージェントの初期化
agent = LightAgent(
     role="あなたはLightAgentです、ユーザーが多くのツールを使用するのを助ける役立つアシスタントです。",  # systemロールの説明
     model="deepseek-chat",  # 対応モデル：openai、chatglm、deepseek、qwenなど
     api_key="your_api_key",  # あなたの大モデルサービスプロバイダAPIキーに置き換えます
     base_url="your_base_url",  # あなたの大モデルサービスプロバイダapi urlに置き換えます
 )
# エージェントを実行
response = agent.run("あなたは誰ですか？")
print(response)
```

### ツール使用のサンプルコード

```python
from LightAgent import LightAgent

# ツールを定義
def get_weather(city_name: str) -> str:
    """
    `city_name`の現在の天気を取得
    """
    return f"問い合わせ結果: {city_name} は晴れです"
# 関数内部でツール情報を定義
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "指定された都市の現在の天気情報を取得",
    "tool_params": [
        {"name": "city_name", "description": "問い合わせる都市名", "type": "string", "required": True},
    ]
}

tools = [get_weather]

# エージェントの初期化
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url="your_base_url", tools=tools)

# エージェントを実行
response = agent.run("上海の天気を教えてください")
print(response)
```
無限のカスタマイズ可能なツールのサポート。

複数のツールの例： tools = ["search_news", "get_weather", "get_stock_realtime_data", "get_stock_kline_data"]

---

## 機能詳細

README には中核的な利用モデルを残し、長い例、アダプタ設定、本番運用の詳細は専用ドキュメントに置いています。

### 1. 分離可能なメモリモジュール（`mem0`）
LightAgent は `store(data, user_id)` と `retrieve(query, user_id)` を持つ任意のメモリ backend を受け付けます。会話分離には `user_id`、共有メモリには `MemoryPolicy` を使います。

### 2. ツール統合
`tool_info` メタデータを持つ Python 関数で Agent に制御された能力を公開します。ToolRegistry、ToolLoader、AsyncToolDispatcher、MCP は [Tools Guide](docs/tools.md) を参照してください。

### 3. ツール生成器
`agent.create_tool()` は API 文書や自然言語説明からツールコードを生成できます。本番前にレビューとテストを行ってください。

### 4. 思考ツリー（ToT）
明示的な計画、反省、ツール選択が必要な場合は `tree_of_thought=True` を有効にします。

### 5. マルチ Agent 協調
`LightSwarm` は専門 Agent 間で作業を委譲します。役割を狭く保ち、メモリ書き込みをポリシーで制御してください。

### 6. ストリーミング API
`agent.run(query, stream=True)` はチャット UI や長文出力向けに OpenAI 互換 chunk を返します。

### 7. Agent 自己学習
自己学習は `MemoryPolicy` と組み合わせ、個人情報、期限切れ、無関係な内容を避けるべきです。

### 8. Trace と Langfuse
LightAgent は組み込み trace または Langfuse で実行を観測できます。

### 9. Agent 評価
Agent 評価は業務シナリオに対する振る舞いを測定する予定です。

### 10. LightFlow Workflow
`LightFlow` は既知の手順で実行するための決定的 workflow 層です。

- ステップ状態：`pending`、`running`、`success`、`failed`、`skipped`、`waiting_approval`。
- DAG 検証：`flow.validate(strict=True)`。
- ステップ制御：`timeout`、`max_retry`、`cancel_if`、`fallback_agent`、`requires_approval`、`approval_handler`。
- 永続化と復旧：`JsonLightFlowStore`、`flow.resume(run_id)`、`flow.rerun_step(run_id, step_name)`、`flow.get_run(run_id)`、`flow.list_runs()`。

[LightFlow](docs/lightflow.md) を参照してください。

### 11. Guardrails
Guardrails は入力、ツール呼び出し、出力を検査する軽量 hook です。

```python
from LightAgent import (
    LightAgent,
    high_risk_parameter_guardrail,
    output_redaction_guardrail,
    privacy_input_guardrail,
    sensitive_tool_confirmation_guardrail,
)

agent = LightAgent(
    model="gpt-4.1",
    api_key="your_api_key",
    base_url="your_base_url",
    input_guardrails=[privacy_input_guardrail()],
    tool_guardrails=[
        sensitive_tool_confirmation_guardrail(["transfer_money"], approved=False),
        high_risk_parameter_guardrail({"amount": lambda value: float(value) <= 1000}),
    ],
    output_guardrails=[output_redaction_guardrail()],
)
```

[Guardrails](docs/guardrails.md) を参照してください。

### 12. SharedMemoryPool
`SharedMemoryPool` はマルチ Agent 共有メモリ実験用のインメモリプロトタイプで、`MemoryPolicy` と併用します。

## 主流エージェントモデルサポート

LightAgent は OpenAI 互換 chat completion endpoint に対応します：OpenAI、OpenRouter、Zhipu ChatGLM、DeepSeek、Qwen、StepFun、Moonshot/Kimi、MiniMax、vLLM、llama.cpp、Ollama、自ホスト gateway。

For provider-specific parameters, base URLs, local model setup, and troubleshooting, see [Model Provider Configuration](docs/model_providers.md).

## 使用シーン

- **スマートカスタマーサービス**：多段階の対話とツール統合により、高効率な顧客サポートを提供します。
- **データ分析**：思考ツリーとマルチエージェント協調を利用して、複雑なデータ分析タスクを処理します。
- **自動化ツール**：自動ツール生成により、カスタマイズツールを迅速に構築します。
- **教育支援**：メモリモジュールとストリームAPIを用いて、個別的な学習体験を提供します。

---

## 🛠️ 貢献ガイドライン

私たちは、あらゆる形態の貢献を歓迎します！コード、ドキュメント、テスト、フィードバックいずれも、プロジェクトに対する大きな助けとなります。良いアイデアやバグを発見した場合は、IssueまたはPull Requestを提出してください。以下は貢献のステップです：

1. **このプロジェクトをフォーク**：右上の`Fork`ボタンをクリックして、プロジェクトをGitHubリポジトリにコピーします。
2. **ブランチを作成**：ローカルに開発ブランチを作成します：  
   ```bash
   git checkout -b feature/YourFeature
   ```
3. **変更をコミット**：開発を完了したら、変更をコミットします：  
   ```bash
   git commit -m 'Add some feature'
   ```
4. **ブランチをプッシュ**：ブランチをリモートリポジトリにプッシュします：  
   ```bash
   git push origin feature/YourFeature
   ```
5. **プルリクエストを提出**：GitHub上でプルリクエストを提出し、変更内容を説明します。

私たちは迅速にあなたの貢献をレビューします！ご支援ありがとうございます！❤️

---

## 🙏 謝辞

LightAgentの開発と実現は、以下のオープンソースプロジェクトのインスピレーションとサポートに寄っています。特に以下の優れたプロジェクトとチームに感謝します：

- **mem0**：メモリモジュールを提供してくれた[mem0](https://github.com/mem0ai/mem0)に感謝します。
- **Swarm**：マルチエージェント協調設計のアイデアを提供してくれた[Swarm](https://github.com/openai/swarm)に感謝します。
- **ChatGLM3**：高性能な中国語大モデルのサポートとデザインのインスピレーションを提供してくれた[ChatGLM3](https://github.com/THUDM/ChatGLM3)に感謝します。
- **Qwen**：高性能な中国語大モデルのサポートを提供してくれた[Qwen](https://github.com/QwenLM/Qwen)に感謝します。
- **DeepSeek-V3**：高性能な中国語大モデルのサポートを提供してくれた[DeepSeek-V3](https://github.com/deepseek-ai/DeepSeek-V3)に感謝します。
- **StepFun**：高性能な中国語大モデルのサポートを提供してくれた[step](https://www.stepfun.com/)に感謝します。

---

## 📄 ライセンス

LightAgentは[Apache 2.0ライセンス](LICENSE)の下で使用されます。本プロジェクトは自由に使用、変更、配布できますが、ライセンスの条項を遵守してください。

---

## 📬 お問い合わせ

何か問題や提案がある場合は、いつでもお問い合わせください：

- **メール**：service@wanxingai.com  
- **GitHub Issues**：[https://github.com/wanxingai/LightAgent/issues](https://github.com/wanxingai/LightAgent/issues)  

あなたのフィードバックをお待ちしております。一緒にLightAgentを強化しましょう！🚀

- **さらに多くのツール** 🛠️：実用的なツールを継続的に統合し、多くのシーンのニーズに応えます。
- **モデルサポートの拡張** 🔄：さらに多くの大モデルをサポートするように継続的に拡張します。
- **機能の追加** 🎯：実用的な機能をさらに追加し、続々と更新を予定していますのでご期待ください！
- **さらなるドキュメント** 📚：詳細なドキュメントがあり、豊富なサンプルで迅速に始められ、プロジェクトに簡単に統合できます。
- **さらなるコミュニティサポート** 👥：活発な開発者コミュニティがあり、いつでも支援を提供します。
- **さらなるパフォーマンス最適化** ⚡：継続的にパフォーマンスを最適化し、同時運用のシーンのニーズに応えます。
- **さらなるオープンソース貢献** 🌟：コードの貢献を歓迎し、より優れたLightAgentの構築に取り組みましょう！

---

<p align="center">
  <strong>LightAgent - インテリジェンスを軽量化し、未来をシンプルに。</strong> 🌈
</p>

 
**LightAgent** —— 軽量で柔軟、強力な能動的エージェントフレームワークで、迅速にインテリジェントなアプリケーションを構築します！