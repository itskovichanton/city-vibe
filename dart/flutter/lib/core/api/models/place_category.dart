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
      id: json['id'] as int,
      code: json['code'] as String,
      title: json['title'] as String,
      titleEn: (json['title_en'] as String?) ?? '',
      iconUrl: json['icon_url'] as String?,
      sortOrder: (json['sort_order'] as int?) ?? 0,
      isActive: (json['is_active'] as bool?) ?? true,
    );
  }
}
