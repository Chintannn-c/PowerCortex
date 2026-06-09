import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:guvnl_project/features/anomalies/controllers/fault_controller.dart';
import 'package:guvnl_project/features/equipment/controllers/transformer_controller.dart';
import '../../core/utils/responsive.dart';
import '../../core/theme/app_colors.dart';
import 'package:get/get.dart';
import '../auth/auth_controller.dart';
import '../dashboard/dashboard_screen.dart';
import '../dashboard/dashboard_skeleton.dart';
import '../forecasting/forecasting_screen.dart';
import '../forecasting/forecasting_skeleton.dart';
import '../equipment/asset_monitoring_screen.dart';
import '../equipment/asset_monitoring_skeleton.dart';
import '../anomalies/fault_theft_screen.dart';
import '../anomalies/fault_theft_skeleton.dart';
import '../assistant/ai_assistant_screen.dart';
import '../assistant/ai_assistant_skeleton.dart';
import '../reports/reports_screen.dart';
import '../reports/reports_skeleton.dart';
import '../system_health/system_health_screen.dart';
import '../system_health/system_health_skeleton.dart';
import '../settings/settings_screen.dart';
import '../settings/settings_skeleton.dart';
import 'dart:ui' as ui;
import '../notifications/notifications_screen.dart';
import '../../core/services/notification_service.dart';
import '../assistant/services/assistant_api_service.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  static HomeShellState? of(BuildContext context) {
    return context.findAncestorStateOfType<HomeShellState>();
  }

  @override
  State<HomeShell> createState() => HomeShellState();
}

class HomeShellState extends State<HomeShell> {
  int _currentIndex = 0;
  final List<int> _history = [];
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  late final PageController _pageController;
  final _searchController = TextEditingController();
  bool _isSearching = false;
  bool _isSmartSearching = false;

  @override
  void initState() {
    super.initState();
    final args = Get.arguments;
    if (args is int) {
      _currentIndex = args;
    }
    _pageController = PageController(initialPage: _currentIndex);
    _searchController.addListener(_onSearchChanged);
    Get.put(NotificationService(), permanent: true);
    Get.put(this);
  }

  void _onSearchChanged() {
    final query = _searchController.text;
    if (Get.isRegistered<TransformerController>()) {
      Get.find<TransformerController>().searchQuery.value = query;
    }
    if (Get.isRegistered<FaultController>()) {
      Get.find<FaultController>().searchQuery.value = query;
    }
    setState(() {});
  }

  void _handleSearchSubmit(String query) async {
    if (query.trim().isEmpty) return;

    setState(() {
      _isSmartSearching = true;
    });

    Get.showSnackbar(GetSnackBar(
      messageText: Row(
        children: [
          const SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          ),
          const SizedBox(width: 12),
          Text(
            'PowerCortex AI is parsing query...',
            style: GoogleFonts.poppins(color: Colors.white, fontSize: 13),
          ),
        ],
      ),
      snackPosition: SnackPosition.BOTTOM,
      backgroundColor: AppColors.primaryBlue.withOpacity(0.9),
      duration: const Duration(seconds: 2),
      borderRadius: 8,
      margin: const EdgeInsets.all(12),
    ));

    try {
      final apiService = AssistantApiService();
      final result = await apiService.querySmartSearch(query);
      
      setState(() {
        _isSmartSearching = false;
      });

      if (result['success'] == true) {
        final intent = result['intent'] as String? ?? 'filter';
        if (intent == 'filter') {
          final tabIndex = result['tab'] as int? ?? 2;
          final filterQuery = result['query'] as String? ?? '';
          
          _navigateTo(tabIndex);
          
          setState(() {
            _searchController.text = filterQuery;
            _isSearching = filterQuery.isNotEmpty;
          });
          
          Get.showSnackbar(GetSnackBar(
            message: 'Navigated to ${_titles[tabIndex]}${filterQuery.isNotEmpty ? " and filtered by \'$filterQuery\'" : ""}',
            snackPosition: SnackPosition.BOTTOM,
            backgroundColor: AppColors.healthy.withOpacity(0.9),
            duration: const Duration(seconds: 3),
            borderRadius: 8,
            margin: const EdgeInsets.all(12),
          ));
        } else if (intent == 'answer') {
          final replyText = result['text'] as String? ?? 'No response content.';
          _showAiSearchReply(query, replyText);
        }
      } else {
        Get.showSnackbar(GetSnackBar(
          message: 'Failed to process AI search. Performing default diagnostics search.',
          snackPosition: SnackPosition.BOTTOM,
          backgroundColor: AppColors.warning.withOpacity(0.9),
          duration: const Duration(seconds: 3),
          borderRadius: 8,
          margin: const EdgeInsets.all(12),
        ));
        _navigateTo(2);
        setState(() {
          _isSearching = true;
        });
      }
    } catch (e) {
      setState(() {
        _isSmartSearching = false;
      });
      Get.showSnackbar(GetSnackBar(
        message: 'Error connecting to search helper. Defaulting to local filter.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.critical.withOpacity(0.9),
        duration: const Duration(seconds: 3),
        borderRadius: 8,
        margin: const EdgeInsets.all(12),
      ));
    }
  }

  List<Map<String, dynamic>> _extractRedirections(String text) {
    final List<Map<String, dynamic>> links = [];
    final Set<String> seen = {};

    // Match faults like FLT-002, FLT-104, etc.
    final faultRegex = RegExp(r'\bFLT-\d+\b', caseSensitive: false);
    for (final match in faultRegex.allMatches(text)) {
      final id = match.group(0)!.toUpperCase();
      if (!seen.contains(id)) {
        seen.add(id);
        links.add({
          'label': id,
          'icon': Icons.warning_amber_rounded,
          'color': AppColors.critical,
          'tab': 3, // Anomalies
          'query': id,
        });
      }
    }

    // Match transformers like T-104, T-108, etc.
    final transRegex = RegExp(r'\bT-\d+\b', caseSensitive: false);
    for (final match in transRegex.allMatches(text)) {
      final id = match.group(0)!.toUpperCase();
      if (!seen.contains(id)) {
        seen.add(id);
        links.add({
          'label': id,
          'icon': Icons.electrical_services_rounded,
          'color': AppColors.primaryBlue,
          'tab': 2, // Diagnostics
          'query': id,
        });
      }
    }

    return links;
  }

  void _showAiSearchReply(String query, String reply) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final links = _extractRedirections(reply);
    
    showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'AI Search Reply',
      barrierColor: Colors.black.withOpacity(0.55),
      transitionDuration: const Duration(milliseconds: 350),
      pageBuilder: (context, animation, secondaryAnimation) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Hero(
              tag: 'ai_search_reply',
              child: Material(
                color: Colors.transparent,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: BackdropFilter(
                    filter: ui.ImageFilter.blur(sigmaX: 16.0, sigmaY: 16.0),
                    child: Container(
                      width: 480,
                      constraints: const BoxConstraints(maxHeight: 450),
                      decoration: BoxDecoration(
                        color: isDark 
                            ? AppColors.darkCard.withOpacity(0.65) 
                            : AppColors.lightCard.withOpacity(0.75),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: (isDark ? Colors.white : Colors.black).withOpacity(0.08),
                          width: 1.5,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.25),
                            blurRadius: 32,
                            offset: const Offset(0, 16),
                          ),
                        ],
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(20),
                            decoration: BoxDecoration(
                              border: Border(
                                bottom: BorderSide(
                                  color: (isDark ? Colors.white : Colors.black).withOpacity(0.06),
                                  width: 1,
                                ),
                              ),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: AppColors.primaryBlue.withOpacity(0.15),
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.auto_awesome,
                                    color: AppColors.primaryBlue,
                                    size: 20,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    'PowerCortex Smart AI',
                                    style: GoogleFonts.poppins(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 16,
                                      color: isDark ? AppColors.darkText : AppColors.lightText,
                                    ),
                                  ),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.close, size: 20),
                                  onPressed: () => Navigator.pop(context),
                                ),
                              ],
                            ),
                          ),
                          Expanded(
                            child: SingleChildScrollView(
                              padding: const EdgeInsets.all(24),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Query: "$query"',
                                    style: GoogleFonts.poppins(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w500,
                                      color: isDark ? Colors.white60 : Colors.black54,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  Text(
                                    reply,
                                    style: GoogleFonts.poppins(
                                      fontSize: 14,
                                      height: 1.6,
                                      color: isDark ? Colors.white : Colors.black,
                                    ),
                                  ),
                                  if (links.isNotEmpty) ...[
                                    const SizedBox(height: 20),
                                    Divider(
                                      color: (isDark ? Colors.white : Colors.black).withOpacity(0.08),
                                      height: 1,
                                    ),
                                    const SizedBox(height: 16),
                                    Text(
                                      'Quick Actions / Redirection:',
                                      style: GoogleFonts.poppins(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600,
                                        letterSpacing: 0.5,
                                        color: isDark ? Colors.white : Colors.black,
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    Wrap(
                                      spacing: 8,
                                      runSpacing: 8,
                                      children: links.map((link) {
                                        return ActionChip(
                                          avatar: Icon(
                                            link['icon'] as IconData,
                                            size: 14,
                                            color: link['color'] as Color,
                                          ),
                                          label: Text(
                                            link['label'] as String,
                                            style: GoogleFonts.poppins(
                                              fontSize: 12,
                                              fontWeight: FontWeight.w600,
                                              color: isDark ? Colors.white : Colors.black87,
                                            ),
                                          ),
                                          backgroundColor: (link['color'] as Color).withOpacity(0.12),
                                          side: BorderSide(
                                            color: (link['color'] as Color).withOpacity(0.25),
                                            width: 1,
                                          ),
                                          shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(8),
                                          ),
                                          onPressed: () {
                                            Navigator.pop(context); // Close the reply dialog
                                            _navigateTo(link['tab'] as int); // Redirect
                                            setState(() {
                                              _searchController.text = link['query'] as String;
                                              _isSearching = true;
                                            });
                                          },
                                        );
                                      }).toList(),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              border: Border(
                                top: BorderSide(
                                  color: (isDark ? Colors.white : Colors.black).withOpacity(0.06),
                                  width: 1,
                                ),
                              ),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                TextButton(
                                  onPressed: () {
                                    Navigator.pop(context);
                                  },
                                  child: Text(
                                    'Close',
                                    style: TextStyle(
                                      color: isDark ? Colors.white70 : Colors.black54,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                ElevatedButton.icon(
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppColors.primaryBlue,
                                    foregroundColor: Colors.white,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                  ),
                                  icon: const Icon(Icons.chat_bubble_outline, size: 16),
                                  label: Text(
                                    'Open Chat Assistant',
                                    style: GoogleFonts.poppins(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  onPressed: () {
                                    Navigator.pop(context);
                                    _navigateTo(4);
                                  },
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
      transitionBuilder: (context, animation, secondaryAnimation, child) {
        return ScaleTransition(
          scale: CurvedAnimation(
            parent: animation,
            curve: Curves.easeOutBack,
          ),
          child: FadeTransition(
            opacity: animation,
            child: child,
          ),
        );
      },
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    _searchController.dispose();
    Get.delete<HomeShellState>();
    super.dispose();
  }

  void navigateTo(int index) {
    _navigateTo(index);
  }

  void _navigateTo(int index) {
    if (_currentIndex != index) {
      _searchController.clear();
      _history.remove(index);
      _history.add(_currentIndex);
      setState(() {
        _currentIndex = index;
        _isSearching = false;
      });

      if (index < 4) {
        if (_pageController.hasClients) {
          _pageController.animateToPage(
            index,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          );
        } else {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (_pageController.hasClients) {
              _pageController.jumpToPage(index);
            }
          });
        }
      }
    }
  }

  void goBack() {
    _goBack();
  }

  void _goBack() {
    _searchController.clear();
    setState(() {
      _isSearching = false;
    });
    if (_history.isNotEmpty) {
      final prev = _history.removeLast();
      setState(() => _currentIndex = prev);
      if (prev < 4) {
        if (_pageController.hasClients) {
          _pageController.animateToPage(
            prev,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          );
        } else {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (_pageController.hasClients) {
              _pageController.jumpToPage(prev);
            }
          });
        }
      }
    } else if (_currentIndex != 0) {
      setState(() => _currentIndex = 0);
      if (_pageController.hasClients) {
        _pageController.animateToPage(
          0,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
      } else {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (_pageController.hasClients) {
            _pageController.jumpToPage(0);
          }
        });
      }
    }
  }

  void _openNotifications() {
    showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Notifications',
      barrierColor: Colors.black54,
      transitionDuration: const Duration(milliseconds: 300),
      pageBuilder: (context, animation, secondaryAnimation) {
        return const Align(
          alignment: Alignment.centerRight,
          child: NotificationsDrawer(),
        );
      },
      transitionBuilder: (context, animation, secondaryAnimation, child) {
        return SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(1, 0),
            end: Offset.zero,
          ).animate(CurvedAnimation(
            parent: animation,
            curve: Curves.easeOutCubic,
          )),
          child: child,
        );
      },
    );
  }

  /// Each page is wrapped with its skeleton counterpart.
  /// _SkeletonPage handles the simulated load → crossfade transition.
  late final List<Widget> _pages = [
    const _SkeletonPage(
      skeleton: DashboardSkeleton(),
      child: DashboardScreen(),
    ),
    const _SkeletonPage(
      skeleton: ForecastingSkeleton(),
      child: ForecastingScreen(),
    ),
    const _SkeletonPage(
      skeleton: AssetMonitoringSkeleton(),
      child: AssetMonitoringScreen(),
    ),
    const _SkeletonPage(
      skeleton: FaultTheftSkeleton(),
      child: FaultTheftScreen(),
    ),
    const _SkeletonPage(
      skeleton: AIAssistantSkeleton(),
      child: AIAssistantScreen(),
    ),
    const _SkeletonPage(skeleton: ReportsSkeleton(), child: ReportsScreen()),
    const _SkeletonPage(
      skeleton: SystemHealthSkeleton(),
      child: SystemHealthScreen(),
    ),
    const _SkeletonPage(skeleton: SettingsSkeleton(), child: SettingsScreen()),
  ];

  final _titles = [
    'Dashboard',
    'Forecasting',
    'Diagnostics',
    'Anomalies',
    'AI Assistant',
    'Reports & Analytics',
    'System Health',
    'Settings',
  ];

  final _navItems = const [
    BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
    BottomNavigationBarItem(icon: Icon(Icons.show_chart), label: 'Forecast'),
    BottomNavigationBarItem(
      icon: Icon(Icons.electrical_services),
      label: 'Diagnostics',
    ),
    BottomNavigationBarItem(
      icon: Icon(Icons.warning_amber),
      label: 'Anomalies',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final width = MediaQuery.of(context).size.width;
    final isDesktop = width >= 1025;
    final isTablet = width >= 601 && width < 1025;

    Widget mainContent;

    // Desktop: sidebar + content
    if (isDesktop) {
      mainContent = Scaffold(
        body: Row(
          children: [
            _buildSidebar(context, isDark),
            Expanded(
              child: Column(
                children: [
                  _buildTopBar(context, isDark),
                  Expanded(child: _buildBody()),
                ],
              ),
            ),
          ],
        ),
      );
    }
    // Tablet: navigation rail + content
    else if (isTablet) {
      mainContent = Scaffold(
        body: Row(
          children: [
            NavigationRail(
              selectedIndex: _currentIndex < 4 ? _currentIndex : 0,
              onDestinationSelected: _navigateTo,
              labelType: NavigationRailLabelType.all,
              backgroundColor: isDark
                  ? AppColors.darkCard
                  : AppColors.lightCard,
              selectedIconTheme: const IconThemeData(
                color: AppColors.primaryBlue,
              ),
              selectedLabelTextStyle: const TextStyle(
                color: AppColors.primaryBlue,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
              unselectedLabelTextStyle: TextStyle(
                color: isDark
                    ? AppColors.darkTextSecondary
                    : AppColors.lightTextSecondary,
                fontSize: 11,
              ),
              leading: Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: Image.asset(
                    'assets/images/logo.png',
                    width: 28,
                    height: 28,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
              destinations: const [
                NavigationRailDestination(
                  icon: Icon(Icons.dashboard),
                  label: Text('Dashboard'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.show_chart),
                  label: Text('Forecast'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.electrical_services),
                  label: Text('Diagnostics'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.warning_amber),
                  label: Text('Anomalies'),
                ),
              ],
              trailing: Expanded(
                child: Align(
                  alignment: Alignment.bottomCenter,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          onPressed: () => _navigateTo(5),
                          icon: Icon(
                            Icons.assessment,
                            color: _currentIndex == 5
                                ? AppColors.primaryBlue
                                : null,
                          ),
                          tooltip: 'Reports',
                        ),
                        IconButton(
                          onPressed: () => _navigateTo(6),
                          icon: Icon(
                            Icons.monitor_heart,
                            color: _currentIndex == 6
                                ? AppColors.primaryBlue
                                : null,
                          ),
                          tooltip: 'System Health',
                        ),
                        IconButton(
                          onPressed: () => _navigateTo(4),
                          icon: Icon(
                            Icons.smart_toy,
                            color: _currentIndex == 4
                                ? AppColors.primaryBlue
                                : null,
                          ),
                          tooltip: 'AI Assistant',
                        ),
                        IconButton(
                          onPressed: () => _navigateTo(7),
                          icon: Icon(
                            Icons.settings,
                            color: _currentIndex == 7
                                ? AppColors.primaryBlue
                                : null,
                          ),
                          tooltip: 'Settings',
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            VerticalDivider(
              width: 1,
              color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
            ),
            Expanded(
              child: Column(
                children: [
                  _buildTopBar(context, isDark),
                  Expanded(child: _buildBody()),
                ],
              ),
            ),
          ],
        ),
      );
    }
    // Mobile: bottom navigation
    else {
      mainContent = Scaffold(
        key: _scaffoldKey,
        appBar: AppBar(
          automaticallyImplyLeading: false,
          leading: _currentIndex != 0
              ? IconButton(
                  icon: const Icon(Icons.arrow_back),
                  onPressed: _goBack,
                  tooltip: 'Go Back',
                )
              : null,
          title: _isSearching
              ? TextField(
                  controller: _searchController,
                  autofocus: true,
                  style: const TextStyle(fontSize: 16),
                  onSubmitted: _handleSearchSubmit,
                  decoration: InputDecoration(
                    hintText: 'Search...',
                    border: InputBorder.none,
                    hintStyle: TextStyle(
                      color: isDark ? Colors.white60 : Colors.black45,
                    ),
                  ),
                )
              : Row(
                  children: [
                    if (_currentIndex == 0) ...[
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: Image.asset(
                          'assets/images/logo.png',
                          width: 24,
                          height: 24,
                          fit: BoxFit.contain,
                        ),
                      ),
                      context.sw(8),
                    ],
                    Expanded(
                      child: Text(
                        _titles[_currentIndex],
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                      ),
                    ),
                  ],
                ),
          actions: [
            if (_isSearching && _searchController.text.isNotEmpty)
              _isSmartSearching
                  ? const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Center(
                        child: SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(AppColors.primaryBlue),
                          ),
                        ),
                      ),
                    )
                  : IconButton(
                      icon: const Icon(Icons.check, color: AppColors.primaryBlue),
                      onPressed: () => _handleSearchSubmit(_searchController.text),
                      tooltip: 'Submit AI Search',
                    ),
            IconButton(
              icon: Icon(_isSearching ? Icons.close : Icons.search),
              onPressed: () {
                setState(() {
                  if (_isSearching) {
                    _isSearching = false;
                    _searchController.clear();
                  } else {
                    _isSearching = true;
                  }
                });
              },
            ),
            Stack(
              children: [
                IconButton(
                  onPressed: _openNotifications,
                  icon: const Icon(Icons.notifications_outlined),
                ),
                Obx(() {
                  final unreadCount = Get.find<NotificationService>().unreadCount.value;
                  if (unreadCount == 0) return const SizedBox.shrink();
                  return Positioned(
                    right: 8,
                    top: 8,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: const BoxDecoration(
                        color: AppColors.critical,
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          '$unreadCount',
                          style: const TextStyle(
                            fontSize: 9,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  );
                }),
              ],
            ),
            if (_currentIndex == 0) ...[
              IconButton(
                icon: const Icon(Icons.menu),
                onPressed: () => _scaffoldKey.currentState?.openEndDrawer(),
                tooltip: 'Open Menu',
              ),
            ],
            context.sw(4),
          ],
        ),
        body: _buildBody(),
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: _currentIndex < 4 ? _currentIndex : 0,
          onTap: _navigateTo,
          items: _navItems,
        ),
        endDrawer: _buildDrawer(context, isDark),
      );
    }

    return PopScope(
      canPop: _currentIndex == 0 && _history.isEmpty,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        _goBack();
      },
      child: mainContent,
    );
  }

  Widget _buildBody() {
    if (_currentIndex < 4) {
      return PageView(
        controller: _pageController,
        onPageChanged: (index) {
          if (index < 4) {
            setState(() {
              if (_currentIndex != index) {
                _history.remove(index);
                _history.add(_currentIndex);
                _currentIndex = index;
              }
            });
          }
        },
        children: _pages.sublist(0, 4),
      );
    } else {
      return _pages[_currentIndex];
    }
  }

  // ─── DESKTOP SIDEBAR ─────────────────────────────────────────

  Widget _buildSidebar(BuildContext context, bool isDark) {
    return Container(
      width: 240,
      color: isDark ? AppColors.darkCard : AppColors.lightCard,
      child: Column(
        children: [
          // Logo
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: AppColors.primaryBlue.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: Image.asset(
                      'assets/images/logo.png',
                      width: 22,
                      height: 22,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
                context.sw(10),
                Text(
                  'PowerCortex',
                  style: GoogleFonts.poppins(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primaryBlue,
                  ),
                ),
              ],
            ),
          ),
          Divider(
            height: 1,
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
          context.sh(8),

          // Nav items
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              children: [
                _sidebarItem(0, Icons.dashboard, 'Dashboard'),
                _sidebarItem(1, Icons.show_chart, 'Forecasting'),
                _sidebarItem(2, Icons.electrical_services, 'Diagnostics'),
                _sidebarItem(3, Icons.warning_amber, 'Anomalies'),
                context.sh(16),
                Padding(
                  padding: const EdgeInsets.only(left: 8, bottom: 8),
                  child: Text(
                    'ANALYTICS',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                      color: isDark
                          ? AppColors.darkTextSecondary
                          : AppColors.lightTextSecondary,
                    ),
                  ),
                ),
                _sidebarItem(5, Icons.assessment, 'Reports'),
                _sidebarItem(6, Icons.monitor_heart, 'System Health'),
                context.sh(16),
                Padding(
                  padding: const EdgeInsets.only(left: 8, bottom: 8),
                  child: Text(
                    'PREFERENCES',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                      color: isDark
                          ? AppColors.darkTextSecondary
                          : AppColors.lightTextSecondary,
                    ),
                  ),
                ),
                _sidebarItem(4, Icons.smart_toy, 'AI Assistant'),
                _sidebarItem(7, Icons.settings, 'Settings'),
              ],
            ),
          ),

          // User
          Divider(
            height: 1,
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.primaryBlue.withOpacity(0.15),
                  child: const Icon(
                    Icons.person,
                    size: 18,
                    color: AppColors.primaryBlue,
                  ),
                ),
                context.sw(10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Obx(() => Text(
                        Get.find<AuthController>().currentUser.value?.fullName ?? 'User',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: isDark
                              ? AppColors.darkText
                              : AppColors.lightText,
                        ),
                      )),
                      Obx(() => Text(
                        Get.find<AuthController>().currentUser.value?.department ?? 'Operator',
                        style: TextStyle(
                          fontSize: 10,
                          color: isDark
                              ? AppColors.darkTextSecondary
                              : AppColors.lightTextSecondary,
                        ),
                      )),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => Get.find<AuthController>().logout(),
                  icon: const Icon(
                    Icons.logout,
                    size: 18,
                    color: AppColors.critical,
                  ),
                  tooltip: 'Logout',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _sidebarItem(int index, IconData icon, String label) {
    final isSelected = _currentIndex == index;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 2),
      child: ListTile(
        dense: true,
        visualDensity: const VisualDensity(vertical: -2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        selected: isSelected,
        selectedTileColor: AppColors.primaryBlue.withOpacity(0.1),
        leading: Icon(
          icon,
          size: 20,
          color: isSelected
              ? AppColors.primaryBlue
              : isDark
              ? AppColors.darkTextSecondary
              : AppColors.lightTextSecondary,
        ),
        title: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
            color: isSelected
                ? AppColors.primaryBlue
                : isDark
                ? AppColors.darkText
                : AppColors.lightText,
          ),
        ),
        onTap: () => _navigateTo(index),
      ),
    );
  }

  // ─── TOP BAR (Tablet/Desktop) ─────────────────────────────────

  Widget _buildTopBar(BuildContext context, bool isDark) {
    return Container(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard : AppColors.lightCard,
        border: Border(
          bottom: BorderSide(
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
        ),
      ),
      child: Row(
        children: [
          if (_currentIndex != 0) ...[
            IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: _goBack,
              tooltip: 'Go Back',
            ),
            context.sw(8),
          ],
          Text(
            _titles[_currentIndex],
            style: GoogleFonts.poppins(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              color: isDark ? AppColors.darkText : AppColors.lightText,
            ),
          ),
          const Spacer(),
          // Search
          SizedBox(
            width: 240,
            height: 38,
            child: TextField(
              controller: _searchController,
              onSubmitted: _handleSearchSubmit,
              decoration: InputDecoration(
                hintText: 'Search...',
                prefixIcon: const Icon(Icons.search, size: 18),
                suffixIcon: _isSmartSearching
                    ? const Padding(
                        padding: EdgeInsets.all(10.0),
                        child: SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(AppColors.primaryBlue),
                          ),
                        ),
                      )
                    : _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 16),
                            padding: EdgeInsets.zero,
                            constraints: const BoxConstraints(),
                            onPressed: () => _searchController.clear(),
                          )
                        : null,
                contentPadding: const EdgeInsets.symmetric(vertical: 0),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                  borderSide: BorderSide(
                    color: isDark
                        ? AppColors.darkBorder
                        : AppColors.lightBorder,
                  ),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                  borderSide: BorderSide(
                    color: isDark
                        ? AppColors.darkBorder
                        : AppColors.lightBorder,
                  ),
                ),
              ),
            ),
          ),
          context.sw(16),
          Stack(
            children: [
              IconButton(
                onPressed: _openNotifications,
                icon: Icon(
                  Icons.notifications_outlined,
                  color: isDark ? AppColors.darkText : AppColors.lightText,
                ),
              ),
              Obx(() {
                  final unreadCount = Get.find<NotificationService>().unreadCount.value;
                  if (unreadCount == 0) return const SizedBox.shrink();
                  return Positioned(
                    right: 8,
                    top: 8,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: const BoxDecoration(
                        color: AppColors.critical,
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          '$unreadCount',
                          style: const TextStyle(
                            fontSize: 9,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  );
              }),
            ],
          ),
          context.sw(8),
          CircleAvatar(
            radius: 16,
            backgroundColor: AppColors.primaryBlue.withOpacity(0.15),
            child: const Icon(
              Icons.person,
              size: 18,
              color: AppColors.primaryBlue,
            ),
          ),
        ],
      ),
    );
  }

  // ─── MOBILE DRAWER ────────────────────────────────────────────

  Widget _buildDrawer(BuildContext context, bool isDark) {
    return Drawer(
      backgroundColor: isDark ? AppColors.darkCard : AppColors.lightCard,
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(color: AppColors.primaryBlue),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircleAvatar(
                  radius: 28,
                  backgroundColor: Colors.white24,
                  child: Icon(Icons.person, color: Colors.white, size: 28),
                ),
                context.sh(12),
                Obx(() => Text(
                  Get.find<AuthController>().currentUser.value?.fullName ?? 'User',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.poppins(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 16,
                  ),
                )),
                Obx(() => Text(
                  Get.find<AuthController>().currentUser.value?.email ?? 'user@powercortex.in',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.poppins(
                    color: Colors.white70,
                    fontSize: 12,
                  ),
                )),
              ],
            ),
          ),
          _drawerItem(5, Icons.assessment, 'Reports & Analytics'),
          _drawerItem(6, Icons.monitor_heart, 'System Health'),
          _drawerItem(4, Icons.smart_toy, 'AI Assistant'),
          _drawerItem(7, Icons.settings, 'Settings'),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: AppColors.critical),
            title: const Text(
              'Logout',
              style: TextStyle(color: AppColors.critical),
            ),
            onTap: () => Get.find<AuthController>().logout(),
          ),
        ],
      ),
    );
  }

  Widget _drawerItem(int index, IconData icon, String label) {
    return ListTile(
      leading: Icon(
        icon,
        color: _currentIndex == index ? AppColors.primaryBlue : null,
      ),
      title: Text(
        label,
        style: TextStyle(
          fontWeight: _currentIndex == index
              ? FontWeight.w600
              : FontWeight.normal,
          color: _currentIndex == index ? AppColors.primaryBlue : null,
        ),
      ),
      onTap: () {
        _navigateTo(index);
        Navigator.pop(context);
      },
    );
  }
}

/// Wrapper that shows a [skeleton] for a brief simulated load,
/// then smoothly crossfades to the real [child] content.
///
/// The skeleton appears only once per widget lifetime (first build).
/// On subsequent rebuilds the real content is shown immediately.
class _SkeletonPage extends StatefulWidget {
  final Widget skeleton;
  final Widget child;

  const _SkeletonPage({required this.skeleton, required this.child});

  @override
  State<_SkeletonPage> createState() => _SkeletonPageState();
}

class _SkeletonPageState extends State<_SkeletonPage> {
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(milliseconds: 1500), () {
      if (mounted) setState(() => _isLoading = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 400),
      switchInCurve: Curves.easeIn,
      switchOutCurve: Curves.easeOut,
      child: _isLoading
          ? KeyedSubtree(
              key: const ValueKey('skeleton'),
              child: widget.skeleton,
            )
          : KeyedSubtree(
              key: const ValueKey('content'),
              child: widget.child,
            ),
    );
  }
}
