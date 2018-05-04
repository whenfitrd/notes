alter table users modify username varchar(200) not null unique;
alter table entries add createtime timestamp not null;
create table roleinfo(
    id int(6) not null primary key auto_increment,
    user_id int(6) not null,
    nickname varchar(20) not null,
    sex int(1),
    old int(2),
    city varchar(20),
    signature varchar(200)
)default charset=utf8;
