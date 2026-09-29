import 'package:flutter/material.dart';

/// Заглушка карты (Google Maps подключим, когда будет API-ключ).
class HomeMapBackdrop extends StatelessWidget {
  const HomeMapBackdrop({super.key});

  static const assetPath = 'assets/images/home_map_placeholder.jpg';

  @override
  Widget build(BuildContext context) {
    return const ColoredBox(
      color: Color(0xFF07060C),
      child: Image(
        image: AssetImage(assetPath),
        fit: BoxFit.cover,
        width: double.infinity,
        height: double.infinity,
        alignment: Alignment.center,
      ),
    );
  }
}
