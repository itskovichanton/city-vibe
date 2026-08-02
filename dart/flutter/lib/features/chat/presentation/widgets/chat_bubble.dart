import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:city_vibe/core/network/media_url_resolver.dart';
import 'package:city_vibe/features/chat/domain/chat_models.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Пузырь сообщения в чате с автором и настройками отображения.
class ChatBubble extends StatelessWidget {
  const ChatBubble({
    super.key,
    required this.message,
    required this.currentUserId,
    required this.settings,
  });

  final ChatMessage message;
  final int currentUserId;
  final ChatDisplaySettings settings;

  bool get _isOutgoing => message.isOutgoingFor(currentUserId);

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final author = message.author;
    final bubbleColor = _isOutgoing
        ? AppColors.accent.withValues(alpha: 0.35)
        : AppColors.card;
    final align =
        _isOutgoing ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final radius = BorderRadius.only(
      topLeft: const Radius.circular(18),
      topRight: const Radius.circular(18),
      bottomLeft: Radius.circular(_isOutgoing ? 18 : 4),
      bottomRight: Radius.circular(_isOutgoing ? 4 : 18),
    );
    final showIncomingAvatar = settings.showAvatars && !_isOutgoing;
    final showOutgoingAvatar =
        settings.showCurrentUserAvatar && _isOutgoing;
    final showName = settings.showAuthorNames;

    final bubble = Flexible(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: radius,
          border: Border.all(
            color: _isOutgoing
                ? AppColors.accent.withValues(alpha: 0.4)
                : AppColors.cardBorder,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message.text, style: textTheme.bodyMedium),
            if (message.time != null) ...[
              const SizedBox(height: 6),
              Align(
                alignment: Alignment.bottomRight,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      message.time!,
                      style: textTheme.labelSmall?.copyWith(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                      ),
                    ),
                    if (message.showReadReceipt) ...[
                      const SizedBox(width: 4),
                      Icon(
                        Icons.done_all_rounded,
                        size: 14,
                        color: Colors.lightBlueAccent.withValues(alpha: 0.9),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );

    final avatar = _ChatMessageAvatar(
      author: author,
      isOutgoing: _isOutgoing,
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: align,
        children: [
          if (showName)
            Padding(
              padding: EdgeInsets.only(
                left: _isOutgoing ? 0 : 4,
                right: _isOutgoing ? 4 : 0,
                bottom: 4,
              ),
              child: Text(
                author.name,
                style: textTheme.labelSmall?.copyWith(
                  color: AppColors.accent,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          Row(
            mainAxisAlignment: _isOutgoing
                ? MainAxisAlignment.end
                : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (showIncomingAvatar) ...[
                avatar,
                const SizedBox(width: 8),
              ],
              bubble,
              if (showOutgoingAvatar) ...[
                const SizedBox(width: 8),
                avatar,
              ],
            ],
          ),
        ],
      ),
    );
  }
}

class _ChatMessageAvatar extends StatelessWidget {
  const _ChatMessageAvatar({
    required this.author,
    required this.isOutgoing,
  });

  static const _radius = 16.0;

  final ChatMessageAuthor author;
  final bool isOutgoing;

  @override
  Widget build(BuildContext context) {
    final imageUrl = MediaUrlResolver.resolve(author.avatarUrl);
    final image = _avatarImage(author.avatarLocalPath, imageUrl);

    return Container(
      width: _radius * 2,
      height: _radius * 2,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: isOutgoing
              ? AppColors.accent.withValues(alpha: 0.55)
              : AppColors.cardBorder,
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.12),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ClipOval(
        child: image != null
            ? Image(
                image: image,
                width: _radius * 2,
                height: _radius * 2,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => _fallback(),
              )
            : _fallback(),
      ),
    );
  }

  Widget _fallback() {
    return ColoredBox(
      color: isOutgoing
          ? AppColors.accent.withValues(alpha: 0.22)
          : AppColors.accent.withValues(alpha: 0.12),
      child: Icon(
        Icons.person_outline_rounded,
        size: 18,
        color: isOutgoing ? AppColors.accent : AppColors.textSecondary,
      ),
    );
  }

  ImageProvider? _avatarImage(String? localPath, String? remoteUrl) {
    if (localPath != null &&
        localPath.isNotEmpty &&
        File(localPath).existsSync()) {
      return FileImage(File(localPath));
    }
    if (remoteUrl != null) {
      return CachedNetworkImageProvider(remoteUrl);
    }
    return null;
  }
}
