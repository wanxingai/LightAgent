
![LightAgent Banner](docs/images/lightagent-banner.jpg)
<div align="center">
  <p>
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
    <a href="https://github.com/wxai-space/LightAgent/releases"><img src="https://img.shields.io/github/release/wxai-space/LightAgent.svg" alt="GitHub release"></a>
    <a href="https://github.com/wxai-space/LightAgent/issues"><img src="https://img.shields.io/github/issues/wxai-space/LightAgent.svg" alt="GitHub issues"></a>
    <a href="https://github.com/wxai-space/LightAgent/stargazers"><img src="https://img.shields.io/github/stars/wxai-space/LightAgent.svg" alt="GitHub stars"></a>
    <a href="https://github.com/wxai-space/LightAgent/network"><img src="https://img.shields.io/github/forks/wxai-space/LightAgent.svg" alt="GitHub forks"></a>
    <a href="https://github.com/wxai-space/LightAgent/graphs/contributors"><img src="https://img.shields.io/github/contributors/wxai-space/LightAgent.svg" alt="GitHub contributors"></a>
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


## 🚧 近日公開

- **エージェント協調通信** 🛠️：エージェント間で情報を共有し、メッセージを伝達することができ、複雑な情報通信とタスク協調を実現します。
- **エージェント評価** 📊：エージェントの評価ツールを内蔵しており、構築したエージェントを評価および最適化し、ビジネスシーンに直結し、知能レベルを継続的に向上させます。

## 内蔵「思考の流れ」
（Thought Flow）方法は、システム的かつ構造的で柔軟な思考過程により、複雑なシーンの課題に効果的に対応できます。
以下は具体的な実施手順です：
```text
問題の定義：コアな問題と目標を明確にする。

情報収集：関連する情報とデータを系統的に収集する。

問題分解：複雑な問題を複数のサブ問題またはモジュールに分解する。

多次元分析：各サブ問題を異なる角度とレベルから分析する。

関連付け：サブ問題間の関連性と依存関係を特定する。

解決策の生成：各サブ問題に対して可能な解決策を提案する。

評価と選択：各解決策の実現可能性と影響を評価し、最適な解決策を選択する。

実施とフィードバック：選定した解決策を実施し、フィードバックに基づいて調整する。
```

---
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

### 1. 分解可能な全自動メモリモジュール（`mem0`）
LightAgentは外部拡張の`mem0`メモリモジュールをサポートし、文脈メモリと履歴管理を自動的に行い、開発者がメモリの追加や検索を手動でトリガーする必要はありません。メモリモジュールを通じて、エージェントは複数回の対話で文脈の一貫性を維持できます。

```python
# メモリモジュールの有効化

# またはカスタムメモリモジュールを使用します。以下はmem0の例です https://github.com/mem0ai/mem0/
from mem0 import Memory
from LightAgent import LightAgent
import os
from loguru import logger

class CustomMemory:
    def __init__(self):
        self.memories = []
        os.environ["OPENAI_API_KEY"] = "your_api_key"
        os.environ["OPENAI_API_BASE"] = "your_base_url"
        # Mem0の初期化
        config = {
            "version": "v1.1"
        }
        # mem0でqdrantをベクターデータベースとして使用する場合、configを次のコードに変更します
        # config = {
        #     "vector_store": {
        #         "provider": "qdrant",
        #         "config": {
        #             "host": "localhost",
        #             "port": 6333,
        #         }
        #     },
        #     "version": "v1.1"
        # }
        self.m = Memory.from_config(config_dict=config)

    def store(self, data: str, user_id):
        """メモリの保存 開発者はストレージメソッドの内部実装を変更できます。現在の例はmem0のメモリ追加メソッドです"""
        result = self.m.add(data, user_id=user_id)
        return result

    def retrieve(self, query: str, user_id):
        """関連メモリの検索 開発者は検索メソッドの内部実装を変更できます。現在の例はmem0のメモリ検索メソッドです"""
        result = self.m.search(query, user_id=user_id)
        return result

agent = LightAgent(
        role="あなたはLightAgentです、ユーザーが多くのツールを使用するのを助ける役立つアシスタントです。",  # systemロールの説明
        model="deepseek-chat",  # 対応モデル：openai、chatglm、deepseek、qwenなど
        api_key="your_api_key",  # あなたの大モデルサービスプロバイダAPIキーに置き換えます
        base_url="your_base_url",  # あなたの大モデルサービスプロバイダapi urlに置き換えます
        memory=CustomMemory(),  # メモリ機能を有効化
        tree_of_thought=False,  # 思考連鎖を有効化
    )

# メモリ付きテスト & ツールを追加する必要がある場合は、エージェントにツールを追加してメモリ付きツール呼び出しを実現します

user_id = "user_01"
logger.info("\n=========== 次の会話 ===========")
query = "三亜には面白い観光スポットがありますか？友達がたくさん三亜へ旅行していたので、私も遊びに行きたいです"
print(agent.run(query, stream=False, user_id=user_id))
logger.info("\n=========== 次の会話 ===========")
query = "私はどこに旅行したいですか？"
print(agent.run(query, stream=False, user_id=user_id))
```

出力は以下のようになります：
```python
=========== 次の会話 ===========
2025-01-01 21:55:15.886 | INFO     | __main__:run_conversation:115 - 
問題を考え始めました: 三亜には面白い観光スポットがありますか？友達がたくさん三亜へ旅行していたので、私も遊びに行きたいです
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:118 - 最終返信: 
三亜は中国海南省の人気旅行都市で、美しいビーチ、熱帯気候、豊富な観光資源で知られています。以下は三亜で訪れる価値のある観光スポットです：

1. **亚龙湾**：東のハワイとも称され、長いビーチと澄んだ海水があり、泳ぐのに最適な場所です。

2. **天涯海角**：壮大な海の景色とロマンチックな伝説に惹かれる著名な文化的スポットです。ここにある大きな石には「天涯」と「海角」という文字が彫られ、永遠の愛を象徴しています。

3. **南山文化観光区**：高さ108メートルの南山海上観音像があり、世界で最も高い海の観音像です。ここでは仏教文化を体験し、寺院や庭園を訪れることができます。

4. **蜈支洲島**：原初の自然の風景と豊富な水中活動で知られる小島です。ここではダイビング、シュノーケリング、海釣りなどが楽しめます。

5. **大東海**：三亜市内にあるビーチで、便利な交通と豊かなナイトライフが人気です。

6. **三亜湾**：22キロの長さを誇るビーチで、夕日を見るのに最適な場所です。比較的静かなビーチで、穏やかに過ごしたい方に向いています。

7. **呀诺达熱帯雨林文化観光区**：熱帯雨林の公園で、熱帯雨林の自然を体験し、さまざまな冒険活動に参加できます。

8. **鹿回頭公園**：山の頂に位置する公園で、三亜市内と三亜湾の美しい景色を眺められます。ここには鹿に関する美しい伝説もあります。

9. **西島**：比較的原始的な小島で、静かなビーチと豊富な海洋生物が観光客を惹きつけます。

10. **三亜千古情**：大規模な文化テーマパークで、パフォーマンスや展示を通じて海南の歴史と文化を紹介しています。

上記の観光スポットに加え、三亜には他にも探索すべき場所が多数あります。熱帯植物園や海鮮市場などもおすすめで、特に新鮮な海鮮や熱帯フルーツは見逃せません。旅行を計画する際は、事前に天候予報と観光地の開園時間を確認し、楽しい旅行体験を確保することをお勧めします。
2025-01-01 21:55:28.676 | INFO     | __main__:<module>:191 - 
=========== 次の会話 ===========
2025-01-01 21:55:28.676 | INFO     | __main__:run_conversation:115 - 
問題を考え始めました: 私はどこに旅行したいですか？
関連するメモリを発見:
ユーザーは三亜に旅行したい
ユーザーの友人は三亜に旅行したことがある。
2025-01-01 21:55:38.797 | INFO     | __main__:run_conversation:118 - 最終返信: 
ユーザーが以前言及した情報に基づくと、ユーザーの友人は既に三亜（Sanya）を訪れており、ユーザー自身も三亜に興味を示しています。そのため、三亜はユーザーにとって適した旅行先かもしれません。以下は三亜についての旅行情報です：

### 三亜観光のおすすめ：
1. **亚龙湾**：美しいビーチと澄んだ海水があり、泳ぎや日光浴が楽しめる場所です。
2. **天涯海角**：三亜の象徴的な観光スポットで、独特の岩とロマンチックな伝説が訪問者を引きつけます。
3. **南山文化観光区**：有名な南山寺と108メートルの海上観音像があり、仏教文化に大きな影響を与えています。
4. **蜈支洲島**：ダイビングや海上のアクティビティに最適で、島には豊富な海洋生物とサンゴ礁があります。 
5. **大東海**：三亜市内のビーチで、交通が便利で家族やカップルに人気です。

### その他のおすすめ：
もしユーザーが三亜について既に知っているか、他の目的地を探求したい場合は、以下の他の人気旅行地を提案します：
1. **桂林**：独特のカルスト地形と漓江の風景で知られています。
2. **麗江**：古都と玉龍雪山が主要な観光スポットで、歴史文化と自然風景を好む旅行者に適しています。
3. **張家界**：特異な石柱と自然景観で有名で、《アバター》映画の撮影地の一つです。

ユーザーは自身の興味と時間に基づいて適した旅行先を選ぶことができます。詳細な情報が必要な場合やスケジュールの計画を手伝ってほしい場合は、いつでもお知らせください！
```

### 2. ツール統合（無限のカスタムツールサポート）
パーソナライズされたツールカスタマイズ（`Tools`）を取り入れ、`tools`メソッドを使って専用ツールを簡単に統合できます。これらのツールは任意のPython関数であり、パラメータ型の注釈をサポートしているため、柔軟性と精度が保証されます。また、AI駆動のツール生成器も提供し、ツールを自動生成してクリエイティブを解放します。

```python

import requests
from LightAgent import LightAgent

# ツールを定義
def get_weather(
        city_name: str
) -> str:
    """
    市の天気情報を取得
    :param city_name: 市名
    :return: 天気情報
    """
    if not isinstance(city_name, str):
        raise TypeError("市名は文字列でなければなりません")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    try:
        resp = requests.get(f"https://wttr.in/{city_name}?format=j1")
        resp.raise_for_status()
        resp = resp.json()
        ret = {k: {_v: resp[k][0][_v] for _v in v} for k, v in key_selection.items()}
    except:
        import traceback
        ret = "天気データの取得中にエラーが発生しました！\n" + traceback.format_exc()

    return str(ret)

# 関数内部でツール情報を定義
get_weather.tool_info = {
    "tool_name": "get_weather",
    "tool_description": "指定した市の現在の天気情報を取得",
    "tool_params": [
        {"name": "city_name", "description": "市名", "type": "string", "required": True},
    ]
}

def search_news(
        keyword: str,
        max_results: int = 5
) -> str:
    """
    キーワードに基づいてニュースを検索
    :param keyword: 検索キーワード
    :param max_results: 最大結果数、デフォルトは5
    :return: ニュース検索結果
    """
    results = f"{keyword}を検索したところ、{max_results}件の関連情報が見つかりました"
    return str(results)

# 関数内部でツール情報を定義
search_news.tool_info = {
    "tool_name": "search_news",
    "tool_description": "キーワードに基づいてニュースを検索",
    "tool_params": [
        {"name": "keyword", "description": "検索キーワード", "type": "string", "required": True},
        {"name": "max_results", "description": "返される最大結果数", "type": "int", "required": False},
    ]
}

def get_user_info(
        user_id: str
) -> str:
    """
    ユーザー情報を取得
    :param user_id: ユーザーID
    :return: ユーザー情報
    """
    if not isinstance(user_id, str):
        raise TypeError("ユーザーIDは文字列でなければなりません")

    try:
        # ユーザー情報APIを使用すると仮定し、サンプルURLを用います
        url = f"https://api.example.com/users/{user_id}"
        response = requests.get(url)
        response.raise_for_status()
        user_data = response.json()
        user_info = {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "created_at": user_data.get("created_at")
        }
    except:
        import traceback
        user_info = "ユーザーデータの取得中にエラーが発生しました！\n" + traceback.format_exc()

    return str(user_info)

# 関数内部でツール情報を定義
get_user_info.tool_info = {
    "tool_name": "get_user_info",
    "tool_description": "指定したユーザーの情報を取得",
    "tool_params": [
        {"name": "user_id", "description": "ユーザーID", "type": "string", "required": True},
    ]
}

# カスタムツール
tools = [get_weather, search_news, get_user_info]  # すべてのツールを含む

# エージェントの初期化
# あなたのモデルパラメータmodel、api_key、base_urlに置き換えます
agent = LightAgent(model="qwen-turbo-2024-11-01", api_key="your_api_key", base_url="your_base_url", tools=tools)

query = "現在の三亜の天気はどうなっていますか？"
response = agent.run(query, stream=False)  # エージェントを使ってクエリを実行
print(response)
```

### 3. ツール生成器
ツール生成器は、ユーザーが提供したテキスト記述に基づいてツールコードを自動生成し、指定されたディレクトリに保存するモジュールです。この機能は、API呼び出しツールやデータ処理ツールなど、迅速に生成する必要があるシーンで特に役立ちます。

使用例

以下はツール生成器を使用するサンプルコードです：

```python
import json
import os
import sys
from LightAgent import LightAgent

# LightAgentを初期化
agent = LightAgent(
    name="エージェントA",  # エージェント名
    instructions="あなたは便利なエージェントです。",  # ロールの説明
    role="あなたはツール生成器です。ユーザーが提供するテキスト記述に基づいて相応しいツールコードを自動生成し、それを指定されたディレクトリに保存する作業を行います。生成されたコードの正確性と有用性を確認してください。",
    model="deepseek-chat",  # あなたのモデルに置き換えます。対応するモデル：openai、chatglm、deepseek、qwenなど
    api_key="your_api_key",  # あなたのAPIキーに置き換えます
    base_url="your_base_url",  # あなたのAPI URLに置き換えます
)

# サンプルテキスト記述
text = """
新浪株式インタフェースは、株式市場データの取得機能を提供し、株価、リアルタイム取引データ、K線チャートデータなどを含みます。

新浪株式インタフェースの機能紹介
1、株式の市場データを取得：
リアルタイムの相場データ: リアルタイム相場APIを使用すると、株式の最新の価格、取引量、上昇幅などの情報を取得できます。
分単位の相場データ: 分単位相場APIを使用すると、株式の逐分取引データ、オープン価格、クローズ価格、高価格、低価格などを取得できます。

2、株式の歴史的K線チャートデータの取得：
K線チャートデータ: K線チャートAPIを通じて、株式の過去の取引データを取得できます。オープン価格、クローズ価格、高価格、低価格、取引量などを含みます。必要に応じて、異なる時間周期および移動平均周期を選択できます。
調整後のデータ: 調整後のK線チャートデータを取得できます。前調整と後調整の選択が可能で、株式の価格変動の分析において、より正確に行えます。

新浪株式インタフェースからデータを取得するサンプル
1、株式の市場データを取得：
APIアドレス：http://hq.sinajs.cn/list=[株式コード]
サンプル：株式コードが"sh600519"（貴州茅台）のリアルタイムの相場データを取得したい場合、次のAPIアドレスを使用します：http://hq.sinajs.cn/list=sh600519
上記のAPIアドレスにHTTP GETリクエストを送信することで、その株式のリアルタイムの相場データが入ったレスポンスを受け取ります。

2、株式の歴史的K線チャートデータを取得：
APIアドレス：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=[株式コード]&scale=[時間周期]&ma=[移動平均周期]&datalen=[データ長]
サンプル：株式コードが"sh600519"（貴州茅台）のデイリーK線チャートデータを取得するには、以下のAPIアドレスを使用します：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=1023
上記のAPIアドレスにHTTP GETリクエストを送信することで、その株式の歴史的K線チャートデータが入ったレスポンスを受け取ります。
"""

# toolsディレクトリのパスを構築
project_root = os.path.dirname(os.path.abspath(__file__))
tools_directory = os.path.join(project_root, "tools")

# toolsディレクトリが存在しない場合は作成
if not os.path.exists(tools_directory):
    os.makedirs(tools_directory)

print(f"Toolsディレクトリが作成されました: {tools_directory}")

# ツールコードを生成するためにエージェントを使用
agent.create_tool(text, tools_directory=tools_directory)
```
実行後、toolsディレクトリにget_stock_kline_data.pyとget_stock_realtime_data.pyの2つのファイルが生成されます。

### 4. 思考ツリー（ToT）
内蔵の思考ツリー機能は、複雑なタスクの分解と多段階推論をサポートします。思考ツリーを通じて、エージェントは複雑なタスクをより良く処理できます。

```python
# 思考の木を有効にする
agent = LightAgent(
    model="gpt-4.1", 
    api_key="your_api_key", 
    base_url= "your_base_url", 
    tree_of_thought=True,  # 思考の木を有効にする
    tot_model="gpt-4o", 
    tot_api_key="sk-uXx0H0B***17778F1",  # あなたの deepseek r1 API Key に置き換えてください
    tot_base_url="https://api.openai.com/v1",  # api url
    filter_tools=False,  # 自適応ツールメカニズムを無効にする
)
```
ToTを有効にすると、デフォルトで自適応ツールメカニズムが有効になります。無効にする必要がある場合は、LightAgentの初期化時にパラメータfilter_tools=Falseを追加してください。

### 5. マルチエージェント協調
Swarmのようなマルチエージェント協調作業をサポートし、タスク処理の効率を向上させます。複数のエージェントが協力して複雑なタスクを完了することができます。

```python
from LightAgent import LightAgent, LightSwarm
# 環境変数OPENAI_API_KEYとOPENAI_BASE_URLを設定
# モデルはデフォルトでgpt-4o-miniを使用

# LightSwarmインスタンスを作成
light_swarm = LightSwarm()

# 複数のエージェントを作成
agent_a = LightAgent(
    name="エージェントA",
    instructions="私はフロントデスク担当者です",
    role="フロントデスク担当者、訪問者を迎え入れ、基本的な情報を提供する役割を持ちます。毎回の回答前に自己紹介を行い、顧客のビジネス問題に直接答えることはできません。他の役割へ案内することしかできません。もし現在は質問を解決できない場合は、今はお手伝いできませんとお答えください。",
)

agent_b = LightAgent(
    name="エージェントB",
    instructions="私は会議室の予約担当です",
    role="会議室予約管理者、1号、2号、3号の会議室の予約、キャンセル、照会を担当します。毎回の回答前に自己紹介を行い、非常に丁寧に質問にお答えします。",
)

agent_c = LightAgent(
    name="エージェントC",
    instructions="私は技術サポートスペシャリストです、技術問題を扱います。毎回の回答前に自己紹介を行い、ユーザーの技術問題に対してできる限り詳しくお答えします。問題が私の能力を超えている場合は、ユーザーをより上位の技術サポートに案内します。",
    role="技術サポートスペシャリスト、ハードウェア、ソフトウェア、ネットワークなどに関する技術問題の相談と解決を担当します。",
)

agent_d = LightAgent(
    name="エージェントD",
    instructions="私は人事担当者です、人事に関連する問題を扱います。毎回の回答前に自己紹介を行い、ユーザーの質問にできる限り詳細にお答えします。問題がさらに進む必要がある場合は、人事部門に連絡するようユーザーを案内します。",
    role="人事担当者、従業員の入職、退職、休暇、福利厚生などの業務の相談と処理を担当します。",
)

# エージェントをLightSwarmインスタンスに自動登録します
light_swarm.register_agent(agent_a, agent_b, agent_c, agent_d)

# エージェントAを実行
res = light_swarm.run(agent=agent_a, query="こんにちは、私はアリスです、王小明が入職を済ませたかどうか確認したいです", stream=False)
print(res)
```
出力は以下のようになります：
```python
こんにちは、私は人事担当者エージェントDです。王小明が入職を済ませたかどうかの質問については、システム記録を確認する必要があります。しばらくお待ちください。
（システム記録を確認中...）
私たちの記録によると、王小明は2025年1月5日に入職手続きを完了しました。すべての必要書類に署名し、社員番号とオフィス位置が割り当てられています。さらなる詳細情報が必要な場合や他に質問があれば、人事部門にご連絡ください。私たちはいつでもお手伝いする準備ができています。
```

### 6. ストリームAPI
OpenAIストリーム形式のAPIサービス出力をサポートし、主要なチャットフレームワークとシームレスに接続できます。

```python
# ストリーム出力を有効化
response = agent.run("AIについての文章を生成してください", stream=True)
for chunk in response:
    print(chunk)
```

### 7. エージェント評価（近日公開）
内蔵のエージェント評価ツールにより、エージェントのパフォーマンスを評価し最適化することが容易になります。

## 主流エージェントモデルサポート
様々な大モデルとの互換性があり、OpenAI、智谱ChatGLM、DeepSeek、Qwenシリーズの大モデルを含みます。

#### 現在テスト済みの大モデル
OpenAI Series
 - gpt-3.5-turbo
 - gpt-4
 - gpt-4o
 - gpt-4o-mini
 - gpt-4.1
 - gpt-4.1-mini
 - gpt-4.1-nano
 - and GPT-5、GPT-5.1、GPT-5.2、GPT-5.3、GPT-5.4 

ChatGLM
 - GLM-5.1
 - GLM-4.7
 - GLM-4.5
 - GLM-4.5-Air
 - GLM-4.5-X
 - GLM-4.5-AirX
 - GLM-4.5-Flash
 - GLM-4-Plus
 - GLM-4-Air-0111
 - GLM-4-Flash
 - GLM-4-FlashX
 - GLM-4-alltools
 - GLM-4
 - GLM-3-Turbo
 - ChatGLM3-6B
 - GLM-4-9B-Chat

DeepSeek Series
 - DeepSeek-r1
 - DeepSeek-v3
 - DeepSeek-v4

stepfun
 - step-1-8k
 - step-1-32k
 - step-1-128k (issues with multi-tool calls)
 - step-1-256k (issues with multi-tool calls)
 - step-1-flash (recommended, cost-effective)
 - step-2-16k (issues with multi-tool calls)
 - step-3.5-flash

Qwen Series
 - qwen-plus-2024-11-25
 - qwen-plus-2024-11-27
 - qwen-plus-1220
 - qwen-plus
 - qwen-plus-latest 
 - qwen2.5-72b-instruct
 - qwen2.5-32b-instruct
 - qwen2.5-14b-instruct
 - qwen2.5-7b-instruct 
 - qwen-turbo-latest
 - qwen-turbo-2024-11-01
 - qwen-turbo
 - qwen-long
 - qwq-32b
 - qwen3-0.6b
 - qwen3-1.7b
 - qwen3-4b
 - qwen3-8b
 - qwen3-14b
 - qwen3-32b
 - qwen3-30b-a3b
 - qwen3-235b-a22b
 - Qwen3-30B-A3B-Thinking-2507
 - Qwen3-30B-A3B-Instruct-2507
 - Qwen3.5
 - Qwen3.6


MiniMax Series
- MiniMax-M2.7
- MiniMax-M2.5
- MiniMax-M2.1
- MiniMax-M2


Moonshot Series (Kimi)
- moonshot-v1-8k
- moonshot-v1-32k
- moonshot-v1-128k
- Kimi K2.6


---

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
- **GitHub Issues**：[https://github.com/wxai-space/lightagent/issues](https://github.com/wxai-space/lightagent/issues)  

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