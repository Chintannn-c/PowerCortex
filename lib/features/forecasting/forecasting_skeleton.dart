import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../core/theme/skeleton_theme.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Forecasting screen loading state.
///
/// Mimics the tabbed layout with forecast KPI cards and large chart area.
class ForecastingSkeleton extends StatelessWidget {
  const ForecastingSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Tab bar placeholder
        _tabBarSkeleton(context),
        context.sh(8),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Forecast KPI row
                LayoutBuilder(
                  builder: (context, constraints) {
                    final crossCount = constraints.maxWidth > 700 ? 3 : 1;
                    return GridView.count(
                      crossAxisCount: crossCount,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      mainAxisSpacing: 10,
                      crossAxisSpacing: 10,
                      childAspectRatio: 2.2,
                      children: List.generate(3, (_) => const SkeletonForecastCard()),
                    );
                  },
                ),
                context.sh(20),
                // Main chart
                const SkeletonChartCard(),
                context.sh(16),
                // Stats bar
                SkeletonCard(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: const [
                      _StatSkeleton(),
                      _StatSkeleton(),
                      _StatSkeleton(),
                      _StatSkeleton(),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _tabBarSkeleton(BuildContext context) {
    return SkeletonShimmer(
      child: Container(
        margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
        height: 46,
        decoration: BoxDecoration(
          color: SkeletonTheme.baseColor(context),
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}

class _StatSkeleton extends StatelessWidget {
  const _StatSkeleton();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SkeletonCircle(size: 18),
        context.sh(6),
        const SkeletonBox(width: 48, height: 14),
        context.sh(4),
        const SkeletonBox(width: 36, height: 10),
      ],
    );
  }
}
