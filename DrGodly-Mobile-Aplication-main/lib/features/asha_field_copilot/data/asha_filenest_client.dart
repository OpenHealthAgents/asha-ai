import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';

/// Client communicating with bezs-filenest for field audio uploads and localized education clips
class AshaFilenestClient {
  final Dio _dio;
  final String filenestBaseUrl;

  AshaFilenestClient({
    Dio? dio,
    this.filenestBaseUrl = 'http://10.0.2.2:8002',
  }) : _dio = dio ??
            Dio(BaseOptions(
              connectTimeout: const Duration(seconds: 15),
              receiveTimeout: const Duration(seconds: 15),
            ));

  /// Uploads local .opus/.aac voice file in chunks to bezs-filenest
  Future<String> uploadAudioFileInChunks({
    required File audioFile,
    required String visitUuid,
    required String workerId,
    required String patientId,
    required String villageLgdCode,
    String languageCode = 'hi',
  }) async {
    final fileBytes = await audioFile.readAsBytes();
    final totalSize = fileBytes.length;
    final fileHash = sha256.convert(fileBytes).toString();
    const chunkSize = 256 * 1024; // 256 KB chunks for 2G/3G networks
    final totalChunks = (totalSize / chunkSize).ceil();

    // 1. Init chunk session
    final initResp = await _dio.post(
      '$filenestBaseUrl/api/v1/media/asha/upload/init',
      data: {
        'file_name': 'visit_audio_${DateTime.now().millisecondsSinceEpoch}.opus',
        'content_type': 'audio/ogg; codecs=opus',
        'total_size_bytes': totalSize,
        'total_chunks': totalChunks,
        'chunk_size_bytes': chunkSize,
        'sha256_hash': fileHash,
        'worker_id': workerId,
        'patient_id': patientId,
        'visit_uuid': visitUuid,
        'village_lgd_code': villageLgdCode,
        'language_code': languageCode,
      },
    );

    final sessionId = initResp.data['session_id'] as String;

    // 2. Upload chunks sequentially
    for (int chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      final start = chunkIndex * chunkSize;
      final end = (start + chunkSize < totalSize) ? start + chunkSize : totalSize;
      final chunkData = fileBytes.sublist(start, end);

      final formData = FormData.fromMap({
        'chunk_index': chunkIndex,
        'chunk': MultipartFile.fromBytes(chunkData, filename: 'chunk_$chunkIndex'),
      });

      await _dio.post(
        '$filenestBaseUrl/api/v1/media/asha/upload/$sessionId/chunk',
        data: formData,
      );
    }

    return sessionId;
  }

  /// Fetches localized audio/visual health education clips from bezs-filenest
  Future<List<Map<String, dynamic>>> fetchHealthEducationClips({
    String? conditionCode,
    String? languageCode,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (conditionCode != null) queryParams['condition_code'] = conditionCode;
      if (languageCode != null) queryParams['language_code'] = languageCode;

      final resp = await _dio.get(
        '$filenestBaseUrl/api/v1/media/health-education',
        queryParameters: queryParams,
      );

      if (resp.statusCode == 200 && resp.data != null) {
        final clips = resp.data['clips'] as List<dynamic>?;
        if (clips != null) {
          return clips.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        }
      }
    } catch (_) {}

    return [];
  }
}
