import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../core/theme/skeleton_theme.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Asset Monitoring screen loading state.
///
/// Mimics search bar, filter chips, summary badges, and asset card list.
class AssetMonitoringSkeleton extends StatelessWidget {
  const AssetMonitoringSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Search bar
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: SkeletonShimmer(
            child: Container(
              height: 48,
              decoration: BoxDecoration(
                color: SkeletonTheme.baseColor(context),
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
        context.sh(12),

        // Filter chips
        SizedBox(
          height: 34,
          child: SkeletonShimmer(
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: 5,
              separatorBuilder: (_, __) => context.sw(8),
              itemBuilder: (_, __) => Container(
                width: 90,
                decoration: BoxDecoration(
                  color: SkeletonTheme.baseColor(context),
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
            ),
          ),
        ),
        context.sh(12),

        // Summary badges
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: SkeletonShimmer(
            child: Row(
              children: List.generate(
                4,
                (_) => Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Container(
                    width: 72,
                    height: 28,
                    decoration: BoxDecoration(
                      color: SkeletonTheme.baseColor(context),
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
        context.sh(12),

        // Asset cards
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: 6,
            itemBuilder: (_, __) => const Padding(
              padding: EdgeInsets.only(bottom: 10),
              child: SkeletonAssetCard(),
            ),
          ),
        ),
      ],
    );
  }
}
