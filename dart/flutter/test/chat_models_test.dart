import 'package:city_vibe/core/api/models/user_models.dart';
import 'package:city_vibe/features/chat/domain/chat_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ChatMessage', () {
    const milana = ChatMessageAuthor(id: 40, name: 'Милана');
    const user = ChatMessageAuthor(id: 7, name: 'Иван');

    test('isOutgoingFor compares author id with current user', () {
      const message = ChatMessage(author: user, text: 'Привет');

      expect(message.isOutgoingFor(7), isTrue);
      expect(message.isOutgoingFor(40), isFalse);
    });

    test('ChatMessageAuthor.fromUserProfile maps profile fields', () {
      const profile = UserProfile(id: 3, name: 'Anna', avatarUrl: 'avatars/3/a.jpg');
      final author = ChatMessageAuthor.fromUserProfile(profile);

      expect(author.id, 3);
      expect(author.name, 'Anna');
      expect(author.avatarUrl, 'avatars/3/a.jpg');
      expect(author.username, isNull);
    });

    test('ChatDisplaySettings holds page-level flags', () {
      const settings = ChatDisplaySettings(
        showAvatars: true,
        showAuthorNames: false,
        showCurrentUserAvatar: true,
      );

      expect(settings.showAvatars, isTrue);
      expect(settings.showAuthorNames, isFalse);
      expect(settings.showCurrentUserAvatar, isTrue);
    });

    test('milana message is not outgoing for logged-in user', () {
      const message = ChatMessage(author: milana, text: 'Я рядом');

      expect(message.isOutgoingFor(7), isFalse);
    });
  });
}
