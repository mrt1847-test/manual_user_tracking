import copy
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger(__name__)

_GOODSCODE_PARAM_KEYS = ("goodscode", "goodsCode", "goods_code", "goodscd", "goodsCd")
_PDP_CLICK_TYPES = (
    "PDP Buynow Click",
    "PDP ATC Click",
    "PDP Gift Click",
    "PDP Join Click",
    "PDP Rental Click",
)


class NetworkTracker:
    """수동 검증 도구에서 사용하는 경량 payload 파서/검증기."""

    def __init__(self, page: Optional[object] = None):
        self.page = page
        self.logs: List[Dict[str, Any]] = []

    def add_log(self, log: Dict[str, Any]) -> None:
        self.logs.append(log)

    def clear_logs(self) -> None:
        self.logs.clear()

    def get_logs(self, request_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if request_type:
            return [log for log in self.logs if log.get("type") == request_type]
        return self.logs.copy()

    def get_pv_logs(self) -> List[Dict[str, Any]]:
        return self.get_logs("PV")

    def _classify_request_type(self, url: str, payload: Optional[Dict[str, Any]] = None) -> str:
        url_lower = url.lower()

        if "/pdp.buynow.click" in url_lower:
            return "PDP Buynow Click"
        if "/pdp.atc.click" in url_lower:
            return "PDP ATC Click"
        if "/pdp.gift.click" in url_lower:
            return "PDP Gift Click"
        if "/pdp.join.click" in url_lower:
            return "PDP Join Click"
        if "/pdp.rental.click" in url_lower:
            return "PDP Rental Click"
        if "/product.atc.click" in url_lower:
            return "Product ATC Click"
        if "/product.click.event" in url_lower:
            return "Product Click"
        if "/product.minidetail.event" in url_lower:
            return "Product Minidetail"
        if "/module.exposure.event" in url_lower:
            return "Module Exposure"
        if "/product.exposure.event" in url_lower:
            return "Product Exposure"

        if "gif" in url_lower:
            if payload and isinstance(payload, dict):
                if str(payload.get("_p_ispdp")) == "1":
                    return "PDP PV"
                if str(payload.get("_p_typ", "")).lower() == "pdp":
                    return "PDP PV"

                decoded_gokey = payload.get("decoded_gokey", {})
                if isinstance(decoded_gokey, dict):
                    params = decoded_gokey.get("params", {})
                    if isinstance(params, dict) and params.get("_p_prod"):
                        return "PDP PV"
                    if self._find_value_for_validation(decoded_gokey, "_p_prod") is not None:
                        return "PDP PV"

                if payload.get("_p_prod"):
                    return "PDP PV"
            return "PV"

        if "exposure" in url_lower:
            return "Exposure"
        if "click" in url_lower or "tap" in url_lower:
            return "Click"
        return "Unknown"

    def _decode_utlogmap(self, utlogmap_str: str) -> Optional[Dict[str, Any]]:
        decoded = utlogmap_str
        for _ in range(3):
            try:
                decoded = unquote(decoded)
                return json.loads(decoded)
            except json.JSONDecodeError:
                continue
            except Exception as exc:
                logger.debug(f"utLogMap 디코딩 실패: {exc}")
                break
        return None

    def _decode_params_exp_or_clk(self, params_str: str) -> Dict[str, Any]:
        decoded_params: Dict[str, Any] = {}
        if not params_str:
            return decoded_params

        try:
            decoded = unquote(params_str)
            for item in decoded.split("&"):
                if "=" not in item:
                    continue
                key, value = item.split("=", 1)
                decoded_key = unquote(key)
                decoded_value = unquote(value)

                if decoded_key == "utLogMap":
                    decoded_params[decoded_key] = {
                        "raw": decoded_value,
                        "parsed": self._decode_utlogmap(decoded_value),
                    }
                else:
                    decoded_params[decoded_key] = decoded_value
        except Exception as exc:
            logger.debug(f"params-exp/clk 디코딩 중 오류: {exc}")
            decoded_params["_raw"] = params_str

        return decoded_params

    def _decode_expdata(self, expdata_str: str) -> Optional[List[Dict[str, Any]]]:
        try:
            expdata = json.loads(expdata_str)
        except Exception as exc:
            logger.debug(f"expdata 디코딩 중 오류: {exc}")
            return None

        if not isinstance(expdata, list):
            return None

        decoded_items = []
        for item in expdata:
            decoded_item = item.copy() if isinstance(item, dict) else {}
            if isinstance(item, dict) and isinstance(item.get("exargs"), dict):
                decoded_exargs = item["exargs"].copy()

                if "params-exp" in item["exargs"]:
                    params_exp_raw = item["exargs"]["params-exp"]
                    decoded_exargs["params-exp"] = {
                        "raw": params_exp_raw,
                        "parsed": self._decode_params_exp_or_clk(str(params_exp_raw)),
                    }

                if "params-clk" in item["exargs"]:
                    params_clk_raw = item["exargs"]["params-clk"]
                    decoded_exargs["params-clk"] = {
                        "raw": params_clk_raw,
                        "parsed": self._decode_params_exp_or_clk(str(params_clk_raw)),
                    }

                decoded_item["exargs"] = decoded_exargs
            decoded_items.append(decoded_item)

        return decoded_items

    def _parse_json_param(self, value: str) -> Optional[Any]:
        if not value or not isinstance(value, str):
            return None

        decoded = value
        for _ in range(3):
            try:
                decoded = unquote(decoded)
                parsed = json.loads(decoded, strict=False)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                continue
        return None

    def _looks_like_json_string(self, value: str) -> bool:
        if not value or not isinstance(value, str):
            return False
        stripped = value.strip()
        if stripped.startswith(("[", "{")):
            return True
        try:
            return unquote(value).strip().startswith(("[", "{"))
        except Exception:
            return False

    def _decode_gokey(self, gokey: str) -> Dict[str, Any]:
        decoded_data: Dict[str, Any] = {}

        try:
            decoded_gokey = unquote(gokey)
            decoded_data["decoded_gokey"] = decoded_gokey

            params: Dict[str, Any] = {}
            tokens = decoded_gokey.split("&")
            idx = 0
            while idx < len(tokens):
                item = tokens[idx]
                if "=" not in item:
                    idx += 1
                    continue

                key, value = item.split("=", 1)
                decoded_key = unquote(key)
                decoded_value = unquote(value)

                if decoded_key == "expdata" and decoded_value.strip().startswith("["):
                    while value.count("[") != value.count("]") and idx + 1 < len(tokens):
                        idx += 1
                        value += "&" + tokens[idx]
                    decoded_value = unquote(value)
                    params[decoded_key] = {
                        "raw": decoded_value,
                        "parsed": self._decode_expdata(decoded_value),
                    }
                    idx += 1
                    continue

                if decoded_key in ("params-clk", "params-exp"):
                    while idx + 1 < len(tokens):
                        next_token = tokens[idx + 1]
                        if "=" in next_token:
                            next_key = next_token.split("=", 1)[0]
                            if next_key and len(unquote(next_key)) <= 20 and not next_key.strip().startswith("["):
                                break
                        value += "&" + next_token
                        idx += 1
                    decoded_value = unquote(value)
                    params[decoded_key] = {
                        "raw": decoded_value,
                        "parsed": self._decode_params_exp_or_clk(decoded_value),
                    }
                    idx += 1
                    continue

                if self._looks_like_json_string(decoded_value):
                    parsed_any = self._parse_json_param(decoded_value)
                    params[decoded_key] = {"raw": decoded_value, "parsed": parsed_any} if parsed_any is not None else decoded_value
                else:
                    params[decoded_key] = decoded_value
                idx += 1

            decoded_data["params"] = params
        except Exception as exc:
            logger.warning(f"gokey 디코딩 중 오류 발생: {exc}")
            decoded_data["error"] = str(exc)
            decoded_data["raw"] = gokey

        return decoded_data

    def _decode_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return payload

        decoded_payload = payload.copy()
        if payload.get("gokey"):
            try:
                decoded_payload["decoded_gokey"] = self._decode_gokey(str(payload["gokey"]))
            except Exception as exc:
                logger.warning(f"gokey 디코딩 실패: {exc}")

        decoded_gokey = decoded_payload.get("decoded_gokey") or {}
        params = decoded_gokey.get("params") or {}
        if not params.get("expdata") and payload.get("expdata"):
            raw_exp = payload["expdata"]
            if isinstance(raw_exp, str):
                parsed_exp = self._decode_expdata(raw_exp)
            elif isinstance(raw_exp, list):
                parsed_exp = raw_exp
            else:
                parsed_exp = None

            if parsed_exp is not None:
                if not isinstance(decoded_payload.get("decoded_gokey"), dict):
                    decoded_payload["decoded_gokey"] = decoded_gokey if decoded_gokey else {}
                decoded_payload["decoded_gokey"].setdefault("params", {})["expdata"] = {
                    "raw": raw_exp if isinstance(raw_exp, str) else json.dumps(raw_exp, ensure_ascii=False),
                    "parsed": parsed_exp,
                }

        return decoded_payload

    def _parse_query_string(self, query_string: str) -> Dict[str, Any]:
        parsed_params: Dict[str, Any] = {}
        if not query_string:
            return parsed_params

        try:
            for item in query_string.split("&"):
                if "=" not in item:
                    continue
                key, value = item.split("=", 1)
                decoded_key = unquote(key)
                decoded_value = unquote(value)
                if decoded_key == "gokey" and decoded_value:
                    parsed_params[decoded_key] = decoded_value
                    parsed_params["decoded_gokey"] = self._decode_gokey(decoded_value)
                else:
                    parsed_params[decoded_key] = decoded_value
        except Exception as exc:
            logger.debug(f"쿼리 문자열 파싱 중 오류: {exc}")
            parsed_params["_raw"] = query_string

        return parsed_params

    def _parse_delimited_key_value_payload(self, payload_text: str) -> Dict[str, Any]:
        parsed_params: Dict[str, Any] = {}
        if not payload_text:
            return parsed_params

        segments = re.split(r"(?:,\s*|\r?\n)+(?=[A-Za-z0-9_.-]+=)", payload_text.strip())
        for segment in segments:
            if "=" not in segment:
                continue
            key, value = segment.split("=", 1)
            decoded_key = unquote(key.strip())
            decoded_value = unquote(value.strip())
            parsed_params[decoded_key] = decoded_value

        if parsed_params.get("gokey"):
            parsed_params["decoded_gokey"] = self._decode_gokey(str(parsed_params["gokey"]))

        return parsed_params

    def _parse_payload(self, post_data: Optional[str]) -> Any:
        if not post_data:
            return None

        try:
            parsed = json.loads(post_data)
            if isinstance(parsed, dict):
                return self._decode_payload(parsed)
            return parsed
        except (json.JSONDecodeError, TypeError):
            if "&" in post_data and "=" in post_data:
                try:
                    return self._parse_query_string(post_data)
                except Exception as exc:
                    logger.debug(f"쿼리 문자열 파싱 실패: {exc}")
            if "=" in post_data:
                try:
                    return self._parse_delimited_key_value_payload(post_data)
                except Exception as exc:
                    logger.debug(f"구분자 기반 key=value 파싱 실패: {exc}")
            return post_data

    @classmethod
    def parse_raw_payload(cls, raw_payload: Optional[str]) -> Any:
        tracker = cls()
        return tracker._parse_payload(raw_payload)

    @classmethod
    def build_manual_log(
        cls,
        raw_payload: Optional[str],
        event_type: Optional[str] = None,
        url: str = "manual://payload",
    ) -> Dict[str, Any]:
        tracker = cls()
        parsed_payload = tracker._parse_payload(raw_payload)
        inferred_type = event_type or tracker._classify_request_type(url, parsed_payload)
        return {
            "type": inferred_type,
            "url": url,
            "payload": parsed_payload,
            "timestamp": time.time(),
            "method": "MANUAL",
        }

    def _extract_goodscode_from_url_like_string(self, url_str: str) -> Optional[str]:
        if not url_str:
            return None
        try:
            query = parse_qs(urlparse(unquote(url_str)).query)
        except Exception:
            return None
        for key in _GOODSCODE_PARAM_KEYS:
            values = query.get(key)
            if values and values[0]:
                return str(values[0])
        return None

    def _find_value_recursive(self, obj: Any, target_keys: List[str], visited: Optional[set] = None) -> Optional[str]:
        if visited is None:
            visited = set()

        if isinstance(obj, (dict, list)):
            obj_id = id(obj)
            if obj_id in visited:
                return None
            visited.add(obj_id)

        try:
            if isinstance(obj, dict):
                for key in target_keys:
                    if key in obj and obj[key] not in (None, ""):
                        return str(obj[key])

                if "parsed" in obj and obj["parsed"] is not None:
                    result = self._find_value_recursive(obj["parsed"], target_keys, visited)
                    if result:
                        return result

                for value in obj.values():
                    result = self._find_value_recursive(value, target_keys, visited)
                    if result:
                        return result

            elif isinstance(obj, list):
                for item in obj:
                    result = self._find_value_recursive(item, target_keys, visited)
                    if result:
                        return result
        finally:
            if isinstance(obj, (dict, list)):
                visited.discard(id(obj))

        return None

    def extract_goodscode(self, log: Dict[str, Any]) -> Optional[str]:
        payload = log.get("payload")
        if not isinstance(payload, dict):
            return None

        for key in ("x_object_id", "_p_prod", *_GOODSCODE_PARAM_KEYS):
            value = payload.get(key)
            if value not in (None, ""):
                return str(value)

        decoded_gokey = payload.get("decoded_gokey", {})
        if decoded_gokey:
            for keys in (["_p_prod"], ["x_object_id"], list(_GOODSCODE_PARAM_KEYS)):
                result = self._find_value_recursive(decoded_gokey, keys)
                if result:
                    return result

        for candidate in (payload.get("_p_url"), log.get("url")):
            if isinstance(candidate, str):
                result = self._extract_goodscode_from_url_like_string(candidate)
                if result:
                    return result

        return None

    def get_logs_by_goodscode(self, goodscode: str, request_type: Optional[str] = None) -> List[Dict[str, Any]]:
        filtered_logs = self.get_logs(request_type)
        result = []

        for log in filtered_logs:
            extracted_goodscode = self.extract_goodscode(log)
            if extracted_goodscode and str(extracted_goodscode) == str(goodscode):
                result.append(log)
            elif request_type in _PDP_CLICK_TYPES and extracted_goodscode is None:
                result.append(log)

        return result

    def get_pv_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "PV") + self.get_logs_by_goodscode(goodscode, "PDP PV")

    def get_pdp_pv_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "PDP PV")

    def get_product_click_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "Product Click")

    def get_product_atc_click_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "Product ATC Click")

    def get_product_minidetail_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "Product Minidetail")

    def get_pdp_buynow_click_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "PDP Buynow Click")

    def get_pdp_atc_click_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "PDP ATC Click")

    def get_pdp_gift_click_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "PDP Gift Click")

    def get_pdp_join_click_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "PDP Join Click")

    def get_pdp_rental_click_logs_by_goodscode(self, goodscode: str) -> List[Dict[str, Any]]:
        return self.get_logs_by_goodscode(goodscode, "PDP Rental Click")

    def _find_spm_recursive(self, obj: Any, visited: Optional[set] = None) -> Optional[str]:
        if visited is None:
            visited = set()

        if isinstance(obj, (dict, list)):
            obj_id = id(obj)
            if obj_id in visited:
                return None
            visited.add(obj_id)

        try:
            if isinstance(obj, dict):
                if "spm" in obj and obj["spm"]:
                    return str(obj["spm"])
                for value in obj.values():
                    result = self._find_spm_recursive(value, visited)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = self._find_spm_recursive(item, visited)
                    if result is not None:
                        return result
        finally:
            if isinstance(obj, (dict, list)):
                visited.discard(id(obj))

        return None

    def _extract_spm_from_log(self, log: Dict[str, Any]) -> Optional[str]:
        payload = log.get("payload")
        if not isinstance(payload, dict):
            return None

        decoded_gokey = payload.get("decoded_gokey", {})
        if isinstance(decoded_gokey, dict):
            params = decoded_gokey.get("params", {})
            if isinstance(params, dict) and params.get("spm"):
                return str(params["spm"])

        return self._find_spm_recursive(payload)

    def _check_spm_match(self, log_spm: str, target_spm: str) -> bool:
        if not log_spm or not target_spm:
            return False
        if log_spm == target_spm:
            return True
        if log_spm.startswith(target_spm + "."):
            return True
        if target_spm.startswith(log_spm + "."):
            return True
        return False

    def get_module_exposure_logs_by_spm(self, spm: str) -> List[Dict[str, Any]]:
        filtered_logs = []
        for log in self.get_logs("Module Exposure"):
            log_spm = self._extract_spm_from_log(log)
            if log_spm and self._check_spm_match(log_spm, spm):
                filtered_logs.append(log)
        return filtered_logs

    def _extract_spm_from_product_exposure_item(self, item: Dict[str, Any]) -> Optional[str]:
        if not isinstance(item, dict):
            return None
        if item.get("spm"):
            return str(item["spm"])
        return self._find_spm_recursive(item)

    def get_product_exposure_logs_by_goodscode(self, goodscode: str, spm: Optional[str] = None) -> List[Dict[str, Any]]:
        if not spm:
            return self.get_logs_by_goodscode(goodscode, "Product Exposure")

        logs = self.get_logs("Product Exposure")
        filtered_logs = []

        for log in logs:
            filtered_log = copy.deepcopy(log)
            payload = filtered_log.get("payload", {})
            decoded_gokey = payload.get("decoded_gokey", {}) or {}
            params = decoded_gokey.get("params", {}) if isinstance(decoded_gokey, dict) else {}
            expdata = params.get("expdata", {}) if isinstance(params, dict) else {}

            if (not expdata or not expdata.get("parsed")) and isinstance(payload, dict) and payload.get("expdata"):
                raw_exp = payload["expdata"]
                if isinstance(raw_exp, str):
                    parsed_fallback = self._decode_expdata(raw_exp) or []
                elif isinstance(raw_exp, list):
                    parsed_fallback = raw_exp
                else:
                    parsed_fallback = []

                if not isinstance(decoded_gokey, dict):
                    payload["decoded_gokey"] = {}
                    decoded_gokey = payload["decoded_gokey"]
                decoded_gokey.setdefault("params", {})["expdata"] = {
                    "raw": raw_exp if isinstance(raw_exp, str) else json.dumps(raw_exp, ensure_ascii=False),
                    "parsed": parsed_fallback,
                }
                expdata = decoded_gokey["params"]["expdata"]

            filtered_items = []
            if isinstance(expdata, dict) and isinstance(expdata.get("parsed", []), list):
                for item in expdata["parsed"]:
                    item_spm = self._extract_spm_from_product_exposure_item(item)
                    if not item_spm or not self._check_spm_match(item_spm, spm):
                        continue

                    item_goodscode = None
                    if isinstance(item, dict) and isinstance(item.get("exargs"), dict):
                        params_exp = item["exargs"].get("params-exp", {})
                        if isinstance(params_exp, dict) and isinstance(params_exp.get("parsed"), dict):
                            parsed = params_exp["parsed"]
                            item_goodscode = parsed.get("_p_prod")
                            if not item_goodscode and isinstance(parsed.get("utLogMap"), dict):
                                utlogmap_parsed = parsed["utLogMap"].get("parsed")
                                if isinstance(utlogmap_parsed, dict):
                                    item_goodscode = utlogmap_parsed.get("x_object_id")

                    if item_goodscode and str(item_goodscode) == str(goodscode):
                        filtered_items.append(item)

            if filtered_items:
                expdata["parsed"] = filtered_items
                filtered_logs.append(filtered_log)

        return filtered_logs

    def get_product_exposure_logs_by_spm(self, spm: str) -> List[Dict[str, Any]]:
        logs = self.get_logs("Product Exposure")
        filtered_logs = []

        for log in logs:
            filtered_log = copy.deepcopy(log)
            payload = filtered_log.get("payload", {})
            decoded_gokey = payload.get("decoded_gokey", {}) or {}
            params = decoded_gokey.get("params", {}) if isinstance(decoded_gokey, dict) else {}
            expdata = params.get("expdata", {}) if isinstance(params, dict) else {}

            filtered_items = []
            if isinstance(expdata, dict) and isinstance(expdata.get("parsed", []), list):
                for item in expdata["parsed"]:
                    item_spm = self._extract_spm_from_product_exposure_item(item)
                    if item_spm and self._check_spm_match(item_spm, spm):
                        filtered_items.append(item)

            if filtered_items:
                expdata["parsed"] = filtered_items
                filtered_logs.append(filtered_log)

        return filtered_logs

    def get_decoded_gokey_params(self, log: Dict[str, Any], param_key: Optional[str] = None) -> Dict[str, Any]:
        payload = log.get("payload")
        if not isinstance(payload, dict):
            return {}

        decoded_gokey = payload.get("decoded_gokey", {})
        params = decoded_gokey.get("params", {}) if isinstance(decoded_gokey, dict) else {}
        if param_key:
            return params.get(param_key, {})
        return params

    def _find_value_for_validation(self, obj: Any, target_key: str, visited: Optional[set] = None) -> Optional[Any]:
        if visited is None:
            visited = set()

        if isinstance(obj, (dict, list)):
            obj_id = id(obj)
            if obj_id in visited:
                return None
            visited.add(obj_id)

        array_index_match = re.match(r"^(.+)\[(\d+)\]$", target_key)
        if array_index_match:
            base_key, index_str = array_index_match.group(1), array_index_match.group(2)
            idx = int(index_str)
            base_value = self._find_value_for_validation(obj, base_key, visited)
            if base_value is not None and isinstance(base_value, list) and 0 <= idx < len(base_value):
                return base_value[idx]

        if isinstance(obj, dict):
            if target_key in obj:
                return obj[target_key]

            if "parsed" in obj and isinstance(obj["parsed"], (dict, list)):
                result = self._find_value_for_validation(obj["parsed"], target_key, visited)
                if result is not None:
                    return result

            for value in obj.values():
                if isinstance(value, str) and value.strip().startswith(("{", "[")):
                    try:
                        parsed = json.loads(value)
                        result = self._find_value_for_validation(parsed, target_key, visited)
                        if result is not None:
                            return result
                    except (json.JSONDecodeError, TypeError):
                        pass

                result = self._find_value_for_validation(value, target_key, visited)
                if result is not None:
                    return result

        elif isinstance(obj, list):
            for item in obj:
                result = self._find_value_for_validation(item, target_key, visited)
                if result is not None:
                    return result

        if isinstance(obj, (dict, list)):
            visited.discard(id(obj))

        return None

    def _validate_payload_fields(
        self,
        payload: Dict[str, Any],
        expected_data: Dict[str, Any],
        goodscode: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
        field_results: List[Dict[str, Any]] = []
        passed_fields: Dict[str, Any] = {}
        errors: List[str] = []

        for key, expected_value in expected_data.items():
            actual_value = payload.get(key) if event_type == "PDP PV" else self._find_value_for_validation(payload, key)
            field_passed = False
            message = ""

            if isinstance(expected_value, str) and expected_value == "__SKIP__":
                actual_value = "(skip)"
                field_passed = True
                message = "검증 스킵"
            elif isinstance(expected_value, str) and expected_value == "":
                if actual_value is None or (isinstance(actual_value, str) and actual_value == ""):
                    field_passed = True
                else:
                    message = f'기대값 (빈 문자열): "", 실제값: {actual_value}'
            elif actual_value is None:
                message = "키에 해당하는 값이 없습니다."
            elif isinstance(expected_value, str) and expected_value == "__MANDATORY__":
                if actual_value is None or (isinstance(actual_value, str) and actual_value.strip() == ""):
                    message = "mandatory 필드이지만 값이 비어있습니다."
                else:
                    field_passed = True
            elif isinstance(expected_value, list):
                if actual_value in expected_value:
                    field_passed = True
                else:
                    message = f"기대값 (리스트 중 하나): {expected_value}, 실제값: {actual_value}"
            else:
                # ab_buckets: 스키마 비어있으면 실제도 비어있어야 PASS; 스키마에 값 있으면 실제값에 스키마 값이 포함되면 PASS
                if key == "ab_buckets" and isinstance(expected_value, str) and expected_value.strip() != "":
                    if actual_value is not None and isinstance(actual_value, str):
                        exp = expected_value.strip()
                        act = actual_value.strip()
                        if exp in act or act == exp:
                            field_passed = True
                        else:
                            message = f"기대값(포함 검증): 실제값에 '{expected_value}'이 포함되어야 합니다. 실제값: {actual_value}"
                    else:
                        message = f"기대값(포함 검증): 실제값에 '{expected_value}'이 포함되어야 합니다. 실제값: {actual_value}"
                elif key == "ab_buckets" and (expected_value is None or (isinstance(expected_value, str) and expected_value.strip() == "")):
                    # 스키마가 비어있으면 실제도 비어있어야 함 (위 빈 문자열 분기에서 이미 처리되나, actual이 다른 타입이면 명시)
                    if actual_value is None or (isinstance(actual_value, str) and actual_value.strip() == ""):
                        field_passed = True
                    else:
                        message = f'기대값 (빈 문자열): "", 실제값: {actual_value}'
                elif key in {"spm", "spm-url", "spm-pre", "spm-cnt"} and isinstance(expected_value, str) and isinstance(actual_value, str):
                    expected_normalized = re.sub(r"\d+$", "", expected_value)
                    actual_normalized = re.sub(r"\d+$", "", actual_value)
                    if (
                        expected_normalized == actual_normalized
                        or expected_normalized in actual_normalized
                        or expected_value in actual_value
                    ):
                        field_passed = True
                    else:
                        message = f"기대값 (포함 여부): {expected_value}, 실제값: {actual_value}"
                elif key == "query" and isinstance(expected_value, str) and isinstance(actual_value, str):
                    if expected_value.strip().lower() == actual_value.strip().lower():
                        field_passed = True
                    else:
                        message = f"기대값: {expected_value}, 실제값: {actual_value}"
                elif str(expected_value) == str(actual_value) or actual_value == expected_value:
                    field_passed = True
                else:
                    message = f"기대값: {expected_value}, 실제값: {actual_value}"

            field_results.append(
                {
                    "field": key,
                    "status": "PASS" if field_passed else "FAIL",
                    "expected": expected_value,
                    "actual": actual_value,
                    "message": message,
                }
            )

            if field_passed:
                passed_fields[key] = {
                    "expected": expected_value,
                    "actual": actual_value,
                }
            else:
                errors.append(f"키 '{key}' {message}")

        return field_results, passed_fields, errors

    def validate_payload_detailed(
        self,
        log: Dict[str, Any],
        expected_data: Dict[str, Any],
        goodscode: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = log.get("payload")
        if payload is None:
            raise AssertionError(f"로그에 payload가 없습니다. URL: {log.get('url')}")
        if isinstance(payload, str):
            raise AssertionError(
                f"payload가 JSON 형식이 아닙니다. "
                f"URL: {log.get('url')}, Payload: {payload[:100]}..."
            )
        if not isinstance(payload, dict):
            raise AssertionError(
                f"payload가 딕셔너리 형식이 아닙니다. "
                f"URL: {log.get('url')}, Payload 타입: {type(payload)}"
            )

        field_results, passed_fields, errors = self._validate_payload_fields(
            payload=payload,
            expected_data=expected_data,
            goodscode=goodscode,
            event_type=event_type,
        )
        decoded_info = payload.get("decoded_gokey", {})

        return {
            "success": not errors,
            "field_results": field_results,
            "passed_fields": passed_fields,
            "errors": errors,
            "decoded_params": decoded_info.get("params", {}) if isinstance(decoded_info, dict) else {},
        }

    def validate_payload(
        self,
        log: Dict[str, Any],
        expected_data: Dict[str, Any],
        goodscode: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        detailed_result = self.validate_payload_detailed(log, expected_data, goodscode, event_type)
        if detailed_result["errors"]:
            error_msg = "\n".join(detailed_result["errors"])
            raise AssertionError(
                f"Payload 검증 실패:\n{error_msg}\n"
                f"디코딩된 gokey 파라미터: {json.dumps(detailed_result['decoded_params'], ensure_ascii=False, indent=2)}"
            )
        return True, detailed_result["passed_fields"]
