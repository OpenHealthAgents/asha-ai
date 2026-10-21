import 'dart:async';
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import '../models/asha_household.dart';
import '../models/asha_beneficiary.dart';
import '../models/asha_care_gap.dart';
import '../models/asha_sync_mutation.dart';

/// Offline-First Persistence Layer for ASHA Field Copilot.
/// Caches Households, Beneficiaries, Care Gaps, and the Offline Mutation Outbox.
class AshaLocalDatabase {
  static final AshaLocalDatabase instance = AshaLocalDatabase._init();
  static Database? _database;

  AshaLocalDatabase._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('asha_copilot_offline.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future<void> _createDB(Database db, int version) async {
    // 1. Households (FHIR Group representation)
    await db.execute('''
      CREATE TABLE asha_households (
        id TEXT PRIMARY KEY,
        village_lgd_code TEXT NOT NULL,
        head_name TEXT NOT NULL,
        address TEXT NOT NULL,
        ward_number TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        member_count INTEGER NOT NULL,
        members_json TEXT
      )
    ''');

    // 2. Beneficiaries (FHIR Patient representation)
    await db.execute('''
      CREATE TABLE asha_beneficiaries (
        id TEXT PRIMARY KEY,
        household_id TEXT NOT NULL,
        name TEXT NOT NULL,
        gender TEXT NOT NULL,
        age_years INTEGER NOT NULL,
        age_months INTEGER NOT NULL,
        abha_id TEXT,
        rch_id TEXT,
        is_maternal INTEGER NOT NULL DEFAULT 0,
        gestational_weeks INTEGER,
        is_child INTEGER NOT NULL DEFAULT 0,
        received_vaccines TEXT,
        completed_anc_visits INTEGER NOT NULL DEFAULT 0,
        last_ncd_screening_date TEXT
      )
    ''');

    // 3. Care Gaps
    await db.execute('''
      CREATE TABLE asha_care_gaps (
        id TEXT PRIMARY KEY,
        household_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        patient_name TEXT NOT NULL,
        gap_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        due_date TEXT NOT NULL,
        days_overdue INTEGER NOT NULL,
        urgency TEXT NOT NULL,
        action TEXT NOT NULL,
        is_resolved INTEGER NOT NULL DEFAULT 0
      )
    ''');

    // 4. Offline Mutation Outbox
    await db.execute('''
      CREATE TABLE asha_sync_outbox (
        mutation_id TEXT PRIMARY KEY,
        visit_uuid TEXT NOT NULL,
        mutation_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        local_audio_file_path TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING',
        retry_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        last_attempted_at TEXT,
        error_message TEXT
      )
    ''');

    // 5. Localized Audio Health Education Cache (from bezs-filenest)
    await db.execute('''
      CREATE TABLE asha_cached_audio_education (
        clip_id TEXT PRIMARY KEY,
        condition_code TEXT NOT NULL,
        language_code TEXT NOT NULL,
        title TEXT NOT NULL,
        audio_stream_url TEXT NOT NULL,
        local_cache_path TEXT,
        duration_seconds INTEGER NOT NULL,
        downloaded_at TEXT NOT NULL
      )
    ''');

    // Performance Indexes
    await db.execute('CREATE INDEX idx_hh_village ON asha_households (village_lgd_code)');
    await db.execute('CREATE INDEX idx_beneficiary_hh ON asha_beneficiaries (household_id)');
    await db.execute('CREATE INDEX idx_care_gaps_hh ON asha_care_gaps (household_id, is_resolved)');
    await db.execute('CREATE INDEX idx_outbox_status ON asha_sync_outbox (status, created_at)');
  }

  // ===========================================================================
  // HOUSEHOLD & BENEFICIARY OPERATIONS
  // ===========================================================================

  Future<void> cacheHouseholds(List<AshaHousehold> households) async {
    final db = await database;
    final batch = db.batch();
    for (final hh in households) {
      batch.insert(
        'asha_households',
        hh.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      for (final member in hh.members) {
        batch.insert(
          'asha_beneficiaries',
          member.toMap(),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    }
    await batch.commit(noResult: true);
  }

  Future<List<AshaHousehold>> getHouseholdsByVillage(String villageLgdCode) async {
    final db = await database;
    final maps = await db.query(
      'asha_households',
      where: 'village_lgd_code = ?',
      whereArgs: [villageLgdCode],
    );
    if (maps.isEmpty) return [];

    List<AshaHousehold> list = [];
    for (final map in maps) {
      final hh = AshaHousehold.fromMap(map);
      // Fetch members
      final memberMaps = await db.query(
        'asha_beneficiaries',
        where: 'household_id = ?',
        whereArgs: [hh.id],
      );
      final members = memberMaps.map((m) => AshaBeneficiary.fromMap(m)).toList();
      list.add(hh.copyWith(members: members));
    }
    return list;
  }

  // ===========================================================================
  // CARE GAP OPERATIONS
  // ===========================================================================

  Future<void> cacheCareGaps(List<AshaCareGap> gaps) async {
    final db = await database;
    final batch = db.batch();
    for (final gap in gaps) {
      batch.insert(
        'asha_care_gaps',
        gap.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<List<AshaCareGap>> getCareGapsForHousehold(String householdId) async {
    final db = await database;
    final maps = await db.query(
      'asha_care_gaps',
      where: 'household_id = ? AND is_resolved = 0',
      whereArgs: [householdId],
      orderBy: 'days_overdue DESC',
    );
    return maps.map((m) => AshaCareGap.fromMap(m)).toList();
  }

  // ===========================================================================
  // OFFLINE MUTATION OUTBOX OPERATIONS
  // ===========================================================================

  Future<void> enqueueMutation(AshaSyncMutation mutation) async {
    final db = await database;
    await db.insert(
      'asha_sync_outbox',
      mutation.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<AshaSyncMutation>> getPendingMutations() async {
    final db = await database;
    final maps = await db.query(
      'asha_sync_outbox',
      where: 'status IN ("PENDING", "FAILED") AND retry_count < 5',
      orderBy: 'created_at ASC',
    );
    return maps.map((m) => AshaSyncMutation.fromMap(m)).toList();
  }

  Future<int> getPendingOutboxCount() async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as cnt FROM asha_sync_outbox WHERE status != "SYNCED"',
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  Future<void> updateMutationStatus(
    String mutationId,
    String status, {
    String? errorMessage,
  }) async {
    final db = await database;
    final nowIso = DateTime.now().toUtc().toIso8601String();
    await db.rawUpdate('''
      UPDATE asha_sync_outbox
      SET status = ?,
          retry_count = retry_count + 1,
          last_attempted_at = ?,
          error_message = ?
      WHERE mutation_id = ?
    ''', [status, nowIso, errorMessage, mutationId]);
  }

  Future<void> markMutationSynced(String mutationId) async {
    final db = await database;
    final nowIso = DateTime.now().toUtc().toIso8601String();
    await db.update(
      'asha_sync_outbox',
      {
        'status': 'SYNCED',
        'last_attempted_at': nowIso,
        'error_message': null,
      },
      where: 'mutation_id = ?',
      whereArgs: [mutationId],
    );
  }

  Future<void> clearAll() async {
    final db = await database;
    await db.delete('asha_households');
    await db.delete('asha_beneficiaries');
    await db.delete('asha_care_gaps');
    await db.delete('asha_sync_outbox');
    await db.delete('asha_cached_audio_education');
  }
}
