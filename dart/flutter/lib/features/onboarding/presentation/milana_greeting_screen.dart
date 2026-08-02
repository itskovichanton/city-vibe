import 'dart:async';

import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/audio/ambient_music.dart';
import 'package:city_vibe/core/milana/milana_account.dart';
import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/core/user/user_providers.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/chat/chat.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:city_vibe/features/onboarding/presentation/widgets/milana_hero_header.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

/// Приветствие от Миланы — служебный аккаунт из API, аватар в локальном кэше.
class MilanaGreetingScreen extends ConsumerWidget {
  const MilanaGreetingScreen({super.key});

  static const _bottomReserve = 200.0;

  static const _chatSettings = ChatDisplaySettings(
    showAvatars: true,
    showAuthorNames: false,
    showCurrentUserAvatar: true,
  );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider).valueOrNull;
    final milanaAsync = ref.watch(milanaAccountProvider);
    final textTheme = Theme.of(context).textTheme;
    final userName = user?.name ?? 'друг';
    final milana = milanaAsync.valueOrNull;
    final categoryCodes = user?.favoriteCategories ?? const [];
    final messages = _milanaGreetingMessages(
      milana: milana,
      user: user,
      timeLabel: DateFormat('HH:mm').format(DateTime.now()),
    );

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
                  child: ChatView(
                    messages: messages,
                    currentUserId: user?.id ?? 0,
                    settings: _chatSettings,
                    loading: milanaAsync.isLoading && milana == null,
                    padding: const EdgeInsets.fromLTRB(
                      20,
                      0,
                      20,
                      _bottomReserve,
                    ),
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
                      unawaited(AmbientMusic.ensurePlaying());
                      if (!context.mounted) return;
                      context.go(AppRoutes.home);
                    },
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

List<ChatMessage> _milanaGreetingMessages({
  required MilanaAccount? milana,
  required UserProfile? user,
  required String timeLabel,
}) {
  final milanaAuthor = milana != null
      ? ChatMessageAuthor.fromMilanaAccount(milana)
      : const ChatMessageAuthor(id: 40, name: 'Милана');
  final userAuthor = user != null
      ? ChatMessageAuthor.fromUserProfile(user)
      : const ChatMessageAuthor(id: 0, name: 'Вы');

  return [
    ChatMessage(
      author: milanaAuthor,
      text:
          'Я — ${milanaAuthor.name}, ваш персональный гид по городу. '
          'Я буду подбирать для вас лучшие места, события и скидки '
          'на основе ваших интересов.',
    ),
    ChatMessage(
      author: userAuthor,
      text:
          'Привет, Милана! 🎉 '
          'Давай вместе найдём места, которые мне точно понравятся.',
      time: timeLabel,
      showReadReceipt: true,
    ),
    ChatMessage(
      author: milanaAuthor,
      text: 'Я рядом и готова помочь вам в любое время. Поехали? 🚀',
      time: timeLabel,
    ),
  ];
}
