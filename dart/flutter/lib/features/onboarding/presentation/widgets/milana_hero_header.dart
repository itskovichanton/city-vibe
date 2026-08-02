import 'package:city_vibe/features/onboarding/presentation/widgets/milana_avatar_image.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Шапка экрана приветствия: карта, пины категорий, аватар Миланы.
class MilanaHeroHeader extends StatelessWidget {
  const MilanaHeroHeader({
    super.key,
    required this.avatarLocalPath,
    required this.avatarStorageKey,
    this.categoryCodes = const [],
  });

  final String? avatarLocalPath;
  final String? avatarStorageKey;
  final List<String> categoryCodes;

  static const _avatarSize = 108.0;

  @override
  Widget build(BuildContext context) {
    final pins = _resolvePins(categoryCodes);

    return SizedBox(
      height: 200,
      child: Stack(
        alignment: Alignment.center,
        clipBehavior: Clip.none,
        children: [
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    AppColors.backgroundDeep.withValues(alpha: 0.35),
                    Colors.transparent,
                  ],
                ),
              ),
              child: CustomPaint(
                painter: _MapGridPainter(),
              ),
            ),
          ),
          for (var i = 0; i < pins.length; i++)
            _CategoryPin(
              icon: pins[i].$1,
              color: pins[i].$2,
              alignment: _pinAlignments[i],
            ),
          Container(
            width: _avatarSize + 10,
            height: _avatarSize + 10,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: AppColors.accent.withValues(alpha: 0.55),
                  blurRadius: 28,
                  spreadRadius: 2,
                ),
              ],
              border: Border.all(
                color: AppColors.accent.withValues(alpha: 0.85),
                width: 3,
              ),
            ),
            child: ClipOval(
              child: MilanaAvatarImage(
                localPath: avatarLocalPath,
                storageKey: avatarStorageKey,
                size: _avatarSize,
              ),
            ),
          ),
        ],
      ),
    );
  }

  static const _pinAlignments = [
    Alignment(-0.92, -0.35),
    Alignment(0.95, -0.25),
    Alignment(-0.75, 0.55),
    Alignment(0.82, 0.45),
  ];

  List<(IconData, Color)> _resolvePins(List<String> codes) {
    const defaults = [
      (Icons.theater_comedy_outlined, Color(0xFFFF6B8A)),
      (Icons.local_bar_outlined, Color(0xFFB24BFF)),
      (Icons.local_cafe_outlined, Color(0xFF5ECF7A)),
      (Icons.restaurant_outlined, Color(0xFFFFD54F)),
    ];

    if (codes.isEmpty) return defaults;

    final mapped = <(IconData, Color)>[];
    for (final code in codes.take(4)) {
      mapped.add(_iconForCategory(code));
    }
    while (mapped.length < 4 && mapped.length < defaults.length) {
      mapped.add(defaults[mapped.length]);
    }
    return mapped;
  }

  (IconData, Color) _iconForCategory(String code) {
    return switch (code) {
      'theaters' || 'theater' => (Icons.theater_comedy_outlined, const Color(0xFFFF6B8A)),
      'bars' || 'nightlife' => (Icons.local_bar_outlined, AppColors.accent),
      'cafes' || 'coffee' => (Icons.local_cafe_outlined, const Color(0xFF5ECF7A)),
      'restaurants' || 'food' => (Icons.restaurant_outlined, const Color(0xFFFFD54F)),
      'parks' => (Icons.park_outlined, const Color(0xFF66BB6A)),
      'museums' => (Icons.museum_outlined, const Color(0xFF64B5F6)),
      _ => (Icons.place_outlined, AppColors.accent),
    };
  }
}

class _CategoryPin extends StatelessWidget {
  const _CategoryPin({
    required this.icon,
    required this.color,
    required this.alignment,
  });

  final IconData icon;
  final Color color;
  final Alignment alignment;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: alignment,
      child: Container(
        width: 34,
        height: 34,
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.92),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: 0.45),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Icon(icon, size: 18, color: Colors.white),
      ),
    );
  }
}

class _MapGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withValues(alpha: 0.04)
      ..strokeWidth = 1;

    const step = 28.0;
    for (var x = 0.0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (var y = 0.0; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }

    final road = Paint()
      ..color = Colors.white.withValues(alpha: 0.06)
      ..strokeWidth = 2;
    canvas.drawLine(
      Offset(size.width * 0.15, size.height * 0.2),
      Offset(size.width * 0.85, size.height * 0.75),
      road,
    );
    canvas.drawLine(
      Offset(size.width * 0.8, size.height * 0.15),
      Offset(size.width * 0.25, size.height * 0.85),
      road,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
