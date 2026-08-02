import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Авторизованная часть приложения (пока заглушка).
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(currentUserProvider);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Center(
          child: userAsync.when(
            loading: () => const CircularProgressIndicator(),
            error: (_, __) => Text(
              'Привет!',
              style: textTheme.headlineMedium,
            ),
            data: (user) => Text(
              'Привет, ${user?.name ?? 'гость'}!',
              textAlign: TextAlign.center,
              style: textTheme.headlineMedium,
            ),
          ),
        ),
      ),
    );
  }
}
