import 'package:flutter/material.dart';

import '../../core/utils/responsive.dart';
import '../../widgets/skeleton/skeletons.dart';

/// Full-page skeleton for the Settings screen.
///
/// Mimics profile card, switch rows, and list tile sections.
class SettingsSkeleton extends StatelessWidget {
  const SettingsSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Profile card
          SkeletonCard(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                const SkeletonCircle(size: 64),
                context.sw(16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SkeletonBox(width: 120, height: 18),
                      context.sh(6),
                      const SkeletonBox(width: 180, height: 10),
                      context.sh(4),
                      const SkeletonBox(width: 140, height: 10),
                    ],
                  ),
                ),
                const SkeletonBox(
                  width: 32,
                  height: 32,
                  borderRadius: BorderRadius.all(Radius.circular(8)),
                ),
              ],
            ),
          ),
          context.sh(24),

          // Appearance section
          const SkeletonBox(width: 90, height: 14),
          context.sh(8),
          _switchRowSkeleton(context),
          context.sh(20),

          // Notifications section
          const SkeletonBox(width: 100, height: 14),
          context.sh(8),
          _switchRowSkeleton(context),
          _switchRowSkeleton(context),
          _switchRowSkeleton(context),
          context.sh(20),

          // Security section
          const SkeletonBox(width: 72, height: 14),
          context.sh(8),
          _listTileSkeleton(context),
          _listTileSkeleton(context),
          context.sh(20),

          // System section
          const SkeletonBox(width: 60, height: 14),
          context.sh(8),
          _listTileSkeleton(context),
          _listTileSkeleton(context),
          _listTileSkeleton(context),
          context.sh(24),
        ],
      ),
    );
  }

  Widget _switchRowSkeleton(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: SkeletonCard(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            const SkeletonBox(width: 36, height: 36, borderRadius: BorderRadius.all(Radius.circular(8))),
            context.sw(14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SkeletonBox(width: 120, height: 14),
                  context.sh(4),
                  const SkeletonBox(width: 160, height: 10),
                ],
              ),
            ),
            const SkeletonBox(width: 44, height: 24, borderRadius: BorderRadius.all(Radius.circular(12))),
          ],
        ),
      ),
    );
  }

  Widget _listTileSkeleton(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: SkeletonCard(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            const SkeletonBox(width: 36, height: 36, borderRadius: BorderRadius.all(Radius.circular(8))),
            context.sw(14),
            const Expanded(child: SkeletonBox(width: 120, height: 14)),
            const SkeletonBox(width: 16, height: 16, borderRadius: BorderRadius.all(Radius.circular(4))),
          ],
        ),
      ),
    );
  }
}
