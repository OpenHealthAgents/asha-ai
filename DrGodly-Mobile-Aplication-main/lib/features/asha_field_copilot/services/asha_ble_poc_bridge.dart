import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

class PocReadingEvent {
  final String deviceType; // "BP_CUFF" | "PULSE_OX" | "GLUCOMETER" | "THERMOMETER" | "HEMOGLOBIN"
  final Map<String, dynamic> values;
  final String deviceName;
  final String timestamp;

  const PocReadingEvent({
    required this.deviceType,
    required this.values,
    required this.deviceName,
    required this.timestamp,
  });
}

/// BLE GATT Bridge connecting low-cost rural screening kits directly to DrGodly
class AshaBlePocBridge {
  static final AshaBlePocBridge instance = AshaBlePocBridge._init();

  final _pocReadingController = StreamController<PocReadingEvent>.broadcast();
  Stream<PocReadingEvent> get readingStream => _pocReadingController.stream;

  final _isScanningController = StreamController<bool>.broadcast();
  Stream<bool> get isScanningStream => _isScanningController.stream;

  bool _isScanning = false;
  bool get isScanning => _isScanning;

  BluetoothDevice? _connectedPocDevice;
  BluetoothDevice? get connectedDevice => _connectedPocDevice;

  AshaBlePocBridge._init();

  /// Starts BLE scanning for recognized Point-of-Care screening devices
  Future<void> startPocScan() async {
    final isSupported = await FlutterBluePlus.isSupported;
    if (!isSupported) {
      if (kDebugMode) print('[AshaBlePocBridge] Bluetooth not supported on this device');
      return;
    }

    _isScanning = true;
    _isScanningController.add(true);

    try {
      await FlutterBluePlus.startScan(
        timeout: const Duration(seconds: 10),
      );

      FlutterBluePlus.scanResults.listen((results) {
        for (final r in results) {
          final name = r.device.platformName.toLowerCase();
          if (name.contains('bp') ||
              name.contains('omron') ||
              name.contains('oximeter') ||
              name.contains('contour') ||
              name.contains('hb') ||
              name.contains('thermo')) {
            connectToPocDevice(r.device);
            break;
          }
        }
      });
    } catch (e) {
      if (kDebugMode) print('[AshaBlePocBridge] Scan error: $e');
    }
  }

  Future<void> connectToPocDevice(BluetoothDevice device) async {
    try {
      await device.connect(autoConnect: false);
      _connectedPocDevice = device;
      await FlutterBluePlus.stopScan();
      _isScanning = false;
      _isScanningController.add(false);

      // Discover GATT services & characteristics
      final services = await device.discoverServices();
      for (final s in services) {
        final uuidStr = s.uuid.str.toUpperCase();

        // 1. Blood Pressure Service (0x1810)
        if (uuidStr.contains('1810')) {
          for (final c in s.characteristics) {
            if (c.uuid.str.toUpperCase().contains('2A35')) {
              await c.setNotifyValue(true);
              c.lastValueStream.listen((data) => _parseBpData(data, device.platformName));
            }
          }
        }

        // 2. Pulse Oximeter Service (0x1822)
        if (uuidStr.contains('1822') || uuidStr.contains('180D')) {
          for (final c in s.characteristics) {
            if (c.uuid.str.toUpperCase().contains('2A5F') || c.uuid.str.toUpperCase().contains('2A37')) {
              await c.setNotifyValue(true);
              c.lastValueStream.listen((data) => _parseOximeterData(data, device.platformName));
            }
          }
        }

        // 3. Health Thermometer (0x1809)
        if (uuidStr.contains('1809')) {
          for (final c in s.characteristics) {
            if (c.uuid.str.toUpperCase().contains('2A1C')) {
              await c.setNotifyValue(true);
              c.lastValueStream.listen((data) => _parseThermometerData(data, device.platformName));
            }
          }
        }
      }
    } catch (e) {
      if (kDebugMode) print('[AshaBlePocBridge] Connection error: $e');
    }
  }

  /// Parses standard BLE GATT 0x2A35 Blood Pressure Measurement packet
  void _parseBpData(List<int> data, String deviceName) {
    if (data.length < 5) return;
    final systolic = data[1] + (data[2] << 8);
    final diastolic = data[3] + (data[4] << 8);
    int? pulse;
    if (data.length >= 8) {
      pulse = data[7];
    }

    _pocReadingController.add(PocReadingEvent(
      deviceType: 'BP_CUFF',
      values: {
        'systolic_bp': systolic.toDouble(),
        'diastolic_bp': diastolic.toDouble(),
        if (pulse != null) 'pulse': pulse.toDouble(),
      },
      deviceName: deviceName.isNotEmpty ? deviceName : 'BLE BP Cuff',
      timestamp: DateTime.now().toUtc().toIso8601String(),
    ));
  }

  /// Parses standard BLE GATT Pulse Oximeter packet
  void _parseOximeterData(List<int> data, String deviceName) {
    if (data.length < 3) return;
    final spo2 = data[1].toDouble();
    final pulse = data[2].toDouble();

    _pocReadingController.add(PocReadingEvent(
      deviceType: 'PULSE_OX',
      values: {
        'spo2': spo2,
        'pulse': pulse,
      },
      deviceName: deviceName.isNotEmpty ? deviceName : 'Pulse Oximeter',
      timestamp: DateTime.now().toUtc().toIso8601String(),
    ));
  }

  /// Parses standard BLE GATT 0x2A1C Temperature Measurement
  void _parseThermometerData(List<int> data, String deviceName) {
    if (data.length < 5) return;
    final mantissa = data[1] | (data[2] << 8) | (data[3] << 16);
    final tempC = mantissa / 100.0;

    _pocReadingController.add(PocReadingEvent(
      deviceType: 'THERMOMETER',
      values: {
        'temperature_c': tempC,
      },
      deviceName: deviceName.isNotEmpty ? deviceName : 'Smart Thermometer',
      timestamp: DateTime.now().toUtc().toIso8601String(),
    ));
  }

  /// Emits simulated pairing reading for testing and offline field demos
  void injectSimulatedReading(PocReadingEvent event) {
    _pocReadingController.add(event);
  }
}
