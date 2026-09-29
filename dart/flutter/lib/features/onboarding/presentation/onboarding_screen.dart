import 'package:city_vibe/core/audio/ambient_music.dart';
import 'package:city_vibe/core/auth/logout_providers.dart';
import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/api/models/catalog_models.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'dart:async';

import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:city_vibe/features/onboarding/presentation/pages/onboarding_interests_page.dart';
import 'package:city_vibe/features/onboarding/presentation/pages/onboarding_step_one_page.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Онбординг: знакомство + bio → товары/услуги → места → приветствие Миланы.
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  static const _matchHint =
      'Мы отметили то, что подходит по вашему рассказу. Можно поправить.';

  final _pageController = PageController();
  final _stepOneKey = GlobalKey<OnboardingStepOnePageState>();
  final _productsKey = GlobalKey<OnboardingInterestsPageState>();
  final _placesKey = GlobalKey<OnboardingInterestsPageState>();
  int _step = 0;
  bool _isSwitchingAccount = false;
  bool _continueBusy = false;
  List<CatalogItem> _productCategories = const [];
  List<CatalogItem> _placeCategories = const [];
  Set<String> _matchedProductCodes = {};
  Set<String> _matchedPlaceCodes = {};

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

  Future<Set<String>> _matchCodes({
    required Future<CatalogMatchResult> Function() match,
    Iterable<String> extra = const [],
  }) async {
    final codes = {...extra.where((c) => c.isNotEmpty)};
    try {
      final result = await match();
      codes.addAll(
        result.items.map((e) => e.code).where((code) => code.isNotEmpty),
      );
    } catch (_) {
      // Match опционален: полный список всё равно покажем.
    }
    return codes;
  }

  Future<void> _onStepOneContinue({
    required String name,
    required String longBio,
    String? avatarFilePath,
  }) async {
    final userId = ref.read(currentUserProvider).valueOrNull?.id;
    if (userId == null) return;

    try {
      await ref.read(currentUserProvider.notifier).updateProfile(name: name);
      if (avatarFilePath != null) {
        await ref.read(currentUserProvider.notifier).uploadAvatar(
              filePath: avatarFilePath,
            );
        unawaited(AmbientMusic.ensurePlaying());
      }
      await ref.read(currentUserProvider.notifier).updateBio(longBio: longBio);

      final catalog = ref.read(catalogClientProvider);
      final user = ref.read(currentUserProvider).valueOrNull;
      final productsFuture = catalog.getProductCategories();
      final placesFuture = ref.read(placeCategoriesRepositoryProvider).getAll();
      final matchedProductsFuture = _matchCodes(
        match: () => catalog.matchProductCategories(longBio, limit: 50),
        extra: user?.favoriteProductCategories ?? const [],
      );
      final matchedPlacesFuture = _matchCodes(
        match: () => catalog.matchPlaceCategories(longBio, limit: 50),
        extra: user?.favoriteCategories ?? const [],
      );

      final products = await productsFuture;
      final places = await placesFuture;
      final matchedProducts = await matchedProductsFuture;
      final matchedPlaces = await matchedPlacesFuture;

      if (!mounted) return;
      setState(() {
        _productCategories = products;
        _placeCategories =
            places.map((e) => e.toCatalogItem()).toList(growable: false);
        _matchedProductCodes = matchedProducts;
        _matchedPlaceCodes = matchedPlaces;
      });
      await _goToStep(1);
    } on ApiException catch (e) {
      if (!mounted || e.requiresReLogin) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message), behavior: SnackBarBehavior.floating),
      );
    }
  }

  Future<void> _promptSwitchAccount() async {
    if (_isSwitchingAccount) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        final dialogTheme = Theme.of(dialogContext).textTheme;
        return AlertDialog(
          backgroundColor: AppColors.backgroundDeep,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
            side: const BorderSide(color: AppColors.cardBorder),
          ),
          title: Text(
            'Сменить аккаунт',
            style: dialogTheme.titleLarge?.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
          content: Text(
            'Вы действительно хотите сменить аккаунт?',
            style: dialogTheme.bodyMedium?.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          actionsPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: Text(
                'Отмена',
                style: dialogTheme.labelLarge?.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: Text(
                'Да, сменить',
                style: dialogTheme.labelLarge?.copyWith(
                  color: AppColors.accent,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) return;
    await _switchAccount();
  }

  bool get _canContinue {
    if (_continueBusy) return false;
    if (_step == 0) {
      return _stepOneKey.currentState?.canContinue ?? false;
    }
    return true;
  }

  String get _continueLabel {
    if (!_continueBusy) return 'Продолжить';
    return _step == 0 ? 'Подбираем интересы…' : 'Сохраняем…';
  }

  Future<void> _onBottomContinue() async {
    if (!_canContinue) return;
    setState(() => _continueBusy = true);
    try {
      if (_step == 0) {
        await _stepOneKey.currentState?.submit();
      } else if (_step == 1) {
        await _onProductsContinue(_productsKey.currentState?.selected ?? {});
      } else {
        await _onPlacesContinue(_placesKey.currentState?.selected ?? {});
      }
    } finally {
      if (mounted) setState(() => _continueBusy = false);
    }
  }

  Future<void> _switchAccount() async {
    if (_isSwitchingAccount) return;
    setState(() => _isSwitchingAccount = true);
    try {
      await ref.read(appLogoutProvider)();
    } finally {
      if (mounted) {
        setState(() => _isSwitchingAccount = false);
      }
    }
  }

  Future<void> _onProductsContinue(Set<String> selected) async {
    try {
      await ref.read(currentUserProvider.notifier).updateProfile(
            favoriteProductCategories: selected.toList(growable: false),
          );
      await _goToStep(2);
    } on ApiException catch (e) {
      if (!mounted || e.requiresReLogin) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message), behavior: SnackBarBehavior.floating),
      );
    }
  }

  Future<void> _onPlacesContinue(Set<String> selected) async {
    try {
      await ref.read(currentUserProvider.notifier).updateProfile(
            favoriteCategories: selected.toList(growable: false),
          );
      await ref.read(currentUserProvider.notifier).completeOnboarding();
      unawaited(ref.read(milanaAccountProvider.future));
      unawaited(AmbientMusic.ensurePlaying());
      if (!mounted) return;
      context.go(AppRoutes.milanaGreeting);
    } on ApiException catch (e) {
      if (!mounted || e.requiresReLogin) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message), behavior: SnackBarBehavior.floating),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
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
                          icon:
                              const Icon(Icons.chevron_left_rounded, size: 32),
                          color: AppColors.textPrimary,
                        )
                      else
                        const SizedBox(width: 48),
                      Expanded(
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: List.generate(3, (i) {
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
                        '${_step + 1} из 3',
                        style: textTheme.labelMedium?.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
                    child: Align(
                      alignment: Alignment.topCenter,
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 420),
                        child: Column(
                          children: [
                            Expanded(
                              child: Container(
                                width: double.infinity,
                                padding:
                                    const EdgeInsets.fromLTRB(20, 22, 20, 20),
                                decoration: BoxDecoration(
                                  color: AppColors.card,
                                  borderRadius: BorderRadius.circular(22),
                                  border:
                                      Border.all(color: AppColors.cardBorder),
                                  boxShadow: [
                                    BoxShadow(
                                      color:
                                          Colors.black.withValues(alpha: 0.35),
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
                                      key: _stepOneKey,
                                      onChanged: () => setState(() {}),
                                      onContinue: _onStepOneContinue,
                                    ),
                                    OnboardingInterestsPage(
                                      key: _productsKey,
                                      title:
                                          'Вас интересуют эти товары и услуги?',
                                      subtitle: _matchHint,
                                      categories: _productCategories,
                                      initialSelected: _matchedProductCodes,
                                    ),
                                    OnboardingInterestsPage(
                                      key: _placesKey,
                                      title:
                                          'Вам интересны эти места вокруг вас?',
                                      subtitle: _matchHint,
                                      categories: _placeCategories,
                                      initialSelected: _matchedPlaceCodes,
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                            GradientButton(
                              label: _continueLabel,
                              onPressed:
                                  _canContinue ? _onBottomContinue : null,
                            ),
                            const SizedBox(height: 88),
                          ],
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
          if (_step == 0)
            Align(
              alignment: Alignment.bottomCenter,
              child: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: TextButton(
                    onPressed:
                        _isSwitchingAccount ? null : _promptSwitchAccount,
                    style: TextButton.styleFrom(
                      foregroundColor: AppColors.textSecondary,
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                    ),
                    child: Text(
                      _isSwitchingAccount ? 'Выходим…' : 'Сменить аккаунт',
                      style: textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary.withValues(alpha: 0.75),
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
