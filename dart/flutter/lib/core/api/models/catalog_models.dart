/// Строка закрытого справочника (`GET /product-categories`, hit из `POST /catalog/match`).
class CatalogItem {
  const CatalogItem({
    required this.code,
    required this.title,
    this.id = 0,
    this.titleEn = '',
    this.iconUrl,
    this.sortOrder = 0,
    this.isActive = true,
    this.why,
    this.score,
    this.source,
  });

  final int id;
  final String code;
  final String title;
  final String titleEn;
  final String? iconUrl;
  final int sortOrder;
  final bool isActive;
  final String? why;
  final double? score;
  /// `alias` | `llm` | `both` — откуда хит в гибриде.
  final String? source;

  factory CatalogItem.fromJson(Map<String, dynamic> json) {
    final code = (json['code'] as String?) ?? (json['slug'] as String?) ?? '';
    final title = (json['title'] as String?) ?? (json['name'] as String?) ?? '';
    return CatalogItem(
      id: (json['id'] as num?)?.toInt() ?? 0,
      code: code,
      title: title,
      titleEn: (json['title_en'] as String?) ?? (json['region'] as String?) ?? '',
      iconUrl: json['icon_url'] as String?,
      sortOrder: (json['sort_order'] as num?)?.toInt() ?? 0,
      isActive: (json['is_active'] as bool?) ?? true,
      why: json['why'] as String?,
      score: (json['score'] as num?)?.toDouble(),
      source: json['source'] as String?,
    );
  }
}

/// Реестр справочника (`GET /catalogs`).
class CatalogInfo {
  const CatalogInfo({
    required this.catalog,
    required this.entityType,
    required this.keyField,
    this.fields = const [],
  });

  final String catalog;
  final String entityType;
  final String keyField;
  final List<String> fields;

  factory CatalogInfo.fromJson(Map<String, dynamic> json) {
    final rawFields = json['fields'];
    return CatalogInfo(
      catalog: json['catalog'] as String? ?? '',
      entityType: json['entity_type'] as String? ?? '',
      keyField: json['key_field'] as String? ?? 'code',
      fields: rawFields is List
          ? rawFields.map((e) => e.toString()).toList(growable: false)
          : const [],
    );
  }
}

/// Ответ `POST /catalog/match`.
class CatalogMatchResult {
  const CatalogMatchResult({
    required this.catalog,
    required this.entityType,
    required this.prompt,
    this.fields = const [],
    this.items = const [],
    this.effort = 0,
    this.usedLlm = false,
  });

  final String catalog;
  final String entityType;
  final String prompt;
  final List<String> fields;
  final List<CatalogItem> items;
  /// УсилиеПоиска: сколько строк справочника ушло в один вызов LLM.
  final int effort;
  final bool usedLlm;

  factory CatalogMatchResult.fromJson(Map<String, dynamic> json) {
    final rawFields = json['fields'];
    final rawItems = json['items'];
    return CatalogMatchResult(
      catalog: json['catalog'] as String? ?? '',
      entityType: json['entity_type'] as String? ?? '',
      prompt: json['prompt'] as String? ?? '',
      fields: rawFields is List
          ? rawFields.map((e) => e.toString()).toList(growable: false)
          : const [],
      items: rawItems is List
          ? rawItems
              .whereType<Map>()
              .map((e) => CatalogItem.fromJson(Map<String, dynamic>.from(e)))
              .toList(growable: false)
          : const [],
      effort: (json['effort'] as num?)?.toInt() ?? 0,
      usedLlm: json['used_llm'] as bool? ?? false,
    );
  }
}
