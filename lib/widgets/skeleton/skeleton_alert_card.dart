import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../core/theme/skeleton_theme.dart';
import 'skeleton_container.dart';

/// Skeleton placeholder for an alert / notification card.
///
/// Mimics [AlertCard]: severity strip, icon, title, description, timestamp.
class SkeletonAlertCard extends StatelessWidget {
  const SkeletonAlertCard({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonCard(
      padding: EdgeInsets.zero,
      child: IntrinsicHeight(
        child: Row(
          children: [
            // Severity side strip
            Container(
              width: 4,
              decoration: BoxDecoration(
                color: SkeletonTheme.baseColor(context),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(12),
                  bottomLeft: Radius.circular(12),
                ),
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    // Icon placeholder
                    const SkeletonBox(
                      width: 36,
                      height: 36,
                      borderRadius: BorderRadius.all(Radius.circular(8)),
                    ),
                    context.sw(12),
                    // Title + description
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const SkeletonBox(width: 140, height: 14),
                          context.sh(6),
                          const SkeletonBox(width: double.infinity, height: 10),
                        ],
                      ),
                    ),
                    context.sw(12),
                    // Severity badge + timestamp
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SkeletonBox(
                          width: 52,
                          height: 20,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        context.sh(6),
                        const SkeletonBox(width: 48, height: 10),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
