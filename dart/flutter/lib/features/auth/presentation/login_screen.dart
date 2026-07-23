import 'package:city_vibe/features/auth/presentation/widgets/auth_text_field.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/social_login_button.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';

/// Экран логина — вёрстка по макету + минимальная UI-логика.
///
/// StatefulWidget нужен, потому что экран **хранит изменяемое состояние**:
/// - текст в полях (через контроллеры + setState для кнопки),
/// - скрыт/показан пароль (`_obscurePassword`).
///
/// Позже сюда прикрутим API auth-service; сейчас onPressed только заглушка.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  /// Контроллеры — «источник правды» для текста полей.
  /// Их обязательно dispose(), иначе утечка памяти.
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  /// true = пароль скрыт точками; false = виден открытым текстом.
  bool _obscurePassword = true;

  /// Кнопка «Войти» активна только если оба поля не пустые (после trim).
  bool get _canSubmit {
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();
    return email.isNotEmpty && password.isNotEmpty;
  }

  @override
  void dispose() {
    // Симметрично create: всё, что создали в State — освобождаем здесь.
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _onFieldsChanged(String _) {
    // TextField сам обновляет controller, но виджет кнопки не узнает об этом,
    // пока мы не вызовем setState → rebuild → пересчёт `_canSubmit`.
    setState(() {});
  }

  void _togglePasswordVisibility() {
    setState(() => _obscurePassword = !_obscurePassword);
  }

  void _onLoginPressed() {
    // Заглушка: логику API добавим позже.
    // ScaffoldMessenger — стандартный способ показать SnackBar.
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Скоро здесь будет реальный вход через api-gateway'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    // SafeArea учитывает notch / status bar / home indicator.
    // LayoutBuilder + SingleChildScrollView — чтобы на маленьких экранах
    // и при открытой клавиатуре форма скроллилась, а не обрезалась.
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const LoginBackground(),
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: ConstrainedBox(
                  // На широких устройствах / web карточка не растягивается бесконечно.
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: Column(
                    children: [
                      _BrandHeader(textTheme: textTheme),
                      const SizedBox(height: 28),
                      _LoginCard(
                        textTheme: textTheme,
                        emailController: _emailController,
                        passwordController: _passwordController,
                        obscurePassword: _obscurePassword,
                        canSubmit: _canSubmit,
                        onFieldsChanged: _onFieldsChanged,
                        onTogglePassword: _togglePasswordVisibility,
                        onLoginPressed: _canSubmit ? _onLoginPressed : null,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Логотип + название + слоган над карточкой.
class _BrandHeader extends StatelessWidget {
  const _BrandHeader({required this.textTheme});

  final TextTheme textTheme;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Круглый логотип (пока геометрическая заглушка под макет).
        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              colors: [AppColors.gradientStart, AppColors.gradientEnd],
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.accent.withValues(alpha: 0.45),
                blurRadius: 20,
              ),
            ],
          ),
          child: const Icon(Icons.nightlife, color: Colors.white, size: 34),
        ),
        const SizedBox(height: 12),
        Text('CityVibe', style: textTheme.displayLarge),
        const SizedBox(height: 8),
        Text(
          'Ваш гид по лучшим событиям и местам в городе',
          textAlign: TextAlign.center,
          style: textTheme.bodyMedium?.copyWith(
            color: AppColors.textPrimary.withValues(alpha: 0.9),
          ),
        ),
      ],
    );
  }
}

/// Полупрозрачная карточка с формой.
class _LoginCard extends StatelessWidget {
  const _LoginCard({
    required this.textTheme,
    required this.emailController,
    required this.passwordController,
    required this.obscurePassword,
    required this.canSubmit,
    required this.onFieldsChanged,
    required this.onTogglePassword,
    required this.onLoginPressed,
  });

  final TextTheme textTheme;
  final TextEditingController emailController;
  final TextEditingController passwordController;
  final bool obscurePassword;
  final bool canSubmit;
  final ValueChanged<String> onFieldsChanged;
  final VoidCallback onTogglePassword;
  final VoidCallback? onLoginPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 24,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Добро пожаловать!', style: textTheme.headlineMedium),
          const SizedBox(height: 6),
          Text('Войдите, чтобы продолжить', style: textTheme.bodyMedium),
          const SizedBox(height: 22),

          AuthTextField(
            controller: emailController,
            hintText: 'Email',
            prefixIcon: Icons.mail_outline_rounded,
            keyboardType: TextInputType.emailAddress,
            onChanged: onFieldsChanged,
          ),
          const SizedBox(height: 12),
          AuthTextField(
            controller: passwordController,
            hintText: 'Пароль',
            prefixIcon: Icons.lock_outline_rounded,
            obscureText: obscurePassword,
            onChanged: onFieldsChanged,
            // IconButton — доступная зона нажатия для «глаза».
            suffix: IconButton(
              onPressed: onTogglePassword,
              tooltip: obscurePassword ? 'Показать пароль' : 'Скрыть пароль',
              icon: Icon(
                obscurePassword
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined,
                color: AppColors.textSecondary,
              ),
            ),
          ),

          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () {},
              style: TextButton.styleFrom(
                foregroundColor: AppColors.accent,
                padding: EdgeInsets.zero,
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: const Text('Забыли пароль?'),
            ),
          ),

          const SizedBox(height: 14),
          GradientButton(
            label: 'Войти',
            // Важно: передаём null, когда форма пустая → disabled.
            onPressed: canSubmit ? onLoginPressed : null,
          ),

          const SizedBox(height: 18),
          const _OrDivider(),
          const SizedBox(height: 14),

          const SocialLoginButton(
            label: 'Продолжить с Google',
            background: AppColors.googleButton,
            foreground: Colors.black87,
            leading: GoogleMark(),
          ),
          const SizedBox(height: 10),
          const SocialLoginButton(
            label: 'Продолжить с Apple',
            background: AppColors.appleButton,
            foreground: Colors.white,
            leading: Icon(Icons.apple, color: Colors.white, size: 22),
          ),

          const SizedBox(height: 18),
          // RichText / Text.rich — разные стили в одной строке.
          Text.rich(
            TextSpan(
              style: textTheme.bodyMedium,
              children: [
                const TextSpan(text: 'Нет аккаунта? '),
                TextSpan(
                  text: 'Зарегистрироваться',
                  style: textTheme.bodyMedium?.copyWith(
                    color: AppColors.accent,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

/// Разделитель «или войдите с помощью».
class _OrDivider extends StatelessWidget {
  const _OrDivider();

  @override
  Widget build(BuildContext context) {
    final line = Expanded(
      child: Container(height: 1, color: const Color(0x33FFFFFF)),
    );
    return Row(
      children: [
        line,
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Text(
            'или войдите с помощью',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12),
          ),
        ),
        line,
      ],
    );
  }
}
