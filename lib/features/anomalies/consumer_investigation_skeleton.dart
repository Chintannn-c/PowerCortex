import 'package:flutter/material.dart';
import '../../core/utils/responsive.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Consumer Investigation screen loading state.
///
/// Mimics the profile details header, AI diagnostic summaries,
/// consumption history charts, and investigation inputs.
class ConsumerInvestigationSkeleton extends StatelessWidget {
  const ConsumerInvestigationSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header Consumer Profile Card placeholder
          SkeletonCard(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SkeletonBox(width: 180, height: 22),
                          context.sh(4),
                          const SkeletonBox(width: 140, height: 14),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    const SkeletonBox(width: 90, height: 30),
                  ],
                ),
                context.sh(16),
                const Divider(),
                context.sh(12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _profileStatSkeleton(context),
                    _profileStatSkeleton(context),
                    _profileStatSkeleton(context),
                  ],
                ),
              ],
            ),
          ),
          context.sh(16),

          // AI Explanation Card placeholder
          SkeletonCard(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const SkeletonCircle(size: 24),
                    context.sw(8),
                    const SkeletonBox(width: 160, height: 16),
                    const Spacer(),
                    const SkeletonBox(width: 70, height: 24),
                  ],
                ),
                context.sh(12),
                const SkeletonBox(width: double.infinity, height: 14),
                context.sh(8),
                const SkeletonBox(width: double.infinity, height: 14),
                context.sh(8),
                const SkeletonBox(width: 220, height: 14),
              ],
            ),
          ),
          context.sh(20),

          // Consumption History Line Chart placeholder
          const SkeletonBox(width: 200, height: 18),
          context.sh(8),
          const SkeletonChartCard(),
          context.sh(20),

          // Overall Risk Distribution Pie Chart placeholder
          const SkeletonBox(width: 180, height: 18),
          context.sh(8),
          const SkeletonChartCard(),
          context.sh(20),

          // Investigation Notes placeholder
          const SkeletonBox(width: 150, height: 18),
          context.sh(8),
          SkeletonCard(
            padding: const EdgeInsets.all(16),
            child: const SkeletonBox(width: double.infinity, height: 80),
          ),
          context.sh(20),

          // Action buttons placeholder
          Row(
            children: [
              Expanded(
                child: SkeletonCard(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: const Center(child: SkeletonBox(width: 60, height: 16)),
                ),
              ),
              context.sw(12),
              Expanded(
                child: SkeletonCard(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: const Center(child: SkeletonBox(width: 80, height: 16)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _profileStatSkeleton(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SkeletonBox(width: 70, height: 10),
        context.sh(4),
        const SkeletonBox(width: 50, height: 16),
      ],
    );
  }
}
