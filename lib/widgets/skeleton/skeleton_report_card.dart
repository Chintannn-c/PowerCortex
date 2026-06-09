import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import 'skeleton_container.dart';

/// Skeleton placeholder for a report list item card.
///
/// Mimics report entries: icon, title, meta info, download buttons.
class SkeletonReportCard extends StatelessWidget {
  const SkeletonReportCard({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonCard(
      child: Row(
        children: [
          // File icon
          const SkeletonBox(
            width: 42,
            height: 42,
            borderRadius: BorderRadius.all(Radius.circular(10)),
          ),
          context.sw(14),
          // Title + meta
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SkeletonBox(width: 160, height: 14),
                context.sh(6),
                const SkeletonBox(width: 120, height: 10),
              ],
            ),
          ),
          // Download buttons
          const SkeletonBox(
            width: 32,
            height: 32,
            borderRadius: BorderRadius.all(Radius.circular(8)),
          ),
          context.sw(8),
          const SkeletonBox(
            width: 32,
            height: 32,
            borderRadius: BorderRadius.all(Radius.circular(8)),
          ),
        ],
      ),
    );
  }
}
