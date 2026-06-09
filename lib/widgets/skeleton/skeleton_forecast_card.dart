import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import 'skeleton_container.dart';

/// Skeleton placeholder for a forecast KPI card.
///
/// Mimics forecast cards: title, predicted value, confidence badge, mini chart.
class SkeletonForecastCard extends StatelessWidget {
  const SkeletonForecastCard({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Title + confidence badge
          Row(
            children: [
              const Expanded(child: SkeletonBox(width: 80, height: 12)),
              SkeletonBox(
                width: 62,
                height: 22,
                borderRadius: BorderRadius.circular(12),
              ),
            ],
          ),
          context.sh(10),
          // Large value
          const SkeletonBox(width: 110, height: 24),
        ],
      ),
    );
  }
}
