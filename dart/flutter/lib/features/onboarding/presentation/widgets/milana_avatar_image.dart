import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:city_vibe/core/network/media_url_resolver.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Аватар Миланы: локальный файл → сеть → placeholder.
class MilanaAvatarImage extends StatelessWidget {
  const MilanaAvatarImage({
    super.key,
    this.localPath,
    this.storageKey,
    this.size = 96,
  });

  final String? localPath;
  final String? storageKey;
  final double size;

  @override
  Widget build(BuildContext context) {
    final local = localPath;
    if (local != null && local.isNotEmpty && File(local).existsSync()) {
      return Image.file(
        File(local),
        width: size,
        height: size,
        fit: BoxFit.cover,
      );
    }

    final url = MediaUrlResolver.resolve(storageKey);
    if (url != null) {
      return CachedNetworkImage(
        imageUrl: url,
        width: size,
        height: size,
        fit: BoxFit.cover,
        placeholder: (_, __) => _placeholder(),
        errorWidget: (_, __, ___) => _placeholder(),
      );
    }

    return _placeholder();
  }

  Widget _placeholder() {
    return Container(
      width: size,
      height: size,
      color: AppColors.accent.withValues(alpha: 0.2),
      child: Icon(
        Icons.smart_toy_outlined,
        size: size * 0.45,
        color: AppColors.accent,
      ),
    );
  }
}
