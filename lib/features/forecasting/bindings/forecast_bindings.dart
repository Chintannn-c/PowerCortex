import 'package:get/get.dart';
import '../controllers/forecast_controller.dart';

class ForecastBindings extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<ForecastController>(() => ForecastController());
  }
}
