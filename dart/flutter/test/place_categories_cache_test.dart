import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:city_vibe/core/cache/place_category_local_store.dart';
import 'package:city_vibe/features/home/domain/home_category_tab.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('MemoryPlaceCategoryLocalStore', () {
    test('replaceAll / getAll round-trip', () async {
      final store = MemoryPlaceCategoryLocalStore();
      expect(await store.getAll(), isEmpty);

      await store.replaceAll(const [
        PlaceCategory(
          id: 1,
          code: 'bars',
          title: 'Бары',
          iconUrl: 'place_categories/bars.png',
          sortOrder: 10,
        ),
        PlaceCategory(id: 2, code: 'cafes', title: 'Кафе', sortOrder: 30),
      ]);

      final all = await store.getAll();
      expect(all, hasLength(2));
      expect(all.first.code, 'bars');
      expect(all.first.iconUrl, 'place_categories/bars.png');
      expect(all.last.title, 'Кафе');
    });
  });

  group('buildHomeCategoryTabs', () {
    const catalog = [
      PlaceCategory(id: 1, code: 'bars', title: 'Бары', sortOrder: 10),
      PlaceCategory(id: 2, code: 'cafes', title: 'Кафе', sortOrder: 30),
      PlaceCategory(
        id: 3,
        code: 'parks',
        title: 'Парки',
        sortOrder: 70,
        isActive: false,
      ),
    ];

    test('always starts with Все места, then favorites in user order', () {
      final tabs = buildHomeCategoryTabs(
        catalog: catalog,
        favoriteCodes: const ['cafes', 'bars', 'cafes', 'unknown'],
      );
      expect(tabs.map((e) => e.code).toList(), ['all_places', 'cafes', 'bars']);
      expect(tabs.first.isAllPlaces, isTrue);
      expect(tabs.first.title, 'Все места');
    });

    test('skips inactive favorites', () {
      final tabs = buildHomeCategoryTabs(
        catalog: catalog,
        favoriteCodes: const ['parks', 'bars'],
      );
      expect(tabs.map((e) => e.code).toList(), ['all_places', 'bars']);
    });
  });
}
