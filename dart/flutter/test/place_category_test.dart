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
        'sort_order': 10,
        'is_active': true,
      });

      expect(cat.id, 2);
      expect(cat.code, 'bars');
      expect(cat.title, 'Бары');
      expect(cat.sortOrder, 10);
      expect(cat.isActive, isTrue);
    });
  });
}
