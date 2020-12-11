About:
-
A database program to keep track of parts. It will allow the user to:


- Log into database through root menu (Username = root, password = abc123)
- Log into database as standard user (username = bob technician, password abc123)  
- Add Parts to inventory via one by one or use of csv file
- Add users to program
- add, edit and close Work-orders

____

Logging in
-
- Log into database through root menu (Username = root, password = abc123)
- Log into database as standard user (username = bob technician, password abc123)  
- username, user id, and most items are carried between pages via the flask [sessions](https://flask.palletsprojects.com/en/1.1.x/quickstart/#sessions) module. If your cookies don't work this page probably won't either.
- Main screen changes if it is a root user or a standard user
- There is no way to make another root user

---

Dashboard
-
- The dashboard will show buttons **Add New User** and **Add New Part** is you are logged in as the root user
- **New Work Order** will allow you to create a new work order
- **Edit / Close Existing Work Order** allows you to search for an existing work order based on a workorder ID
- **Log Off** ends your session and returns a text log off page
- **Add New User** and **Add New Part** do just that

New Work Order
-
- There are two machine locations in this database - **A15-02** and **B12-09**
- Descriptions require you to have a text / int string longer than 10 characters and use regex to determine acceptability
- **Is Part Needed?** is not necessary but you can add parts as you wish
- You can add parts but a sample part number is **1234**

Edit / Close Existing Work Order
-
- Modify Work Order requires a Workorder ID, these are generated at creation of a workorder
- *1, 2 and 3 are all sample Workorder IDs*
- The Workorder is auto-filled on submit and shows up on the Modify Work Order page
- Closing the order closes it on the sqlite database; the user will not be able to access it again

Root Menu
==

Add New User
-
- Add New User Requires a username and password.
    - There are no complexity requirements for the password

Add New Part
-
- Part ID is the part number
- Part Description is what the part is
- Part Revision is if the part was revised
- **Import Parts List**
    - Allows you to select a .csv file that is specifically formatted to add parts.
   - There is on added already under **test_part_sheet.csv**



Notes:
-

Locations:
- A15-02 and B12-09




