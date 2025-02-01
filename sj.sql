create table sj
(
    id           INTEGER
        constraint sj_pk
            primary key autoincrement,
    img_path     TEXT,
    img_name     TEXT,
    img_note     TEXT,
    img_seq      TEXT,
    url_get      TEXT,
    url_delete   TEXT,
    upload_by    TEXT,
    upload_time  TEXT,
    belong_group TEXT,
    is_deleted   INTEGER default 1,
    group_id     INTEGER
);

