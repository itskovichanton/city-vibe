import 'dart:math' as math;

import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Декоративный фон экрана логина: ночная карта + неон-скайлайн.
///
/// Почему CustomPaint, а не картинка целиком?
/// Макет — это уже готовый скрин с формой. Если положить его как Image,
/// получится «двойной» UI (нарисованная форма + наша форма).
/// Поэтому атмосферу рисуем сами, а форму собираем виджетами.
class LoginBackground extends StatelessWidget {
  const LoginBackground({super.key});

  @override
  Widget build(BuildContext context) {
    return const Stack(
      fit: StackFit.expand,
      children: [
        // 1) Базовый градиент ночи.
        DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF0B0714),
                AppColors.background,
                Color(0xFF1A0B2E),
              ],
            ),
          ),
        ),
        // 2) «Карта» с пинами в верхней половине.
        CustomPaint(painter: _MapPinsPainter()),
        // 3) Неоновый силуэт города снизу.
        Align(
          alignment: Alignment.bottomCenter,
          child: SizedBox(
            height: 220,
            width: double.infinity,
            child: CustomPaint(painter: _NeonSkylinePainter()),
          ),
        ),
        // 4) Затемнение по центру, чтобы карточка читалась.
        DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0x66000000),
                Color(0x99000000),
                Color(0xCC07060C),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

/// Рисует сетку «улиц» и цветные точки-пины (еда, музыка…).
class _MapPinsPainter extends CustomPainter {
  const _MapPinsPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()
      ..color = const Color(0x22FFFFFF)
      ..strokeWidth = 1;

    // Редкая сетка — намёк на карту, не чертёж.
    const step = 42.0;
    for (double x = 0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height * 0.55), grid);
    }
    for (double y = 0; y < size.height * 0.55; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }

    // Несколько «пинов» с разными цветами.
    final pins = <(Offset, Color)>[
      (Offset(size.width * 0.18, size.height * 0.12), const Color(0xFFFF4D6D)),
      (Offset(size.width * 0.72, size.height * 0.10), const Color(0xFF4D9FFF)),
      (Offset(size.width * 0.55, size.height * 0.22), const Color(0xFFB24BFF)),
      (Offset(size.width * 0.30, size.height * 0.28), const Color(0xFFFFC14D)),
      (Offset(size.width * 0.82, size.height * 0.30), const Color(0xFF4DFFB5)),
      (Offset(size.width * 0.12, size.height * 0.38), const Color(0xFFFF6BCB)),
    ];

    for (final (pos, color) in pins) {
      final glow = Paint()
        ..color = color.withValues(alpha: 0.35)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);
      canvas.drawCircle(pos, 10, glow);
      canvas.drawCircle(pos, 4.5, Paint()..color = color);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Упрощённый неон-скайлайн (колесо обозрения + дома + мост).
class _NeonSkylinePainter extends CustomPainter {
  const _NeonSkylinePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()..moveTo(0, size.height);

    // Силуэт слева направо — ломаная «крыш».
    final peaks = <Offset>[
      Offset(0, size.height * 0.75),
      Offset(size.width * 0.08, size.height * 0.55),
      Offset(size.width * 0.14, size.height * 0.70),
      Offset(size.width * 0.22, size.height * 0.40),
      Offset(size.width * 0.28, size.height * 0.62),
      Offset(size.width * 0.38, size.height * 0.35),
      Offset(size.width * 0.46, size.height * 0.58),
      Offset(size.width * 0.55, size.height * 0.28),
      Offset(size.width * 0.62, size.height * 0.50),
      Offset(size.width * 0.72, size.height * 0.32),
      Offset(size.width * 0.80, size.height * 0.55),
      Offset(size.width * 0.90, size.height * 0.38),
      Offset(size.width, size.height * 0.60),
    ];
    for (final p in peaks) {
      path.lineTo(p.dx, p.dy);
    }
    path
      ..lineTo(size.width, size.height)
      ..close();

    final fill = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0xFF5B2BFF), Color(0xFF1A0B2E)],
      ).createShader(Offset.zero & size);
    canvas.drawPath(path, fill);

    // Обводка неона по контуру.
    final stroke = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..color = const Color(0xAACF7BFF)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2);
    canvas.drawPath(path, stroke);

    // Колесо обозрения (намёк на макет).
    final wheelCenter = Offset(size.width * 0.78, size.height * 0.42);
    final wheelPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..color = const Color(0xFFB24BFF);
    canvas.drawCircle(wheelCenter, 28, wheelPaint);
    for (var i = 0; i < 8; i++) {
      final a = (i / 8) * math.pi * 2;
      canvas.drawLine(
        wheelCenter,
        wheelCenter + Offset(math.cos(a), math.sin(a)) * 28,
        wheelPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
