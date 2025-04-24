CREATE TABLE TRACK(
   TIME           DATE NOT NULL,
   TIMESTEMP           DATE NOT NULL,
   MAC            TEXT      NOT NULL,
   EVENT         TEXT      NOT NULL,
   POINT_X      INT      NOT NULL,
   POINT_Y      INT      NOT NULL,
   IMG_PATH  TEXT      NOT NULL,
   IMG_DATA  BLOB,
   FLAG   INT
);
CREATE INDEX idx_date ON TRACK(TIME);
CREATE INDEX idx_date ON TRACK(TIMESTEMP);