import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Нижняя навигация из макета — пока только внешний вид.
class HomeBottomNav extends StatelessWidget {
  const HomeBottomNav({super.key});

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.paddingOf(context).bottom;
    return ColoredBox(
      color: const Color(0xF20B0714),
      child: Padding(
        padding: EdgeInsets.fromLTRB(8, 6, 8, 6 + bottom),
        child: const Row(
          children: [
            _NavItem(icon: Icons.map_outlined, label: 'Карта', selected: true),
            _NavItem(icon: Icons.chat_bubble_outline, label: 'Чаты'),
            _CenterPlus(),
            _NavItem(icon: Icons.calendar_month_outlined, label: 'События'),
            _NavItem(icon: Icons.person_outline, label: 'Профиль'),
          ],
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.label,
    this.selected = false,
  });

  final IconData icon;
  final String label;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppColors.accent : AppColors.textSecondary;
    return Expanded(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
        ],
      ),
    );
  }
}

class _CenterPlus extends StatelessWidget {
  const _CenterPlus();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6),
      child: Container(
        width: 48,
        height: 48,
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [AppColors.gradientStart, AppColors.gradientEnd],
          ),
          boxShadow: [
            BoxShadow(
              color: Color(0x88B24BFF),
              blurRadius: 12,
            ),
          ],
        ),
        child: const Icon(Icons.add, color: Colors.white, size: 28),
      ),
    );
  }
}
