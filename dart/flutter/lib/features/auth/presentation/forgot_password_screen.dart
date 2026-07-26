import 'dart:async';

import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/features/auth/presentation/widgets/auth_text_field.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

/// Весь флоу «Забыли пароль?» на одном экране: 3 шага в горизонтальном PageView.
///
/// 1) identifier → `POST /auth/password/forgot`
/// 2) OTP → `POST /auth/password/forgot/verify` → `reset_token`
/// 3) новый пароль → `POST /auth/password/reset` → логин
class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

enum _IdChannel { email, phone }

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _pageController = PageController();
  final _identifierController = TextEditingController();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();
  final _passwordRepeatController = TextEditingController();
  final _otpFocus = FocusNode();

  _IdChannel _channel = _IdChannel.email;
  int _step = 0;

  Challenge? _challenge;
  String? _resetToken;
  DateTime? _expiresAt;
  DateTime? _sentAt;
  Timer? _ticker;

  bool _submitting = false;
  bool _resending = false;
  bool _obscurePassword = true;
  bool _obscurePasswordRepeat = true;

  @override
  void dispose() {
    _ticker?.cancel();
    _pageController.dispose();
    _identifierController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    _passwordRepeatController.dispose();
    _otpFocus.dispose();
    super.dispose();
  }

  void _onFieldsChanged([String? _]) => setState(() {});

  int get _passwordStrength {
    final p = _passwordController.text;
    if (p.isEmpty) return 0;
    var score = 0;
    if (p.length >= 8) score++;
    if (p.length >= 12) score++;
    if (RegExp(r'[A-ZА-Я]').hasMatch(p) && RegExp(r'[a-zа-я]').hasMatch(p)) {
      score++;
    }
    if (RegExp(r'[0-9]').hasMatch(p) ||
        RegExp(r'[^A-Za-zА-Яа-я0-9]').hasMatch(p)) {
      score++;
    }
    return score.clamp(0, 4);
  }

  bool get _canSendCode {
    final id = _identifierController.text.trim();
    if (_submitting || id.isEmpty) return false;
    if (_channel == _IdChannel.email) return id.contains('@');
    return id.length >= 8;
  }

  int get _secondsLeft {
    final exp = _expiresAt;
    if (exp == null) return 0;
    final left = exp.difference(DateTime.now()).inSeconds;
    return left < 0 ? 0 : left;
  }

  bool get _canConfirmOtp {
    return !_submitting &&
        _challenge != null &&
        _secondsLeft > 0 &&
        _codeController.text.trim().length == 6;
  }

  bool get _canResetPassword {
    return !_submitting &&
        (_resetToken?.isNotEmpty ?? false) &&
        _passwordController.text.length >= 8 &&
        _passwordController.text == _passwordRepeatController.text;
  }

  String get _timerLabel {
    final s = _secondsLeft;
    return '${(s ~/ 60).toString().padLeft(2, '0')}:${(s % 60).toString().padLeft(2, '0')}';
  }

  Future<void> _goToStep(int index) async {
    setState(() => _step = index);
    await _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 320),
      curve: Curves.easeOutCubic,
    );
    if (index == 1 && mounted) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _otpFocus.requestFocus();
      });
    }
  }

  void _startOtpTimer(Challenge challenge) {
    _ticker?.cancel();
    _challenge = challenge;
    _sentAt = DateTime.now();
    _expiresAt = _sentAt!.add(Duration(seconds: challenge.expiresIn));
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() {});
      if (_secondsLeft <= 0) _ticker?.cancel();
    });
  }

  Future<void> _onSendCode() async {
    if (!_canSendCode) return;
    setState(() => _submitting = true);
    try {
      final challenge = await ref.read(authClientProvider).forgotPassword(
            ForgotPasswordRequest(
              identifier: _identifierController.text.trim(),
              channel: _channel == _IdChannel.email ? 'email' : 'phone',
            ),
          );
      if (!mounted) return;
      _codeController.clear();
      _startOtpTimer(challenge);
      setState(() {});
      await _goToStep(1);
    } on ApiException catch (e) {
      if (!mounted) return;
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _onConfirmOtp() async {
    final challenge = _challenge;
    if (!_canConfirmOtp || challenge == null) return;
    setState(() => _submitting = true);
    try {
      final result = await ref.read(authClientProvider).forgotVerify(
            VerifyRequest(
              challengeId: challenge.challengeId,
              code: _codeController.text.trim(),
            ),
          );
      if (!mounted) return;
      setState(() => _resetToken = result.resetToken);
      await _goToStep(2);
    } on ApiException catch (e) {
      if (!mounted) return;
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _onResendOtp() async {
    final challenge = _challenge;
    if (_resending || challenge == null) return;
    setState(() => _resending = true);
    try {
      final next = await ref.read(authClientProvider).resendOtp(
            challengeId: challenge.challengeId,
          );
      if (!mounted) return;
      _codeController.clear();
      _startOtpTimer(next);
      setState(() {});
      _snack('Новый код отправлен');
      _otpFocus.requestFocus();
    } on ApiException catch (e) {
      if (!mounted) return;
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _resending = false);
    }
  }

  Future<void> _onResetPassword() async {
    final token = _resetToken;
    if (!_canResetPassword || token == null) return;
    setState(() => _submitting = true);
    try {
      await ref.read(authClientProvider).resetPassword(
            ResetPasswordRequest(
              resetToken: token,
              newPassword: _passwordController.text,
            ),
          );
      if (!mounted) return;
      _snack('Пароль обновлён. Войдите с новым паролем.');
      context.go(AppRoutes.login);
    } on ApiException catch (e) {
      if (!mounted) return;
      _snack(e.message);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _snack(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  void _onBack() {
    if (_step > 0) {
      _goToStep(_step - 1);
      return;
    }
    if (context.canPop()) {
      context.pop();
    } else {
      context.go(AppRoutes.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const LoginBackground(),
          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(8, 4, 8, 0),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: IconButton(
                      onPressed: _onBack,
                      tooltip: 'Назад',
                      icon: const Icon(Icons.chevron_left_rounded, size: 32),
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                Expanded(
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      return SingleChildScrollView(
                        padding: const EdgeInsets.fromLTRB(20, 0, 20, 180),
                        child: ConstrainedBox(
                          constraints: BoxConstraints(
                            minHeight: constraints.maxHeight - 8,
                            maxWidth: 420,
                          ),
                          child: Column(
                            children: [
                              const SizedBox(height: 8),
                              _BrandHeader(textTheme: textTheme),
                              const SizedBox(height: 18),
                              _StepIndicator(current: _step),
                              const SizedBox(height: 18),
                              SizedBox(
                                height: 460,
                                child: PageView(
                                  controller: _pageController,
                                  physics: const NeverScrollableScrollPhysics(),
                                  onPageChanged: (i) =>
                                      setState(() => _step = i),
                                  children: [
                                    _StepIdentifierPage(
                                      textTheme: textTheme,
                                      channel: _channel,
                                      identifierController:
                                          _identifierController,
                                      submitting: _submitting,
                                      canSubmit: _canSendCode,
                                      onChannelChanged: (c) => setState(() {
                                        _channel = c;
                                        _identifierController.clear();
                                      }),
                                      onChanged: _onFieldsChanged,
                                      onSubmit: _onSendCode,
                                    ),
                                    _StepOtpPage(
                                      textTheme: textTheme,
                                      challenge: _challenge,
                                      codeController: _codeController,
                                      focusNode: _otpFocus,
                                      timerLabel: _timerLabel,
                                      sentAt: _sentAt,
                                      submitting: _submitting,
                                      resending: _resending,
                                      canConfirm: _canConfirmOtp,
                                      onCodeChanged: _onFieldsChanged,
                                      onConfirm: _onConfirmOtp,
                                      onResend: _onResendOtp,
                                    ),
                                    _StepNewPasswordPage(
                                      textTheme: textTheme,
                                      passwordController: _passwordController,
                                      passwordRepeatController:
                                          _passwordRepeatController,
                                      obscurePassword: _obscurePassword,
                                      obscurePasswordRepeat:
                                          _obscurePasswordRepeat,
                                      passwordStrength: _passwordStrength,
                                      submitting: _submitting,
                                      canSubmit: _canResetPassword,
                                      onChanged: _onFieldsChanged,
                                      onTogglePassword: () => setState(
                                        () => _obscurePassword =
                                            !_obscurePassword,
                                      ),
                                      onTogglePasswordRepeat: () => setState(
                                        () => _obscurePasswordRepeat =
                                            !_obscurePasswordRepeat,
                                      ),
                                      onSubmit: _onResetPassword,
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 16),
                              const _OrDivider(),
                              const SizedBox(height: 12),
                              const _SupportButton(),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
          const Align(
            alignment: Alignment.bottomCenter,
            child: ScrollingCityDecorBar(),
          ),
        ],
      ),
    );
  }
}

class _BrandHeader extends StatelessWidget {
  const _BrandHeader({required this.textTheme});

  final TextTheme textTheme;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              colors: [AppColors.gradientStart, AppColors.gradientEnd],
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.accent.withValues(alpha: 0.4),
                blurRadius: 18,
              ),
            ],
          ),
          child: const Icon(Icons.nightlife_rounded, color: Colors.white, size: 28),
        ),
        const SizedBox(height: 10),
        Text('CityVibe', style: textTheme.displayLarge?.copyWith(fontSize: 28)),
        const SizedBox(height: 12),
        Text('Забыли пароль?', style: textTheme.headlineMedium),
        const SizedBox(height: 8),
        Text(
          'Не переживайте! Мы поможем вам восстановить доступ к аккаунту.',
          textAlign: TextAlign.center,
          style: textTheme.bodyMedium,
        ),
      ],
    );
  }
}

class _StepIndicator extends StatelessWidget {
  const _StepIndicator({required this.current});

  final int current;

  static const _labels = ['Email или телефон', 'Проверка', 'Новый пароль'];

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (var i = 0; i < 3; i++) ...[
          if (i > 0)
            Expanded(
              child: Padding(
                padding: const EdgeInsets.only(bottom: 18),
                child: CustomPaint(
                  painter: _DashedLinePainter(
                    color: i <= current
                        ? AppColors.accent.withValues(alpha: 0.7)
                        : AppColors.fieldBorder,
                  ),
                  size: const Size(double.infinity, 2),
                ),
              ),
            ),
          Expanded(
            flex: 0,
            child: Column(
              children: [
                Container(
                  width: 30,
                  height: 30,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: i <= current
                        ? AppColors.accent
                        : AppColors.fieldFill,
                    border: Border.all(
                      color: i <= current
                          ? AppColors.accent
                          : AppColors.fieldBorder,
                    ),
                  ),
                  child: Text(
                    '${i + 1}',
                    style: TextStyle(
                      color: i <= current
                          ? Colors.white
                          : AppColors.textSecondary,
                      fontWeight: FontWeight.w700,
                      fontSize: 13,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                SizedBox(
                  width: 88,
                  child: Text(
                    _labels[i],
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 11,
                      color: i == current
                          ? AppColors.accent
                          : AppColors.textSecondary,
                      fontWeight:
                          i == current ? FontWeight.w600 : FontWeight.w400,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _DashedLinePainter extends CustomPainter {
  _DashedLinePainter({required this.color});

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;
    const dash = 4.0;
    const gap = 3.0;
    var x = 0.0;
    final y = size.height / 2;
    while (x < size.width) {
      canvas.drawLine(Offset(x, y), Offset((x + dash).clamp(0, size.width), y), paint);
      x += dash + gap;
    }
  }

  @override
  bool shouldRepaint(covariant _DashedLinePainter oldDelegate) =>
      oldDelegate.color != color;
}

class _StepCard extends StatelessWidget {
  const _StepCard({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 22, 20, 20),
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
      child: child,
    );
  }
}

class _StepIdentifierPage extends StatelessWidget {
  const _StepIdentifierPage({
    required this.textTheme,
    required this.channel,
    required this.identifierController,
    required this.submitting,
    required this.canSubmit,
    required this.onChannelChanged,
    required this.onChanged,
    required this.onSubmit,
  });

  final TextTheme textTheme;
  final _IdChannel channel;
  final TextEditingController identifierController;
  final bool submitting;
  final bool canSubmit;
  final ValueChanged<_IdChannel> onChannelChanged;
  final ValueChanged<String> onChanged;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    final isEmail = channel == _IdChannel.email;
    return _StepCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.accent.withValues(alpha: 0.18),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.mark_email_unread_outlined,
                color: AppColors.accent,
                size: 28,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            'Введите Email или телефон',
            textAlign: TextAlign.center,
            style: textTheme.headlineMedium?.copyWith(fontSize: 18),
          ),
          const SizedBox(height: 6),
          Text(
            'Мы отправим вам код для сброса пароля на указанный email или номер телефона.',
            textAlign: TextAlign.center,
            style: textTheme.bodyMedium?.copyWith(fontSize: 13),
          ),
          const SizedBox(height: 16),
          _ChannelTabs(
            channel: channel,
            onChanged: onChannelChanged,
          ),
          const SizedBox(height: 12),
          AuthTextField(
            controller: identifierController,
            hintText: isEmail ? 'Введите ваш email' : 'Введите номер телефона',
            prefixIcon:
                isEmail ? Icons.mail_outline_rounded : Icons.phone_outlined,
            keyboardType: isEmail
                ? TextInputType.emailAddress
                : TextInputType.phone,
            onChanged: onChanged,
          ),
          const SizedBox(height: 16),
          GradientButton(
            label: submitting ? 'Отправляем…' : 'Отправить код',
            onPressed: canSubmit ? onSubmit : null,
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.verified_user_outlined,
                size: 16,
                color: AppColors.accent.withValues(alpha: 0.9),
              ),
              const SizedBox(width: 6),
              Text(
                'Мы заботимся о безопасности ваших данных',
                style: textTheme.bodyMedium?.copyWith(
                  fontSize: 12,
                  color: AppColors.accent,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ChannelTabs extends StatelessWidget {
  const _ChannelTabs({
    required this.channel,
    required this.onChanged,
  });

  final _IdChannel channel;
  final ValueChanged<_IdChannel> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: AppColors.fieldFill,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.fieldBorder),
      ),
      child: Row(
        children: [
          Expanded(
            child: _ChannelChip(
              label: 'Email',
              icon: Icons.mail_outline_rounded,
              selected: channel == _IdChannel.email,
              onTap: () => onChanged(_IdChannel.email),
            ),
          ),
          Expanded(
            child: _ChannelChip(
              label: 'Телефон',
              icon: Icons.phone_outlined,
              selected: channel == _IdChannel.phone,
              onTap: () => onChanged(_IdChannel.phone),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChannelChip extends StatelessWidget {
  const _ChannelChip({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? AppColors.accent : Colors.transparent,
      borderRadius: BorderRadius.circular(11),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(11),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 18,
                color: selected ? Colors.white : AppColors.textSecondary,
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  color: selected ? Colors.white : AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StepOtpPage extends StatelessWidget {
  const _StepOtpPage({
    required this.textTheme,
    required this.challenge,
    required this.codeController,
    required this.focusNode,
    required this.timerLabel,
    required this.sentAt,
    required this.submitting,
    required this.resending,
    required this.canConfirm,
    required this.onCodeChanged,
    required this.onConfirm,
    required this.onResend,
  });

  final TextTheme textTheme;
  final Challenge? challenge;
  final TextEditingController codeController;
  final FocusNode focusNode;
  final String timerLabel;
  final DateTime? sentAt;
  final bool submitting;
  final bool resending;
  final bool canConfirm;
  final ValueChanged<String> onCodeChanged;
  final VoidCallback onConfirm;
  final VoidCallback onResend;

  @override
  Widget build(BuildContext context) {
    final digits = codeController.text.padRight(6).substring(0, 6);
    final channel = challenge?.channel ?? 'email';
    final dest = challenge?.destinationMasked ?? '…';
    final sentLabel = sentAt == null
        ? ''
        : 'Код отправлен сегодня в ${DateFormat('HH:mm').format(sentAt!)}';

    return _StepCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.accent.withValues(alpha: 0.18),
                shape: BoxShape.circle,
              ),
              child: Icon(
                channel == 'sms' ? Icons.sms_outlined : Icons.mail_outline_rounded,
                color: AppColors.accent,
                size: 28,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            channel == 'sms' ? 'Введите код из SMS' : 'Введите код из письма',
            textAlign: TextAlign.center,
            style: textTheme.headlineMedium?.copyWith(fontSize: 18),
          ),
          const SizedBox(height: 6),
          Text(
            channel == 'sms'
                ? 'Мы отправили SMS с кодом на номер $dest'
                : 'Мы отправили письмо с кодом на $dest',
            textAlign: TextAlign.center,
            style: textTheme.bodyMedium?.copyWith(fontSize: 13),
          ),
          if (sentLabel.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              sentLabel,
              textAlign: TextAlign.center,
              style: textTheme.bodyMedium?.copyWith(fontSize: 12),
            ),
          ],
          const SizedBox(height: 18),
          Stack(
            alignment: Alignment.center,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: List.generate(6, (i) {
                  final ch = digits[i].trim();
                  final filled = ch.isNotEmpty && ch != ' ';
                  final focused =
                      focusNode.hasFocus && codeController.text.length == i;
                  return Container(
                    width: 44,
                    height: 52,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: AppColors.fieldFill,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: focused || filled
                            ? AppColors.accent
                            : AppColors.fieldBorder,
                        width: focused ? 1.6 : 1,
                      ),
                    ),
                    child: Text(
                      filled ? ch : '',
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 22,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  );
                }),
              ),
              Opacity(
                opacity: 0.01,
                child: TextField(
                  controller: codeController,
                  focusNode: focusNode,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  autofillHints: const [AutofillHints.oneTimeCode],
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  decoration: const InputDecoration(
                    counterText: '',
                    border: InputBorder.none,
                  ),
                  onChanged: onCodeChanged,
                  onSubmitted: (_) => onConfirm(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text.rich(
            TextSpan(
              style: textTheme.bodyMedium?.copyWith(fontSize: 13),
              children: [
                const TextSpan(text: 'Код действителен еще '),
                TextSpan(
                  text: timerLabel,
                  style: const TextStyle(
                    color: AppColors.accent,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          GradientButton(
            label: submitting ? 'Проверяем…' : 'Подтвердить',
            onPressed: canConfirm ? onConfirm : null,
          ),
          const SizedBox(height: 12),
          Text.rich(
            TextSpan(
              style: textTheme.bodyMedium?.copyWith(fontSize: 13),
              children: [
                const TextSpan(text: 'Не получили код? '),
                WidgetSpan(
                  alignment: PlaceholderAlignment.baseline,
                  baseline: TextBaseline.alphabetic,
                  child: GestureDetector(
                    onTap: resending ? null : onResend,
                    child: Text(
                      resending ? 'Отправляем…' : 'Отправить повторно',
                      style: TextStyle(
                        color: resending
                            ? AppColors.textSecondary
                            : AppColors.accent,
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                      ),
                    ),
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

class _StepNewPasswordPage extends StatelessWidget {
  const _StepNewPasswordPage({
    required this.textTheme,
    required this.passwordController,
    required this.passwordRepeatController,
    required this.obscurePassword,
    required this.obscurePasswordRepeat,
    required this.passwordStrength,
    required this.submitting,
    required this.canSubmit,
    required this.onChanged,
    required this.onTogglePassword,
    required this.onTogglePasswordRepeat,
    required this.onSubmit,
  });

  final TextTheme textTheme;
  final TextEditingController passwordController;
  final TextEditingController passwordRepeatController;
  final bool obscurePassword;
  final bool obscurePasswordRepeat;
  final int passwordStrength;
  final bool submitting;
  final bool canSubmit;
  final ValueChanged<String> onChanged;
  final VoidCallback onTogglePassword;
  final VoidCallback onTogglePasswordRepeat;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return _StepCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.accent.withValues(alpha: 0.18),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.lock_reset_rounded,
                color: AppColors.accent,
                size: 28,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            'Придумайте новый пароль',
            textAlign: TextAlign.center,
            style: textTheme.headlineMedium?.copyWith(fontSize: 18),
          ),
          const SizedBox(height: 6),
          Text(
            'Пароль должен содержать минимум 8 символов.',
            textAlign: TextAlign.center,
            style: textTheme.bodyMedium?.copyWith(fontSize: 13),
          ),
          const SizedBox(height: 16),
          AuthTextField(
            controller: passwordController,
            hintText: 'Новый пароль',
            prefixIcon: Icons.lock_outline_rounded,
            obscureText: obscurePassword,
            onChanged: onChanged,
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
          _PasswordStrengthRow(strength: passwordStrength),
          const SizedBox(height: 12),
          AuthTextField(
            controller: passwordRepeatController,
            hintText: 'Повторите пароль',
            prefixIcon: Icons.lock_outline_rounded,
            obscureText: obscurePasswordRepeat,
            onChanged: onChanged,
            suffix: IconButton(
              onPressed: onTogglePasswordRepeat,
              tooltip:
                  obscurePasswordRepeat ? 'Показать пароль' : 'Скрыть пароль',
              icon: Icon(
                obscurePasswordRepeat
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          const SizedBox(height: 16),
          GradientButton(
            label: submitting ? 'Сохраняем…' : 'Сохранить пароль',
            onPressed: canSubmit ? onSubmit : null,
          ),
        ],
      ),
    );
  }
}

class _PasswordStrengthRow extends StatelessWidget {
  const _PasswordStrengthRow({required this.strength});

  final int strength;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(
            'Минимум 8 символов',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12),
          ),
        ),
        Row(
          children: List.generate(4, (i) {
            final filled = i < strength;
            return Container(
              width: 22,
              height: 4,
              margin: EdgeInsets.only(left: i == 0 ? 0 : 4),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(2),
                color: filled
                    ? AppColors.accent
                    : AppColors.textSecondary.withValues(alpha: 0.35),
              ),
            );
          }),
        ),
      ],
    );
  }
}

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
            'или',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontSize: 12),
          ),
        ),
        line,
      ],
    );
  }
}

class _SupportButton extends StatelessWidget {
  const _SupportButton();

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Поддержка скоро будет доступна'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
        borderRadius: BorderRadius.circular(14),
        child: Ink(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.cardBorder),
            color: AppColors.card.withValues(alpha: 0.55),
          ),
          child: const Row(
            children: [
              Icon(Icons.headset_mic_outlined, color: Colors.white, size: 20),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Нужна помощь? Связаться с поддержкой',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: AppColors.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}
