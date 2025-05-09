"""
JSONスキーマに基づく設定データ読み込み機能
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Literal, Self, Union, cast

import yaml
from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic import ValidationError as PydanticValidationError

# カスタム例外をインポート
from .exceptions import ConfigLoadError, ConfigValidationError, XlsxValuePickerError
from .validator.validation_common import ValidationContext, ValidationResult
from .validator.validation_expressions import ExpressionType

# ConfigValidationError は exceptions.py に移動済みのため削除


class ConfigParser:
    @staticmethod
    def parse_file(file_path: str) -> dict[str, Any]:
        """
        設定ファイル（YAMLまたはJSON）を読み込み、Pythonオブジェクトに変換する

        Args:
            file_path: 設定ファイルのパス

        Returns:
            dict: 設定データ

        Raises:
            ConfigLoadError: ファイルが存在しない、またはサポートされていない形式の場合
        """
        if not os.path.exists(file_path):
            # FileNotFoundError の代わりに ConfigLoadError を送出
            raise ConfigLoadError(f"設定ファイルが見つかりません: {file_path}")
        yaml_extentions = [".yaml", ".yml"]
        json_extentions = [".json"]
        supported_extensions = yaml_extentions + json_extentions
        if not any(file_path.endswith(ext) for ext in supported_extensions):
            raise ConfigLoadError(f"サポートされていないファイル形式です: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                ext = os.path.splitext(file_path)[1].lower()
                if ext in yaml_extentions:
                    # yaml.safe_load は Any を返すため、cast と ignore を使用
                    return cast(dict[str, Any], yaml.safe_load(f))
                if ext in json_extentions:
                    # json.load は Any を返すため、cast と ignore を使用
                    return cast(dict[str, Any], json.load(f))

                # サポートされている拡張子のいずれかであるべきだが、念のため
                raise ConfigLoadError(f"サポートされていないファイル形式です: {file_path}")

        except (yaml.YAMLError, json.JSONDecodeError) as e:  # yaml.parser.ParserError は yaml.YAMLError に含まれる
            print(f"DEBUG: Caught exception type: {type(e)}")  # デバッグ出力追加
            print(f"DEBUG: Exception message: {e}")  # デバッグ出力追加
            raise ConfigLoadError(f"設定ファイルのパースに失敗しました: {file_path}") from e
        except Exception as e:  # その他の予期せぬ読み込みエラー
            print(e)
            raise ConfigLoadError(f"設定ファイルの読み込み中に予期せぬエラーが発生しました: {file_path}") from e


# SchemaValidator クラスは削除 (JSONスキーマ検証は Pydantic に一本化)
# バリデーション式関連のコードは validation_expressions.py に移動済み
class Rule(BaseModel):
    """バリデーションルール"""

    name: str
    expression: ExpressionType
    error_message: str

    # @model_validator(mode="before")
    # @classmethod
    # def validate_expression(cls, data: dict[str, Any]) -> dict[str, Any]:
    #     """式のデータを適切な型に変換する"""
    #     if isinstance(data, dict) and "expression" in data and isinstance(data["expression"], dict):
    #         # validation_expressions の convert_expression を使用
    #         data["expression"] = convert_expression(data["expression"])
    #     return data

    def validate(self, context: ValidationContext) -> ValidationResult:  # type: ignore[override]
        """
        ルールのバリデーションを実行する

        Args:
            context: バリデーションコンテキスト

        Returns:
            ValidationResult: バリデーション結果
        """
        # 内部の式を評価 (self.expression は ExpressionType)
        result: ValidationResult = self.expression.validate_in(context, self.error_message)

        # ルール名と場所情報を追加
        if not result.is_valid:
            result.rule_name = self.name
            # Ensure locations are populated if fields exist
            if result.error_fields and not result.error_locations:
                locations = [
                    context.get_field_location(f) for f in result.error_fields if context.get_field_location(f)
                ]
                result.error_locations = sorted(
                    {loc for loc in locations if loc is not None}  # 明示的にセット内包表記でフィルタリング
                )  # Use set to avoid duplicates if expression already added some

        return result


class OutputFormat(BaseModel):
    """出力形式設定"""

    format: str = "json"
    template_file: str | None = None
    template: str | None = None

    @model_validator(mode="after")
    def check_jinja2_template(self) -> Self:
        """Jinja2形式の場合はテンプレートが必要"""
        if self.format == "jinja2" and not (self.template_file or self.template):
            raise ValueError("Jinja2出力形式の場合、template_fileまたはtemplateが必要です")

        if self.format == "jinja2" and self.template_file and self.template:
            raise ValueError("template_fileとtemplateを同時に指定することはできません")

        if self.format not in ["json", "yaml", "jinja2", "csv"]:  # csv を追加 (仮)
            # TODO: csv サポートを正式に追加する際に修正
            raise ValueError(f"サポートされていない出力形式です: {self.format}")
            # pass # 一旦許容

        return self


class ConfigModel(BaseModel):
    """設定ファイルのモデル"""

    fields: dict[str, str]
    rules: list[Rule] = []
    output: OutputFormat = Field(default_factory=OutputFormat)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls: type["ConfigModel"], v: dict[str, str]) -> dict[str, str]:
        """フィールド定義の検証"""
        import re  # re をインポート

        if not v:
            raise ValueError("少なくとも1つのフィールド定義が必要です")

        pattern = r"^[^!]+![A-Z]+[0-9]+$"
        for _, cell_addr in v.items():
            if not re.match(pattern, cell_addr):
                raise ValueError(f"無効なセル参照形式です: {cell_addr}。正しい形式は 'Sheet1!A1' です。")

        return v


class ConfigLoader:
    """設定ファイルローダー"""

    # DEFAULT_SCHEMA_PATH は不要なため削除

    def __init__(self) -> None:
        """
        初期化
        (スキーマ検証を行わないため、引数は不要)
        """
        # スキーマバリデーターの初期化は不要
        pass

    def load_config(self, config_path: str) -> ConfigModel:
        """
        設定ファイルを読み込み、モデルオブジェクトを返す

        Args:
            config_path: 設定ファイルのパス

        Returns:
            ConfigModel: 設定モデルオブジェクト

        Raises:
            ConfigLoadError: 設定ファイルの読み込みやパースに失敗した場合
            ConfigValidationError: 設定ファイルのスキーマ検証やモデル検証に失敗した場合
        """
        try:
            # 設定ファイルのパース (ConfigLoadError が発生する可能性)
            config_data = ConfigParser.parse_file(config_path)

            # JSONスキーマによる検証は削除

            # モデルオブジェクトの生成 (PydanticValidationError が発生する可能性)
            model = ConfigModel.model_validate(config_data)
            return model

        except ConfigLoadError as e:
            # パース時のエラーはそのまま ConfigLoadError として送出
            raise e
        # except ConfigValidationError as e: # スキーマ検証のエラーハンドリングは削除
        #     raise e
        except PydanticValidationError as e:
            # Pydantic のバリデーションエラーを ConfigValidationError にラップして送出
            # エラーメッセージを整形して分かりやすくする
            error_details = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            raise ConfigValidationError(f"設定ファイルのモデル検証に失敗しました: {error_details}") from e
        except Exception as e:
            # その他の予期せぬエラー
            raise ConfigValidationError(
                f"設定ファイルの読み込み時に予期しないエラーが発生しました: {config_path}"
            ) from e

    def load_mcp_config(self, config_path: str) -> "MCPConfig":
        """
        MCP設定ファイルを読み込み、MCPConfigモデルオブジェクトを返す

        Args:
            config_path: MCP設定ファイルのパス

        Returns:
            MCPConfig: MCP設定モデルオブジェクト

        Raises:
            ConfigLoadError: 設定ファイルの読み込みやパースに失敗した場合
            ConfigValidationError: 設定ファイルのモデル検証に失敗した場合
        """
        try:
            # 設定ファイルのパース
            config_data = ConfigParser.parse_file(config_path)

            # MCPConfigモデルオブジェクトの生成
            mcp_config = MCPConfig.model_validate(config_data)
            mcp_config.origin = Path(config_path).absolute()
            return mcp_config

        except ConfigLoadError as e:
            raise e
        except PydanticValidationError as e:
            error_details = "; ".join([f"{err['loc']}: {err['msg']}" for err in e.errors()])
            raise ConfigValidationError(f"MCP設定ファイルのモデル検証に失敗しました: {error_details}") from e
        except Exception as e:
            raise XlsxValuePickerError(f"MCP設定ファイルの処理中に予期せぬエラーが発生しました: {e}") from e


# Pydanticモデルの循環参照を解決するために再構築
Rule.model_rebuild()
ConfigModel.model_rebuild()

"""
MCPサーバー設定関連クラス
"""


class MCPAvailableConfigModel(ConfigModel):
    """MCPサーバ設定用に追加項目を付与して拡張したモデル"""

    model_name: str | None = None
    model_description: str | None = None


type ToolNames = Literal["listModels", "getModelInfo", "getDiagnostics", "getFileContent"]


class MCPConfig(BaseModel):
    models: list[Union["ModelConfigReference", "GlobModelConfigReference"]]
    config: "MCPConfigDetails"
    origin: Path | None = None
    # 以降内部用フィールド
    loaded_models: list[MCPAvailableConfigModel] = Field(default=[], exclude=True)

    def cache_models(self) -> None:
        """モデル一覧をパースしてモデル設定をキャッシュする"""
        # モデル設定をロード
        self.loaded_models: list[MCPAvailableConfigModel] = [
            model for definition in self.models for model in definition.get_models(self)
        ]

    def handle_list_models(self) -> str:
        """モデル情報を取得するためのハンドラー"""
        # モデル情報を取得
        simplified_models = [
            f"Model Name: {model.model_name}. Description: {model.model_description}" for model in self.loaded_models
        ]
        return "\n".join(simplified_models)

    def configure(self) -> FastMCP[Any]:
        """設定内容に基づいてFastMCPサーバのインスタンスを構築して返す"""
        self.cache_models()

        # FastMCP サーバーを構築
        server: FastMCP[Any] = FastMCP()

        # ハンドラーを登録
        server.add_tool(
            name="listModels",
            fn=self.handle_list_models,
            description="""
supply summarized list of parsable Excel file informations with `getFileContent` tool.

""",
        )
        # server.add_tool(
        #     name="getModelInfo",
        #     fn=self.handle_get_model_info,
        #     description="get detailed information about specified Excel file ",
        # )
        # server.add_tool(name="getDiagnostics", fn=self.handle_get_diagnostics)
        # server.add_tool(name="getFileContent", fn=self.handle_get_file_content)

        return server


class IModelReferences(ABC):
    """モデル設定を表すインターフェース"""

    @abstractmethod
    def get_models(self, context: MCPConfig) -> list[MCPAvailableConfigModel]:
        """モデル設定を取得する"""
        raise NotImplementedError("get_models メソッドは実装されていません")


class ModelConfigReference(BaseModel, IModelReferences):
    config_path: str = Field(..., alias="config")
    model_name: str | None = None
    model_description: str | None = None

    def get_models(self, context: MCPConfig) -> list[MCPAvailableConfigModel]:
        """モデル設定を取得する"""
        path = Path(self.config_path)
        # パス表記が絶対パスでない場合はMCP設定ファイルの親フォルダからの相対パスとして解釈する
        if not path.is_absolute() and context.origin is not None:
            path = context.origin.parent / path
        # 設定ファイルを読み込む
        config = ConfigParser.parse_file(str(path))

        # モデル名と説明をMCP設定ファイルの内容で上書き
        if self.model_name:
            config["model_name"] = self.model_name
        if self.model_description:
            config["model_description"] = self.model_description

        return [MCPAvailableConfigModel.model_validate(config)]


class GlobModelConfigReference(BaseModel, IModelReferences):
    config_path_pattern: str

    def get_models(self, context: MCPConfig) -> list[MCPAvailableConfigModel]:
        """モデル設定を取得する"""
        # glob パターンを展開してモデル設定を取得
        # import glob

        # models = []
        # for path in glob.glob(self.config_path_pattern):
        #     model_ref = ModelConfigReference(config_path=path)
        #     models.extend(model_ref.get_models())

        # return models
        raise NotImplementedError("メソッドは実装されていません")


class MCPConfigDetails(BaseModel):
    tool_descriptions: dict[ToolNames, str]
