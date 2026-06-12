--
-- PostgreSQL database dump
--

\restrict EauRw3Wmy3QVsYPP9SDEraIhc9fy9cMM0CGIGfemNmnOGG0eAdpoVhS11AO1ahe

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_settings (
    id integer NOT NULL,
    electricity_price_per_kw bigint
);


--
-- Name: app_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: app_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.app_settings_id_seq OWNED BY public.app_settings.id;


--
-- Name: store_chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.store_chat_messages (
    id integer NOT NULL,
    store_id integer NOT NULL,
    from_admin boolean NOT NULL,
    author_telegram_id bigint NOT NULL,
    body text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: store_chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.store_chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: store_chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.store_chat_messages_id_seq OWNED BY public.store_chat_messages.id;


--
-- Name: store_debt_payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.store_debt_payments (
    id integer NOT NULL,
    store_id integer NOT NULL,
    amount bigint NOT NULL,
    debt_after bigint NOT NULL,
    created_by_telegram_id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: store_debt_payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.store_debt_payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: store_debt_payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.store_debt_payments_id_seq OWNED BY public.store_debt_payments.id;


--
-- Name: store_electricity_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.store_electricity_logs (
    id integer NOT NULL,
    store_id integer NOT NULL,
    period_from timestamp with time zone NOT NULL,
    period_to timestamp with time zone NOT NULL,
    reading_before integer NOT NULL,
    reading_after integer NOT NULL,
    delta_kw integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: store_electricity_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.store_electricity_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: store_electricity_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.store_electricity_logs_id_seq OWNED BY public.store_electricity_logs.id;


--
-- Name: stores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stores (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    owner_phone character varying(16),
    owner_invite_token character varying(64),
    address text,
    store_date timestamp with time zone,
    monthly_amount bigint,
    electricity_kw integer,
    debt_tok integer NOT NULL,
    debt_balance bigint NOT NULL,
    rent_cycles_accrued integer NOT NULL,
    rent_reminder_sent_for timestamp with time zone,
    created_by_telegram_id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: stores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.stores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: stores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.stores_id_seq OWNED BY public.stores.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_id bigint NOT NULL,
    username character varying(255),
    full_name character varying(255),
    phone_number character varying(32),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: app_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings ALTER COLUMN id SET DEFAULT nextval('public.app_settings_id_seq'::regclass);


--
-- Name: store_chat_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_chat_messages ALTER COLUMN id SET DEFAULT nextval('public.store_chat_messages_id_seq'::regclass);


--
-- Name: store_debt_payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_debt_payments ALTER COLUMN id SET DEFAULT nextval('public.store_debt_payments_id_seq'::regclass);


--
-- Name: store_electricity_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_electricity_logs ALTER COLUMN id SET DEFAULT nextval('public.store_electricity_logs_id_seq'::regclass);


--
-- Name: stores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stores ALTER COLUMN id SET DEFAULT nextval('public.stores_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: app_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.app_settings (id, electricity_price_per_kw) FROM stdin;
1	1200
\.


--
-- Data for Name: store_chat_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.store_chat_messages (id, store_id, from_admin, author_telegram_id, body, created_at) FROM stdin;
7	5	t	687999627	Salom	2026-04-19 06:07:36.838426+00
8	5	t	687999627	Tokni to’labqo’ying	2026-04-19 06:09:53.437173+00
\.


--
-- Data for Name: store_debt_payments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.store_debt_payments (id, store_id, amount, debt_after, created_by_telegram_id, created_at) FROM stdin;
6	5	1000000	12000000	687999627	2026-04-19 06:11:00.92508+00
7	6	2000000	5300000	687999627	2026-04-21 06:24:18.645195+00
8	6	2000000	3300000	687999627	2026-04-28 11:44:27.019834+00
9	6	1500000	1800000	687999627	2026-04-28 11:44:53.248196+00
10	6	1800000	0	687999627	2026-04-28 11:59:20.79953+00
11	11	2000000	2000000	687999627	2026-04-28 12:16:34.699348+00
12	5	12000000	0	687999627	2026-04-28 12:37:48.970641+00
13	14	4300000	0	687999627	2026-04-28 13:44:04.835347+00
14	11	1000000	1000000	687999627	2026-04-30 13:44:15.256677+00
\.


--
-- Data for Name: store_electricity_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.store_electricity_logs (id, store_id, period_from, period_to, reading_before, reading_after, delta_kw, created_at) FROM stdin;
\.


--
-- Data for Name: stores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.stores (id, name, description, owner_phone, owner_invite_token, address, store_date, monthly_amount, electricity_kw, debt_tok, debt_balance, rent_cycles_accrued, rent_reminder_sent_for, created_by_telegram_id, created_at) FROM stdin;
6	Ayisha parda magazin	\N	+998952127272	inv_7502085a1f8ff12757c442fa8691a3b5	Stayanka	2026-04-16 19:00:00+00	7300000	500	0	7300000	2	\N	687999627	2026-04-19 07:50:39.674067+00
5	Osmonli kim magazini	\N	+998940188896	inv_51e20cf72e85a2ac8b034f431090e774	Stayanka	2026-04-04 19:00:00+00	13000000	27975	0	26000000	3	2026-06-10 19:01:30.305036+00	687999627	2026-04-19 06:04:54.154093+00
7	1001 maydachuda magazin	\N	+998952225588	inv_c356e50c74e8b0b584f5db740b37d23e	Stayanka	2026-04-09 19:00:00+00	3500000	130	0	10500000	3	2026-06-10 19:01:30.305036+00	687999627	2026-04-19 08:19:15.705491+00
14	Samsun elji bitaviy shamsidin	\N	+998952488860	inv_512c6c216047cea5fcecc0398e78b033	Stayanka	2026-03-31 19:00:00+00	4300000	100	0	8600000	3	2026-05-29 19:24:12.378238+00	687999627	2026-04-28 13:38:43.001719+00
3	Shois ayolar kiymi	\N	+998909700339	inv_694ba7535aa38acd74b5411d61a318de	Stayanka	2026-04-17 19:00:00+00	10000000	455	0	20000000	2	\N	687999627	2026-04-18 17:02:05.514147+00
9	Erkatoy kalaska magazin	\N	+998900757005	inv_6184c9e9ed0d501022eec12b86a97474	Stayanka	2026-04-24 19:00:00+00	4000000	100	0	8000000	2	\N	687999627	2026-04-28 09:40:15.42352+00
11	Asl chinilar muborak	\N	+998946142677	inv_907cf4a473559cdb8955a6778676361e	Stayanka	2026-04-24 19:00:00+00	4000000	200	0	5000000	2	2026-05-19 19:17:48.947745+00	687999627	2026-04-28 12:15:35.819399+00
12	Sof chinilar muxayo	\N	+998905223008	inv_137fac87ac37490aa8a4a677a1276f29	Stayanka	2026-04-24 19:00:00+00	4500000	100	0	9000000	2	\N	687999627	2026-04-28 12:21:44.557352+00
8	Salon krasata	\N	+998975534783	inv_f6a05abdfc5106906bf28f612da94241	Stayanka	2026-04-04 19:00:00+00	1000000	1000	0	3000000	3	\N	6645040376	2026-04-20 11:14:32.643796+00
10	Moshin zapchast dilmurod	\N	+998915501333	inv_a2ec5392bdb8b72f7d9c90d78656fb6f	Stayanka	2026-04-04 19:00:00+00	10000000	400	0	30000000	3	\N	687999627	2026-04-28 12:05:07.763579+00
13	Gopra zapchast xusi	\N	+998993777704	inv_9bdd4ae0378226118d6b545d69611972	Stayanka	2026-04-04 19:00:00+00	13000000	100	0	39000000	3	\N	687999627	2026-04-28 12:27:49.324125+00
15	Texnaxaus bitaviy o’ktam	\N	+998977862929	inv_4d2d042c1091f214c159bf6530112c2d	Stayanka	2026-04-04 19:00:00+00	11700000	100	0	35100000	3	\N	687999627	2026-05-02 14:22:38.592508+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, telegram_id, username, full_name, phone_number, created_at) FROM stdin;
1	5081646633	Mirshod_forward	Mirshodforward	\N	2026-04-18 07:56:04.151107+00
2	7547827275	StarsPaymeeSupport	StarsPaymee Support	+998941339383	2026-04-18 08:11:40.642578+00
3	6645040376	zakhidxon	zakhidxon⚜️	\N	2026-04-18 13:52:48.505147+00
4	7523523570	\N	♾️	+998946590921	2026-04-18 13:53:23.22465+00
5	7353066196	sherzod_2125	🐬	+998932252125	2026-04-18 13:54:05.438525+00
6	687999627	suxrob010101	Suxrob 🏴	\N	2026-04-18 16:57:59.858518+00
7	6727695062	\N	Хусниддин	+998940188896	2026-04-19 06:08:59.26631+00
8	73768864	\N	F.kamolov	\N	2026-04-19 07:11:49.255016+00
9	6398603004	Abdulatif_1001	Abdulatif Mengboyev	+998952225588	2026-04-19 08:22:40.831534+00
10	1658667044	\N	M	+998946142677	2026-04-28 12:17:25.38688+00
11	7145302749	\N	Shamsiddin	+998952488860	2026-04-28 13:42:57.838819+00
12	1331526283	\N	Dilmurod	\N	2026-05-02 08:13:23.36851+00
\.


--
-- Name: app_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_settings_id_seq', 1, false);


--
-- Name: store_chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.store_chat_messages_id_seq', 8, true);


--
-- Name: store_debt_payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.store_debt_payments_id_seq', 14, true);


--
-- Name: store_electricity_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.store_electricity_logs_id_seq', 5, true);


--
-- Name: stores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.stores_id_seq', 15, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 12, true);


--
-- Name: app_settings app_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT app_settings_pkey PRIMARY KEY (id);


--
-- Name: store_chat_messages store_chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_chat_messages
    ADD CONSTRAINT store_chat_messages_pkey PRIMARY KEY (id);


--
-- Name: store_debt_payments store_debt_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_debt_payments
    ADD CONSTRAINT store_debt_payments_pkey PRIMARY KEY (id);


--
-- Name: store_electricity_logs store_electricity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_electricity_logs
    ADD CONSTRAINT store_electricity_logs_pkey PRIMARY KEY (id);


--
-- Name: stores stores_owner_invite_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stores
    ADD CONSTRAINT stores_owner_invite_token_key UNIQUE (owner_invite_token);


--
-- Name: stores stores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stores
    ADD CONSTRAINT stores_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_store_chat_messages_store_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_store_chat_messages_store_id ON public.store_chat_messages USING btree (store_id);


--
-- Name: ix_store_debt_payments_store_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_store_debt_payments_store_id ON public.store_debt_payments USING btree (store_id);


--
-- Name: ix_store_electricity_logs_store_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_store_electricity_logs_store_id ON public.store_electricity_logs USING btree (store_id);


--
-- Name: ix_users_telegram_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_telegram_id ON public.users USING btree (telegram_id);


--
-- Name: store_chat_messages store_chat_messages_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_chat_messages
    ADD CONSTRAINT store_chat_messages_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.stores(id) ON DELETE CASCADE;


--
-- Name: store_debt_payments store_debt_payments_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_debt_payments
    ADD CONSTRAINT store_debt_payments_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.stores(id) ON DELETE CASCADE;


--
-- Name: store_electricity_logs store_electricity_logs_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.store_electricity_logs
    ADD CONSTRAINT store_electricity_logs_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.stores(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict EauRw3Wmy3QVsYPP9SDEraIhc9fy9cMM0CGIGfemNmnOGG0eAdpoVhS11AO1ahe

