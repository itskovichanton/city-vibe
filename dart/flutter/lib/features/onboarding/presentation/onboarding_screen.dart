import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:city_vibe/features/onboarding/presentation/pages/onboarding_step_one_page.dart';
import 'package:city_vibe/features/onboarding/presentation/pages/onboarding_step_two_page.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Онбординг: 2 слайда (профиль + bio) перед приветствием Миланы.
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _pageController = PageController();
  int _step = 0;

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _goToStep(int index) async {
    setState(() => _step = index);
    await _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 320),
      curve: Curves.easeOutCubic,
    );
  }

  Future<void> _onStepOneContinue({
    required String name,
    required Set<String> selectedCategoryCodes,
    String? avatarFilePath,
  }) async {
    final userId = ref.read(currentUserProvider).valueOrNull?.id;
    if (userId == null) return;

    try {
      await ref.read(currentUserProvider.notifier).updateProfile(
            name: name,
            favoriteCategories: selectedCategoryCodes.toList(growable: false),
          );
      if (avatarFilePath != null) {
        await ref.read(currentUserProvider.notifier).uploadAvatar(
              filePath: avatarFilePath,
            );
      }
      await _goToStep(1);
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message), behavior: SnackBarBehavior.floating),
      );
    }
  }

  Future<void> _onStepTwoContinue(String longBio) async {
    try {
      await ref.read(currentUserProvider.notifier).updateBio(longBio: longBio);
      await ref.read(currentUserProvider.notifier).completeOnboarding();
      ref.read(milanaWelcomePendingProvider.notifier).state = true;
      if (!mounted) return;
      context.go(AppRoutes.milanaGreeting);
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message), behavior: SnackBarBehavior.floating),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final categoriesAsync = ref.watch(onboardingCategoriesProvider);
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const LoginBackground(),
          SafeArea(
            child: Column(
              children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(8, 4, 16, 0),
                child: Row(
                  children: [
                    if (_step > 0)
                      IconButton(
                        onPressed: () => _goToStep(_step - 1),
                        icon: const Icon(Icons.chevron_left_rounded, size: 32),
                        color: AppColors.textPrimary,
                      )
                    else
                      const SizedBox(width: 48),
                    Expanded(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(2, (i) {
                          final active = i <= _step;
                          return Container(
                            width: i == _step ? 28 : 18,
                            height: 4,
                            margin: const EdgeInsets.symmetric(horizontal: 3),
                            decoration: BoxDecoration(
                              color: active
                                  ? AppColors.accent
                                  : AppColors.fieldBorder,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          );
                        }),
                      ),
                    ),
                    Text(
                      '${_step + 1} из 2',
                      style: textTheme.labelMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: categoriesAsync.when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (e, _) => Center(child: Text('Ошибка: $e')),
                  data: (categories) => Padding(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 120),
                    child: Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 420),
                        child: Container(
                          padding: const EdgeInsets.fromLTRB(20, 22, 20, 20),
                          decoration: BoxDecoration(
                            color: AppColors.card,
                            borderRadius: BorderRadius.circular(22),
                            border: Border.all(color: AppColors.cardBorder),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.35),
                                blurRadius: 24,
                                offset: const Offset(0, 12),
                              ),
                            ],
                          ),
                          child: PageView(
                            controller: _pageController,
                            physics: const NeverScrollableScrollPhysics(),
                            children: [
                              OnboardingStepOnePage(
                                categories: categories,
                                onContinue: _onStepOneContinue,
                              ),
                              OnboardingStepTwoPage(
                                onContinue: _onStepTwoContinue,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
          const Align(
            alignment: Alignment.bottomCenter,
            child: ScrollingCityDecorBar(),
          ),
        ],
      ),
    );
  }
}
