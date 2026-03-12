# Manual Validation Tool

`pytest-bdd` 자동화 구조와 분리된 수동 트래킹 payload 검증 도구입니다.

## 포함 구조

```text
manual_validation_tool/
├── config.json
├── manual_validation_gui.py
├── requirements.txt
├── README.md
├── gui/
│   ├── __init__.py
│   └── manual_validator_app.py
├── utils/
│   ├── __init__.py
│   ├── NetworkTracker.py
│   ├── manual_validation_service.py
│   └── validation_helpers.py
└── tracking_schemas/
    ├── app/
    ├── pc/
    └── mweb/
```

이 폴더만 별도로 복사해서 새 프로젝트처럼 사용할 수 있습니다.

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python manual_validation_gui.py
```

## 시트 → JSON 변환

`manual_validation_tool/scripts/sheets_to_json.py`도 함께 포함되어 있어 이 폴더 안에서 바로 실행할 수 있습니다.

예시:

```bash
python scripts/sheets_to_json.py --platform mweb --area SRP --module "먼저 둘러보세요" --overwrite
python scripts/sheets_to_json.py --platform app --area SRP --sheet --overwrite
```

## 사용 방법

1. `플랫폼`, `환경`, `영역`, `모듈`, `nth`, `이벤트`를 선택합니다.
2. 선택한 `플랫폼` 기준으로 `tracking_schemas/{platform}/{area}` 하위 스키마가 로드됩니다.
3. `상품번호`, 검색어/카테고리, 광고 여부, 가격 정보를 필요에 따라 입력합니다.
4. raw payload 원문을 붙여넣습니다.
5. `검증 실행`을 누르면 필드별 `PASS/FAIL` 결과를 확인할 수 있습니다.

## 참고

- `tracking_schemas`는 원본 프로젝트 기준 스키마 복사본입니다.
- 스키마는 `tracking_schemas/app`, `tracking_schemas/pc`, `tracking_schemas/mweb`로 분리되며 GUI의 `플랫폼` 선택값과 연동됩니다.
- `config.json`의 `environment` 값은 `<environment>` placeholder 치환 기본값으로 사용됩니다.
- `config.json`의 `spreadsheet_id`는 `scripts/sheets_to_json.py` 실행에 사용됩니다.
- `spm`은 수동 도구에서 `platform + area + schema suffix` 조합으로 재구성됩니다.
- `spm-cnt`, `spm-pre`, `spm-url`은 `tracking_schemas` 원문 값을 유지하되 맨 앞 환경 prefix(`gmktpc`, `gmktm`, `gmktapp`)만 대체합니다.
- 이 독립 도구는 `playwright` 없이 실행되도록 경량화되어 있습니다.
- 구글 시트 서비스 계정 JSON도 함께 복사해 두었습니다.
- 현재 구조는 수동 payload 검증 목적만 분리한 것이며, 기존 자동화 테스트 코드는 포함하지 않습니다.
