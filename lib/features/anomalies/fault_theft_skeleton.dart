import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../core/theme/skeleton_theme.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Fault & Theft Detection screen.
///
/// Mimics the tabbed layout with KPI row, fault list, and bar chart.
class FaultTheftSkeleton extends StatelessWidget {
  const FaultTheftSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Tab bar
        _tabBarSkeleton(context),
        context.sh(8),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // KPI Row
                Row(
                  children: [
                    Expanded(child: _kpiSkeleton(context)),
                    context.sw(10),
                    Expanded(child: _kpiSkeleton(context)),
                    context.sw(10),
                    Expanded(child: _kpiSkeleton(context)),
                  ],
                ),
                context.sh(20),

                // Section title
                const SkeletonBox(width: 100, height: 14),
                context.sh(10),

                // Fault / Theft cards
                ...List.generate(
                  4,
                  (_) => const Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: SkeletonAlertCard(),
                  ),
                ),
                context.sh(20),

                // Chart
                const SkeletonBox(width: 140, height: 14),
                context.sh(10),
                const SkeletonChartCard(),
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

  Widget _kpiSkeleton(BuildContext context) {
    return SkeletonCard(
      child: Column(
        children: [
          const SkeletonBox(width: 48, height: 24),
          context.sh(6),
          const SkeletonBox(width: 72, height: 10),
        ],
      ),
    );
  }
}
