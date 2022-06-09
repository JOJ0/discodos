PRAGMA table_info(release);
.print ''
ALTER TABLE release DROP column m_atch_method;
.print ''
PRAGMA table_info(release);
