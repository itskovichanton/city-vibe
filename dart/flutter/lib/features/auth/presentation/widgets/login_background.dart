import 'package:flutter/material.dart';

/// Фон экрана логина — растровый макет из assets.
class LoginBackground extends StatelessWidget {
  const LoginBackground({super.key});

  static const assetPath = 'assets/images/bg.png';

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      assetPath,
      fit: BoxFit.cover,
      width: double.infinity,
      height: double.infinity,
      alignment: Alignment.center,
    );
  }
}
