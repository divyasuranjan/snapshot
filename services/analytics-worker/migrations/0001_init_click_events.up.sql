CREATE TABLE IF NOT EXISTS click_events (
    id            BIGSERIAL PRIMARY KEY,
    stream_id     VARCHAR(32) NOT NULL UNIQUE,
    code          VARCHAR(16) NOT NULL,
    clicked_at    TIMESTAMPTZ NOT NULL,
    ip            TEXT,
    user_agent    TEXT,
    referrer      TEXT,
    referrer_host VARCHAR(255),
    device_type   VARCHAR(20),
    browser       VARCHAR(64),
    os            VARCHAR(64),
    country       VARCHAR(64),
    country_code  VARCHAR(2),
    region        VARCHAR(64),
    city          VARCHAR(64),
    lat           DOUBLE PRECISION,
    lon           DOUBLE PRECISION,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_click_events_code ON click_events (code);
CREATE INDEX IF NOT EXISTS idx_click_events_clicked_at ON click_events (clicked_at);
CREATE INDEX IF NOT EXISTS idx_click_events_country_code ON click_events (country_code);
