alter table users modify username varchar(200) not null unique;
alter table entries add createtime timestamp not null;
