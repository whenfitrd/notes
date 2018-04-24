create database notesdb character set 'utf8';
use notesdb;
create table entries(
    id int(6) not null primary key auto_increment,
    user_id int(6) not null,
    title varchar(200) not null,
    content varchar(1000) not null
)default charset=utf8;
create table users(
    id int(6) not null primary key auto_increment,
    username varchar(200) not null unique,
    password varchar(200) not null,
    aeskey varchar(50) not null
);
