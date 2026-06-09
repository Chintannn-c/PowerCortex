import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import '../../core/theme/skeleton_theme.dart';

/// A foundational shimmer wrapper used by every skeleton widget.
///
/// Wraps its [child] in a subtle, enterprise-grade shimmer effect
/// that loops infinitely at 1200ms with no pulse or glow artifacts.
class SkeletonShimmer extends StatelessWidget {
  final Widget child;

  const SkeletonShimmer({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: SkeletonTheme.baseColor(context),
      highlightColor: SkeletonTheme.highlightColor(context),
      period: SkeletonTheme.shimmerDuration,
      child: child,
    );
  }
}

/// A single skeleton placeholder box.
///
/// Used as the atomic building block for all skeleton card layouts.
/// Supports custom [width], [height], and [borderRadius].
class SkeletonBox extends StatelessWidget {
  final double? width;
  final double height;
  final BorderRadius? borderRadius;

  const SkeletonBox({
    super.key,
    this.width,
    this.height = 16,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: SkeletonTheme.baseColor(context),
        borderRadius: borderRadius ?? SkeletonTheme.smallRadius,
      ),
    );
  }
}

/// A skeleton circle placeholder (for avatar / icon areas).
class SkeletonCircle extends StatelessWidget {
  final double size;

  const SkeletonCircle({super.key, this.size = 40});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: SkeletonTheme.baseColor(context),
        shape: BoxShape.circle,
      ),
    );
  }
}

/// A full skeleton card container with shimmer applied.
///
/// Provides the standard card frame (rounded corners, border, surface color)
/// and wraps content in a shimmer animation. Use [padding] and [child] to
/// define inner layout.
class SkeletonCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;

  const SkeletonCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: SkeletonTheme.cardColor(context),
        borderRadius: SkeletonTheme.borderRadius,
        border: Border.all(
          color: isDark
              ? const Color(0xFF1E293B)
              : const Color(0xFFE2E8F0),
        ),
      ),
      child: SkeletonShimmer(
        child: Padding(
          padding: padding,
          child: child,
        ),
      ),
    );
  }
}
