CREATE TABLE IF NOT EXISTS parsed_emails (
    id SERIAL PRIMARY KEY,
    input_text TEXT NOT NULL,
    reply_type VARCHAR(50),
    proposed_time TIMESTAMP,
    meeting_link TEXT,
    delegate_to VARCHAR(255),
    additional_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 