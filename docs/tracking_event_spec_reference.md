# Tracking Event Spec Reference

## Purpose
이 문서는 이벤트별 공식 스펙을 한곳에 모으고, `tracking_schemas`를 어떤 기준으로 작성할지 정의하는 기준 문서다. 현재 1차 범위는 `product_exposure`이며, 다른 이벤트는 공식 문서가 확보되는 대로 같은 형식으로 추가한다.

## Coverage Status
| Event | Official Spec Status | Schema Refresh Status | Notes |
|---|---|---|---|
| `product_exposure` | Ready | In progress | 이 문서에 공식 스펙과 대표 스키마 기준 정리 |
| `product_click` | Ready | In progress | 이 문서에 공식 스펙 추가 |
| `product_atc_click` | Ready | In progress | 이 문서에 공식 스펙 추가 |
| `module_exposure` | Ready (top-level) | In progress | top-level 공식 스펙 추가, 하위 파라미터는 후속 보강 |

## Shared Schema Authoring Rules
`tracking_schemas`의 공식 문서형 스키마는 아래 표현만 사용한다.

| Schema value | Meaning |
|---|---|
| `mandatory` | 값이 존재해야 함 |
| `""` | optional이며 empty 또는 null 허용 |
| fixed string | 값이 정확히 일치해야 함 |
| `skip` | 가급적 사용하지 않음. 공식 문서에 없는 필드는 제거를 우선 |

추가 원칙:
- 스키마는 공식 문서에 있는 필드만 유지한다.
- path나 raw payload 구조를 그대로 복제하지 않고, 문서가 정의한 논리 필드 중심으로 작성한다.
- Derived Rules는 기준 문서에는 남기되, 초기 스키마 값으로 직접 표현하지 않는다.
- 현재 검증기는 경로보다 필드명을 재귀 탐색하는 구조이므로, 스키마는 leaf field 중심으로 단순화한다.

## Product Exposure

### Top-level Params
| field | path | sample_value | description | empty_or_null_rule | required | search_arch | recommend_arch | clients |
|---|---|---|---|---|---|---|---|---|
| `spm` | `/` | `spma.b.c.d` | spm position of current slot | - | mandatory |  |  | App + Web |
| `spm-cnt` | `/` | `spma.b` | spm position of current page | - | mandatory |  |  | App + Web |
| `spm-url` | `/` | `url-spma.b.c.d` | source spm position | null when there is no previous page | optional |  |  | App + Web |
| `spm-pre` | `/` | `pre-spma.b.c.d` | source of source spm position | null when there is no previous-page chain | optional |  |  | App + Web |
| `cguid` | `/` | `cguid` | GMarket cguid | - | mandatory |  |  | App + Web |
| `pguid` | `/` | `pguid` | GMarket pguid | - | mandatory |  |  | App + Web |
| `sguid` | `/` | `sguid` | GMarket sguid | - | mandatory |  |  | App + Web |
| `_p_prod` | `/` | `item id` | goods code / item id | - | mandatory |  |  | App + Web |
| `_p_sku` | `/` | `0` | sku id (first option code) | - | mandatory |  |  | App + Web |
| `_p_catalog` | `/` | `catalog id` | catalog id of item | empty if item has no catalog | optional |  |  | App + Web |
| `_p_group` | `/` | `group id` | group id of item | empty if item has no group | optional |  |  | App + Web |
| `gmkt_page_id` | `/` | `page id` | GMarket page id | fixed as empty string | optional |  |  | App + Web |
| `gmkt_area_code` | `/` | `area_code` | GMarket area code | - | mandatory |  |  | App + Web |
| `section_index` | `/` | `0` | source tab index, starts from 0 | empty except Mobile Home section identification | optional |  |  | App + Web |
| `module_index` | `/` | `0` | source module index, starts from 0, may be non-continuous | - | mandatory |  |  | App + Web |
| `is_ad` | `/` | `Y / N` | `Y = ad traffic`, `N = organic traffic` | - | mandatory |  |  | App + Web |
| `channel_code` | `/` | `200000033` | jaehu_id in gmkt cookie | may be empty for about 15 percent traffic | optional |  |  | App + Web |
| `item_status` | `/` | `1 / -1` | `1 = normal`, `-1 = sold out` | only used in cart and vip | optional |  |  | App + Web |
| `ab_buckets` | `/` | `sceneID#layerID^version#bucketID` | AB test bucket info | empty if no experiment or user not assigned | optional |  |  | App + Web |
| `is_airticket` | `/` | `Y / N` | airticket flag | - | optional |  |  | App + Web |
| `utLogMap` | `/` | `URL-encoded JSON` | item component metadata from server side | non-item components do not contain this field | mandatory |  |  | App + Web |

### utLogMap Params
| field | sample_value | description | empty_or_null_rule | required | search_arch | recommend_arch |
|---|---|---|---|---|---|---|
| `scene` | `search / recommendation / campaign` | scene type | - | mandatory | Y | Y |
| `sub_scene` | `main_srp / rvi / lowprice / hpjfy / rpp_itemlist` | sub scene type | - | mandatory | Y | Y |
| `x_object_id` | `item id` | exposed item id | - | mandatory | Y | Y |
| `x_object_type` | `item / store / lp` | exposed card type | item cards are fixed as `item` | mandatory | Y | Y |
| `x_sku_id` | `0` | exposed sku id | fixed as `0` | mandatory | Y | Y |
| `pageIndex` | `0` | backend request page index, starts from 0 | ETC pages may use `0` | mandatory |  |  |
| `pagePos` | `0` | relative position within corresponding backend request, starts from 0 | resets for every backend request | mandatory |  |  |
| `pageSize` | `10` | total count of returned items in corresponding backend request | - | mandatory |  |  |
| `listno` | `0` | absolute position in current page-module | calculated as `pageIndex * pageSize + pagePos` | mandatory |  |  |
| `sort` | `popularity / order / priceasc / pricedesc / reviewcount / latest` | sort option for SRP and LP only | empty on non-search page | optional |  |  |
| `searchScenario` | `keyword / category / other / keyword-filter / category-filter / other-filter` | search scenario for SRP and LP only | empty on non-search page | optional |  |  |
| `query` | `dress` | search query for SRP only | empty on non-SRP page | optional |  |  |
| `pvid` | `7875da6bc08bfe1781960c6b74a855cd` | backend request unique id | - | mandatory | Y | Y |
| `pvid_sys` | `gmkt server / aidc server` | backend request source system | `gmkt` unless AIDC ABTest scenario | mandatory | Y | Y |
| `search_session_id` | `unique id` | unique id for one search instance | empty on non-search page | optional |  |  |
| `origin_price` | `45200` | exposed original price | may be empty in special domains | optional | Y | Y |
| `promotion_price` | `42220` | exposed promotion price | empty if there is no promotion price | optional | Y | Y |
| `coupon_price` | `40680` | exposed coupon price | empty if there is no coupon price | optional | Y | Y |
| `trafficType` | `organic / ad` | traffic type | - | mandatory | Y | Y |
| `adProduct` | `N / J` | ad product type; `N = search ads`, `J = recommendation ads` | empty if non-ad | optional | Y | Y |
| `adSubProduct` | `F / A` | ad sub product type; `A = power click`, `F = ai boost` | empty if non-ad | optional | Y | Y |
| `seed_item_id` | `item id` | seed item id for recommendation scenes | empty for non-seed modules | optional |  | Y |
| `seed_item_index` | `0` | seed item index, starts from 0 | empty for non-seed modules | optional |  | Y |
| `seed_item_keyword` | `keyword` | seed item keyword | empty for non-seed modules | optional |  | Y |
| `ab_buckets` | `sceneID#layerID^version#bucketID` | AB test bucket info | empty if no experiment or user not assigned | optional | Y | Y |
| `childConfigId` | `1753066336000` | timestamp of effectiveness of low-priced items | only for recommended low-price item modules | optional |  | Y |
| `self_ab_id` | `abtest id` | internal AIDC recommend engine AB test id | only for AIDC scenarios such as `rvi`, `lowprice`, `vip_vt`, `vip_bt` | optional |  | Y |
| `match_type` | `keywords2i` | algorithm recall type from AIDC engine | only for AIDC scenarios such as `rvi`, `lowprice`, `vip_vt`, `vip_bt` | optional |  | Y |
| `cate_leaf_id` | `300027831` | leaf category id of item | only for AIDC scenarios such as `rvi`, `lowprice`, `vip_vt`, `vip_bt` | optional |  | Y |
| `biz_source` | `lowprice / emart / super_deal` | business source of product | only for AIDC scenarios | optional |  | Y |
| `sub_biz_source` | `main / theme / sub` | subtype of `biz_source` | required when `biz_source = super_deal` | optional |  | Y |
| `module_private_id` | `UUID` | module content version id | only within RPP module | optional |  |  |

### Derived Rules
| field | rule |
|---|---|
| `listno` | `pageIndex * pageSize + pagePos` |
| `pageIndex` | backend request index, starts from 0 |
| `pagePos` | relative item index within one backend request, starts from 0 and resets per request |
| `section_index` | meaningful mainly for Mobile Home section |
| `module_index` | sequential but may be non-continuous, for example `0 -> 2 -> 3 -> 5` |

### Empty Value Notes
| field | rule |
|---|---|
| `spm-url` | null when there is no previous page |
| `spm-pre` | null when there is no previous-page chain |
| `gmkt_page_id` | fixed as empty string |
| `sort` | empty on non-search page |
| `searchScenario` | empty on non-search page |
| `query` | empty on non-SRP page |
| `search_session_id` | empty on non-search page |
| `promotion_price` | empty if no promotion price |
| `coupon_price` | empty if no coupon price |
| `adProduct` | empty if non-ad |
| `adSubProduct` | empty if non-ad |
| `_p_catalog` | empty if no catalog |
| `_p_group` | empty if no group |
| `ab_buckets` | empty if no experiment or user not assigned |

### Special Notes for origin_price
| domain_or_case | note |
|---|---|
| Consulting | may be empty string |
| Travel | consulting start price |
| Funeral Service | monthly fee |
| Internet | monthly fee |
| Subscription | special subscription handling |
| Phone | installment price |
| E-learning | 1 won may be interpreted as subscription |
| Rental | monthly rental fee |

## Product Click

### Top-level Params
| field | path | sample_value | description | empty_or_null_rule | required | clients |
|---|---|---|---|---|---|---|
| `spm` | `/` | `spma.b.c.d` | spm position of current slot. e.g. `a211g0.searchlist.${tab_name}_${module_name}.${index}` |  | mandatory | App + Web |
| `spm-cnt` | `/` | `spma.b` | spm position of current page. e.g. `a211g0.pdp` |  | mandatory | App + Web |
| `spm-url` | `/` | `url-spma.b.c.d` | source spm position. e.g. `a211g0.searchlist.list.1` | There is no previous page. e.g. first time entering the app -> Home (`spm-url = null`) | optional | App + Web |
| `spm-pre` | `/` | `pre-spma.b.c.d` | source of source spm position. e.g. `a211g0.search.history.2` | There is no previous page. e.g. first time entering the app -> Home -> SRP (`spm-pre = null`) | optional | App + Web |
| `cguid` | `/` | `cguid` | GMarket cguid |  | mandatory | App + Web |
| `pguid` | `/` | `pguid` | GMarket pguid |  | mandatory | App + Web |
| `sguid` | `/` | `sguid` | GMarket sguid |  | mandatory | App + Web |
| `_p_prod` | `/` | `item id` | item id (goods code) |  | mandatory | App + Web |
| `_p_sku` | `/` | `0` | sku id (first option code) |  | mandatory | App + Web |
| `_p_catalog` | `/` | `catalog id` | if this item has a catalog. Could be empty string for some domains (e.g. some modules in VIP) | if item has no catalog | optional | App + Web |
| `_p_group` | `/` | `group id` | if this item has a group. Could be empty string for some domains (e.g. some modules in VIP) | if item has no group | optional | App + Web |
| `gmkt_page_id` | `/` | `page_id` | GMarket page id | Fixed as empty string | optional | App + Web |
| `gmkt_area_code` | `/` | `area_code` | GMarket area code |  | mandatory | App + Web |
| `section_index` | `/` | `source tab index` | The index is sequential (`0 -> 1 -> 2 -> ...`), starting from 0 | Only meaningful for identifying Mobile Home's section. All other components have empty string | optional | App + Web |
| `module_index` | `/` | `source module index` | The index is sequential but non-continuous now, starting from 0. e.g. `0 -> 2 -> 3 -> 5` |  | mandatory | App + Web |
| `is_ad` | `/` | `Y/N` | `N` means organic traffic, `Y` means ad traffic |  | mandatory | App + Web |
| `channel_code` | `/` | `jaehu_id in gmkt cookie` | e.g. `200000033` | 15% traffic don't have channel code | optional | App + Web |
| `item_status` | `/` | `1 (normal)` / `-1 (sold out)` | only in cart and vip |  | optional | App + Web |
| `ab_buckets` | `/` | `sceneID1#layerID1^version1#bucketID1 _sceneID2#layerID2^version2#bucketID2` | ab test bucket. ab layers are split by `_`; scene / layer / bucket are split by `#`; if there's no scene id, keep `#`, like `#layerID1#bucketID1_#layerID2#bucketID2`; the sceneID is always empty string in recommend abtest; if there is no version, `^version` can be empty, like `sceneID#layerId#bucketId`; e.g. `#108^3#A_49546#110^3#B_#sp-common-rank-l1#535844` | if there's no ongoing experiment, or there is an ongoing experiment but the user is not assigned to any test group | optional | App + Web |
| `is_airticket` | `/` | `Y/N` | airticket flag |  | optional | App + Web |
| `utLogMap` | `/` | `URL-encoded JSON` | all item components have this parameter; non-item components don't contain this parameter. All info from utLogMap are from server side. JSON format, URL encoded |  | mandatory | App + Web |

### utLogMap Params
| field | sample_value | description | empty_or_null_rule | required | clients |
|---|---|---|---|---|---|
| `scene` | `search / recommendation / campaign` | search, recommendation or campaign scene |  | mandatory | App + Web |
| `sub_scene` | `search: main_srp / find_similiar / image_search` `recommendation: rvi / lowprice / vip_vt / vip_bt / pdpjfy / hpjfy` `campaign: rpp_itemlist` | sub scene |  | mandatory | App + Web |
| `x_object_id` | `item id` | exposure item id |  | mandatory | App + Web |
| `x_object_type` | `item` / `store` / `lp` | exposure card type. item card (including organic and ad item): `item`; seller card: `store`; other card (link to any other landing pages): `lp`. Fixed as item (`x_object_type = \"item\"`) for item card |  | mandatory | App + Web |
| `x_sku_id` | `0` | exposure sku id (first option code). Fixed as 0 |  | mandatory | App + Web |
| `pageIndex` | `SRP, Home > Superdeal: incremented per every request in a session; ETC: 0` | back-end request page index, starting from 0 |  | mandatory | App + Web |
| `pagePos` | `0` | relative position within the corresponding back-end request, starting from 0; refresh indexing for every back-end request. About filter-rules, different modules adopt different methods. before-modules follow previous definitions as shown in 1.10. newly-added-modules prefer to use post-filtering |  | mandatory | App + Web |
| `pageSize` | `10` | total count of returned items in the corresponding back-end request |  | mandatory | App + Web |
| `listno` | `0` | absolute position in the current page-module, starting from 0. Calculation logic: `pageIndex * pageSize + pagePos` |  | mandatory | App + Web |
| `sort` | `SRP: popularity / order / priceasc / pricedesc / reviewcount / latest` `ETC: Empty String` | for Search channel only: sort by | non-search page | optional | App + Web |
| `searchScenario` | `SRP: keyword / category / other / keyword-filter / category-filter / other-filter` `ETC: Empty String` | for Search channel only: search scenario | non-search page | optional | App + Web |
| `query` | `SRP: dress` `ETC: Empty String` | for Search channel only: query | non-search page | optional | App + Web |
| `pvid` | `7875da6bc08bfe1781960c6b74a855cd` | back-end request unique id, including Gmkt + AIDC old and new servers. GMKT: UUID |  | mandatory | App + Web |
| `pvid_sys` | `gmkt server / aidc server` | When scenario for AIDC ABTest (from TPP Proxy), `pvid_sys = 'aidc server'`; otherwise, `pvid_sys = 'gmarket server'` (from Gmarket Module Service) |  | mandatory | App + Web |
| `search_session_id` | `SRP: unique id for one search instance` `ETC: Empty String` | for Search channel only | non-search page | optional | App + Web |
| `origin_price` | `45200` | exposed price | empty string in some edge cases: Consulting / Travel: Consulting start price / Funeral Service: Monthly fee / Internet: Monthly fee / Subscription / Phone: Installment price / E-learning: 1 won (automatically interpreted as subscription) / Rental: Monthly rental fee | optional | App + Web |
| `promotion_price` | `42220` | promotion price | when there is no promotion price | optional | App + Web |
| `coupon_price` | `40680` | coupon price | when there is no coupon price | optional | App + Web |
| `trafficType` | `organic / ad` | organic or ad traffic type |  | mandatory | App + Web |
| `adProduct` | `N / J` | ad product type. `N`: search ads, `J`: recommendation ads. When scenario for AIDC ABTest (from TPP Proxy), `adProduct` is not empty string | non-ad product is empty string | optional | App + Web |
| `adSubProduct` | `F / A` | ad sub product type. `A`: power click, `F`: ai boost. When scenario for AIDC ABTest (from TPP Proxy), `adProduct` is not empty string | non-ad product is empty string | optional | App + Web |
| `seed_item_id` | `item id` | for Recommendation channel only: seed item id. It is valid for the case which has seed item (e.g. RVI, VIP) | non-seed item module | optional | App + Web |
| `seed_item_index` | `starting from 0` | for Recommendation channel only: seed item index (new version has this) | non-seed item module | optional | App + Web |
| `seed_item_keyword` | `keyword` | for Recommendation channel only: seed item keyword (new version has this) | non-seed item module | optional | App + Web |
| `ab_buckets` | `sceneID1#layerID1^version1#bucketID1 _sceneID2#layerID2^version2#bucketID2` | ab test bucket. ab layers are split by `_`; scene / layer / bucket are split by `#`; if there's no scene id, keep `#`, like `#layerID1#bucketID1_#layerID2#bucketID2`; the sceneID is always empty string in recommend abtest; if there is no version, `^version` can be empty, like `sceneID#layerId#bucketId`; e.g. `#108^3#A_49546#110^3#B_#sp-common-rank-l1#535844` | if there's no ongoing experiment, or there is an ongoing experiment but the user is not assigned to any test group | optional | App + Web |
| `childConfigId` | `1753066336000` | The timestamp of the effectiveness of low-priced items. For Recommendation channel only: only the recommended low-priced item modules have this value | only the recommended low-priced item modules have this value | optional | App + Web |
| `self_ab_id` | `abtest id` | From AIDC Recommend algo engine. Abtest ID inside the AIDC algorithm engine. Required when `utparam-url.sub_scene` is in `rvi / lowprice / vip_vt / vip_bt` (and future new AIDC subscenes as well). Only AIDC scenario |  | optional | App + Web |
| `match_type` | `keywords2i` | From AIDC Recommend algo engine. Algorithm recall type. Required when `utparam-url.sub_scene` is in `rvi / lowprice / vip_vt / vip_bt` (and future new AIDC subscenes as well). Only AIDC scenario |  | optional | App + Web |
| `cate_leaf_id` | `300027831` | From AIDC Recommend algo engine. The leaf category of the item. Required when `utparam-url.sub_scene` is in `rvi / lowprice / vip_vt / vip_bt` (and future new AIDC subscenes as well). Only AIDC scenario |  | optional | App + Web |
| `biz_source` | `lowprice / emart / super_deal` | From AIDC Recommend algo engine, but can be updated by gmkt server. The business source of the product. When module = `lowprice`, biz_source is `lowprice` or null. When module in `(vip_vt, vip_bt, emart_vt, emart_bt)`, biz_source is `emart` or null. When module = `hpjfy`, biz_source is `super_deal` or null. Only AIDC scenario |  | optional | App + Web |
| `sub_biz_source` | `main / theme / sub` | From AIDC Recommend algo engine, but can be updated by gmkt server. Sub types of business sources for products. Required when `biz_source = \"super_deal\"`; `sub_biz_source` will be `main / theme / sub`. Only AIDC scenario |  | optional | App + Web |
| `module_private_id` | `Unique UUID` | Only within the RPP module. Version ID of module content |  | optional | App + Web |

## Module Exposure

### Top-level Params
| field | value | Comment | Empty value explanation | Necessity | Clients |
|---|---|---|---|---|---|
| `spm` | `spma.b.c` | spm position of current slot. e.g. `a211g0.searchlist.${section_name}_${module_name}` |  | mandatory | App + Web |
| `spm-cnt` | `spma.b` | spm position of current page. e.g. `a211g0.pdp` |  | mandatory | App + Web |
| `spm-url` | `url-spma.b.c.d` | source spm position. e.g. `a211g0.searchlist.list.1` | There is no previous page | optional | App + Web |
| `spm-pre` | `pre-spma.b.c.d` | source of source spm position. e.g. `a211g0.search.history.2` | There is no previous page | optional | App + Web |
| `cguid` | `cguid` | GMarket cguid |  | mandatory | App + Web |
| `pguid` | `pguid` | GMarket pguid |  | mandatory | App + Web |
| `sguid` | `sguid` | GMarket sguid |  | mandatory | App + Web |
| `gmkt_page_id` | `page_id` | GMarket page id | Fixed as empty string | optional | App + Web |
| `gmkt_area_code` | `area_code` | GMarket area code | `gmkt_area_code` will not be present in module exposure | optional | App + Web |
| `section_index` |  | tab index. The index is sequential (`0 -> 1 -> 2 -> ...`), starting from 0 | Only meaningful for identifying Mobile Home's section. All other components have empty string | optional | App + Web |
| `module_index` |  | module index. The index is sequential but non-continuous now, starting from 0. e.g. `0 -> 2 -> 3 -> 5` |  | mandatory | App + Web |
| `channel_code` | `jaehu_id in gmkt cookie` | e.g. `200000033` | 15% traffic don't have channel code | optional | App + Web |
| `ab_buckets` | `sceneID1#layerID1^version1#bucketID1 _sceneID2#layerID2^version2#bucketID2` | ab test bucket. ab layers are split by `_`; scene / layer / bucket are split by `#`; if there's no scene id, keep `#`, like `#layerID1#bucketID1_#layerID2#bucketID2`; the sceneID is always empty string in recommend abtest; if there is no version, `^version` can be empty, like `sceneID#layerId#bucketId`; e.g. `#108^3#A_49546#110^3#B_#sp-common-rank-l1#535844` | if there's no ongoing experiment, or there is an ongoing experiment but the user is not assigned to any test group | optional | App + Web |

### Notes
- 현재 확보한 공식 문서는 `module_exposure`의 top-level 항목만 포함합니다.
- 하위 JSON 또는 서버 사이드 파라미터 정의가 확보되면 같은 형식으로 후속 추가합니다.
- `gmkt_area_code`는 일반적으로 쓰이지만 `module_exposure`에는 없을 수 있으므로 optional로 기록합니다.

## Product ATC Click

### Top-level Params
| field | key (level 2) | value | Comment | Empty value explanation | Necessity | Clients |
|---|---|---|---|---|---|---|
| `spm` |  | `spma.b.c.d` | spm position of current slot. e.g. `a211g0.searchlist.${tab_name}_${module_name}.${index}` |  | mandatory | App + Web |
| `spm-cnt` |  | `spma.b` | spm position of current page. e.g. `a211g0.pdp` |  | mandatory | App + Web |
| `spm-url` |  | `url-spma.b.c.d` | source spm position. e.g. `a211g0.searchlist.list.1` | There is no previous page. e.g. first time entering the app -> Home (`spm-url = null`) | optional | App + Web |
| `spm-pre` |  | `pre-spma.b.c.d` | source of source spm position. e.g. `a211g0.search.history.2` | There is no previous page. e.g. first time entering the app -> Home -> SRP (`spm-pre = null`) | optional | App + Web |
| `cguid` |  | `cguid` | GMarket cguid |  | mandatory | App + Web |
| `pguid` |  | `pguid` | GMarket pguid |  | mandatory | App + Web |
| `sguid` |  | `sguid` | GMarket sguid |  | mandatory | App + Web |
| `_p_prod` |  | `item id` | item id (goods code) |  | mandatory | App + Web |
| `_p_sku` |  | `sku id` | sku id (a2c option code) |  | mandatory | App + Web |
| `_p_catalog` |  | `catalog id` | if this item has a catalog. Could be empty string for some domains (e.g. some modules in VIP) | if item has no catalog | optional | App + Web |
| `_p_group` |  | `group id` | if this item has a group. Could be empty string for some domains (e.g. some modules in VIP) | if item has no group | optional | App + Web |
| `atc_quantity` |  | `2` | direct a2c quantity |  | mandatory | App + Web |
| `gmkt_page_id` |  | `page_id` | GMarket page id | Fixed as empty string | optional | App + Web |
| `gmkt_area_code` |  | `area_code` | GMarket area code |  | mandatory | App + Web |
| `section_index` |  |  | tab index. The index is sequential (`0 -> 1 -> 2 -> ...`), starting from 0. Only meaningful for identifying Mobile Home's section. All other components have empty string | Only meaningful for identifying Mobile Home's section. All other components have empty string | optional | App + Web |
| `module_index` |  |  | module index. The index is sequential but non-continuous now, starting from 0. e.g. `0 -> 2 -> 3 -> 5` |  | mandatory | App + Web |
| `is_ad` |  | `Y/N` | `N` means organic traffic, `Y` means ad traffic |  | mandatory | App + Web |
| `channel_code` |  | `jaehu_id in gmkt cookie` | e.g. `200000033` | 15% traffic don't have channel code | optional | App + Web |
| `ab_buckets` |  | `sceneID1#layerID1^version1#bucketID1 _sceneID2#layerID2^version2#bucketID2` | ab test bucket. ab layers are split by `_`; scene / layer / bucket are split by `#`; if there's no scene id, keep `#`, like `#layerID1#bucketID1_#layerID2#bucketID2`; the sceneID is always empty string in recommend abtest; if there is no version, `^version` can be empty, like `sceneID#layerId#bucketId`; e.g. `#108^3#A_49546#110^3#B_#sp-common-rank-l1#535844` | if there's no ongoing experiment, or there is an ongoing experiment but the user is not assigned to any test group | optional | App + Web |
| `utLogMap` |  | `URL-encoded JSON` | all item components have this parameter; non-item components don't contain this parameter. All info from utLogMap are from server side. JSON format, URL encoded |  | mandatory | App + Web |

### utLogMap Params
| field | sample_value | description | empty_or_null_rule | required | clients |
|---|---|---|---|---|---|
| `scene` | `search / recommendation / campaign` | search, recommendation or campaign scene |  | mandatory | App + Web |
| `sub_scene` | `search: main_srp / find_similiar / image_search` `recommendation: rvi / lowprice / vip_vt / vip_bt / pdpjfy / hpjfy` `campaign: rpp_itemlist` | sub scene |  | mandatory | App + Web |
| `x_object_id` | `item id` | exposure item id |  | mandatory | App + Web |
| `x_object_type` | `Fixed as item (x_object_type: "item")` | exposure card type |  | mandatory | App + Web |
| `x_sku_id` | `0` | exposure sku id (first option code). Fixed as 0 |  | mandatory | App + Web |
| `pageIndex` | `SRP, Home > Superdeal: incremented per every request in a session; ETC: 0` | back-end request page index, starting from 0 |  | mandatory | App + Web |
| `pagePos` | `0` | relative position within the corresponding back-end request, starting from 0; refresh indexing for every back-end request. About filter-rules, different modules adopt different methods. before-modules follow previous definitions as shown in 1.10. newly-added-modules prefer to use post-filtering |  | mandatory | App + Web |
| `pageSize` | `10` | total count of returned items in the corresponding back-end request |  | mandatory | App + Web |
| `listno` | `0` | absolute position in the current page, starting from 0. Calculation logic: `pageIndex * pageSize + pagePos` |  | mandatory | App + Web |
| `sort` | `SRP: popularity / order / priceasc / pricedesc / reviewcount / latest` `ETC: Empty String` | for Search channel only: sort by | non-search page | optional | App + Web |
| `searchScenario` | `SRP: keyword / category / other / keyword-filter / category-filter / other-filter` `ETC: Empty String` | for Search channel only: search_scenario | non-search page | optional | App + Web |
| `query` | `SRP: dress` `ETC: Empty String` | for Search channel only: query | non-search page | optional | App + Web |
| `pvid` | `7875da6bc08bfe1781960c6b74a855cd` | back-end request unique id including Gmkt + AIDC old and new servers. GMKT: UUID |  | mandatory | App + Web |
| `pvid_sys` | `gmkt server / aidc server` | back-end request from Gmkt or AIDC server. When scenario for AIDC ABTest (from TPP Proxy), `pvid_sys = 'aidc server'`; otherwise, `pvid_sys = 'gmarket server'` (from Gmarket Module Service) |  | mandatory | App + Web |
| `search_session_id` | `SRP: unique id for one search instance` `ETC: Empty String` | for Search channel only | non-search page | optional | App + Web |
| `origin_price` | `45200` | exposed price | empty string in some edge cases: Consulting / Travel: Consulting start price / Funeral Service: Monthly fee / Internet: Monthly fee / Subscription / Phone: Installment price / E-learning: 1 won (automatically interpreted as subscription) / Rental: Monthly rental fee | optional | App + Web |
| `promotion_price` | `42220` | promotion price | when there is no promotion price | optional | App + Web |
| `coupon_price` | `40680` | coupon price | when there is no coupon price | optional | App + Web |
| `trafficType` | `organic / ad` | organic or ad traffic type |  | mandatory | App + Web |
| `adProduct` | `N / J` | ad product type. When scenario for AIDC ABTest (from TPP Proxy), `adProduct` is not empty string. `N`: search ads, `J`: recommendation ads | non adProduct is empty string | optional | App + Web |
| `adSubProduct` | `F / A` | ad sub product type. When scenario for AIDC ABTest (from TPP Proxy), `adProduct` is not empty string. `A`: power click, `F`: ai boost | non adProduct is empty string | optional | App + Web |
| `seed_item_id` |  | for Recommendation channel only: seed item id. It is valid for the case which has seed item (e.g. RVI, VIP) | non-seed item module | optional | App + Web |
| `seed_item_index` | `starting from 0` | for Recommendation channel only: seed item index (new version has this) | non-seed item module | optional | App + Web |
| `seed_item_keyword` |  | for Recommendation channel only: seed item keyword (new version has this) | non-seed item module | optional | App + Web |
| `ab_buckets` | `sceneID1#layerID1^version1#bucketID1 _sceneID2#layerID2^version2#bucketID2` | ab test bucket. ab layers are split by `_`; scene / layer / bucket are split by `#`; if there's no scene id, keep `#`, like `#layerID1#bucketID1_#layerID2#bucketID2`; the sceneID is always empty string in recommend abtest; if there is no version, `^version` can be empty, like `sceneID#layerId#bucketId`; e.g. `#108^3#A_49546#110^3#B_#sp-common-rank-l1#535844` | if there's no ongoing experiment, or there is an ongoing experiment but the user is not assigned to any test group | optional | App + Web |
| `childConfigId` | `1753066336000` | The timestamp of the effectiveness of low-priced items. For Recommendation channel only: only the recommended low-priced item modules have this value | Only the recommended low-priced item modules have this value | optional | App + Web |
| `self_ab_id` |  | From AIDC Recommend algo engine. Abtest ID inside the AIDC algorithm engine. Required under the following conditions: `utparam-url.sub_scene` in `rvi / lowprice / vip_vt / vip_bt` (if there are new AIDC subscenes, they also need to be added). Only AIDC scenario |  | optional | App + Web |
| `match_type` | `keywords2i` | From AIDC Recommend algo engine. Algorithm recall type. Required under the following conditions: `utparam-url.sub_scene` in `rvi / lowprice / vip_vt / vip_bt` (if there are new AIDC subscenes, they also need to be added). Only AIDC scenario |  | optional | App + Web |
| `cate_leaf_id` | `300027831` | From AIDC Recommend algo engine. The leaf category of the item. Required under the following conditions: `utparam-url.sub_scene` in `rvi / lowprice / vip_vt / vip_bt` (if there are new AIDC subscenes, they also need to be added). Only AIDC scenario |  | optional | App + Web |
| `biz_source` | `lowprice / emart / super_deal` | From AIDC Recommend algo engine, but can be updated by gmkt server. The business source of the product. When modules occur in the following scenarios, `biz_source` may have the following value: when module = `lowprice`, `biz_source` is `lowprice` or null; when module in `(vip_vt, vip_bt, emart_vt, emart_bt)`, `biz_source` is `emart` or null; when module = `hpjfy`, `biz_source` is `super_deal` or null. Only AIDC scenario |  | optional | App + Web |
| `sub_biz_source` | `main / theme / sub` | From AIDC Recommend algo engine, but can be updated by gmkt server. Sub types of business sources for products. Required under the following conditions: when `biz_source = "super_deal"`, `sub_biz_source` will be `main / theme / sub`. Only AIDC scenario |  | optional | App + Web |
| `module_private_id` | `Unique UUID` | Only within the RPP module. Version ID of module content |  | optional | App + Web |

## Product Exposure Schema Mapping
현재 대표 파일 [tracking_schemas/mweb/SRP/0번 구좌.json](C:/Users/mrt1847/Documents/GitHub/manual_user_tracking/tracking_schemas/mweb/SRP/0번 구좌.json)의 `product_exposure`는 공식 문서와 비교하면 아래처럼 분류할 수 있다.

| Category | Fields | Decision |
|---|---|---|
| Keep as official top-level | `spm`, `spm-cnt`, `spm-url`, `spm-pre`, `cguid`, `pguid`, `sguid`, `_p_prod`, `_p_sku`, `_p_catalog`, `_p_group`, `gmkt_page_id`, `gmkt_area_code`, `section_index`, `module_index`, `is_ad`, `channel_code`, `item_status`, `ab_buckets`, `is_airticket`, `utLogMap` | 대표 스키마에 유지 |
| Keep as official `utLogMap` field | `scene`, `sub_scene`, `x_object_id`, `x_object_type`, `x_sku_id`, `pageIndex`, `pagePos`, `pageSize`, `listno`, `sort`, `searchScenario`, `query`, `pvid`, `pvid_sys`, `search_session_id`, `origin_price`, `promotion_price`, `coupon_price`, `trafficType`, `adProduct`, `adSubProduct`, `seed_item_id`, `seed_item_index`, `seed_item_keyword`, `ab_buckets`, `childConfigId`, `self_ab_id`, `match_type`, `cate_leaf_id`, `biz_source`, `sub_biz_source`, `module_private_id` | 대표 스키마에 유지 |
| Remove from schema example | `_eventType`, `_f_t`, `_g_encode`, `_gr_uid_`, `_isCombine`, `_is_auto_exp`, `_method`, `_p_url`, `_pkgSize`, `b`, `cache`, `cna`, `customSdkId`, `device_model`, `expdata`, `gmkey`, `gokey`, `ism`, `jsver`, `language`, `logtype`, `lstag`, `lver`, `m`, `o`, `os`, `os_version`, `p`, `platformType`, `rd`, `s`, `scr`, `st_page_id`, `stag`, `tag`, `ts`, `uidaplus`, `w`, `pid`, `server_env`, `raw`, `parsed`, `params-exp`, `exargs` | 공식 문서 기준 스키마에서는 제거 |
| Relax value semantics | `cguid`, `pguid`, `sguid`, `channel_code`, `ab_buckets`, `is_airticket`, `origin_price`, `promotion_price`, `coupon_price`, `adProduct`, `adSubProduct` | 존재/optional 의미를 문서 기준으로 재해석 |

## Representative Schema Decisions
대표 예시 파일은 현재 raw payload 구조를 그대로 복제하지 않고, 공식 문서의 논리 필드만 드러내는 형태로 작성한다.

- top-level에 공식 문서 top-level 필드만 배치
- `utLogMap`은 별도 중첩 객체로 유지
- `raw`, `parsed`, `params-exp`, `exargs`, `expdata` 같은 구현 상세 구조는 예시 스키마에서 제거
- SRP `0번 구좌`의 현재 샘플에서 확정 가능한 값만 fixed string으로 두고, 나머지는 `mandatory` 또는 `""`로 표현

## Follow-up Validator Work
스키마를 먼저 공식 문서형으로 단순화하면, 현재 검증 로직은 아래 항목을 후속으로 보강해야 한다.

1. `optional`의 의미 확장
   - 현재 `""`는 `empty or missing`만 허용하고 `값이 있어도 optional`인 경우를 표현하지 못한다.
   - `channel_code`, `ab_buckets`, `promotion_price`, `coupon_price`, `adProduct`, `adSubProduct`에 영향이 있다.
2. `utLogMap` 컨테이너 존재 검증
   - 현재는 내부 leaf field만 펼쳐서 검증하므로 `utLogMap` 자체 존재 여부를 명확히 FAIL 처리하지 못한다.
3. top-level과 nested field 우선순위
   - 현재는 동일 키가 여러 위치에 있으면 먼저 찾은 값을 사용한다.
   - 문서상 `utLogMap`에 있어야 하는 값과 top-level 값이 혼재할 때 오탐 가능성이 있다.
4. Derived Rules 검증
   - `listno = pageIndex * pageSize + pagePos` 같은 규칙은 현재 스키마 표현만으로 강제하지 않는다.
   - 후속 단계에서 별도 rule validator가 필요하다.
5. conditional optional
   - `item_status`는 cart/vip에서만 의미 있고, `sub_biz_source`는 `biz_source = super_deal`일 때 의미가 있다.
   - 현재 검증기는 조건부 필드 규칙을 직접 표현하지 못한다.

## Next Expansion
공식 문서가 확보되면 아래 순서로 같은 문서 형식에 추가한다.

1. follow-up schema examples for `product_click`, `product_atc_click`, `module_exposure`
