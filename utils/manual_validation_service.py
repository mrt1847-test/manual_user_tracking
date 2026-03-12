import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.NetworkTracker import NetworkTracker
from utils.validation_helpers import (
    EVENT_TYPE_CONFIG_KEY_MAP,
    MINIDETAIL_PRICE_EXCLUDE_FIELDS,
    build_expected_from_module_config,
    load_module_config,
)


_NTH_PATTERN = re.compile(r"^(?P<base>.+)\((?P<nth>\d+)\)$")
_SPM_PLATFORM_PREFIX_MAP = {
    "pc": "gmktpc",
    "mweb": "gmktm",
    "app": "gmktapp",
}
_SPM_AREA_SEGMENT_MAP = {
    "SRP": "searchlist",
    "LP": "searchlistcategory",
    "PDP": "pdp",
}
_EVENT_TYPES_WITH_OPTIONAL_GOODSCODE = {
    "PV",
    "Module Exposure",
}


@dataclass
class ManualValidationInput:
    platform: str = "mweb"
    environment: str = ""
    area: str = ""
    module_title: str = ""
    nth: Optional[str] = None
    event_type: str = ""
    goodscode: str = ""
    keyword: str = ""
    category_id: str = ""
    is_ad: str = ""
    origin_price: str = ""
    promotion_price: str = ""
    coupon_price: str = ""
    payload_raw: str = ""
    request_url: str = "manual://payload"


@dataclass
class ManualValidationResult:
    success: bool
    summary: Dict[str, int]
    field_results: List[Dict[str, Any]]
    errors: List[str]
    parsed_payload: Any
    expected_fields: Dict[str, Any]
    decoded_params: Dict[str, Any]
    module_config_path: str
    schema_preview: str
    event_type: str
    area: str
    module_title: str
    nth: Optional[str] = None


class ManualValidationService:
    def __init__(self, schema_root: Optional[Path] = None):
        self.schema_root = schema_root or (Path(__file__).resolve().parent.parent / "tracking_schemas")
        self._config_path = Path(__file__).resolve().parent.parent / "config.json"

    def get_default_environment(self) -> str:
        try:
            with open(self._config_path, "r", encoding="utf-8") as file:
                config = json.load(file)
        except FileNotFoundError:
            return "prod"
        return str(config.get("environment", "prod"))

    def list_areas(self) -> List[str]:
        if not self.schema_root.exists():
            return []
        return sorted(
            path.name
            for path in self.schema_root.iterdir()
            if path.is_dir() and not path.name.startswith("_")
        )

    def list_modules(self, area: str) -> List[str]:
        area_path = self.schema_root / area
        if not area_path.exists():
            return []

        modules = set()
        for path in area_path.glob("*.json"):
            if path.stem.startswith("_"):
                continue
            match = _NTH_PATTERN.match(path.stem)
            modules.add(match.group("base") if match else path.stem)
        return sorted(modules)

    def list_nth_values(self, area: str, module_title: str) -> List[str]:
        area_path = self.schema_root / area
        if not area_path.exists():
            return []

        nth_values = []
        for path in area_path.glob(f"{module_title}(*).json"):
            match = _NTH_PATTERN.match(path.stem)
            if match and match.group("base") == module_title:
                nth_values.append(match.group("nth"))
        return sorted(set(nth_values), key=lambda value: int(value))

    def list_event_types(self, area: str, module_title: str, nth: Optional[str] = None) -> List[str]:
        module_config = self.load_module_config_with_path(area, module_title, nth)["config"]
        events = []
        for event_type, config_key in EVENT_TYPE_CONFIG_KEY_MAP.items():
            if config_key in module_config:
                events.append(event_type)
        return events

    def load_module_config_with_path(
        self,
        area: str,
        module_title: str,
        nth: Optional[str] = None
    ) -> Dict[str, Any]:
        if not area:
            raise ValueError("영역(area)을 선택해주세요.")
        if not module_title:
            raise ValueError("모듈(module_title)을 선택해주세요.")

        area_path = self.schema_root / area
        if not area_path.exists():
            raise ValueError(f"존재하지 않는 영역입니다: {area}")

        config_path = area_path / f"{module_title}.json"
        if nth is not None and str(nth).strip():
            nth_path = area_path / f"{module_title}({nth}).json"
            if nth_path.exists():
                config_path = nth_path

        module_config = load_module_config(area=area, module_title=module_title, nth=nth)
        if not module_config:
            raise ValueError(f"스키마 파일을 찾을 수 없습니다: {config_path}")

        return {
            "config": module_config,
            "path": str(config_path),
        }

    def get_schema_preview(
        self,
        area: str,
        module_title: str,
        nth: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> str:
        loaded = self.load_module_config_with_path(area, module_title, nth)
        module_config = loaded["config"]
        if event_type:
            config_key = EVENT_TYPE_CONFIG_KEY_MAP.get(event_type)
            preview_target = module_config.get(config_key, {})
        else:
            preview_target = module_config
        return json.dumps(preview_target, ensure_ascii=False, indent=2)

    def validate(self, request: ManualValidationInput) -> ManualValidationResult:
        self._validate_required_fields(request)
        goodscode = request.goodscode.strip()
        goodscode_for_validation = goodscode or None

        loaded = self.load_module_config_with_path(request.area, request.module_title, request.nth)
        module_config = loaded["config"]
        config_key = EVENT_TYPE_CONFIG_KEY_MAP.get(request.event_type)
        if not config_key or config_key not in module_config:
            raise ValueError(f"선택한 모듈에 '{request.event_type}' 이벤트 정의가 없습니다.")

        environment = request.environment or self.get_default_environment()
        frontend_data = self._build_frontend_data(request)
        exclude_fields = self._get_exclude_fields(request.event_type)
        expected_fields = build_expected_from_module_config(
            module_config=module_config,
            event_type=request.event_type,
            goodscode=goodscode,
            frontend_data=frontend_data,
            exclude_fields=exclude_fields,
            environment_override=environment,
        )
        expected_fields = self._assemble_spm_fields(
            expected_fields=expected_fields,
            platform=request.platform,
            area=request.area,
            module_title=request.module_title,
        )

        manual_log = NetworkTracker.build_manual_log(
            raw_payload=request.payload_raw.strip(),
            event_type=request.event_type,
            url=request.request_url,
        )
        tracker = NetworkTracker(page=None)

        detailed_result = tracker.validate_payload_detailed(
            log=manual_log,
            expected_data=expected_fields,
            goodscode=goodscode_for_validation,
            event_type=request.event_type,
        )

        summary = self._build_summary(detailed_result["field_results"])
        schema_preview = json.dumps(module_config.get(config_key, {}), ensure_ascii=False, indent=2)
        return ManualValidationResult(
            success=detailed_result["success"],
            summary=summary,
            field_results=detailed_result["field_results"],
            errors=detailed_result["errors"],
            parsed_payload=manual_log["payload"],
            expected_fields=expected_fields,
            decoded_params=detailed_result["decoded_params"],
            module_config_path=loaded["path"],
            schema_preview=schema_preview,
            event_type=request.event_type,
            area=request.area,
            module_title=request.module_title,
            nth=request.nth,
        )

    def _validate_required_fields(self, request: ManualValidationInput) -> None:
        required_fields = {
            "environment": request.environment or self.get_default_environment(),
            "area": request.area,
            "module_title": request.module_title,
            "event_type": request.event_type,
            "payload_raw": request.payload_raw,
        }
        if request.event_type not in _EVENT_TYPES_WITH_OPTIONAL_GOODSCODE:
            required_fields["goodscode"] = request.goodscode
        missing = [name for name, value in required_fields.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"필수 입력값이 비어 있습니다: {', '.join(missing)}")

    def _build_frontend_data(self, request: ManualValidationInput) -> Optional[Dict[str, Any]]:
        frontend_data: Dict[str, Any] = {
            "platform": request.platform,
        }

        if request.keyword.strip():
            frontend_data["keyword"] = request.keyword.strip()
        if request.category_id.strip():
            frontend_data["category_id"] = request.category_id.strip()
        if request.is_ad.strip():
            frontend_data["is_ad"] = request.is_ad.strip()
        if request.origin_price.strip():
            frontend_data["origin_price"] = request.origin_price.strip()
        if request.promotion_price.strip():
            frontend_data["promotion_price"] = request.promotion_price.strip()
        if request.coupon_price.strip() or request.coupon_price == "":
            frontend_data["coupon_price"] = request.coupon_price.strip()

        return frontend_data or None

    def _get_exclude_fields(self, event_type: str) -> List[str]:
        if event_type == "Product Minidetail":
            return list(MINIDETAIL_PRICE_EXCLUDE_FIELDS)
        return []

    def _build_summary(self, field_results: List[Dict[str, Any]]) -> Dict[str, int]:
        total = len(field_results)
        passed = sum(1 for row in field_results if row.get("status") == "PASS")
        failed = total - passed
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
        }

    def _assemble_spm_fields(
        self,
        expected_fields: Dict[str, Any],
        platform: str,
        area: str,
        module_title: str
    ) -> Dict[str, Any]:
        assembled = dict(expected_fields)
        spm_value = assembled.get("spm")
        if isinstance(spm_value, str) and spm_value:
            assembled["spm"] = self._assemble_spm_value(
                raw_value=spm_value,
                platform=platform,
                area=area,
                module_title=module_title,
            )

        for field_name in ("spm-cnt", "spm-pre", "spm-url"):
            value = assembled.get(field_name)
            if isinstance(value, str) and value:
                assembled[field_name] = self._replace_spm_prefix_only(
                    raw_value=value,
                    platform=platform,
                )
        return assembled

    def _assemble_spm_value(
        self,
        raw_value: str,
        platform: str,
        area: str,
        module_title: str
    ) -> str:
        del module_title  # 현재는 schema suffix를 사용하고, 필요 시 모듈별 규칙으로 확장 가능

        parts = raw_value.split(".")
        if len(parts) < 3 or not parts[0].startswith("gmkt"):
            return raw_value

        platform_prefix = _SPM_PLATFORM_PREFIX_MAP.get((platform or "").strip().lower(), parts[0])
        area_segment = _SPM_AREA_SEGMENT_MAP.get((area or "").strip().upper(), parts[1])
        suffix = ".".join(parts[2:])
        return f"{platform_prefix}.{area_segment}.{suffix}"

    def _replace_spm_prefix_only(self, raw_value: str, platform: str) -> str:
        parts = raw_value.split(".")
        if len(parts) < 2 or not parts[0].startswith("gmkt"):
            return raw_value

        platform_prefix = _SPM_PLATFORM_PREFIX_MAP.get((platform or "").strip().lower(), parts[0])
        return ".".join([platform_prefix, *parts[1:]])


def pretty_json(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False, indent=2)
