import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Кнопка с градиентом «Войти».
///
/// Обычный ElevatedButton плохо дружит с LinearGradient, поэтому делаем
/// InkWell + DecoratedBox. Когда [onPressed] == null — кнопка disabled:
/// другой цвет и игнор нажатий.
class GradientButton extends StatelessWidget {
  const GradientButton({
    super.key,
    required this.label,
    required this.onPressed,
  });

  final String label;

  /// null ⇒ disabled (требование: пустые email/пароль).
  final VoidCallback? onPressed;

  bool get _enabled => onPressed != null;

  @override
  Widget build(BuildContext context) {
    return AnimatedOpacity(
      duration: const Duration(milliseconds: 180),
      opacity: _enabled ? 1 : 0.45,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          // InkWell рисует ripple; onTap: null отключает жест.
          onTap: onPressed,
          borderRadius: BorderRadius.circular(14),
          child: Ink(
            height: 52,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              gradient: LinearGradient(
                colors: _enabled
                    ? const [AppColors.gradientStart, AppColors.gradientEnd]
                    : const [AppColors.disabledButton, AppColors.disabledButton],
              ),
              boxShadow: _enabled
                  ? [
                      BoxShadow(
                        color: AppColors.accent.withValues(alpha: 0.35),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ]
                  : null,
            ),
            child: Center(
              child: Text(
                label,
                style: Theme.of(context).textTheme.labelLarge,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
