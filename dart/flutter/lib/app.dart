import 'package:city_vibe/features/auth/presentation/login_screen.dart';
import 'package:city_vibe/theme/app_theme.dart';
import 'package:flutter/material.dart';

/// Корневой виджет приложения.
///
/// MaterialApp задаёт:
/// - тему (ThemeData),
/// - стартовый экран (home),
/// - заголовок для OS / web tab,
/// - локализацию (позже добавим intl).
class CityVibeApp extends StatelessWidget {
  const CityVibeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CityVibe',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      // Пока единственный экран — логин. Дальше появится Navigator / go_router.
      home: const LoginScreen(),
    );
  }
}
