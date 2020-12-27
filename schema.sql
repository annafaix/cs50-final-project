CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT NOT NULL
);

CREATE TABLE fridge (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL, 
  date DATE NOT NULL,
  quantity INT NOT NULL , 
  unit TEXT NOT NULL,
  user TEXT NOT NULL
)

CREATE TABLE shoppinglist (
  name TEXT NOT NULL, 
  user TEXT NOT NULL
)