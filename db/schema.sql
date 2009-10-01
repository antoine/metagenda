drop table if exists events;
-- the timestamp using a default or on update should be declared first....
create table events(
    id int(11) not null auto_increment,
    time_taken timestamp not null default current_timestamp,
    name varchar(250) not null,
    place varchar(250) not null,
    id_location int(11),
    time_start timestamp not null ,
    cancelled boolean default false,
    finished boolean default false,
    duplicateof int(11),
    url varchar(500),
    info varchar(500),
    style varchar(100),
    is_free int(1) not null default 0,
    taken_from varchar(100) not null,
    updated timestamp ,
    primary key(id)
);

drop table if exists locations;

create table locations(
    id int(11) not null auto_increment,
    comparison_name varchar(250) not null,
    `longitude` dec(10,6) NOT NULL,
    `latitude` dec(10, 6) NOT NULL,
    originalmapurl varchar(500) NOT NULL,
    primary key(id)
);



