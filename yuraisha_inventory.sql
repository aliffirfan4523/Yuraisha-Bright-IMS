-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 29, 2026 at 08:46 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `yuraisha_inventory`
--

-- --------------------------------------------------------

--
-- Table structure for table `audit_logs`
--

CREATE TABLE `audit_logs` (
  `audit_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(50) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `entity_id` int(11) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `audit_logs`
--

INSERT INTO `audit_logs` (`audit_id`, `user_id`, `action`, `entity_type`, `entity_id`, `details`, `created_at`) VALUES
(1, 1, 'login', 'user', 1, 'User signed in.', '2026-05-27 06:54:06'),
(2, 1, 'mark_all_read', 'notification', NULL, 'Marked all alerts as read.', '2026-05-27 06:54:22'),
(3, 1, 'mark_read', 'notification', 5, 'Marked alert as read.', '2026-05-27 06:54:25'),
(4, 1, 'mark_read', 'notification', 6, 'Marked alert as read.', '2026-05-27 06:54:26'),
(5, 1, 'mark_read', 'notification', 7, 'Marked alert as read.', '2026-05-27 06:54:27'),
(6, 1, 'mark_read', 'notification', 8, 'Marked alert as read.', '2026-05-27 06:54:28'),
(7, 1, 'mark_read', 'notification', 9, 'Marked alert as read.', '2026-05-27 06:54:28'),
(8, 1, 'mark_read', 'notification', 10, 'Marked alert as read.', '2026-05-27 06:54:29'),
(9, 1, 'mark_read', 'notification', 11, 'Marked alert as read.', '2026-05-27 06:54:29'),
(10, 1, 'mark_read', 'notification', 12, 'Marked alert as read.', '2026-05-27 06:54:29'),
(11, 1, 'mark_read', 'notification', 13, 'Marked alert as read.', '2026-05-27 06:54:30'),
(12, 1, 'login', 'user', 1, 'User signed in.', '2026-05-27 15:55:26'),
(13, 1, 'calculate', 'usage_calculation', 1, 'Production usage calculated.', '2026-05-27 15:58:19'),
(14, 1, 'calculate', 'usage_calculation', 2, 'Production usage calculated.', '2026-05-27 15:58:58'),
(15, 1, 'calculate', 'usage_calculation', 3, 'Production usage calculated.', '2026-05-27 15:59:12'),
(16, 1, 'calculate', 'usage_calculation', 4, 'Production usage calculated.', '2026-05-27 16:02:05'),
(17, 1, 'calculate', 'usage_calculation', 5, 'Production usage calculated.', '2026-05-27 16:03:54'),
(18, 1, 'calculate', 'usage_calculation', 6, 'Production usage calculated.', '2026-05-27 16:04:02'),
(19, 1, 'calculate', 'usage_calculation', 7, 'Production usage calculated.', '2026-05-27 16:04:05'),
(20, 1, 'calculate', 'usage_calculation', 8, 'Production usage calculated.', '2026-05-27 16:04:06'),
(21, 1, 'calculate', 'usage_calculation', 9, 'Production usage calculated.', '2026-05-27 16:04:27'),
(22, 1, 'calculate', 'usage_calculation', 10, 'Production usage calculated.', '2026-05-27 16:04:38'),
(23, 1, 'calculate', 'usage_calculation', 11, 'Production usage calculated.', '2026-05-27 16:04:43'),
(24, 1, 'create', 'client_transaction', 6, 'Transaction added. inbound: Test Supplier.', '2026-05-27 16:12:34'),
(25, 1, 'delete', 'client_transaction', 6, 'Deleted client transaction.', '2026-05-27 16:12:34'),
(26, 1, 'create', 'user', 2, 'Created user test1234.', '2026-05-27 16:15:13'),
(27, 1, 'logout', 'user', 1, 'User signed out.', '2026-05-27 16:15:32'),
(28, 2, 'login', 'user', 2, 'User signed in.', '2026-05-27 16:15:39'),
(29, 2, 'logout', 'user', 2, 'User signed out.', '2026-05-27 16:15:49'),
(30, 1, 'login', 'user', 1, 'User signed in.', '2026-05-27 16:15:51'),
(31, 1, 'quick_update', 'inventory_item', 5, 'Quantity set to 48.0.', '2026-05-27 16:28:04'),
(32, 1, 'quick_update', 'inventory_item', 5, 'Quantity set to 51.0.', '2026-05-27 16:28:12'),
(33, 1, 'mark_read', 'notification', 15, 'Marked alert as read.', '2026-05-27 16:28:19'),
(34, 1, 'calculate', 'usage_calculation', 12, 'Production usage calculated.', '2026-05-27 16:43:07'),
(35, 1, 'calculate', 'usage_calculation', 13, 'Production usage calculated.', '2026-05-27 16:43:07'),
(36, 1, 'calculate', 'usage_calculation', 14, 'Production usage calculated.', '2026-05-27 16:43:26'),
(37, 1, 'calculate', 'usage_calculation', 15, 'Production usage calculated.', '2026-05-27 16:48:15'),
(38, 1, 'produce', 'inventory_item', 7, 'Produced 1 10kg Box boxes.', '2026-05-27 17:01:01'),
(42, 1, 'login', 'user', 1, 'User signed in.', '2026-05-29 15:12:03'),
(43, 1, 'update', 'inventory_item', 14, 'Updated 10kg Plastic Packs.', '2026-05-29 15:12:26'),
(44, 1, 'quick_update', 'inventory_item', 14, 'Quantity set to 10000.0.', '2026-05-29 15:12:32'),
(45, 1, 'update', 'inventory_item', 13, 'Updated 10kg Empty Boxes.', '2026-05-29 15:12:44'),
(46, 1, 'update', 'inventory_item', 12, 'Updated 5kg Empty Boxes.', '2026-05-29 15:12:50'),
(47, 1, 'update', 'inventory_item', 11, 'Updated 3kg Empty Boxes.', '2026-05-29 15:12:52'),
(48, 1, 'update', 'inventory_item', 7, 'Updated Finished 10kg Box.', '2026-05-29 15:12:55'),
(49, 1, 'produce', 'inventory_item', 20, 'Produced 62 1kg Box boxes.', '2026-05-29 15:14:12'),
(50, 1, 'update', 'inventory_item', 7, 'Updated Finished 10kg Box.', '2026-05-29 15:14:33'),
(51, 1, 'update', 'inventory_item', 16, 'Updated 5kg Bottles.', '2026-05-29 15:14:59'),
(52, 1, 'update', 'inventory_item', 15, 'Updated 3kg Bottles.', '2026-05-29 15:15:04'),
(53, 1, 'produce', 'inventory_item', 21, 'Produced 96 3kg Box boxes.', '2026-05-29 15:15:58'),
(54, 1, 'produce', 'inventory_item', 22, 'Produced 110 5kg Box boxes.', '2026-05-29 15:16:09'),
(55, 1, 'produce', 'inventory_item', 7, 'Produced 50 10kg Box boxes.', '2026-05-29 15:16:22'),
(56, 1, 'mark_read', 'notification', 24, 'Marked alert as read.', '2026-05-29 15:21:21'),
(57, 1, 'mark_read', 'notification', 23, 'Marked alert as read.', '2026-05-29 15:21:21'),
(58, 1, 'mark_read', 'notification', 17, 'Marked alert as read.', '2026-05-29 15:21:22'),
(59, 1, 'mark_read', 'notification', 18, 'Marked alert as read.', '2026-05-29 15:21:22'),
(60, 1, 'mark_read', 'notification', 19, 'Marked alert as read.', '2026-05-29 15:21:22'),
(61, 1, 'mark_read', 'notification', 20, 'Marked alert as read.', '2026-05-29 15:21:23'),
(62, 1, 'mark_read', 'notification', 21, 'Marked alert as read.', '2026-05-29 15:21:23'),
(63, 1, 'mark_read', 'notification', 22, 'Marked alert as read.', '2026-05-29 15:21:23'),
(64, 1, 'mark_read', 'notification', 16, 'Marked alert as read.', '2026-05-29 15:21:23'),
(65, 1, 'create', 'client_transaction', 7, 'Transaction added. inbound: Ahmad Crops.', '2026-05-29 16:26:18'),
(66, 1, 'delete', 'client_transaction', 7, 'Deleted client transaction.', '2026-05-29 16:34:05'),
(67, 1, 'delete', 'supplier_delivery', 3, 'Deleted delivery record.', '2026-05-29 16:39:23'),
(68, 1, 'delete', 'supplier_delivery', 2, 'Deleted delivery record.', '2026-05-29 16:39:25'),
(69, 1, 'delete', 'supplier_delivery', 1, 'Deleted delivery record.', '2026-05-29 16:39:27'),
(70, 1, 'update', 'supplier_delivery', 4, 'Updated delivery record.', '2026-05-29 16:53:41'),
(71, 1, 'create', 'client_transaction', 8, 'Transaction added. inbound: Ahmad Crops.', '2026-05-29 16:54:14'),
(72, 1, 'create', 'client_transaction', 9, 'Transaction added. inbound: Ahmad Crops.', '2026-05-29 17:03:01'),
(73, 1, 'delete', 'client_transaction', 9, 'Deleted client transaction.', '2026-05-29 17:04:38'),
(74, 1, 'create', 'client_transaction', 10, 'Transaction added. inbound: Ahmad Crops.', '2026-05-29 17:04:48'),
(75, 1, 'mark_all_read', 'notification', NULL, 'Marked all alerts as read.', '2026-05-29 17:05:44'),
(76, 1, 'delete', 'client_transaction', 10, 'Deleted client transaction.', '2026-05-29 17:50:47'),
(77, 1, 'quick_update', 'inventory_item', 5, 'Quantity set to 51.0.', '2026-05-29 17:51:04'),
(78, 1, 'create', 'client_transaction', 11, 'Transaction added. inbound: Ahmad Crops.', '2026-05-29 17:55:10'),
(79, 1, 'update', 'supplier_delivery', 14, 'Updated delivery record.', '2026-05-29 17:55:24'),
(80, 1, 'delete', 'client_transaction', 8, 'Deleted client transaction.', '2026-05-29 17:57:52'),
(81, 1, 'quick_update', 'inventory_item', 5, 'Quantity set to 1051.0.', '2026-05-29 17:58:32'),
(82, 1, 'update', 'inventory_item', 2, 'Updated Steel Beam (SB-12M).', '2026-05-29 18:10:33'),
(83, 1, 'create', 'client_transaction', 12, 'Transaction added. inbound: Ahmad Crops.', '2026-05-29 18:24:43'),
(84, 1, 'create', 'user', 3, 'Created user test1235.', '2026-05-29 18:33:17'),
(85, 1, 'logout', 'user', 1, 'User signed out.', '2026-05-29 18:33:19'),
(86, 1, 'login', 'user', 1, 'User signed in.', '2026-05-29 18:33:32'),
(87, 1, 'logout', 'user', 1, 'User signed out.', '2026-05-29 18:33:39'),
(88, 3, 'login', 'user', 3, 'User signed in.', '2026-05-29 18:33:47'),
(89, 3, 'logout', 'user', 3, 'User signed out.', '2026-05-29 18:33:59'),
(90, 1, 'login', 'user', 1, 'User signed in.', '2026-05-29 18:34:01');

-- --------------------------------------------------------

--
-- Table structure for table `client_transactions`
--

CREATE TABLE `client_transactions` (
  `transaction_id` int(11) NOT NULL,
  `movement_type` enum('inbound','outbound') NOT NULL DEFAULT 'outbound',
  `item_id` int(11) DEFAULT NULL,
  `quantity` decimal(10,2) NOT NULL DEFAULT 0.00,
  `unit` varchar(20) NOT NULL DEFAULT 'Units',
  `client_name` varchar(100) NOT NULL,
  `boxes_sold` int(11) NOT NULL,
  `transaction_date` date NOT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `amount` decimal(10,2) NOT NULL DEFAULT 0.00,
  `payment_status` enum('pending','completed','failed') DEFAULT 'completed'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `client_transactions`
--

INSERT INTO `client_transactions` (`transaction_id`, `movement_type`, `item_id`, `quantity`, `unit`, `client_name`, `boxes_sold`, `transaction_date`, `notes`, `created_at`, `amount`, `payment_status`) VALUES
(1, 'outbound', 1, 50.00, 'Boxes', 'MegaCorp Manufacturing', 50, '2026-05-25', NULL, '2026-05-25 19:12:15', 14200.00, 'completed'),
(2, 'outbound', 1, 30.00, 'Boxes', 'Steelworks Global', 30, '2026-05-24', NULL, '2026-05-25 19:12:15', 8450.00, 'pending'),
(3, 'outbound', 1, 100.00, 'Boxes', 'Apex Logistics', 100, '2026-05-23', NULL, '2026-05-25 19:12:15', 22100.00, 'completed'),
(4, 'outbound', 1, 15.00, 'Boxes', 'Brighton Auto', 15, '2026-05-22', NULL, '2026-05-25 19:12:15', 3200.00, 'pending'),
(5, 'outbound', 1, 75.00, 'Boxes', 'MegaCorp Manufacturing', 75, '2026-05-21', NULL, '2026-05-25 19:12:15', 18750.00, 'completed'),
(11, 'inbound', 5, 1000.00, 'Units', 'Ahmad Crops', 1000, '2026-05-30', '', '2026-05-29 17:55:10', 15000.00, 'completed'),
(12, 'inbound', 11, 1000.00, 'Boxes', 'Ahmad Crops', 1000, '2026-05-30', '', '2026-05-29 18:24:43', 15000.00, 'completed');

-- --------------------------------------------------------

--
-- Table structure for table `inventory_categories`
--

CREATE TABLE `inventory_categories` (
  `category_key` varchar(50) NOT NULL,
  `category_label` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventory_categories`
--

INSERT INTO `inventory_categories` (`category_key`, `category_label`, `created_at`) VALUES
('bottle_3kg', '3kg Bottles', '2026-05-29 18:27:04'),
('bottle_5kg', '5kg Bottles', '2026-05-29 18:27:04'),
('box_10kg', '10kg Boxes', '2026-05-29 18:27:04'),
('box_1kg', '1kg Boxes', '2026-05-29 18:27:04'),
('box_3kg', '3kg Boxes', '2026-05-29 18:27:04'),
('box_5kg', '5kg Boxes', '2026-05-29 18:27:04'),
('cooking_oil', 'Cooking Oil', '2026-05-29 18:27:04'),
('defect', 'Defect Stock', '2026-05-29 18:27:04'),
('finished_goods', 'Finished Goods', '2026-05-29 18:27:04'),
('plastic_10kg', '10kg Plastic Packs', '2026-05-29 18:27:04'),
('plastic_1kg', '1kg Plastic Packs', '2026-05-29 18:27:04');

-- --------------------------------------------------------

--
-- Table structure for table `inventory_items`
--

CREATE TABLE `inventory_items` (
  `item_id` int(11) NOT NULL,
  `item_name` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `quantity` decimal(10,2) NOT NULL DEFAULT 0.00,
  `unit` varchar(20) NOT NULL,
  `minimum_stock` decimal(10,2) NOT NULL DEFAULT 0.00,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventory_items`
--

INSERT INTO `inventory_items` (`item_id`, `item_name`, `category`, `quantity`, `unit`, `minimum_stock`, `updated_at`) VALUES
(1, 'Industrial Valves (V-200)', 'box_1kg', 1239.00, 'Units', 200.00, '2026-05-29 16:53:41'),
(2, 'Steel Beam (SB-12M)', 'box_1kg', 99.00, 'Units', 100.00, '2026-05-29 18:10:33'),
(3, 'Lubricant Oil (LUB-50L)', 'cooking_oil', 508.00, 'Liters', 500.00, '2026-05-29 15:16:22'),
(4, 'Copper Wiring (CW-100M)', 'box_1kg', 12000.00, 'Meters', 2000.00, '2026-05-29 17:04:38'),
(5, 'Carbon Steel Pipe (CSP-092)', 'box_1kg', 1051.00, 'Units', 50.00, '2026-05-29 17:58:32'),
(6, 'Raw Plastic Pellets', 'plastic_1kg', 1.00, 'Kg', 500.00, '2026-05-29 15:14:12'),
(7, 'Finished 10kg Box', 'finished_goods', 50.00, 'Boxes', 0.00, '2026-05-29 15:16:22'),
(11, '3kg Empty Boxes', 'box_3kg', 9904.00, 'Boxes', 100.00, '2026-05-29 15:15:58'),
(12, '5kg Empty Boxes', 'box_5kg', 9890.00, 'Boxes', 100.00, '2026-05-29 15:16:09'),
(13, '10kg Empty Boxes', 'box_10kg', 9950.00, 'Boxes', 80.00, '2026-05-29 15:16:22'),
(14, '10kg Plastic Packs', 'plastic_10kg', 9950.00, 'Pcs', 100.00, '2026-05-29 15:16:22'),
(15, '3kg Bottles', 'bottle_3kg', 1616.00, 'Pcs', 250.00, '2026-05-29 15:15:58'),
(16, '5kg Bottles', 'bottle_5kg', 1780.00, 'Pcs', 200.00, '2026-05-29 15:16:09'),
(20, 'Finished 1kg Box', 'finished_goods', 62.00, 'Boxes', 0.00, '2026-05-29 15:14:12'),
(21, 'Finished 3kg Box', 'finished_goods', 96.00, 'Boxes', 0.00, '2026-05-29 15:15:58'),
(22, 'Finished 5kg Box', 'finished_goods', 110.00, 'Boxes', 0.00, '2026-05-29 15:16:09');

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `notification_id` int(11) NOT NULL,
  `title` varchar(150) NOT NULL,
  `message` text NOT NULL,
  `type` enum('low_stock','delayed_delivery','general') NOT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`notification_id`, `title`, `message`, `type`, `is_read`, `created_at`) VALUES
(1, 'Critical Stock Level', 'Carbon Steel Pipe (SKU: CSP-092) has dropped below minimum threshold.', 'low_stock', 1, '2026-05-25 19:12:15'),
(2, 'Delivery Arrived', 'Shipment #8821 from Global Metals Inc. is ready for inspection.', 'delayed_delivery', 1, '2026-05-25 19:12:15'),
(3, 'Quality Check Passed', 'Batch QA-442 components cleared for assembly line use.', 'general', 1, '2026-05-25 19:12:15'),
(4, 'Delayed Delivery: TRK-1', 'Delivery from Global Metals Inc. was expected on 2026-05-25 and is now delayed.', 'delayed_delivery', 1, '2026-05-27 06:33:59'),
(15, 'Low Stock: Carbon Steel Pipe (CSP-092)', 'Carbon Steel Pipe (CSP-092) is at 48.00 and has reached the minimum stock level of 50.00.', 'low_stock', 1, '2026-05-27 16:28:04'),
(16, 'Low Stock: Finished 10kg Box', 'Finished 10kg Box is at 0.00 and has reached the minimum stock level of 0.00.', 'low_stock', 1, '2026-05-27 17:03:51'),
(17, 'Low Stock: 3kg Empty Boxes', '3kg Empty Boxes is at 0.00 and has reached the minimum stock level of 100.00.', 'low_stock', 1, '2026-05-27 17:21:37'),
(18, 'Low Stock: 5kg Empty Boxes', '5kg Empty Boxes is at 0.00 and has reached the minimum stock level of 100.00.', 'low_stock', 1, '2026-05-27 17:21:37'),
(19, 'Low Stock: 10kg Empty Boxes', '10kg Empty Boxes is at 0.00 and has reached the minimum stock level of 80.00.', 'low_stock', 1, '2026-05-27 17:21:37'),
(20, 'Low Stock: 10kg Plastic Packs', '10kg Plastic Packs is at 0.00 and has reached the minimum stock level of 100.00.', 'low_stock', 1, '2026-05-27 17:21:37'),
(21, 'Low Stock: 3kg Bottles', '3kg Bottles is at 0.00 and has reached the minimum stock level of 250.00.', 'low_stock', 1, '2026-05-27 17:21:37'),
(22, 'Low Stock: 5kg Bottles', '5kg Bottles is at 0.00 and has reached the minimum stock level of 200.00.', 'low_stock', 1, '2026-05-27 17:21:37'),
(23, 'Delayed Delivery: TRK-3', 'Delivery from Chemical Corp was expected on 2026-05-28 and is now delayed.', 'delayed_delivery', 1, '2026-05-29 15:12:03'),
(24, 'Low Stock: Raw Plastic Pellets', 'Raw Plastic Pellets is at 1.00 and has reached the minimum stock level of 500.00.', 'low_stock', 1, '2026-05-29 15:14:12'),
(25, 'Delayed Delivery: TRK-4', 'Delivery from MegaCorp Manufacturing was expected on 2026-05-25 and is now delayed.', 'delayed_delivery', 1, '2026-05-29 16:53:41'),
(26, 'Low Stock: Steel Beam (SB-12M)', 'Steel Beam (SB-12M) is at 99.00 and has reached the minimum stock level of 100.00.', 'low_stock', 0, '2026-05-29 18:10:33');

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `report_id` int(11) NOT NULL,
  `report_type` enum('inventory','supplier','transaction','stock_summary') NOT NULL,
  `generated_by` int(11) DEFAULT NULL,
  `generated_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `supplier_deliveries`
--

CREATE TABLE `supplier_deliveries` (
  `delivery_id` int(11) NOT NULL,
  `movement_type` enum('inbound','outbound') NOT NULL DEFAULT 'inbound',
  `supplier_name` varchar(100) NOT NULL,
  `item_id` int(11) NOT NULL,
  `transaction_id` int(11) DEFAULT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `expected_date` date DEFAULT NULL,
  `received_date` date DEFAULT NULL,
  `status` enum('pending','received','delayed') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `supplier_deliveries`
--

INSERT INTO `supplier_deliveries` (`delivery_id`, `movement_type`, `supplier_name`, `item_id`, `transaction_id`, `quantity`, `expected_date`, `received_date`, `status`, `created_at`) VALUES
(4, 'outbound', 'MegaCorp Manufacturing', 1, 1, 50.00, '2026-05-25', NULL, 'delayed', '2026-05-29 16:32:18'),
(5, 'outbound', 'Steelworks Global', 1, 2, 30.00, '2026-05-24', '2026-05-24', 'received', '2026-05-29 16:32:18'),
(6, 'outbound', 'Apex Logistics', 1, 3, 100.00, '2026-05-23', '2026-05-23', 'received', '2026-05-29 16:32:18'),
(7, 'outbound', 'Brighton Auto', 1, 4, 15.00, '2026-05-22', '2026-05-22', 'received', '2026-05-29 16:32:18'),
(8, 'outbound', 'MegaCorp Manufacturing', 1, 5, 75.00, '2026-05-21', '2026-05-21', 'received', '2026-05-29 16:32:18'),
(14, 'inbound', 'Ahmad Crops', 5, 11, 1000.00, '2026-05-30', '2026-05-30', 'received', '2026-05-29 17:55:10'),
(15, 'inbound', 'Ahmad Crops', 11, 12, 1000.00, '2026-05-30', NULL, 'pending', '2026-05-29 18:24:43');

-- --------------------------------------------------------

--
-- Table structure for table `usage_calculations`
--

CREATE TABLE `usage_calculations` (
  `calculation_id` int(11) NOT NULL,
  `available_oil` decimal(10,2) NOT NULL,
  `available_plastic` decimal(10,2) NOT NULL,
  `boxes_can_produce` int(11) NOT NULL,
  `remaining_oil` decimal(10,2) NOT NULL,
  `remaining_plastic` decimal(10,2) NOT NULL,
  `calculated_by` int(11) DEFAULT NULL,
  `calculated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `box_size_kg` decimal(10,2) NOT NULL DEFAULT 1.00,
  `oil_ratio` decimal(10,2) NOT NULL DEFAULT 1.00,
  `plastic_ratio` decimal(10,2) NOT NULL DEFAULT 0.10,
  `units_per_box` int(11) NOT NULL DEFAULT 20,
  `available_boxes` decimal(10,2) NOT NULL DEFAULT 0.00,
  `remaining_boxes` decimal(10,2) NOT NULL DEFAULT 0.00,
  `record_type` varchar(20) NOT NULL DEFAULT 'estimate'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `usage_calculations`
--

INSERT INTO `usage_calculations` (`calculation_id`, `available_oil`, `available_plastic`, `boxes_can_produce`, `remaining_oil`, `remaining_plastic`, `calculated_by`, `calculated_at`, `box_size_kg`, `oil_ratio`, `plastic_ratio`, `units_per_box`, `available_boxes`, `remaining_boxes`, `record_type`) VALUES
(1, 4500.00, 1241.00, 9000, 0.00, 341.00, 1, '2026-05-27 15:58:19', 1.00, 1.00, 0.10, 20, 0.00, 0.00, 'estimate'),
(2, 4000.00, 1241.00, 8000, 0.00, 441.00, 1, '2026-05-27 15:58:58', 1.00, 1.00, 0.10, 20, 0.00, 0.00, 'estimate'),
(3, 2000.00, 1241.00, 4000, 0.00, 841.00, 1, '2026-05-27 15:59:12', 1.00, 1.00, 0.10, 20, 0.00, 0.00, 'estimate'),
(4, 100.00, 20.00, 20, 0.00, 10.00, 1, '2026-05-27 16:02:05', 5.00, 5.00, 0.50, 20, 0.00, 0.00, 'estimate'),
(5, 4500.00, 1241.00, 450, 0.00, 791.00, 1, '2026-05-27 16:03:54', 10.00, 10.00, 1.00, 20, 0.00, 0.00, 'estimate'),
(6, 4500.00, 1241.00, 900, 0.00, 791.00, 1, '2026-05-27 16:04:02', 5.00, 5.00, 0.50, 20, 0.00, 0.00, 'estimate'),
(7, 4500.00, 1241.00, 1500, 0.00, 791.00, 1, '2026-05-27 16:04:05', 3.00, 3.00, 0.30, 20, 0.00, 0.00, 'estimate'),
(8, 4500.00, 1241.00, 4500, 0.00, 791.00, 1, '2026-05-27 16:04:06', 1.00, 1.00, 0.10, 20, 0.00, 0.00, 'estimate'),
(9, 1500.00, 1241.00, 1500, 0.00, 1091.00, 1, '2026-05-27 16:04:27', 1.00, 1.00, 0.10, 20, 0.00, 0.00, 'estimate'),
(10, 4500.00, 641.00, 4500, 0.00, 191.00, 1, '2026-05-27 16:04:38', 1.00, 1.00, 0.10, 20, 0.00, 0.00, 'estimate'),
(11, 4500.00, 141.00, 1410, 3090.00, 0.00, 1, '2026-05-27 16:04:43', 1.00, 1.00, 0.10, 20, 0.00, 0.00, 'estimate'),
(12, 100.00, 100.00, 5, 0.00, 0.00, 1, '2026-05-27 16:43:07', 1.00, 20.00, 20.00, 20, 10.00, 5.00, 'estimate'),
(13, 100.00, 100.00, 10, 0.00, 90.00, 1, '2026-05-27 16:43:07', 10.00, 10.00, 1.00, 1, 10.00, 0.00, 'estimate'),
(14, 100.00, 100.00, 5, 0.00, 0.00, 1, '2026-05-27 16:43:26', 1.00, 20.00, 20.00, 20, 10.00, 5.00, 'estimate'),
(15, 4500.00, 1241.00, 450, 0.00, 791.00, 1, '2026-05-27 16:48:15', 10.00, 10.00, 1.00, 1, 14101.00, 13651.00, 'estimate'),
(16, 508.00, 1616.00, 42, 4.00, 1448.00, 1, '2026-05-29 18:36:06', 3.00, 12.00, 4.00, 4, 9904.00, 9862.00, 'estimate');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','manager') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `last_login_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `full_name`, `username`, `email`, `password_hash`, `role`, `created_at`, `is_active`, `last_login_at`) VALUES
(1, 'test', 'test123', 'test@test.com', 'scrypt:32768:8:1$vnrREvc1eAeezrU5$6bc8817020f6baaf29050086a307769882fd1871c27d10ba18392689e5cff3620067bc158a34c88ccc782279a0f2fa53491c97587921220f9364f77b4551513e', 'admin', '2026-05-25 15:42:56', 1, '2026-05-29 18:34:01'),
(2, 'test1', 'test1234', 'test1@test.com', 'scrypt:32768:8:1$s7t3ckZgeLwYU8ih$0fafb9535ac0867b5400a8e167a964eb2e5242e5dbec8ca11781158a009a64fabbc42241216f6bd3df4f3189efb8f01fb1853c80f38f9493a76bc8d9ebb6a8e6', 'manager', '2026-05-27 16:15:13', 1, '2026-05-27 16:15:39'),
(3, 'test2', 'test1235', 'test2@test.com', 'scrypt:32768:8:1$uSUo2HzWaJ1XTe7y$1a4d58d7f1cce55fd6a4bd84f1215a67e01617f13eaa0f9ee3f488241d27b8a49ed5194285d697a2ac8ac49dd5d39d63de1c8cfe3ecc9da75adc02064a219c9c', 'manager', '2026-05-29 18:33:17', 1, '2026-05-29 18:33:47');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD PRIMARY KEY (`audit_id`),
  ADD KEY `idx_audit_logs_user_date` (`user_id`,`created_at`);

--
-- Indexes for table `client_transactions`
--
ALTER TABLE `client_transactions`
  ADD PRIMARY KEY (`transaction_id`),
  ADD KEY `idx_transactions_status_date` (`payment_status`,`transaction_date`),
  ADD KEY `fk_transactions_item` (`item_id`),
  ADD KEY `idx_transactions_movement_item` (`movement_type`,`item_id`);

--
-- Indexes for table `inventory_categories`
--
ALTER TABLE `inventory_categories`
  ADD PRIMARY KEY (`category_key`);

--
-- Indexes for table `inventory_items`
--
ALTER TABLE `inventory_items`
  ADD PRIMARY KEY (`item_id`),
  ADD KEY `idx_inventory_category` (`category`),
  ADD KEY `idx_inventory_stock` (`quantity`,`minimum_stock`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`notification_id`),
  ADD UNIQUE KEY `uq_notifications_title_type` (`title`,`type`),
  ADD KEY `idx_notifications_read_type` (`is_read`,`type`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`report_id`),
  ADD KEY `generated_by` (`generated_by`);

--
-- Indexes for table `supplier_deliveries`
--
ALTER TABLE `supplier_deliveries`
  ADD PRIMARY KEY (`delivery_id`),
  ADD UNIQUE KEY `transaction_id` (`transaction_id`),
  ADD KEY `idx_deliveries_status_date` (`status`,`expected_date`),
  ADD KEY `idx_deliveries_item` (`item_id`);

--
-- Indexes for table `usage_calculations`
--
ALTER TABLE `usage_calculations`
  ADD PRIMARY KEY (`calculation_id`),
  ADD KEY `calculated_by` (`calculated_by`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `audit_logs`
--
ALTER TABLE `audit_logs`
  MODIFY `audit_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=91;

--
-- AUTO_INCREMENT for table `client_transactions`
--
ALTER TABLE `client_transactions`
  MODIFY `transaction_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `inventory_items`
--
ALTER TABLE `inventory_items`
  MODIFY `item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `notification_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `report_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `supplier_deliveries`
--
ALTER TABLE `supplier_deliveries`
  MODIFY `delivery_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `usage_calculations`
--
ALTER TABLE `usage_calculations`
  MODIFY `calculation_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `client_transactions`
--
ALTER TABLE `client_transactions`
  ADD CONSTRAINT `fk_transactions_item` FOREIGN KEY (`item_id`) REFERENCES `inventory_items` (`item_id`) ON DELETE SET NULL;

--
-- Constraints for table `reports`
--
ALTER TABLE `reports`
  ADD CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`generated_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `supplier_deliveries`
--
ALTER TABLE `supplier_deliveries`
  ADD CONSTRAINT `fk_deliveries_transaction` FOREIGN KEY (`transaction_id`) REFERENCES `client_transactions` (`transaction_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `supplier_deliveries_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory_items` (`item_id`);

--
-- Constraints for table `usage_calculations`
--
ALTER TABLE `usage_calculations`
  ADD CONSTRAINT `usage_calculations_ibfk_1` FOREIGN KEY (`calculated_by`) REFERENCES `users` (`user_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
