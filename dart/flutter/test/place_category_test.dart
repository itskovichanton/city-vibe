import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PlaceCategory', () {
    test('fromJson parses catalog item', () {
      final cat = PlaceCategory.fromJson({
        'id': 2,
        'code': 'bars',
        'title': 'Бары',
        'title_en': 'Bars',
        'icon_url': 'place_categories/bars.png',
        'sort_order': 10,
        'is_active': true,
      });

      expect(cat.id, 2);
      expect(cat.code, 'bars');
      expect(cat.title, 'Бары');
      expect(cat.iconUrl, 'place_categories/bars.png');
      expect(cat.sortOrder, 10);
      expect(cat.isActive, isTrue);
    });

    test('toJson / fromCatalogItem round-trip', () {
      const item = CatalogItem(
        id: 2,
        code: 'bars',
        title: 'Бары',
        titleEn: 'Bars',
        iconUrl: 'place_categories/bars.png',
        sortOrder: 10,
      );
      final cat = PlaceCategory.fromCatalogItem(item);
      expect(cat.toCatalogItem().code, 'bars');
      expect(PlaceCategory.fromJson(cat.toJson()).iconUrl, item.iconUrl);
    });
  });
}
