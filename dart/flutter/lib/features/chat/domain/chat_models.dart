import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/core/milana/milana_account.dart';

/// Автор сообщения в чате (сокращённый профиль).
class ChatMessageAuthor {
  const ChatMessageAuthor({
    required this.id,
    required this.name,
    this.username,
    this.avatarUrl,
    this.avatarLocalPath,
  });

  final int id;
  final String name;
  final String? username;
  final String? avatarUrl;
  final String? avatarLocalPath;

  factory ChatMessageAuthor.fromUserProfile(
    UserProfile profile, {
    String? avatarLocalPath,
  }) {
    return ChatMessageAuthor(
      id: profile.id,
      name: profile.name,
      avatarUrl: profile.avatarUrl,
      avatarLocalPath: avatarLocalPath,
    );
  }

  factory ChatMessageAuthor.fromMilanaAccount(MilanaAccount account) {
    return ChatMessageAuthor(
      id: account.profile.id,
      name: account.name,
      avatarUrl: account.avatarStorageKey,
      avatarLocalPath: account.avatarLocalPath,
    );
  }
}

/// Сообщение в групповом чате.
class ChatMessage {
  const ChatMessage({
    required this.author,
    required this.text,
    this.time,
    this.showReadReceipt = false,
  });

  final ChatMessageAuthor author;
  final String text;
  final String? time;
  final bool showReadReceipt;

  bool isOutgoingFor(int currentUserId) => author.id == currentUserId;
}

/// Настройки отображения чата на конкретном экране.
class ChatDisplaySettings {
  const ChatDisplaySettings({
    required this.showAvatars,
    required this.showAuthorNames,
    required this.showCurrentUserAvatar,
  });

  /// Показывать аватарки других участников (слева у входящих).
  final bool showAvatars;

  /// Подписывать имена авторов над пузырями.
  final bool showAuthorNames;

  /// Показывать аватар текущего пользователя (справа у исходящих).
  final bool showCurrentUserAvatar;
}
