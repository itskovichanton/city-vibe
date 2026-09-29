import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Шапка главного экрана по макету: логотип + поиск + колокол (пока без действий).
class HomeTopBar extends StatelessWidget {
  const HomeTopBar({super.key});

  @override
  Widget build(BuildContext context) {
    final logoStyle = Theme.of(context).textTheme.displayLarge?.copyWith(
      fontSize: 28,
      height: 1,
      shadows: const [
        Shadow(color: AppColors.accent, blurRadius: 12),
      ],
    );

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 8, 8),
      child: Row(
        children: [
          Expanded(
            child: Text.rich(
              TextSpan(
                style: logoStyle,
                children: const [
                  TextSpan(text: 'City'),
                  TextSpan(
                    text: 'Vibe',
                    style: TextStyle(color: AppColors.accent),
                  ),
                ],
              ),
            ),
          ),
          IconButton(
            onPressed: () {},
            tooltip: 'Поиск',
            icon: const Icon(Icons.search_rounded, color: Colors.white),
          ),
          IconButton(
            onPressed: () {},
            tooltip: 'Уведомления',
            icon: Badge(
              smallSize: 8,
              backgroundColor: const Color(0xFFFF4D67),
              child: Icon(
                Icons.notifications_none_rounded,
                color: Colors.white.withValues(alpha: 0.92),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
