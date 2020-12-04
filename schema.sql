CREATE TABLE part(
  part_id INT PRIMARY KEY NOT NULL,
  part_description TEXT,
  part_revision INT
);

CREATE TABLE machine(
	machine_location text PRIMARY KEY,
   	machine_theme text,
	machine_active int DEFAULT 1
  );

CREATE TABLE tech(
  tech_id INT PRIMARY KEY NOT NULL,
  tech_password TEXT,
  tech_name TEXT
);


cREATE TABLE workorder(
workorder_id INT PRIMARY KEY,
workorder_description TEXT NOT NULL,
machine_location INT,
part_id INT,
status INT DEFAULT 0,
FOREIGN KEY (part_id)REFERENCES part (part_id),
FOREIGN KEY (machine_location) REFERENCES machine (machine_location))
;

INSERT INTO tech VALUES (1,'abc123','root');
INSERT INTO tech VALUES (1,'abc123','user')

INSERT INTO machine VALUES ("A15-02", "Golden Bananas",1);
INSERT INTO machine VALUES ("B12-09", "Bees!",0);

INSERT INTO part VALUES (1234, "Bill Validator",0);
INSERT INTO part VALUES (56789, "Win Switch",0);

INSERT INTO workorder(workorder_id,workorder_description,machine_location,part_id) VALUES (1,"description","A15-02",1234);
