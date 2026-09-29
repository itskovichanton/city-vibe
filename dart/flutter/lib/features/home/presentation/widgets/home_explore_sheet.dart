import 'package:city_vibe/core/milana/milana_account.dart';
import 'package:city_vibe/features/onboarding/onboarding_providers.dart';
import 'package:city_vibe/features/onboarding/presentation/widgets/milana_avatar_image.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Панель поверх карты: шапка / половина / почти весь экран.
class HomeExploreSheet extends ConsumerWidget {
  const HomeExploreSheet({super.key});

  static const collapsedSize = 0.22;
  static const halfSize = 0.52;
  static const expandedSize = 1.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final milana = ref.watch(milanaAccountProvider).valueOrNull;

    return DraggableScrollableSheet(
      initialChildSize: halfSize,
      minChildSize: collapsedSize,
      maxChildSize: expandedSize,
      snap: true,
      snapSizes: const [collapsedSize, halfSize, expandedSize],
      builder: (context, scrollController) {
        return DecoratedBox(
          decoration: const BoxDecoration(
            color: Color(0xF20E0A18),
            borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
            border: Border(
              top: BorderSide(color: Color(0x33FFFFFF)),
            ),
            boxShadow: [
              BoxShadow(
                color: Color(0x66000000),
                blurRadius: 24,
                offset: Offset(0, -4),
              ),
            ],
          ),
          child: ListView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(14, 6, 14, 20),
            children: [
              const _GrabHandle(),
              _SheetHeaderCards(milana: milana),
              const SizedBox(height: 14),
              const _ActionChipsRow(),
              const SizedBox(height: 16),
              const _SchematicPostCard(),
              const SizedBox(height: 12),
              const _SchematicComment(),
              const SizedBox(height: 14),
              const _SchematicComposer(),
            ],
          ),
        );
      },
    );
  }
}

class _GrabHandle extends StatelessWidget {
  const _GrabHandle();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        width: 36,
        height: 4,
        margin: const EdgeInsets.only(bottom: 10),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.28),
          borderRadius: BorderRadius.circular(99),
        ),
      ),
    );
  }
}

class _SheetHeaderCards extends StatelessWidget {
  const _SheetHeaderCards({this.milana});

  final MilanaAccount? milana;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _PersonCard(
            title: milana?.name ?? 'Милана',
            subtitle: 'ИИ-ассистент',
            leading: ClipOval(
              child: MilanaAvatarImage(
                localPath: milana?.avatarLocalPath,
                storageKey: milana?.avatarStorageKey,
                size: 44,
              ),
            ),
          ),
        ),
        const SizedBox(width: 10),
        const Expanded(
          child: _PersonCard(
            title: 'Ёмкость',
            subtitle: 'Бар · 0,2 км',
            leading: _PlaceThumb(),
          ),
        ),
      ],
    );
  }
}

class _PersonCard extends StatelessWidget {
  const _PersonCard({
    required this.title,
    required this.subtitle,
    required this.leading,
  });

  final String title;
  final String subtitle;
  final Widget leading;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 8, 10, 8),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1328),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0x22FFFFFF)),
      ),
      child: Row(
        children: [
          leading,
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
                Text(
                  subtitle,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PlaceThumb extends StatelessWidget {
  const _PlaceThumb();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF5B2BFF), Color(0xFF1A1228)],
        ),
      ),
      child:
          const Icon(Icons.sports_bar_outlined, color: Colors.white, size: 22),
    );
  }
}

class _ActionChipsRow extends StatelessWidget {
  const _ActionChipsRow();

  @override
  Widget build(BuildContext context) {
    const items = <(IconData, String)>[
      (Icons.event_seat_outlined, 'Бронь стола'),
      (Icons.local_offer_outlined, 'Спец. предложения'),
      (Icons.inventory_2_outlined, 'Бюро находок'),
      (Icons.chat_bubble_outline, 'Флудилка'),
    ];
    return SizedBox(
      height: 36,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: items.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final item = items[index];
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1328),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0x33FFFFFF)),
            ),
            child: Row(
              children: [
                Icon(item.$1, size: 16, color: AppColors.textSecondary),
                const SizedBox(width: 6),
                Text(
                  item.$2,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _SchematicPostCard extends StatelessWidget {
  const _SchematicPostCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF161022),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0x22FFFFFF)),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(12, 12, 12, 8),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 14,
                  backgroundColor: Color(0xFF5B2BFF),
                  child: Icon(Icons.sports_bar, size: 16, color: Colors.white),
                ),
                SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Ёмкость',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                        ),
                      ),
                      Text(
                        'Сегодня, 18:30',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Container(
            height: 140,
            width: double.infinity,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [Color(0xFF2A1038), Color(0xFF5B2BFF)],
              ),
            ),
            padding: const EdgeInsets.all(16),
            alignment: Alignment.centerRight,
            child: const Text(
              '2 ПИВА\nПО ЦЕНЕ 1\n+\nГРЕНКИ\nЗА 500 ₽',
              textAlign: TextAlign.right,
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w800,
                fontSize: 18,
                height: 1.15,
                shadows: [Shadow(color: AppColors.accent, blurRadius: 12)],
              ),
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(12, 10, 12, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Два пива по цене одного + гренки за 500 руб.\nАкция действует сегодня до 00:00!',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    height: 1.35,
                  ),
                ),
                SizedBox(height: 8),
                Row(
                  children: [
                    Icon(Icons.favorite, size: 16, color: Color(0xFFFF4D67)),
                    SizedBox(width: 4),
                    Text(
                      '10',
                      style: TextStyle(
                          color: AppColors.textSecondary, fontSize: 12),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SchematicComment extends StatelessWidget {
  const _SchematicComment();

  @override
  Widget build(BuildContext context) {
    return const Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CircleAvatar(
          radius: 16,
          backgroundColor: Color(0xFF3A2A55),
          child: Text('И', style: TextStyle(color: Colors.white, fontSize: 13)),
        ),
        SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Илья_89  ·  Сегодня, 18:45',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 11),
              ),
              SizedBox(height: 2),
              Text(
                'Круто! Мы придём! 🍻',
                style: TextStyle(color: AppColors.textPrimary, fontSize: 13),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SchematicComposer extends StatelessWidget {
  const _SchematicComposer();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Container(
        height: 44,
        padding: const EdgeInsets.symmetric(horizontal: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1328),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: const Color(0x33FFFFFF)),
        ),
        child: const Row(
          children: [
            Icon(Icons.add, color: AppColors.accent),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Напишите сообщение...',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
              ),
            ),
            Icon(Icons.mic_none_rounded, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}
