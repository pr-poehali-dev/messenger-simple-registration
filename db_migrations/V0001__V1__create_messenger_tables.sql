
CREATE TABLE IF NOT EXISTS t_p28244525_messenger_simple_reg.users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS t_p28244525_messenger_simple_reg.sessions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES t_p28244525_messenger_simple_reg.users(id),
  token VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS t_p28244525_messenger_simple_reg.contacts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES t_p28244525_messenger_simple_reg.users(id),
  contact_id INTEGER REFERENCES t_p28244525_messenger_simple_reg.users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, contact_id)
);

CREATE TABLE IF NOT EXISTS t_p28244525_messenger_simple_reg.chats (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  is_group BOOLEAN DEFAULT FALSE,
  created_by INTEGER REFERENCES t_p28244525_messenger_simple_reg.users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS t_p28244525_messenger_simple_reg.chat_members (
  id SERIAL PRIMARY KEY,
  chat_id INTEGER REFERENCES t_p28244525_messenger_simple_reg.chats(id),
  user_id INTEGER REFERENCES t_p28244525_messenger_simple_reg.users(id),
  joined_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS t_p28244525_messenger_simple_reg.messages (
  id SERIAL PRIMARY KEY,
  chat_id INTEGER REFERENCES t_p28244525_messenger_simple_reg.chats(id),
  sender_id INTEGER REFERENCES t_p28244525_messenger_simple_reg.users(id),
  text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
