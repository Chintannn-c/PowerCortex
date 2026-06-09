import 'package:flutter/material.dart';

/// Skeleton color tokens for light and dark modes.
/// Matches the PowerCortex enterprise design spec.
class SkeletonTheme {
  SkeletonTheme._();

  // ─── Light Mode ──────────────────────────────────────────
  static const Color lightBase = Color(0xFFE2E8F0);
  static const Color lightHighlight = Color(0xFFF1F5F9);
  static const Color lightCard = Color(0xFFFFFFFF);
  static const Color lightBackground = Color(0xFFF8FAFC);

  // ─── Dark Mode ───────────────────────────────────────────
  static const Color darkBase = Color(0xFF1E293B);
  static const Color darkHighlight = Color(0xFF334155);
  static const Color darkCard = Color(0xFF111827);
  static const Color darkBackground = Color(0xFF0B1220);

  // ─── Animation ───────────────────────────────────────────
  static const Duration shimmerDuration = Duration(milliseconds: 1200);

  /// Get the base shimmer color for the current brightness.
  static Color baseColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? darkBase
        : lightBase;
  }

  /// Get the highlight shimmer color for the current brightness.
  static Color highlightColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? darkHighlight
        : lightHighlight;
  }

  /// Get the card surface color for the current brightness.
  static Color cardColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? darkCard
        : lightCard;
  }

  /// Standard border radius used across all skeleton widgets.
  static BorderRadius get borderRadius => BorderRadius.circular(12);

  /// Small border radius for inline elements.
  static BorderRadius get smallRadius => BorderRadius.circular(8);

  /// Pill border radius for badges and chips.
  static BorderRadius get pillRadius => BorderRadius.circular(20);
}
