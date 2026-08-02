import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Пузырь сообщения в чате (Милана / пользователь).
class ChatBubble extends StatelessWidget {
  const ChatBubble({
    super.key,
    required this.text,
    this.isOutgoing = false,
    this.senderName,
    this.avatarUrl,
    this.time,
  });

  final String text;
  final bool isOutgoing;
  final String? senderName;
  final String? avatarUrl;
  final String? time;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final bubbleColor = isOutgoing
        ? AppColors.accent.withValues(alpha: 0.35)
        : AppColors.card;
    final align = isOutgoing ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final radius = BorderRadius.only(
      topLeft: const Radius.circular(18),
      topRight: const Radius.circular(18),
      bottomLeft: Radius.circular(isOutgoing ? 18 : 4),
      bottomRight: Radius.circular(isOutgoing ? 4 : 18),
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: align,
        children: [
          if (senderName != null && !isOutgoing)
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 4),
              child: Text(
                senderName!,
                style: textTheme.labelSmall?.copyWith(
                  color: AppColors.accent,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          Row(
            mainAxisAlignment:
                isOutgoing ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (!isOutgoing) ...[
                CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.accent.withValues(alpha: 0.25),
                  backgroundImage:
                      avatarUrl != null ? NetworkImage(avatarUrl!) : null,
                  child: avatarUrl == null
                      ? Icon(Icons.smart_toy_outlined,
                          size: 18, color: AppColors.accent)
                      : null,
                ),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  decoration: BoxDecoration(
                    color: bubbleColor,
                    borderRadius: radius,
                    border: Border.all(
                      color: isOutgoing
                          ? AppColors.accent.withValues(alpha: 0.4)
                          : AppColors.cardBorder,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(text, style: textTheme.bodyMedium),
                      if (time != null) ...[
                        const SizedBox(height: 6),
                        Align(
                          alignment: Alignment.bottomRight,
                          child: Text(
                            time!,
                            style: textTheme.labelSmall?.copyWith(
                              color: AppColors.textSecondary,
                              fontSize: 11,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
