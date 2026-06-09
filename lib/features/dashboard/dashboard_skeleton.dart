import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import 'package:guvnl_project/core/theme/skeleton_theme.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Dashboard loading state.
///
/// Mimics the real dashboard layout: executive summary banner,
/// AI insight chips, KPI grid, chart panels, and alert feed.
class DashboardSkeleton extends StatelessWidget {
  const DashboardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Executive Summary Banner
          SkeletonCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SkeletonBox(width: 140, height: 14),
                context.sh(16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    _SummarySkeleton(),
                    _SummarySkeleton(),
                    _SummarySkeleton(),
                    _SummarySkeleton(),
                    _SummarySkeleton(),
                    _SummarySkeleton(),
                  ],
                ),
              ],
            ),
          ),
          context.sh(16),

          // AI Insights row
          const SkeletonBox(width: 80, height: 14),
          context.sh(10),
          SizedBox(
            height: 80,
            child: SkeletonShimmer(
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: 4,
                separatorBuilder: (_, __) => context.sw(12),
                itemBuilder: (_, __) => Container(
                  width: 280,
                  decoration: BoxDecoration(
                    color: SkeletonTheme.baseColor(context),
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ),
          context.sh(20),

          // KPI Cards
          const SkeletonBox(width: 160, height: 14),
          context.sh(10),
          LayoutBuilder(
            builder: (context, constraints) {
              final width = constraints.maxWidth;
              if (width > 720) {
                return Column(
                  children: [
                    Row(
                      children: [
                        const Expanded(child: SkeletonMetricCard()),
                        context.sw(10),
                        const Expanded(child: SkeletonMetricCard()),
                        context.sw(10),
                        const Expanded(child: SkeletonMetricCard()),
                      ],
                    ),
                    context.sh(10),
                    Row(
                      children: [
                        const Expanded(child: SkeletonMetricCard()),
                        context.sw(10),
                        const Expanded(child: SkeletonMetricCard()),
                        context.sw(10),
                        const Expanded(child: SkeletonMetricCard()),
                      ],
                    ),
                  ],
                );
              } else {
                return Column(
                  children: [
                    Row(
                      children: [
                        const Expanded(child: SkeletonMetricCard()),
                        context.sw(10),
                        const Expanded(child: SkeletonMetricCard()),
                      ],
                    ),
                    context.sh(10),
                    Row(
                      children: [
                        const Expanded(child: SkeletonMetricCard()),
                        context.sw(10),
                        const Expanded(child: SkeletonMetricCard()),
                      ],
                    ),
                    context.sh(10),
                    Row(
                      children: [
                        const Expanded(child: SkeletonMetricCard()),
                        context.sw(10),
                        const Expanded(child: SkeletonMetricCard()),
                      ],
                    ),
                  ],
                );
              }
            },
          ),
          context.sh(20),

          // Charts
          LayoutBuilder(
            builder: (context, constraints) {
              if (constraints.maxWidth > 700) {
                return Column(
                  children: [
                    Row(
                      children: [
                        const Expanded(child: SkeletonChartCard()),
                        context.sw(12),
                        const Expanded(child: SkeletonChartCard()),
                      ],
                    ),
                    context.sh(12),
                    Row(
                      children: [
                        const Expanded(child: SkeletonChartCard()),
                        context.sw(12),
                        const Expanded(child: SkeletonChartCard()),
                      ],
                    ),
                  ],
                );
              }
              return Column(
                children: List.generate(
                  4,
                  (_) => const Padding(
                    padding: EdgeInsets.only(bottom: 12),
                    child: SkeletonChartCard(),
                  ),
                ),
              );
            },
          ),
          context.sh(20),

          // Alerts
          const SkeletonBox(width: 100, height: 14),
          context.sh(10),
          ...List.generate(
            3,
            (_) => const Padding(
              padding: EdgeInsets.only(bottom: 8),
              child: SkeletonAlertCard(),
            ),
          ),
          context.sh(24),
        ],
      ),
    );
  }
}

/// Mini skeleton for a single executive summary item.
class _SummarySkeleton extends StatelessWidget {
  const _SummarySkeleton();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SkeletonCircle(size: 20),
        context.sh(6),
        const SkeletonBox(width: 48, height: 18),
        context.sh(4),
        const SkeletonBox(width: 36, height: 10),
      ],
    );
  }
}
