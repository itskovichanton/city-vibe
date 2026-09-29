import 'package:city_vibe/features/home/home_providers.dart';
import 'package:city_vibe/features/home/presentation/widgets/home_bottom_nav.dart';
import 'package:city_vibe/features/home/presentation/widgets/home_category_bar.dart';
import 'package:city_vibe/features/home/presentation/widgets/home_explore_sheet.dart';
import 'package:city_vibe/features/home/presentation/widgets/home_map_backdrop.dart';
import 'package:city_vibe/features/home/presentation/widgets/home_top_bar.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Главный экран после онбординга: категории, карта, выдвижная панель.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Прогреваем кэш справочника (cache-first внутри репозитория).
    ref.watch(placeCategoriesProvider);

    return const Scaffold(
      backgroundColor: AppColors.background,
      body: Column(
        children: [
          SafeArea(
            bottom: false,
            child: Column(
              children: [
                HomeTopBar(),
                HomeCategoryBar(),
              ],
            ),
          ),
          Expanded(
            child: Stack(
              children: [
                Positioned.fill(child: HomeMapBackdrop()),
                HomeExploreSheet(),
              ],
            ),
          ),
          HomeBottomNav(),
        ],
      ),
    );
  }
}
