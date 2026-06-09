import 'package:flutter/material.dart';
import '../../core/utils/responsive.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Fault Details screen loading state.
///
/// Mimics the layout with ID and status chip, fault type title,
/// AI recommendation card, telemetry metrics grid, and diagnostics table.
class FaultDetailsSkeleton extends StatelessWidget {
  const FaultDetailsSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status and ID Row
          Row(
            children: [
              const SkeletonBox(width: 120, height: 16),
              const Spacer(),
              const SkeletonBox(width: 80, height: 24),
            ],
          ),
          context.sh(16),
          // Fault Type Title
          const SkeletonBox(width: 200, height: 28),
          context.sh(8),
          // Asset Name Row
          Row(
            children: [
              const SkeletonCircle(size: 16),
              context.sw(4),
              const SkeletonBox(width: 140, height: 14),
            ],
          ),
          context.sh(24),

          // AI Recommendation Card placeholder
          SkeletonCard(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const SkeletonCircle(size: 24),
                    context.sw(8),
                    const SkeletonBox(width: 160, height: 18),
                  ],
                ),
                context.sh(12),
                const SkeletonBox(width: double.infinity, height: 14),
                context.sh(8),
                const SkeletonBox(width: double.infinity, height: 14),
                context.sh(8),
                const SkeletonBox(width: 180, height: 14),
              ],
            ),
          ),
          context.sh(24),

          // Telemetry values grid
          const SkeletonBox(width: 140, height: 18),
          context.sh(12),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.4,
            children: List.generate(4, (_) => _metricTileSkeleton(context)),
          ),
          context.sh(24),

          // Diagnostic information
          const SkeletonBox(width: 160, height: 18),
          context.sh(12),
          _detailRowSkeleton(context),
          _detailRowSkeleton(context),
          _detailRowSkeleton(context),
        ],
      ),
    );
  }

  Widget _metricTileSkeleton(BuildContext context) {
    return SkeletonCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const SkeletonBox(width: 60, height: 12),
              const SkeletonCircle(size: 20),
            ],
          ),
          const SkeletonBox(width: 80, height: 20),
        ],
      ),
    );
  }

  Widget _detailRowSkeleton(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const SkeletonBox(width: 100, height: 14),
          const SkeletonBox(width: 120, height: 14),
        ],
      ),
    );
  }
}
