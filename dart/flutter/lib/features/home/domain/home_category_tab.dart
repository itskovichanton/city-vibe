import 'package:city_vibe/core/api/models/place_category.dart';

/// Сентинел вкладки «Все места» — не код из `place_categories`.
const kAllPlacesCategoryCode = 'all_places';

class HomeCategoryTab {
  const HomeCategoryTab({
    required this.code,
    required this.title,
    this.iconUrl,
    this.assetIcon,
    this.isAllPlaces = false,
  });

  static const allPlaces = HomeCategoryTab(
    code: kAllPlacesCategoryCode,
    title: 'Все места',
    assetIcon: 'assets/images/all_places.png',
    isAllPlaces: true,
  );

  final String code;
  final String title;
  final String? iconUrl;
  final String? assetIcon;
  final bool isAllPlaces;
}

/// «Все места» + избранные категории юзера в его порядке.
List<HomeCategoryTab> buildHomeCategoryTabs({
  required List<PlaceCategory> catalog,
  required List<String> favoriteCodes,
}) {
  final byCode = {for (final c in catalog) c.code: c};
  final tabs = <HomeCategoryTab>[HomeCategoryTab.allPlaces];
  final seen = <String>{kAllPlacesCategoryCode};
  for (final code in favoriteCodes) {
    if (code.isEmpty || !seen.add(code)) continue;
    final cat = byCode[code];
    if (cat == null || !cat.isActive) continue;
    tabs.add(
      HomeCategoryTab(
        code: cat.code,
        title: cat.title,
        iconUrl: cat.iconUrl,
      ),
    );
  }
  return tabs;
}
