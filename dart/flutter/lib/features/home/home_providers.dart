import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/api/models/place_category.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/home/domain/home_category_tab.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

export 'package:city_vibe/features/home/domain/home_category_tab.dart';

/// Справочник категорий мест: диск → память, сеть только если кэш пуст / в фоне.
final placeCategoriesProvider = FutureProvider<List<PlaceCategory>>((ref) {
  return ref.watch(placeCategoriesRepositoryProvider).getAll();
});

final selectedHomeCategoryCodeProvider = StateProvider<String>(
  (ref) => kAllPlacesCategoryCode,
);

final homeCategoryTabsProvider = Provider<List<HomeCategoryTab>>((ref) {
  final catalog = ref.watch(placeCategoriesProvider).valueOrNull ?? const [];
  final favorites =
      ref.watch(currentUserProvider).valueOrNull?.favoriteCategories ??
          const [];
  return buildHomeCategoryTabs(
    catalog: catalog,
    favoriteCodes: favorites,
  );
});
