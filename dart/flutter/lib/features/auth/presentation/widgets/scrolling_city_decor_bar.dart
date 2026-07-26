import 'dart:async';
import 'dart:ui' as ui;

import 'package:city_vibe/core/device/device_capability.dart';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

/// Нижняя декоративная полоса: контейнер зафиксирован у низа экрана,
/// а бесшовная картинка города едет с постоянной скоростью слева направо.
///
/// На слабых устройствах ([isWeakDevice]) анимация отключена — статичный кадр.
///
/// Рисуем одну декодированную [ui.Image] многократно подряд
/// (`… | city | city | city | …`), чтобы ширины экрана всегда хватало.
class ScrollingCityDecorBar extends StatefulWidget {
  const ScrollingCityDecorBar({
    super.key,
    this.height = 168,
    /// Логических пикселей в секунду — постоянная скорость без ускорений.
    this.speed = 10,
  });

  final double height;
  final double speed;

  static const assetPath = 'assets/images/decor_bar_bottom_city_long.png';

  @override
  State<ScrollingCityDecorBar> createState() => _ScrollingCityDecorBarState();
}

class _ScrollingCityDecorBarState extends State<ScrollingCityDecorBar>
    with SingleTickerProviderStateMixin {
  Ticker? _ticker;
  late final _ScrollPhase _phase;
  ui.Image? _image;
  late final bool _animate;

  @override
  void initState() {
    super.initState();
    _phase = _ScrollPhase();
    _animate = !isWeakDevice();
    if (_animate) {
      _ticker = createTicker((elapsed) {
        // Линейный рост времени → одинаковая скорость; стык через % в painter.
        _phase.value = elapsed.inMicroseconds / 1e6 * widget.speed;
      })..start();
    }
    _loadImage();
  }

  Future<void> _loadImage() async {
    final resolved = await _resolveAssetImage(ScrollingCityDecorBar.assetPath);
    if (!mounted) {
      resolved.dispose();
      return;
    }
    setState(() => _image = resolved);
  }

  Future<ui.Image> _resolveAssetImage(String path) {
    final completer = Completer<ui.Image>();
    final stream = AssetImage(path).resolve(ImageConfiguration.empty);
    late final ImageStreamListener listener;
    listener = ImageStreamListener(
      (info, _) {
        stream.removeListener(listener);
        completer.complete(info.image.clone());
      },
      onError: (error, stack) {
        stream.removeListener(listener);
        completer.completeError(error, stack);
      },
    );
    stream.addListener(listener);
    return completer.future;
  }

  @override
  void dispose() {
    _ticker?.dispose();
    _phase.dispose();
    _image?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final image = _image;
    return IgnorePointer(
      child: SizedBox(
        height: widget.height,
        width: double.infinity,
        child: image == null
            ? const SizedBox.expand()
            : ClipRect(
                child: CustomPaint(
                  // repaint только canvas, без setState всего дерева.
                  painter: _SeamlessCityPainter(
                    image: image,
                    phase: _phase,
                    leftToRight: true,
                    animate: _animate,
                  ),
                  isComplex: true,
                  willChange: _animate,
                ),
              ),
      ),
    );
  }
}

/// Линейный сдвиг в px; [Listenable] для перерисовки CustomPaint.
class _ScrollPhase extends ChangeNotifier {
  double _value = 0;

  double get value => _value;

  set value(double v) {
    if (_value == v) return;
    _value = v;
    notifyListeners();
  }
}

class _SeamlessCityPainter extends CustomPainter {
  _SeamlessCityPainter({
    required this.image,
    required this.phase,
    required this.leftToRight,
    required this.animate,
  }) : super(repaint: animate ? phase : null);

  final ui.Image image;
  final _ScrollPhase phase;
  final bool leftToRight;
  final bool animate;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;

    final scale = size.height / image.height;
    final tileW = image.width * scale;
    if (tileW <= 0) return;

    // Фаза внутри одной плитки — непрерывная, без прыжка на цикле.
    // На слабых устройствах phase.value == 0 → статичный город.
    final scrolled = animate ? (phase.value % tileW) : 0.0;

    // LTR: содержимое уезжает вправо.
    // Слева всегда дорисовываем предыдущую копию той же картинки.
    final startX = leftToRight ? (-tileW + scrolled) : (-scrolled);

    final paint = Paint()
      ..isAntiAlias = true
      ..filterQuality = animate ? FilterQuality.medium : FilterQuality.low;

    final src = Rect.fromLTWH(
      0,
      0,
      image.width.toDouble(),
      image.height.toDouble(),
    );

    for (var x = startX; x < size.width; x += tileW) {
      canvas.drawImageRect(
        image,
        src,
        Rect.fromLTWH(x, 0, tileW, size.height),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _SeamlessCityPainter oldDelegate) {
    return oldDelegate.image != image ||
        oldDelegate.leftToRight != leftToRight ||
        oldDelegate.animate != animate ||
        oldDelegate.phase != phase;
  }
}
