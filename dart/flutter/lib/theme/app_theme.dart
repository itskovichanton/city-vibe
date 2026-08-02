import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Глобальная тема MaterialApp.
ThemeData buildAppTheme() {
  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppColors.background,
    colorScheme: const ColorScheme.dark(
      primary: AppColors.accent,
      surface: AppColors.backgroundDeep,
    ),
  );

  final display = GoogleFonts.pacificoTextTheme(base.textTheme);
  final body = GoogleFonts.interTextTheme(base.textTheme);

  return base.copyWith(
    textTheme: body.copyWith(
      displayLarge: display.displayLarge?.copyWith(
        color: AppColors.textPrimary,
        fontSize: 42,
        height: 1.1,
        shadows: const [
          Shadow(color: AppColors.accent, blurRadius: 18),
          Shadow(color: Colors.white24, blurRadius: 4),
        ],
      ),
      headlineMedium: body.headlineMedium?.copyWith(
        color: AppColors.textPrimary,
        fontWeight: FontWeight.w700,
        fontSize: 22,
      ),
      bodyMedium: body.bodyMedium?.copyWith(
        color: AppColors.textSecondary,
        fontSize: 14,
        height: 1.35,
      ),
      labelLarge: body.labelLarge?.copyWith(
        color: AppColors.textPrimary,
        fontWeight: FontWeight.w600,
        fontSize: 16,
      ),
    ),
  );
}
