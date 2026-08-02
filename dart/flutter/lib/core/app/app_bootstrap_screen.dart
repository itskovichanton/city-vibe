import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Splash при cold start: пока читаем secure storage и кэш профиля.
///
/// Не показываем login до выяснения, есть ли сохранённая сессия.
class AppBootstrapScreen extends StatelessWidget {
  const AppBootstrapScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.background,
      body: Center(
        child: SizedBox(
          width: 28,
          height: 28,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            color: AppColors.accent,
          ),
        ),
      ),
    );
  }
}
