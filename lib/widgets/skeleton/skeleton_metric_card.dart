import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import 'skeleton_container.dart';

/// Skeleton loading placeholder for a KPI / Metric Card.
///
/// Mimics the real [KpiCard] structure:
/// icon box, title text, large value, and trend badge.
class SkeletonMetricCard extends StatelessWidget {
  const SkeletonMetricCard({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Icon + trend row
          Row(
            children: [
              const SkeletonBox(width: 36, height: 36, borderRadius: BorderRadius.all(Radius.circular(8))),
              const Spacer(),
              SkeletonBox(width: 56, height: 22, borderRadius: BorderRadius.circular(20)),
            ],
          ),
          context.sh(14),
          // Title
          const SkeletonBox(width: 80, height: 12),
          context.sh(8),
          // Value + unit
          Row(
            children: [
              const SkeletonBox(width: 72, height: 28),
              context.sw(6),
              const SkeletonBox(width: 24, height: 14),
            ],
          ),
        ],
      ),
    );
  }
}
