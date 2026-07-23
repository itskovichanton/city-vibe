import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Кнопки «Продолжить с Google / Apple» — пока только верстка.
class SocialLoginButton extends StatelessWidget {
  const SocialLoginButton({
    super.key,
    required this.label,
    required this.background,
    required this.foreground,
    required this.leading,
    this.onPressed,
  });

  final String label;
  final Color background;
  final Color foreground;

  /// Виджет слева (логотип).
  final Widget leading;

  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50,
      width: double.infinity,
      child: OutlinedButton(
        onPressed: onPressed ?? () {},
        style: OutlinedButton.styleFrom(
          backgroundColor: background,
          foregroundColor: foreground,
          side: BorderSide(
            color: background == AppColors.appleButton
                ? const Color(0x33FFFFFF)
                : Colors.transparent,
          ),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          padding: const EdgeInsets.symmetric(horizontal: 16),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            leading,
            const SizedBox(width: 10),
            Text(
              label,
              style: TextStyle(
                color: foreground,
                fontWeight: FontWeight.w600,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Простой цветной «G» без внешних SVG-пакетов (достаточно для верстки).
class GoogleMark extends StatelessWidget {
  const GoogleMark({super.key});

  @override
  Widget build(BuildContext context) {
    return const Text(
      'G',
      style: TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w800,
        // Классические цвета Google упрощённо через один акцентный синий.
        color: Color(0xFF4285F4),
      ),
    );
  }
}
