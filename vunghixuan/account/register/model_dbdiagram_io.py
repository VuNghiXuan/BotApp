"""


Table User {
  id integer [pk]
  username varchar [unique, not null]
  password varchar [not null]
  email varchar [unique]
  is_active boolean [default: true]
}

Table Group {
  id integer [pk]
  name varchar [unique, not null]
  description varchar
}

Table Roll {
  id integer [pk]
  name varchar [unique, not null]
  description varchar
}

Table Permission {
  id integer [pk]
  name varchar [unique, not null]
  description varchar
}

Table App {
  id integer [pk]
  name varchar [unique, not null]
  description varchar
}

Table Interface {
  id integer [pk]
  name varchar [unique, not null]
  description varchar
  app_id integer [ref: > App.id]
}

Table user_group {
  user_id integer [ref: > User.id]
  group_id integer [ref: > Group.id]
  PRIMARY KEY (user_id, group_id)
}

Table group_roll {
  group_id integer [ref: > Group.id]
  roll_id integer [ref: > Roll.id]
  PRIMARY KEY (group_id, roll_id)
}

Table roll_permission {
  roll_id integer [ref: > Roll.id]
  permission_id integer [ref: > Permission.id]
  PRIMARY KEY (roll_id, permission_id)
}

Table app_permission {
    app_id integer [ref: > App.id]
    permission_id integer [ref: > Permission.id]
    PRIMARY KEY (app_id, permission_id)
}

Table interface_permission {
    interface_id integer [ref: > Interface.id]
    permission_id integer [ref: > Permission.id]
    PRIMARY KEY (interface_id, permission_id)
}

"""