import 'package:city_vibe/core/api/models/catalog_models.dart';

/// Категория мест (`GET /categories`).
class PlaceCategory {
  const PlaceCategory({
    required this.id,
    required this.code,
    required this.title,
    this.titleEn = '',
    this.iconUrl,
    this.sortOrder = 0,
    this.isActive = true,
  });

  final int id;
  final String code;
  final String title;
  final String titleEn;
  final String? iconUrl;
  final int sortOrder;
  final bool isActive;

  factory PlaceCategory.fromJson(Map<String, dynamic> json) {
    return PlaceCategory(
      id: (json['id'] as num?)?.toInt() ?? 0,
      code: json['code'] as String? ?? '',
      title: json['title'] as String? ?? '',
      titleEn: (json['title_en'] as String?) ?? '',
      iconUrl: json['icon_url'] as String?,
      sortOrder: (json['sort_order'] as num?)?.toInt() ?? 0,
      isActive: json['is_active'] is bool
          ? json['is_active'] as bool
          : (json['is_active'] as num?)?.toInt() != 0,
    );
  }

  factory PlaceCategory.fromCatalogItem(CatalogItem item) {
    return PlaceCategory(
      id: item.id,
      code: item.code,
      title: item.title,
      titleEn: item.titleEn,
      iconUrl: item.iconUrl,
      sortOrder: item.sortOrder,
      isActive: item.isActive,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'code': code,
        'title': title,
        'title_en': titleEn,
        'icon_url': iconUrl,
        'sort_order': sortOrder,
        'is_active': isActive,
      };

  CatalogItem toCatalogItem() => CatalogItem(
        id: id,
        code: code,
        title: title,
        titleEn: titleEn,
        iconUrl: iconUrl,
        sortOrder: sortOrder,
        isActive: isActive,
      );
}
