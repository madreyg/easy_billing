-- CREATE DATABASE billing;

CREATE TABLE public."user"
(
  id         INTEGER PRIMARY KEY NOT NULL,
  created_at TIMESTAMP           NOT NULL,
  name       VARCHAR(32) CHECK (name != '')
);
CREATE UNIQUE INDEX user_id_uindex
  ON public."user" (id);

CREATE TABLE public.invoice
(
  id          SERIAL PRIMARY KEY       NOT NULL,
  user_id     INT                      NOT NULL,
  currency_id INT                      NOT NULL,
  balance     NUMERIC(32, 2) DEFAULT 0 NOT NULL CHECK (balance >= 0),
  created_at  TIMESTAMP                NOT NULL,
  updated_at  TIMESTAMP,
  CONSTRAINT invoice_user_id_fk FOREIGN KEY (user_id) REFERENCES "user" (id)
);
CREATE UNIQUE INDEX invoice_id_uindex
  ON public.invoice (id);
COMMENT ON TABLE public.invoice IS 'status: active - 1, blocked - -1';

CREATE TABLE public.currency
(
  id       SERIAL PRIMARY KEY      NOT NULL,
  name     VARCHAR(8)              NOT NULL CHECK (name != ''),
  rate_usd NUMERIC(8, 2) DEFAULT 1 NOT NULL
);
CREATE UNIQUE INDEX currency_id_uindex
  ON public.currency (id);

ALTER TABLE public.invoice
  ADD CONSTRAINT invoice_currency_id_fk
FOREIGN KEY (currency_id) REFERENCES currency (id);

INSERT INTO currency (name, rate_usd) VALUES
  ('USD', 1),
  ('EUR', 0.90),
  ('CNY', 6.94);

CREATE TABLE public.transaction
(
  id              SERIAL PRIMARY KEY NOT NULL,
  uuid            UUID   NOT NULL,
  invoice_id_from INT,
  invoice_id_to   INT                NOT NULL,
  created_at      TIMESTAMP          NOT NULL,
  updated_at      TIMESTAMP,
  amount          NUMERIC(32, 2)     NOT NULL,
  status          INT DEFAULT 1
);
CREATE UNIQUE INDEX transaction_id_uindex
  ON public.transaction (id);
CREATE UNIQUE INDEX transaction_uuid_uindex
  ON public.transaction (uuid);
COMMENT ON TABLE public.transaction IS 'statuses: 0 - success, 1 - in process, -1 canceled';