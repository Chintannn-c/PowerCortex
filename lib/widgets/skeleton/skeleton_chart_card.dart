import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import 'skeleton_container.dart';

/// Skeleton placeholder for a chart card.
///
/// Mimics [ChartContainer]: title row, filter chips, and large chart area.
class SkeletonChartCard extends StatelessWidget {
  const SkeletonChartCard({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title row
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SkeletonBox(width: 120, height: 14),
                    context.sh(6),
                    const SkeletonBox(width: 80, height: 10),
                  ],
                ),
              ),
              const SkeletonBox(width: 28, height: 28, borderRadius: BorderRadius.all(Radius.circular(6))),
            ],
          ),
          context.sh(16),
          // Chart area
          const SkeletonBox(width: double.infinity, height: 200, borderRadius: BorderRadius.all(Radius.circular(8))),
        ],
      ),
    );
  }
}
