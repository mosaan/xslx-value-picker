"""
バリデーション機能の共通定義

このモジュールは、バリデーション機能で使用される共通のクラスやインターフェースを定義します。
循環インポートを防ぐため、validation.pyとconfig_loader.pyから共通して使用される
クラス・インターフェースをこのモジュールに集約しています。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union


@dataclass
class ValidationContext:
    """
    バリデーション実行時のコンテキスト情報を保持するクラス

    Attributes:
        cell_values: フィールド名とその値のマッピング
        field_locations: フィールド名とExcelセル位置のマッピング
    """

    cell_values: Dict[str, Any]
    field_locations: Dict[str, str]

    def get_field_value(self, field_name: str) -> Any:
        """指定されたフィールドの値を取得します"""
        return self.cell_values.get(field_name)

    def get_field_location(self, field_name: str) -> Optional[str]:
        """指定されたフィールドのセル位置を取得します"""
        return self.field_locations.get(field_name)


@dataclass
class ValidationResult:
    """
    バリデーション結果を表すクラス

    Attributes:
        is_valid: 検証が成功したかどうか
        error_message: エラーメッセージ（検証失敗時）
        error_fields: エラーが発生したフィールドのリスト
        error_locations: エラーが発生したセル位置のリスト
        severity: エラーの重要度（"error", "warning"など）
        rule_name: エラーが発生したルール名（オプショナル）
    """

    is_valid: bool
    error_message: Optional[str] = None
    error_fields: Optional[List[str]] = None
    error_locations: Optional[List[str]] = None
    severity: str = "error"
    rule_name: Optional[str] = None

    def __post_init__(self):
        # error_fieldsが指定されていない場合は空のリストに初期化
        if not self.is_valid and self.error_fields is None:
            self.error_fields = []
        # error_locationsが指定されていない場合は空のリストに初期化
        if not self.is_valid and self.error_locations is None:
            self.error_locations = []


class IExpression(ABC):
    """バリデーション式のインターフェース"""

    @abstractmethod
    def validate(self, context: ValidationContext, error_message_template: str) -> ValidationResult:
        """
        ルール式の検証を行い結果を返す

        Args:
            context: バリデーションコンテキスト
            error_message_template: エラーメッセージのテンプレート

        Returns:
            ValidationResult: 検証結果
        """
        pass
