import 'package:cached_network_image/cached_network_image.dart';
import 'package:city_vibe/core/network/media_url_resolver.dart';
import 'package:city_vibe/features/home/home_providers.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Горизонтальная строка: «Все места» + favourite-категории мест.
class HomeCategoryBar extends ConsumerWidget {
  const HomeCategoryBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tabs = ref.watch(homeCategoryTabsProvider);
    final selected = ref.watch(selectedHomeCategoryCodeProvider);

    return SizedBox(
      height: 92,
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 4),
        scrollDirection: Axis.horizontal,
        itemCount: tabs.length,
        separatorBuilder: (_, __) => const SizedBox(width: 10),
        itemBuilder: (context, index) {
          final tab = tabs[index];
          final isSelected = tab.code == selected;
          return _CategoryTile(
            key: ValueKey('home-category-${tab.code}'),
            tab: tab,
            selected: isSelected,
            onTap: () {
              ref.read(selectedHomeCategoryCodeProvider.notifier).state =
                  tab.code;
            },
          );
        },
      ),
    );
  }
}

class _CategoryTile extends StatelessWidget {
  const _CategoryTile({
    super.key,
    required this.tab,
    required this.selected,
    required this.onTap,
  });

  final HomeCategoryTab tab;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        width: 72,
        child: Column(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              width: 54,
              height: 54,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF161022),
                border: Border.all(
                  color: selected
                      ? const Color(0xFFD48BFF)
                      : const Color(0x33FFFFFF),
                  width: selected ? 1.6 : 1,
                ),
                boxShadow: selected
                    ? [
                        BoxShadow(
                          color: AppColors.accent.withValues(alpha: 0.55),
                          blurRadius: 16,
                          spreadRadius: 0.5,
                        ),
                      ]
                    : null,
              ),
              child:
                  Center(child: _CategoryGlyph(tab: tab, selected: selected)),
            ),
            const SizedBox(height: 6),
            Text(
              tab.title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 11,
                height: 1.1,
                fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                color:
                    selected ? AppColors.textPrimary : AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CategoryGlyph extends StatelessWidget {
  const _CategoryGlyph({required this.tab, required this.selected});

  final HomeCategoryTab tab;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final color = selected ? const Color(0xFFE8C4FF) : Colors.white;
    final asset = tab.assetIcon;
    if (asset != null) {
      return ColorFiltered(
        colorFilter: ColorFilter.mode(color, BlendMode.srcIn),
        child: Image.asset(asset, width: 26, height: 26),
      );
    }

    final url = MediaUrlResolver.resolve(tab.iconUrl);
    if (url != null) {
      return CachedNetworkImage(
        imageUrl: url,
        width: 26,
        height: 26,
        color: color,
        colorBlendMode: BlendMode.srcIn,
        errorWidget: (_, __, ___) => Icon(
          Icons.place_outlined,
          size: 22,
          color: color,
        ),
        placeholder: (_, __) => Icon(
          Icons.place_outlined,
          size: 22,
          color: color.withValues(alpha: 0.4),
        ),
      );
    }

    return Icon(Icons.place_outlined, size: 22, color: color);
  }
}
