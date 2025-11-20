CREATE TABLE public.authorization_key (
    auth_id  SERIAL PRIMARY KEY,
    auth_key VARCHAR(100) NOT NULL
);

CREATE TABLE public.barangay_admin (
    admin_id      SERIAL PRIMARY KEY,
    admin_fname   VARCHAR(40) NOT NULL,
    admin_lname   VARCHAR(40) NOT NULL,
    admin_mname   VARCHAR(40),
    admin_dob     DATE NOT NULL,
    admin_address VARCHAR(100) NOT NULL
);

CREATE TABLE public.facial_data (
    face_id    SERIAL PRIMARY KEY,
    face_image BYTEA NOT NULL,
    embedding  TEXT NOT NULL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    juv_id     INTEGER NOT NULL,
    CONSTRAINT fk_facialdata_juvenile
        FOREIGN KEY (juv_id) REFERENCES juvenile_profile(juv_id) ON DELETE CASCADE
);

CREATE TABLE public.juvenile_guardian_profile (
    grdn_id                  SERIAL PRIMARY KEY,
    grdn_full_name           VARCHAR(100) NOT NULL,
    grdn_juv_relationship    VARCHAR(50) NOT NULL,
    grdn_sex                 VARCHAR(10) NOT NULL,
    grdn_dob                 DATE,
    grdn_age                 INTEGER,
    grdn_civil_status        VARCHAR(20),
    grdn_citizenship         VARCHAR(50),
    grdn_occupation          VARCHAR(50),
    grdn_email_address       VARCHAR(100),
    grdn_contact_no          VARCHAR(20),
    grdn_residential_address VARCHAR(255),
    juv_id                   INTEGER NOT NULL,
    CONSTRAINT juvenile_guardian_profile_grdn_age_check CHECK (grdn_age > 0),
    CONSTRAINT juvenile_guardian_profile_grdn_sex_check CHECK (
        UPPER(grdn_sex) = ANY (ARRAY['MALE', 'FEMALE'])
    ),
    CONSTRAINT fk_guardian_juvenile
        FOREIGN KEY (juv_id) REFERENCES juvenile_profile(juv_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX idx_guardian_email_unique
ON juvenile_guardian_profile (grdn_email_address)
WHERE grdn_email_address IS NOT NULL AND grdn_email_address <> '';

CREATE TABLE public.juvenile_profile (
    juv_id             SERIAL PRIMARY KEY,
    juv_lname          VARCHAR(50) NOT NULL,
    juv_fname          VARCHAR(50) NOT NULL,
    juv_mname          VARCHAR(50),
    juv_suffix         VARCHAR(10),
    juv_sex            VARCHAR(10) NOT NULL,
    juv_gender         VARCHAR(20),
    juv_age            INTEGER,
    juv_dob            DATE NOT NULL,
    juv_place_of_birth VARCHAR(100),
    juv_citizenship    VARCHAR(50),
    juv_state_province VARCHAR(100),
    juv_municipality   VARCHAR(100),
    juv_barangay       VARCHAR(100),
    juv_street         VARCHAR(100),
    CONSTRAINT juvenile_profile_juv_age_check CHECK (juv_age > 0),
    CONSTRAINT juvenile_profile_juv_sex_check CHECK (
        UPPER(juv_sex) = ANY (ARRAY['MALE', 'FEMALE'])
    )
);

CREATE TABLE public.offense_information (
    offns_id                         SERIAL PRIMARY KEY,
    offns_type                       VARCHAR(100) NOT NULL,
    offns_case_record_no             VARCHAR(50) NOT NULL UNIQUE,
    offns_date_time                  TIMESTAMP NOT NULL,
    offns_location                   VARCHAR(255) NOT NULL,
    offns_description                TEXT,
    offns_complainant                VARCHAR(100),
    offns_barangay_officer_in_charge VARCHAR(100),
    juv_id                           INTEGER NOT NULL,
    CONSTRAINT fk_offense_juvenile
        FOREIGN KEY (juv_id) REFERENCES juvenile_profile(juv_id) ON DELETE CASCADE
);

CREATE TABLE public.users (
    user_id       SERIAL PRIMARY KEY,
    user_role     VARCHAR(10) NOT NULL,
    user_username VARCHAR(50) NOT NULL UNIQUE,
    user_password VARCHAR(500) NOT NULL,
    admin_id      INTEGER,
    CONSTRAINT users_user_role_check CHECK (
        user_role = ANY (ARRAY['Admin', 'admin', 'ADMIN'])
    ),
    CONSTRAINT users_admin_id_fkey
        FOREIGN KEY (admin_id) REFERENCES barangay_admin(admin_id)
);


-- Insert a sample authorization key (hashed for security)
INSERT INTO authorization_key (auth_key)
VALUES (crypt('authorization_key_12345', gen_salt('bf')));
