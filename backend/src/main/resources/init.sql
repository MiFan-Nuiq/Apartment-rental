CREATE DATABASE IF NOT EXISTS apartment_rental_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE apartment_rental_db;

DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS repairs;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS contracts;
DROP TABLE IF EXISTS apartments;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    real_name VARCHAR(50),
    phone VARCHAR(20),
    role VARCHAR(20),
    create_time DATETIME NOT NULL,
    update_time DATETIME
);

CREATE TABLE apartments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200),
    building VARCHAR(20),
    unit VARCHAR(20),
    room_number VARCHAR(20),
    area DECIMAL(10, 2),
    monthly_rent DECIMAL(10, 2),
    status VARCHAR(20),
    description VARCHAR(500),
    floor VARCHAR(20),
    landlord_id BIGINT,
    image_url VARCHAR(500),
    create_time DATETIME NOT NULL,
    update_time DATETIME,
    FOREIGN KEY (landlord_id) REFERENCES users(id)
);

CREATE TABLE contracts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_no VARCHAR(50) NOT NULL,
    apartment_id BIGINT NOT NULL,
    tenant_id BIGINT NOT NULL,
    landlord_id BIGINT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_rent DECIMAL(10, 2),
    deposit DECIMAL(10, 2),
    payment_method VARCHAR(20),
    status VARCHAR(20),
    remark VARCHAR(500),
    create_time DATETIME NOT NULL,
    update_time DATETIME,
    FOREIGN KEY (apartment_id) REFERENCES apartments(id),
    FOREIGN KEY (tenant_id) REFERENCES users(id),
    FOREIGN KEY (landlord_id) REFERENCES users(id)
);

CREATE TABLE appointments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    apartment_id BIGINT NOT NULL,
    tenant_id BIGINT NOT NULL,
    landlord_id BIGINT NOT NULL,
    appointment_time DATETIME NOT NULL,
    status VARCHAR(20),
    remark VARCHAR(500),
    reply VARCHAR(500),
    create_time DATETIME NOT NULL,
    update_time DATETIME,
    FOREIGN KEY (apartment_id) REFERENCES apartments(id),
    FOREIGN KEY (tenant_id) REFERENCES users(id),
    FOREIGN KEY (landlord_id) REFERENCES users(id)
);

CREATE TABLE payments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    payment_no VARCHAR(50) NOT NULL,
    contract_id BIGINT NOT NULL,
    tenant_id BIGINT NOT NULL,
    landlord_id BIGINT NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(10, 2),
    payment_type VARCHAR(20),
    payment_method VARCHAR(20),
    status VARCHAR(20),
    remark VARCHAR(500),
    create_time DATETIME NOT NULL,
    update_time DATETIME,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (tenant_id) REFERENCES users(id),
    FOREIGN KEY (landlord_id) REFERENCES users(id)
);

CREATE TABLE repairs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    apartment_id BIGINT NOT NULL,
    contract_id BIGINT NOT NULL,
    tenant_id BIGINT NOT NULL,
    landlord_id BIGINT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description VARCHAR(1000),
    status VARCHAR(20),
    reply VARCHAR(500),
    create_time DATETIME NOT NULL,
    update_time DATETIME,
    FOREIGN KEY (apartment_id) REFERENCES apartments(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (tenant_id) REFERENCES users(id),
    FOREIGN KEY (landlord_id) REFERENCES users(id)
);

CREATE TABLE messages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    content VARCHAR(2000),
    sender_id BIGINT,
    receiver_id BIGINT,
    type VARCHAR(20),
    target_role VARCHAR(20),
    status VARCHAR(20),
    create_time DATETIME NOT NULL,
    update_time DATETIME,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

INSERT INTO apartments (name, address, building, unit, room_number, area, monthly_rent, status, description, floor, landlord_id, create_time, update_time) VALUES
('阳光花园A栋101', '北京市朝阳区阳光花园小区', 'A栋', '1单元', '101', 85.50, 3500.00, '空置', '精装修，南北通透，采光好', '1层', 2, NOW(), NOW()),
('阳光花园A栋102', '北京市朝阳区阳光花园小区', 'A栋', '1单元', '102', 75.00, 3000.00, '空置', '简装修，适合年轻人居住', '1层', 2, NOW(), NOW()),
('阳光花园A栋201', '北京市朝阳区阳光花园小区', 'A栋', '2单元', '201', 90.00, 3800.00, '空置', '精装修，带阳台，视野开阔', '2层', 2, NOW(), NOW()),
('阳光花园B栋101', '北京市朝阳区阳光花园小区', 'B栋', '1单元', '101', 95.00, 4200.00, '空置', '豪华装修，带车位', '1层', 2, NOW(), NOW()),
('翠湖名苑1号楼501', '北京市海淀区翠湖名苑', '1号楼', '', '501', 120.00, 6500.00, '空置', '高端公寓，湖景房', '5层', 2, NOW(), NOW()),
('翠湖名苑1号楼502', '北京市海淀区翠湖名苑', '1号楼', '', '502', 110.00, 5800.00, '空置', '高端公寓，视野开阔', '5层', 2, NOW(), NOW()),
('翠湖名苑2号楼301', '北京市海淀区翠湖名苑', '2号楼', '', '301', 100.00, 5000.00, '空置', '精装修，环境优美', '3层', 2, NOW(), NOW()),
('翠湖名苑2号楼302', '北京市海淀区翠湖名苑', '2号楼', '', '302', 95.00, 4800.00, '空置', '精装修，交通便利', '3层', 2, NOW(), NOW());
