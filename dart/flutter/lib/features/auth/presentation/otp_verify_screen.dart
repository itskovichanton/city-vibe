import 'dart:async';

import 'package:city_vibe/core/api/api_providers.dart';
import 'package:city_vibe/core/api/models/auth_models.dart';
import 'package:city_vibe/core/auth/auth_providers.dart';
import 'package:city_vibe/core/network/api_exception.dart';
import 'package:city_vibe/core/router/app_router.dart';
import 'package:city_vibe/features/auth/presentation/widgets/gradient_button.dart';
import 'package:city_vibe/features/auth/presentation/widgets/login_background.dart';
import 'package:city_vibe/features/auth/presentation/widgets/scrolling_city_decor_bar.dart';
import 'package:city_vibe/theme/app_colors.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

/// Аргументы экрана OTP после `POST /auth/register` (или login).
class OtpVerifyArgs {
  const OtpVerifyArgs({
    required this.challenge,
    this.purpose = OtpPurpose.register,
  });

  final Challenge challenge;
  final OtpPurpose purpose;
}

enum OtpPurpose { register, login }

/// Экран двухфакторной аутентификации (OTP).
///
/// - Подтверждение: `POST /auth/register/verify` (или login/verify)
/// - Повтор: `POST /auth/otp/resend`
class OtpVerifyScreen extends ConsumerStatefulWidget {
  const OtpVerifyScreen({super.key, required this.args});

  final OtpVerifyArgs args;

  @override
  ConsumerState<OtpVerifyScreen> createState() => _OtpVerifyScreenState();
}

class _OtpVerifyScreenState extends ConsumerState<OtpVerifyScreen> {
  final _codeController = TextEditingController();
  final _focusNode = FocusNode();

  late Challenge _challenge;
  late DateTime _expiresAt;
  late final DateTime _sentAt;
  Timer? _ticker;
  bool _submitting = false;
  bool _resending = false;

  @override
  void initState() {
    super.initState();
    _challenge = widget.args.challenge;
    _sentAt = DateTime.now();
    _expiresAt = _sentAt.add(Duration(seconds: _challenge.expiresIn));
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() {});
      if (_secondsLeft <= 0) _ticker?.cancel();
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _focusNode.requestFocus();
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    _codeController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  int get _secondsLeft {
    final left = _expiresAt.difference(DateTime.now()).inSeconds;
    return left < 0 ? 0 : left;
  }

  String get _timerLabel {
    final s = _secondsLeft;
    final mm = (s ~/ 60).toString().padLeft(2, '0');
    final ss = (s % 60).toString().padLeft(2, '0');
    return '$mm:$ss';
  }

  bool get _canConfirm {
    return !_submitting &&
        _secondsLeft > 0 &&
        _codeController.text.trim().length == 6;
  }

  String get _channelTitle {
    return _challenge.channel == 'sms'
        ? 'Введите код из SMS'
        : 'Введите код из письма';
  }

  String get _headerSubtitle {
    final dest = _challenge.destinationMasked;
    if (_challenge.channel == 'sms') {
      return 'Мы отправили SMS с кодом подтверждения на номер $dest';
    }
    return 'Мы отправили письмо с кодом подтверждения на $dest';
  }

  String get _sentAtLabel {
    final t = DateFormat('HH:mm').format(_sentAt);
    return 'Код отправлен сегодня в $t';
  }

  Future<void> _onConfirm() async {
    if (!_canConfirm) return;
    setState(() => _submitting = true);
    try {
      final client = ref.read(authClientProvider);
      final body = VerifyRequest(
        challengeId: _challenge.challengeId,
        code: _codeController.text.trim(),
      );
      final tokens = widget.args.purpose == OtpPurpose.register
          ? await client.registerVerify(body)
          : await client.loginVerify(body);
      if (!mounted) return;

      await ref.read(authSessionProvider.notifier).establish(tokens);

      if (!mounted) return;
      final session = ref.read(authSessionProvider).valueOrNull;
      if (session == null) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            widget.args.purpose == OtpPurpose.register
                ? 'Аккаунт создан. Добро пожаловать!'
                : 'Вход выполнен',
          ),
          behavior: SnackBarBehavior.floating,
        ),
      );
      // Роутер сам решит: onboarding / milana / home по профилю.
      context.go(AppRoutes.home);
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.message),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _onResend() async {
    if (_resending) return;
    setState(() => _resending = true);
    try {
      final next = await ref.read(authClientProvider).resendOtp(
            challengeId: _challenge.challengeId,
          );
      if (!mounted) return;
      setState(() {
        _challenge = next;
        _expiresAt = DateTime.now().add(Duration(seconds: next.expiresIn));
        _codeController.clear();
        _ticker?.cancel();
        _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
          if (!mounted) return;
          setState(() {});
          if (_secondsLeft <= 0) _ticker?.cancel();
        });
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Новый код отправлен'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      _focusNode.requestFocus();
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.message),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _resending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final digits = _codeController.text.padRight(6).substring(0, 6);

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
                    onPressed: () => context.pop(),
                    tooltip: 'Назад',
                    icon: const Icon(Icons.chevron_left_rounded, size: 32),
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
              Expanded(
                child: Center(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 180),
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 420),
                      child: Column(
                        children: [
                          const SizedBox(height: 40),
                          Text(
                            'Двухфакторная аутентификация',
                            textAlign: TextAlign.center,
                            style: textTheme.headlineMedium,
                          ),
                          const SizedBox(height: 10),
                          Text(
                            _headerSubtitle,
                            textAlign: TextAlign.center,
                            style: textTheme.bodyMedium,
                          ),
                          const SizedBox(height: 24),
                          Container(
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
                            child: Column(
                              children: [
                                Container(
                                  width: 56,
                                  height: 56,
                                  decoration: BoxDecoration(
                                    color: AppColors.accent.withValues(alpha: 0.18),
                                    shape: BoxShape.circle,
                                  ),
                                  child: Icon(
                                    _challenge.channel == 'sms'
                                        ? Icons.sms_outlined
                                        : Icons.mail_outline_rounded,
                                    color: AppColors.accent,
                                    size: 28,
                                  ),
                                ),
                                const SizedBox(height: 14),
                                Text(
                                  _channelTitle,
                                  style: textTheme.headlineMedium?.copyWith(
                                    fontSize: 18,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  _sentAtLabel,
                                  style: textTheme.bodyMedium?.copyWith(
                                    fontSize: 12,
                                  ),
                                ),
                                const SizedBox(height: 20),
                                Stack(
                                  alignment: Alignment.center,
                                  children: [
                                    Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.spaceBetween,
                                      children: List.generate(6, (i) {
                                        final ch = digits[i].trim();
                                        final filled =
                                            ch.isNotEmpty && ch != ' ';
                                        final focused =
                                            _focusNode.hasFocus &&
                                            _codeController.text.length == i;
                                        return Container(
                                          width: 44,
                                          height: 52,
                                          alignment: Alignment.center,
                                          decoration: BoxDecoration(
                                            color: AppColors.fieldFill,
                                            borderRadius:
                                                BorderRadius.circular(12),
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
                                        controller: _codeController,
                                        focusNode: _focusNode,
                                        keyboardType: TextInputType.number,
                                        maxLength: 6,
                                        autofillHints: const [
                                          AutofillHints.oneTimeCode,
                                        ],
                                        inputFormatters: [
                                          FilteringTextInputFormatter
                                              .digitsOnly,
                                        ],
                                        decoration: const InputDecoration(
                                          counterText: '',
                                          border: InputBorder.none,
                                        ),
                                        onChanged: (_) => setState(() {}),
                                        onSubmitted: (_) => _onConfirm(),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 14),
                                Text.rich(
                                  TextSpan(
                                    style: textTheme.bodyMedium
                                        ?.copyWith(fontSize: 13),
                                    children: [
                                      const TextSpan(
                                        text: 'Код действителен еще ',
                                      ),
                                      TextSpan(
                                        text: _timerLabel,
                                        style: const TextStyle(
                                          color: AppColors.accent,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(height: 18),
                                GradientButton(
                                  label: _submitting
                                      ? 'Проверяем…'
                                      : 'Подтвердить',
                                  onPressed: _canConfirm ? _onConfirm : null,
                                ),
                                const SizedBox(height: 14),
                                Text.rich(
                                  TextSpan(
                                    style: textTheme.bodyMedium
                                        ?.copyWith(fontSize: 13),
                                    children: [
                                      const TextSpan(
                                        text: 'Не получили код? ',
                                      ),
                                      WidgetSpan(
                                        alignment:
                                            PlaceholderAlignment.baseline,
                                        baseline: TextBaseline.alphabetic,
                                        child: GestureDetector(
                                          onTap: _resending ? null : _onResend,
                                          child: Text(
                                            _resending
                                                ? 'Отправляем…'
                                                : 'Отправить повторно',
                                            style: TextStyle(
                                              color: _resending
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
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 20),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.verified_user_outlined,
                                size: 18,
                                color: AppColors.accent.withValues(alpha: 0.9),
                              ),
                              const SizedBox(width: 8),
                              Flexible(
                                child: Text(
                                  'Это дополнительный уровень защиты вашего аккаунта',
                                  textAlign: TextAlign.center,
                                  style: textTheme.bodyMedium?.copyWith(
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
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
