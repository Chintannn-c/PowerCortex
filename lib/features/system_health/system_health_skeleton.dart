import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the System Health screen.
///
/// Mimics the overall status banner, service cards, and ML pipeline rows.
class SystemHealthSkeleton extends StatelessWidget {
  const SystemHealthSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Overall status banner
          SkeletonCard(
            child: Row(
              children: [
                const SkeletonCircle(size: 48),
                context.sw(16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SkeletonBox(width: 180, height: 14),
                      context.sh(6),
                      const SkeletonBox(width: 140, height: 10),
                    ],
                  ),
                ),
                SkeletonBox(
                  width: 80,
                  height: 34,
                  borderRadius: BorderRadius.circular(8),
                ),
              ],
            ),
          ),
          context.sh(20),

          // Backend section
          const SkeletonBox(width: 120, height: 14),
          context.sh(10),
          _serviceCardSkeleton(context),
          context.sh(10),

          // Database section
          const SkeletonBox(width: 72, height: 14),
          context.sh(10),
          _serviceCardSkeleton(context),
          context.sh(10),
          // Storage bar
          SkeletonCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    SkeletonBox(width: 90, height: 10),
                    Spacer(),
                    SkeletonBox(width: 80, height: 10),
                  ],
                ),
                context.sh(8),
                const SkeletonBox(
                  width: double.infinity,
                  height: 8,
                  borderRadius: BorderRadius.all(Radius.circular(4)),
                ),
              ],
            ),
          ),
          context.sh(20),

          // AI Services
          const SkeletonBox(width: 90, height: 14),
          context.sh(10),
          _serviceCardSkeleton(context),
          context.sh(20),

          // ML Pipeline
          const SkeletonBox(width: 140, height: 14),
          context.sh(10),
          ...List.generate(
            4,
            (_) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _mlRowSkeleton(context),
            ),
          ),
          context.sh(24),
        ],
      ),
    );
  }

  Widget _serviceCardSkeleton(BuildContext context) {
    return SkeletonCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const SkeletonBox(width: 36, height: 36, borderRadius: BorderRadius.all(Radius.circular(8))),
              context.sw(12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SkeletonBox(width: 120, height: 14),
                    SizedBox(height: 4),
                    SkeletonBox(width: 160, height: 10),
                  ],
                ),
              ),
              const SkeletonBox(width: 68, height: 26, borderRadius: BorderRadius.all(Radius.circular(20))),
            ],
          ),
          context.sh(14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SkeletonBox(width: 40, height: 9),
                  context.sh(4),
                  const SkeletonBox(width: 56, height: 13),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SkeletonBox(width: 40, height: 9),
                  context.sh(4),
                  const SkeletonBox(width: 56, height: 13),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SkeletonBox(width: 40, height: 9),
                  context.sh(4),
                  const SkeletonBox(width: 56, height: 13),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SkeletonBox(width: 40, height: 9),
                  context.sh(4),
                  const SkeletonBox(width: 56, height: 13),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _mlRowSkeleton(BuildContext context) {
    return SkeletonCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          const SkeletonCircle(size: 20),
          context.sw(12),
          const Expanded(child: SkeletonBox(width: 120, height: 14)),
          const SkeletonBox(width: 48, height: 10),
          context.sw(12),
          const SkeletonBox(width: 68, height: 26, borderRadius: BorderRadius.all(Radius.circular(20))),
        ],
      ),
    );
  }
}
