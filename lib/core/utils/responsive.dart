import 'package:flutter/material.dart';

/// Extension on [BuildContext] to provide dynamic responsive sizing
/// based on the screen's size using [MediaQuery].
extension ResponsiveContext on BuildContext {
  // Screen sizes
  double get screenWidth => MediaQuery.of(this).size.width;
  double get screenHeight => MediaQuery.of(this).size.height;

  // Orientations
  Orientation get orientation => MediaQuery.of(this).orientation;
  bool get isLandscape => orientation == Orientation.landscape;

  // Breakpoints
  bool get isMobile => screenWidth < 601;
  bool get isTablet => screenWidth >= 601 && screenWidth < 1025;
  bool get isDesktop => screenWidth >= 1025;

  /// Dynamic height scaling (reference design height is 800px)
  /// For desktops/large screens, we moderate the scaling to prevent excessively large sizes.
  double rh(double value) {
    if (isDesktop) {
      return (screenHeight / 900) * value;
    } else if (isTablet) {
      return (screenHeight / 850) * value;
    }
    return (screenHeight / 800) * value;
  }

  /// Dynamic width scaling (reference design width is 375px)
  /// For desktops/large screens, we moderate the scaling to prevent excessively large sizes.
  double rw(double value) {
    if (isDesktop) {
      return (screenWidth / 1440) * value;
    } else if (isTablet) {
      return (screenWidth / 768) * value;
    }
    return (screenWidth / 375) * value;
  }

  /// Dynamic average scaling (takes average of scaled width and height)
  /// Perfect for proportional margins, borders, or paddings.
  double rv(double value) {
    return (rh(value) + rw(value)) / 2;
  }

  /// Dynamic responsive [SizedBox] for height
  Widget sh(double height) => SizedBox(height: rh(height));

  /// Dynamic responsive [SizedBox] for width
  Widget sw(double width) => SizedBox(width: rw(width));
}
