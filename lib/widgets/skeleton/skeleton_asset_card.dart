import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import 'skeleton_container.dart';


/// Skeleton placeholder for an asset / equipment card.
///
/// Mimics [AssetCard]: icon, name, type, health gauge, status badge, timestamp.
class SkeletonAssetCard extends StatelessWidget {
  const SkeletonAssetCard({super.key});

  @override
  Widget build(BuildContext context) {
    return SkeletonCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon + Name + Status
          Row(
            children: [
              const SkeletonBox(
                width: 42,
                height: 42,
                borderRadius: BorderRadius.all(Radius.circular(10)),
              ),
              context.sw(12),
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
              SkeletonBox(
                width: 68,
                height: 26,
                borderRadius: BorderRadius.circular(20),
              ),
            ],
          ),
          context.sh(16),
          // Health score bar
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SkeletonBox(width: 72, height: 10),
              context.sh(8),
              Row(
                children: [
                  const Expanded(
                    child: SkeletonBox(height: 6, borderRadius: BorderRadius.all(Radius.circular(3))),
                  ),
                  context.sw(8),
                  const SkeletonBox(width: 32, height: 12),
                ],
              ),
            ],
          ),
          context.sh(10),
          // Timestamp
          Row(
            children: [
              const SkeletonCircle(size: 13),
              context.sw(6),
              const SkeletonBox(width: 90, height: 10),
            ],
          ),
        ],
      ),
    );
  }
}
