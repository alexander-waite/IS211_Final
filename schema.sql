CREATE TABLE part(
  part_id INT PRIMARY KEY NOT NULL,
  part_number INT NOT NULL,
  part_description TEXT,
  part_color TEXT,
  part_revision INT
);

CREATE TABLE machine(
  machine_id INT PRIMARY KEY NOT NULL,
  machine_location TEXT NOT NULL,
  machine_theme INT NOT NULL,
  machine_active INT
  machine_problem TEXT
);

CREATE TABLE tech(
  tech_id INT PRIMARY KEY NOT NULL,
  tech_password_ TEXT
);


CREATE TABLE tech_log(
  tech_log_id TEXT,
  tech_log_description TEXT,
  machine_id INT
  FOREIGN KEY (machine_id)
  	REFERENCES machine (machine_id),
  FOREIGN KEY (part)
  	REFERENCES part (part_number)
);

