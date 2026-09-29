import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:city_vibe/core/network/api_http.dart';

/// Справочники и NL-подбор строк (`GET /catalogs`, `POST /catalog/match`).
///
/// Гибрид на Милане: алиасы + DeepSeek порциями [effort] строк.
class CatalogClient {
  CatalogClient(this._http);

  final ApiHttp _http;

  /// `GET /catalogs` — какие справочники можно матчить.
  Future<List<CatalogInfo>> getCatalogs() {
    return _http.get(
      '/catalogs',
      parse: (data) {
        final list = data as List<dynamic>;
        return list
            .whereType<Map>()
            .map((e) => CatalogInfo.fromJson(Map<String, dynamic>.from(e)))
            .toList(growable: false);
      },
    );
  }

  /// `GET /product-categories` — полный справочник товаров и услуг.
  Future<List<CatalogItem>> getProductCategories({int? limit}) {
    return _http.get(
      '/product-categories',
      parse: (data) {
        final list = data as List<dynamic>;
        final items = list
            .whereType<Map>()
            .map((e) => CatalogItem.fromJson(Map<String, dynamic>.from(e)))
            .where((c) => c.isActive)
            .toList(growable: false)
          ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
        if (limit != null && limit > 0 && items.length > limit) {
          return items.sublist(0, limit);
        }
        return items;
      },
    );
  }

  /// `POST /catalog/match` — алиасы + LLM (порции по [effort]).
  Future<CatalogMatchResult> match({
    required String prompt,
    String? catalog,
    String? entityType,
    List<String>? fields,
    int limit = 8,
    int? effort,
  }) {
    return _http.post(
      '/catalog/match',
      timeout: const Duration(seconds: 90),
      body: {
        'prompt': prompt,
        if (catalog != null) 'catalog': catalog,
        if (entityType != null) 'entity_type': entityType,
        if (fields != null) 'fields': fields,
        'limit': limit,
        if (effort != null) 'effort': effort,
      },
      parse: (data) =>
          CatalogMatchResult.fromJson(Map<String, dynamic>.from(data as Map)),
    );
  }

  /// Подбор категорий товаров/услуг по bio (limit до 50, effort=50 — весь справочник за вызов).
  Future<CatalogMatchResult> matchProductCategories(
    String prompt, {
    int limit = 50,
    int effort = 50,
    List<String> fields = const ['title'],
  }) {
    return match(
      prompt: prompt,
      catalog: 'product_categories',
      fields: fields,
      limit: limit,
      effort: effort,
    );
  }
}
