# xlsx-value-picker プロジェクト ドキュメントガイド

このディレクトリにはxlsx-value-pickerプロジェクトに関するドキュメントが格納されています。ドキュメントはジャンルごとに整理されており、目的に応じて適切なドキュメントを参照してください。

## ドキュメント構成

### プロジェクト概要文書

- [プロジェクト現状文書](./project-status.md): プロジェクトの現在の状況、進行中の作業、今後の計画などを記載

### ジャンル別ドキュメント

#### プロジェクト文書 (`project/`)

プロジェクト全体に関わる計画、状況、方針などの文書

- [要件定義書](./project/requirements.md): プロジェクトの要件定義
- [技術選定ドキュメント](./project/technology-selection.md): 採用技術とその選定理由

#### 仕様文書 (`spec/`)

機能仕様、API仕様、データスキーマなどの文書

- [CLIインターフェース仕様](./spec/cli-spec.md): コマンドラインインターフェースの仕様
- [バリデーションルールスキーマ](./spec/rule-schema.json): バリデーションルールを定義するJSONスキーマ
- [MCPサーバー仕様](./spec/mcp-server-spec.md): Model Context Protocol サーバーの仕様

#### 設計文書 (`design/`)

アーキテクチャ設計、モジュール設計、機能設計などの文書

- [バリデーション設計ドキュメント](./design/validation-design.md): バリデーション機能の設計
- [設定ローダー設計](./design/config-loader-design.md): 設定ファイル読み込み機能の設計
- [MCPサーバー設計](./design/mcp-server-design.md): MCPサーバー機能の設計

#### ガイドライン (`guide/`)

開発ガイドライン、コーディング規約、スタイルガイドなど

- [Mermaidスタイルガイド](./guide/mermaid-style-guide.md): Mermaidダイアグラム作成のガイドライン
- [ディレクトリ構造ガイドライン](./guide/directory-structure-guideline.md): プロジェクトのディレクトリ構造と役割
- [バージョン管理ガイドライン](./guide/version-control-guideline.md): Git利用時のブランチ戦略やコミットルール
- [依存関係管理ガイドライン](./guide/dependency-management-guideline.md): Pythonパッケージの依存関係管理ルール
- [Pydanticモデル設計ガイドライン](./guide/pydantic-model-design-guideline.md): Pydanticモデルの設計方針に関するガイドライン

#### タスク記録 (`task_log/`)

特定の機能開発や改善タスクに関する作業計画や実施記録を格納します。

## ドキュメント作成・更新のガイドライン

### 新規ドキュメント作成時の配置

- プロジェクト全体に関わる計画、状況、方針に関する文書: `project/`
- 機能仕様、API仕様、データスキーマに関する文書: `spec/`
- アーキテクチャ設計、モジュール設計、機能設計に関する文書: `design/`
- 開発ガイドライン、コーディング規約、スタイルガイドに関する文書: `guide/`
- 個別タスクの作業計画や実施記録: `task_log/`

### 文書間の相互参照

- 同一ディレクトリ内のファイルを参照: `ファイル名.md`
- 他のディレクトリのファイルを参照: `ディレクトリ名/ファイル名.md`
- docs/直下のファイルを参照: `./ファイル名.md`

---

最終更新日: 2025年4月30日