CREATE TABLE track_ext_temp (
        d_release_id INTEGER NOT NULL,
        d_track_no TEXT NOT NULL,
        key TEXT,
        key_notes TEXT,
        bpm INTEGER,
        notes TEXT,
        PRIMARY KEY (d_release_id, d_track_no)
        );

INSERT INTO track_ext_temp
        SELECT d_release_id, d_track_no, key, key_notes, bpm, notes
        FROM track_ext;

--SELECT * FROM track_ext_temp;

DROP TABLE track_ext;

ALTER TABLE track_ext_temp RENAME TO track_ext;

--SELECT * FROM track_ext;



CREATE TABLE track_temp (
        d_release_id INTEGER NOT NULL,
        d_track_no TEXT NOT NULL,
        d_artist TEXT,
        d_track_name TEXT,
        import_timestamp TEXT,
        m_rec_id TEXT,
        m_match_method TEXT,
        m_match_time TEXT,
        PRIMARY KEY (d_release_id, d_track_no)
        );

INSERT INTO track_temp
        SELECT d_release_id, d_track_no, d_artist, d_track_name, import_timestamp,
        m_rec_id, m_match_method, m_match_time
        FROM track;

--SELECT * FROM track_temp;

DROP TABLE track;

ALTER TABLE track_temp RENAME TO track ;

--seLECT * FROM track;



