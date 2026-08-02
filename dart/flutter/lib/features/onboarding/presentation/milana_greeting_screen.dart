import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/chat/presentation/widgets/chat_bubble.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Приветствие от Миланы — статичный чат (заготовка под живой чат).
class MilanaGreetingScreen extends ConsumerWidget {
  const MilanaGreetingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider).valueOrNull;
    final milanaAsync = ref.watch(milanaAccountProvider);
    final textTheme = Theme.of(context).textTheme;
    final userName = user?.name ?? 'друг';

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const LoginBackground(),
          SafeArea(
            child: Column(
              children: [
              const SizedBox(height: 12),
              Text(
                'Привет, $userName! 👋',
                style: textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Expanded(
                child: milanaAsync.when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (_, __) => _ChatBody(
                    milanaName: 'Милана',
                    milanaAvatarUrl: null,
                    userName: userName,
                  ),
                  data: (milana) => _ChatBody(
                    milanaName: milana.name,
                    milanaAvatarUrl: milana.avatarUrl,
                    userName: userName,
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 8),
                child: GradientButton(
                  label: 'Начать путешествие с Миланой',
                  onPressed: () {
                    ref.read(milanaWelcomePendingProvider.notifier).state =
                        false;
                    context.go(AppRoutes.home);
                  },
                ),
              ),
              Text(
                'Я всегда с вами',
                style: textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 8),
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
    required this.milanaName,
    required this.milanaAvatarUrl,
    required this.userName,
  });

  final String milanaName;
  final String? milanaAvatarUrl;
  final String userName;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 100),
      children: [
        ChatBubble(
          senderName: milanaName,
          avatarUrl: milanaAvatarUrl,
          text:
              'Я — $milanaName, ваш персональный гид по городу. '
              'Я буду подбирать для вас лучшие места, события и скидки '
              'на основе ваших интересов.',
        ),
        ChatBubble(
          isOutgoing: true,
          text: 'Отличный выбор категорий! 🎉',
          time: '11:32',
        ),
        ChatBubble(
          senderName: milanaName,
          avatarUrl: milanaAvatarUrl,
          text:
              'Давайте вместе найдём места, которые вам точно понравятся.',
          time: '11:32',
        ),
        ChatBubble(
          senderName: milanaName,
          avatarUrl: milanaAvatarUrl,
          text: 'Я рядом и готова помочь вам в любое время. Поехали? 🚀',
          time: '11:32',
        ),
      ],
    );
  }
}
