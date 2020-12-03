CREATE TABLE part(
  part_id INT PRIMARY KEY NOT NULL,
  part_description TEXT,
  part_revision INT
);

CREATE TABLE machine(
  machine_id INT PRIMARY KEY NOT NULL,
  machine_location TEXT NOT NULL,
  machine_theme INT NOT NULL,
  machine_active INT
);

CREATE TABLE tech(
  tech_id INT PRIMARY KEY NOT NULL,
  tech_password TEXT,
  tech_name TEXT
);


CREATE TABLE workorder(
  workorder_id INT PRIMARY KEY NOT NULL,
  workorder_description TEXT,
  machine_id INT,
  part_id INT,
  FOREIGN KEY (machine_id)
  	REFERENCES machine (machine_id),
  FOREIGN KEY (part_id)
  	REFERENCES part (part_id)
);

INSERT INTO tech VALUES (1,'abc123','root');
INSERT INTO tech VALUES (1,'abc123','user')
