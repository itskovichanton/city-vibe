import 'package:city_vibe/core/milana/milana_account.dart';
import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/chat/presentation/widgets/chat_bubble.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:city_vibe/features/onboarding/presentation/widgets/milana_hero_header.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

/// Приветствие от Миланы — служебный аккаунт из API, аватар в локальном кэше.
class MilanaGreetingScreen extends ConsumerWidget {
  const MilanaGreetingScreen({super.key});

  static const _bottomReserve = 200.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider).valueOrNull;
    final milanaAsync = ref.watch(milanaAccountProvider);
    final textTheme = Theme.of(context).textTheme;
    final userName = user?.name ?? 'друг';
    final timeLabel = DateFormat('HH:mm').format(DateTime.now());
    final milana = milanaAsync.valueOrNull;
    final categoryCodes = user?.favoriteCategories ?? const [];

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const LoginBackground(),
          SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                MilanaHeroHeader(
                  avatarLocalPath: milana?.avatarLocalPath,
                  avatarStorageKey: milana?.avatarStorageKey,
                  categoryCodes: categoryCodes,
                ),
                const SizedBox(height: 8),
                Text(
                  'Привет, $userName! 👋',
                  style: textTheme.headlineMedium,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                Expanded(
                  child: _ChatBody(
                    milana: milana,
                    timeLabel: timeLabel,
                    loadingMilana: milanaAsync.isLoading,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(24, 0, 24, 8),
                  child: GradientButton(
                    label: 'Начать путешествие с Миланой',
                    onPressed: () async {
                      await ref
                          .read(milanaWelcomeCompletedProvider.notifier)
                          .markCompleted();
                      if (!context.mounted) return;
                      context.go(AppRoutes.home);
                    },
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    'Я всегда с вами',
                    style: textTheme.bodySmall?.copyWith(
                      color: AppColors.textSecondary,
                    ),
                    textAlign: TextAlign.center,
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

class _ChatBody extends StatelessWidget {
  const _ChatBody({
    required this.milana,
    required this.timeLabel,
    required this.loadingMilana,
  });

  final MilanaAccount? milana;
  final String timeLabel;
  final bool loadingMilana;

  @override
  Widget build(BuildContext context) {
    final milanaName = milana?.name ?? 'Милана';
    final avatarLocalPath = milana?.avatarLocalPath;
    final avatarStorageKey = milana?.avatarStorageKey;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, MilanaGreetingScreen._bottomReserve),
      children: [
        if (loadingMilana && milana == null)
          const Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: Center(
              child: SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
          ),
        ChatBubble(
          senderName: milanaName,
          avatarUrl: avatarStorageKey,
          avatarLocalPath: avatarLocalPath,
          text:
              'Я — $milanaName, ваш персональный гид по городу. '
              'Я буду подбирать для вас лучшие места, события и скидки '
              'на основе ваших интересов.',
        ),
        ChatBubble(
          isOutgoing: true,
          showReadReceipt: true,
          text:
              'Отличный выбор категорий! 🎉 '
              'Давайте вместе найдём места, которые вам точно понравятся.',
          time: timeLabel,
        ),
        ChatBubble(
          senderName: milanaName,
          avatarUrl: avatarStorageKey,
          avatarLocalPath: avatarLocalPath,
          text: 'Я рядом и готова помочь вам в любое время. Поехали? 🚀',
          time: timeLabel,
        ),
      ],
    );
  }
}
